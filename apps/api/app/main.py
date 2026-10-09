"""
DocPilot API — Application factory.

Wiring order:
  1. Logging (structlog)
  2. Sentry (error tracking)
  3. Middleware: CORS, request-ID, security headers
  4. Routes: /v1 router
  5. Exception handlers: RFC 7807 problem responses
"""
from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.logging import setup_logging

logger = structlog.get_logger(__name__)


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown event handler."""
    # Startup
    setup_logging()

    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.2,
        )
        logger.info("Sentry initialized")

    logger.info(
        "DocPilot API starting",
        environment=settings.environment,
        auth_disabled=settings.auth_disabled,
    )

    yield

    # Shutdown
    logger.info("DocPilot API shutting down")


# ─── App factory ──────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="DocPilot API",
        description=(
            "DocPilot — AI workspace assistant. "
            "RAG over your documents with verified citations, "
            "agent tool-use with human confirmation, and built-in evals."
        ),
        version="0.1.0",
        # Disable interactive docs in production to reduce attack surface
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        openapi_url="/openapi.json" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # ── CORS ────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id", "X-Response-Time-Ms", "X-RateLimit-Limit",
                        "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )

    # ── Request-ID + timing middleware ──────────────────────────────────────
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next: ...) -> Response:  # type: ignore[type-arg]
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Bind request context for structured logging
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000)

        response.headers["X-Request-Id"] = request_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)

        # Security headers (supplement Vercel/CDN headers in production)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        logger.info(
            "request completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response

    # ── Routes ──────────────────────────────────────────────────────────────
    app.include_router(api_v1_router, prefix="/v1")

    # ── Global exception handlers (RFC 7807 Problem Details) ────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "Unhandled exception",
            exc_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={
                "type": "https://docpilot.dev/errors/internal-server-error",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred. The error has been logged.",
                "instance": str(request.url),
            },
        )

    return app


# Module-level app instance (used by uvicorn / gunicorn)
app = create_app()
