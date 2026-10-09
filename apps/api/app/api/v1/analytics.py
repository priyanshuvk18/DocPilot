"""Analytics/monitoring API stub — Phase 5."""
from __future__ import annotations

from fastapi import APIRouter
from app.core.security import CurrentUser

router = APIRouter()


@router.get("/usage", summary="Usage analytics (latency, tokens, cost)")
async def get_usage(user: CurrentUser) -> dict[str, str]:
    """Implemented in Phase 5."""
    return {"status": "not_implemented", "phase": "5"}


@router.get("/quality", summary="Quality metrics (feedback, eval scores)")
async def get_quality(user: CurrentUser) -> dict[str, str]:
    """Implemented in Phase 5."""
    return {"status": "not_implemented", "phase": "5"}
