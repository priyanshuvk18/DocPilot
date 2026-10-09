"""Evals API stub — Phase 5."""
from __future__ import annotations

from fastapi import APIRouter
from app.core.security import CurrentUser

router = APIRouter()


@router.get("", summary="List eval sets")
async def list_eval_sets(user: CurrentUser) -> dict[str, str]:
    """Implemented in Phase 5."""
    return {"status": "not_implemented", "phase": "5"}


@router.post("", summary="Create an eval set")
async def create_eval_set(user: CurrentUser) -> dict[str, str]:
    """Implemented in Phase 5."""
    return {"status": "not_implemented", "phase": "5"}
