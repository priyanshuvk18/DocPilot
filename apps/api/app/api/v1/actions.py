"""Actions API stub — Phase 4."""
from __future__ import annotations

from fastapi import APIRouter
from app.core.security import CurrentUser

router = APIRouter()


@router.get("", summary="List proposed/confirmed actions")
async def list_actions(user: CurrentUser) -> dict[str, str]:
    """Implemented in Phase 4."""
    return {"status": "not_implemented", "phase": "4"}


@router.post("/{action_id}/confirm", summary="Confirm a proposed agent action")
async def confirm_action(action_id: str, user: CurrentUser) -> dict[str, str]:
    """Implemented in Phase 4."""
    return {"status": "not_implemented", "phase": "4"}


@router.post("/{action_id}/reject", summary="Reject a proposed agent action")
async def reject_action(action_id: str, user: CurrentUser) -> dict[str, str]:
    """Implemented in Phase 4."""
    return {"status": "not_implemented", "phase": "4"}
