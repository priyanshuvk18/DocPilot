"""Feedback API stub — Phase 3."""
from __future__ import annotations

from fastapi import APIRouter
from app.core.security import CurrentUser

router = APIRouter()


@router.post("/{message_id}/feedback", summary="Submit thumbs up/down feedback")
async def submit_feedback(message_id: str, user: CurrentUser) -> dict[str, str]:
    """Implemented in Phase 3."""
    return {"status": "not_implemented", "phase": "3"}
