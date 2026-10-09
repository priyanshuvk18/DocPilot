"""
Documents API — Phase 2 (stub for Phase 0).
POST /v1/documents/upload-url
POST /v1/documents/{id}/complete
GET  /v1/documents
GET  /v1/documents/{id}
DELETE /v1/documents/{id}
POST /v1/documents/{id}/reindex
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.security import CurrentUser

router = APIRouter()


@router.get("", summary="List documents")
async def list_documents(user: CurrentUser) -> dict[str, str]:
    """Implemented in Phase 2."""
    return {"status": "not_implemented", "phase": "2"}


@router.post("/upload-url", summary="Request a signed upload URL")
async def request_upload_url(user: CurrentUser) -> dict[str, str]:
    """Implemented in Phase 2."""
    return {"status": "not_implemented", "phase": "2"}
