"""
ARQ worker configuration.

ARQ is an async Redis queue library. Workers are separate processes
from the API server — heavy tasks (ingestion, evals, cleanup) run here
without blocking chat responses.

Start a worker:
    make api-worker
    # or: uv run arq app.workers.settings.WorkerSettings

Architecture.md §1: Workers → Redis queue → Postgres + Object Storage
"""
from __future__ import annotations

from arq.connections import RedisSettings

from app.core.config import settings
from app.workers import tasks


class WorkerSettings:
    """
    ARQ worker configuration class.
    ARQ discovers this class by name: `arq app.workers.settings.WorkerSettings`
    """

    # Tasks this worker can handle
    functions = [
        tasks.ingest_document,
        tasks.run_eval_set,
        tasks.cleanup_failed_documents,
    ]

    # Redis connection
    redis_settings = RedisSettings.from_dsn(settings.redis_url)

    # Concurrency — keep ingestion from overwhelming the DB or embedding API
    max_jobs = 10

    # Job timeout (seconds) — fail jobs that take longer than this
    job_timeout = 300  # 5 minutes

    # Retry settings
    max_tries = 3

    # Health check — ARQ writes a heartbeat to Redis; monitors can check it
    health_check_interval = 60

    # Run startup/shutdown hooks
    on_startup = tasks.worker_startup
    on_shutdown = tasks.worker_shutdown
