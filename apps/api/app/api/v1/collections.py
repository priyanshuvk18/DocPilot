"""
Collections API — Phase 2 (stub for Phase 0).
GET/POST /v1/collections
PATCH/DELETE /v1/collections/{id}
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.security import CurrentUser

router = APIRouter()


@router.get("", summary="List collections")
async def list_collections(user: CurrentUser) -> dict[str, str]:
    """Implemented in Phase 2."""
    return {"status": "not_implemented", "phase": "2"}
