"""
Structured logging configuration using structlog.

Output format:
  - Development: coloured, human-readable console output
  - Production / CI: JSON lines (one log record per line, machine-parseable)

Usage:
  import structlog
  logger = structlog.get_logger(__name__)
  logger.info("event name", key=value, ...)

Request-scoped context (request_id, user_id, workspace_id) is injected via
structlog.contextvars and automatically included in every log line within the
same async task/coroutine chain.
"""
from __future__ import annotations

import logging
import sys

import structlog

from app.core.config import settings


def setup_logging() -> None:
    """Configure structlog and stdlib logging. Call once at application startup."""
    log_level = logging.getLevelName(settings.log_level.upper())

    is_production = settings.environment == "production"

    shared_processors: list[structlog.types.Processor] = [
        # Inject request-scoped context (request_id etc.) from contextvars
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_production:
        # JSON output for log aggregators (Datadog, Grafana Loki, etc.)
        processors: list[structlog.types.Processor] = [
            *shared_processors,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Pretty console output for local development
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Also configure stdlib logging so third-party libraries (SQLAlchemy,
    # uvicorn, httpx) emit structured logs through the same pipeline.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Suppress noisy loggers in production
    if is_production:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
