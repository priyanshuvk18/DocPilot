"""
Chat API — Phase 3 (stub for Phase 0).
POST /v1/chat/threads
GET  /v1/chat/threads
GET  /v1/chat/threads/{id}
POST /v1/chat/threads/{id}/messages  (SSE streaming)
DELETE /v1/chat/threads/{id}
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.security import CurrentUser

router = APIRouter()


@router.post("/threads", summary="Create a new chat thread")
async def create_thread(user: CurrentUser) -> dict[str, str]:
    """Implemented in Phase 3."""
    return {"status": "not_implemented", "phase": "3"}


@router.get("/threads", summary="List chat threads")
async def list_threads(user: CurrentUser) -> dict[str, str]:
    """Implemented in Phase 3."""
    return {"status": "not_implemented", "phase": "3"}
