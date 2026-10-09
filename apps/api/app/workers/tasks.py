"""
ARQ background task definitions.

Each function decorated with async def is a task that the API can enqueue
and the worker will execute. Tasks must be idempotent — they may be retried
on failure.

Tasks defined here (implemented fully in later phases):
  Phase 2: ingest_document
  Phase 5: run_eval_set
  Phase 0: cleanup_failed_documents (simple, used to test the worker)
"""
from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ─── Lifecycle hooks ───────────────────────────────────────────────────────────

async def worker_startup(ctx: dict[str, Any]) -> None:
    """Called once when the worker process starts."""
    from app.core.logging import setup_logging
    setup_logging()
    logger.info("DocPilot worker starting")
    # Phase 1+: initialize DB session pool here
    # ctx["db_pool"] = await create_pool(settings.database_url)


async def worker_shutdown(ctx: dict[str, Any]) -> None:
    """Called once when the worker process shuts down."""
    logger.info("DocPilot worker shutting down")
    # Phase 1+: close DB session pool here


# ─── Tasks ────────────────────────────────────────────────────────────────────

async def ingest_document(ctx: dict[str, Any], document_id: str) -> dict[str, Any]:
    """
    Full document ingestion pipeline — Phase 2.

    Steps:
      1. Verify magic bytes (type safety)
      2. Parse (PyMuPDF for PDF, python-docx for DOCX, chardet for TXT/MD)
      3. Clean (strip headers/footers, normalize whitespace)
      4. Chunk (≈500 tokens, 80 overlap, heading-aware, metadata: page + heading)
      5. Embed (Voyage AI batched)
      6. Insert chunks + tsvector into Postgres
      7. Update document.status = 'ready'
      8. Write audit_log entry

    Idempotent: re-running with the same document_id is safe.
    """
    logger.info("ingest_document task received (Phase 2 not yet implemented)", document_id=document_id)
    return {"status": "not_implemented", "document_id": document_id}


async def run_eval_set(ctx: dict[str, Any], eval_set_id: str, config: dict[str, Any]) -> dict[str, Any]:
    """
    Run a golden-set evaluation — Phase 5.

    Replays each Q&A case through the same RAG pipeline (pinned config),
    computes faithfulness / relevance / citation validity via Ragas + DeepEval,
    writes eval_results, updates eval_runs.summary.
    """
    logger.info("run_eval_set task received (Phase 5 not yet implemented)", eval_set_id=eval_set_id)
    return {"status": "not_implemented", "eval_set_id": eval_set_id}


async def cleanup_failed_documents(ctx: dict[str, Any]) -> dict[str, Any]:
    """
    Periodic cleanup — removes document rows stuck in 'failed' for > 24 hours.
    Implemented in Phase 0 as a simple sanity-check task.
    """
    logger.info("cleanup_failed_documents: no-op in Phase 0")
    return {"cleaned": 0}
