"""
Health check endpoint.

GET /v1/health — liveness (no auth, no DB check)
GET /v1/health/ready — readiness (checks DB + Redis connectivity)

Used by:
  - Docker health checks
  - Fly.io HTTP health checks
  - Load balancer probes
  - CI smoke tests
"""
from __future__ import annotations

import time

import structlog
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()

_start_time = time.time()


class HealthResponse(BaseModel):
    """Liveness response schema."""

    status: str
    version: str
    environment: str
    uptime_seconds: float


class ReadinessResponse(BaseModel):
    """Readiness response schema — checks downstream dependencies."""

    status: str
    version: str
    environment: str
    checks: dict[str, str]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns 200 if the API process is alive. No dependency checks.",
    status_code=status.HTTP_200_OK,
)
async def health_live() -> HealthResponse:
    """Liveness probe — always returns 200 if the process is running."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        environment=settings.environment,
        uptime_seconds=round(time.time() - _start_time, 2),
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description=(
        "Returns 200 if all critical dependencies (Postgres, Redis) are reachable. "
        "Returns 503 if any dependency is down."
    ),
)
async def health_ready() -> JSONResponse:
    """
    Readiness probe — checks Postgres and Redis connectivity.
    Returns 503 with a descriptive payload if any check fails.
    """
    checks: dict[str, str] = {}
    all_ok = True

    # ── Postgres ─────────────────────────────────────────────────────────
    try:
        import asyncpg
        conn = await asyncpg.connect(
            settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
            timeout=3,
        )
        await conn.execute("SELECT 1")
        await conn.close()
        checks["postgres"] = "ok"
    except Exception as exc:
        checks["postgres"] = f"error: {exc}"
        all_ok = False
        logger.warning("Readiness: Postgres check failed", error=str(exc))

    # ── Redis ─────────────────────────────────────────────────────────────
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url, socket_timeout=2)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"
        all_ok = False
        logger.warning("Readiness: Redis check failed", error=str(exc))

    http_status = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    payload = ReadinessResponse(
        status="ok" if all_ok else "degraded",
        version="0.1.0",
        environment=settings.environment,
        checks=checks,
    )
    return JSONResponse(status_code=http_status, content=payload.model_dump())
