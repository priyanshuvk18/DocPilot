"""
Workspaces API — Phase 1 (stub for Phase 0).
GET  /v1/workspaces/me
POST /v1/workspaces/{id}/members
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.security import CurrentUser

router = APIRouter()


@router.get("/me", summary="Get current user's workspace membership")
async def get_my_workspace(user: CurrentUser) -> dict[str, str]:
    """Returns the workspace the current user belongs to. Implemented in Phase 1."""
    return {"status": "not_implemented", "phase": "1"}
