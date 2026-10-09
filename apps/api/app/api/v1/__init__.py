"""v1 API router — aggregates all sub-routers."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    actions,
    analytics,
    chat,
    collections,
    documents,
    evals,
    feedback,
    health,
    workspaces,
)

router = APIRouter()

# Health check — no auth required (used by load balancer + Fly.io health checks)
router.include_router(health.router, tags=["health"])

# Authenticated routes
router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
router.include_router(collections.router, prefix="/collections", tags=["collections"])
router.include_router(documents.router, prefix="/documents", tags=["documents"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(feedback.router, prefix="/messages", tags=["feedback"])
router.include_router(actions.router, prefix="/actions", tags=["actions"])
router.include_router(evals.router, prefix="/eval-sets", tags=["evals"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
