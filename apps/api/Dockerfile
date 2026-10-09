# DocPilot API — Dockerfile
# Multi-stage build: slim final image, no dev tools in production.
# Base image: official Python 3.12 slim (Debian bookworm)

# ─── Stage 1: dependency builder ─────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# System deps needed to compile some Python packages (pymupdf, asyncpg, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency manifests first for layer caching
COPY pyproject.toml ./

# Install dependencies into /app/.venv (no --system so we get a clean venv)
RUN uv venv .venv && \
    uv sync --no-dev

# ─── Stage 2: production image ───────────────────────────────────────────────
FROM python:3.12-slim AS production

# Minimal runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN groupadd --gid 1001 docpilot && \
    useradd --uid 1001 --gid docpilot --shell /bin/bash --create-home docpilot

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv .venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy application source
COPY --chown=docpilot:docpilot app/ ./app/
COPY --chown=docpilot:docpilot alembic.ini ./

USER docpilot

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Run with gunicorn + uvicorn workers in production
# Override CMD in docker-compose for worker containers
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--timeout", "120", \
     "--keep-alive", "5"]
