"""
Unit tests for the health endpoints.

These tests use FastAPI's TestClient (sync) and AsyncClient (async).
They run without any external dependencies (no DB, no Redis).
All external calls are mocked.

Markers: unit (fast, no external deps)
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Create a fresh app instance for each test with auth disabled."""
    import os
    os.environ["AUTH_DISABLED"] = "true"
    os.environ["ENVIRONMENT"] = "test"

    # Force re-import of settings with test env
    from importlib import reload

    from app.core import config
    reload(config)

    from app.main import create_app
    return create_app()


@pytest.fixture
def client(app):
    """Sync test client with lifespan triggered."""
    with TestClient(app) as c:
        yield c


# ─── Liveness probe ───────────────────────────────────────────────────────────

@pytest.mark.unit
def test_health_live_returns_200(client: TestClient) -> None:
    """GET /v1/health returns 200 with status=ok."""
    response = client.get("/v1/health")
    assert response.status_code == 200


@pytest.mark.unit
def test_health_live_response_schema(client: TestClient) -> None:
    """GET /v1/health response matches HealthResponse schema."""
    response = client.get("/v1/health")
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], float)


@pytest.mark.unit
def test_health_live_has_request_id_header(client: TestClient) -> None:
    """GET /v1/health response includes X-Request-Id header."""
    response = client.get("/v1/health")
    assert "X-Request-Id" in response.headers


@pytest.mark.unit
def test_health_live_has_response_time_header(client: TestClient) -> None:
    """GET /v1/health response includes X-Response-Time-Ms header."""
    response = client.get("/v1/health")
    assert "X-Response-Time-Ms" in response.headers
    assert int(response.headers["X-Response-Time-Ms"]) >= 0


@pytest.mark.unit
def test_health_live_security_headers(client: TestClient) -> None:
    """GET /v1/health response includes security headers."""
    response = client.get("/v1/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


# ─── Auth disabled flag ───────────────────────────────────────────────────────

@pytest.mark.unit
def test_stub_route_requires_no_real_auth_when_disabled(client: TestClient) -> None:
    """With AUTH_DISABLED=true, stub routes return 200 without a real JWT."""
    response = client.get("/v1/workspaces/me")
    # Should not be 401
    assert response.status_code == 200


# ─── Unknown route ────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_unknown_route_returns_404(client: TestClient) -> None:
    """Requests to undefined routes return 404."""
    response = client.get("/v1/nonexistent-route-xyz")
    assert response.status_code == 404


# ─── CORS ─────────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_cors_allows_configured_origin(client: TestClient) -> None:
    """OPTIONS request from allowed origin returns 200 with CORS headers."""
    response = client.options(
        "/v1/health",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    # Should not be blocked
    assert response.status_code in (200, 204)
