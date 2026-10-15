"""
Pytest configuration and fixtures.
Ensures app directory is on sys.path and provides shared test fixtures.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add apps/api to sys.path so 'app' is importable from anywhere
api_root = Path(__file__).resolve().parent.parent
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Create a fresh app instance for each test with auth disabled."""
    os.environ["AUTH_DISABLED"] = "true"
    os.environ["ENVIRONMENT"] = "test"

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
