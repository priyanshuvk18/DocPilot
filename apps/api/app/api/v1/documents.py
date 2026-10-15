"""
Documents API.
Architecture.md §3.1 & §5.
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.db.session import get_db, set_rls_context
from app.models import Chunk, Document
from app.schemas import (
    ChunkOut,
    DocumentOut,
    DocumentUploadUrlRequest,
    DocumentUploadUrlResponse,
)
from app.services.ingestion.pipeline import ingest_document_pipeline
from app.services.storage import storage_service

router = APIRouter()


@router.get("", response_model=list[DocumentOut], summary="List documents")
async def list_documents(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    collection_id: uuid.UUID | None = None,
) -> list[DocumentOut]:
    await set_rls_context(db, str(user.user_id))
    ws_id = user.workspace_id or uuid.UUID("00000000-0000-0000-0000-000000000002")

    stmt = select(Document).where(Document.workspace_id == ws_id)
    if collection_id:
        stmt = stmt.where(Document.collection_id == collection_id)
    stmt = stmt.order_by(Document.created_at.desc())

    result = await db.execute(stmt)
    docs = result.scalars().all()
    return [DocumentOut.model_validate(d) for d in docs]


@router.post("/upload-url", response_model=DocumentUploadUrlResponse, summary="Request signed upload URL")
async def request_upload_url(
    payload: DocumentUploadUrlRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentUploadUrlResponse:
    user.require_role("owner", "member")
    await set_rls_context(db, str(user.user_id))
    ws_id = user.workspace_id or uuid.UUID("00000000-0000-0000-0000-000000000002")

    doc_id = uuid.uuid4()
    storage_path = f"uploads/{ws_id}/{doc_id}_{payload.filename}"

    doc = Document(
        id=doc_id,
        workspace_id=ws_id,
        collection_id=payload.collection_id,
        filename=payload.filename,
        storage_path=storage_path,
        content_hash=f"pending_{doc_id}",
        status="queued",
        created_by=user.user_id,
    )
    db.add(doc)
    await db.commit()

    return DocumentUploadUrlResponse(
        document_id=doc_id,
        upload_url=f"/v1/documents/{doc_id}/upload-direct",
        storage_path=storage_path,
        expires_in_seconds=3600,
    )


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED, summary="Direct file upload")
async def upload_document_direct(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
    collection_id: uuid.UUID | None = Form(None),
) -> DocumentOut:
    user.require_role("owner", "member")
    await set_rls_context(db, str(user.user_id))
    ws_id = user.workspace_id or uuid.UUID("00000000-0000-0000-0000-000000000002")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    content_hash = hashlib.sha256(content).hexdigest()

    # Check for existing document with same content hash in workspace
    existing = await db.execute(
        select(Document).where(
            Document.workspace_id == ws_id,
            Document.content_hash == content_hash,
        )
    )
    doc = existing.scalar_one_or_none()
    if not doc:
        doc_id = uuid.uuid4()
        storage_filename = f"{ws_id}_{doc_id}_{file.filename}"
        storage_path = storage_service.save_file(storage_filename, content)

        doc = Document(
            id=doc_id,
            workspace_id=ws_id,
            collection_id=collection_id,
            filename=file.filename or "uploaded_document",
            storage_path=storage_path,
            content_hash=content_hash,
            status="queued",
            created_by=user.user_id,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

    # Run ingestion pipeline
    await ingest_document_pipeline(db, doc.id)
    await db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.post("/{document_id}/complete", response_model=DocumentOut, summary="Trigger ingestion after upload")
async def complete_upload(
    document_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentOut:
    await set_rls_context(db, str(user.user_id))
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await ingest_document_pipeline(db, doc.id)
    await db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.get("/{document_id}", response_model=DocumentOut, summary="Get document details")
async def get_document(
    document_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentOut:
    await set_rls_context(db, str(user.user_id))
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut.model_validate(doc)


@router.get("/{document_id}/chunks", response_model=list[ChunkOut], summary="Get chunks for document")
async def get_document_chunks(
    document_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ChunkOut]:
    await set_rls_context(db, str(user.user_id))
    result = await db.execute(
        select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.ordinal.asc())
    )
    chunks = result.scalars().all()
    return [ChunkOut.model_validate(c) for c in chunks]


@router.post("/{document_id}/reindex", response_model=DocumentOut, summary="Re-index document")
async def reindex_document(
    document_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentOut:
    user.require_role("owner", "member")
    await set_rls_context(db, str(user.user_id))
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await ingest_document_pipeline(db, doc.id)
    await db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete document")
async def delete_document(
    document_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    user.require_role("owner", "member")
    await set_rls_context(db, str(user.user_id))
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc:
        await db.delete(doc)
        await db.commit()
