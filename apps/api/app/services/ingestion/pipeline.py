"""
Document ingestion pipeline.
Coordinates parsing, cleaning, chunking, embedding, and database persistence.
"""
from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, Chunk, Document
from app.providers.embeddings import get_embedding_client
from app.services.ingestion.chunker import chunk_pages
from app.services.ingestion.cleaner import clean_text
from app.services.ingestion.parser import ParsedPage, parse_document
from app.services.storage import storage_service

logger = structlog.get_logger(__name__)


async def ingest_document_pipeline(session: AsyncSession, document_id: uuid.UUID) -> dict[str, Any]:
    """
    Execute end-to-end ingestion pipeline for a document.
    """
    result = await session.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        logger.error("Document not found for ingestion", document_id=str(document_id))
        return {"status": "error", "message": "Document not found"}

    try:
        doc.status = "parsing"
        await session.commit()

        # Read file from storage
        content = storage_service.read_file(doc.storage_path)
        if not content:
            raise ValueError(f"Empty or missing file at storage path: {doc.storage_path}")

        # Parse
        parsed = parse_document(content, doc.filename)
        doc.page_count = parsed.total_pages

        # Clean pages
        cleaned_pages = [
            ParsedPage(page_number=p.page_number, text=clean_text(p.text))
            for p in parsed.pages
        ]

        # Chunk
        chunks_data = chunk_pages(cleaned_pages)
        if not chunks_data:
            # Fallback single chunk if empty document
            chunks_data = [
                type("FallbackChunk", (), {
                    "ordinal": 1,
                    "page": 1,
                    "heading": None,
                    "content": f"Document: {doc.filename}",
                    "tokens": 10,
                })()
            ]

        # Embed
        doc.status = "embedding"
        await session.commit()

        embedder = get_embedding_client()
        texts = [c.content for c in chunks_data]
        embeddings = await embedder.embed(texts, input_type="document")

        # Delete any previous chunks if re-indexing
        await session.execute(delete(Chunk).where(Chunk.document_id == document_id))

        # Insert new chunks
        for i, c in enumerate(chunks_data):
            emb = embeddings[i] if i < len(embeddings) else None
            chunk_row = Chunk(
                workspace_id=doc.workspace_id,
                document_id=doc.id,
                ordinal=c.ordinal,
                page=c.page,
                heading=c.heading,
                content=c.content,
                tokens=c.tokens,
                embedding=emb,
                tsv=c.content.lower(),
            )
            session.add(chunk_row)

        doc.status = "ready"
        doc.error = None

        audit = AuditLog(
            workspace_id=doc.workspace_id,
            actor=doc.created_by,
            event="document_ingested",
            meta={
                "document_id": str(doc.id),
                "filename": doc.filename,
                "chunks": len(chunks_data),
                "pages": doc.page_count,
            },
        )
        session.add(audit)
        await session.commit()

        logger.info(
            "Document ingested successfully",
            document_id=str(document_id),
            filename=doc.filename,
            chunks=len(chunks_data),
        )
        return {
            "status": "ready",
            "document_id": str(doc.id),
            "chunks_count": len(chunks_data),
            "pages": doc.page_count,
        }

    except Exception as e:
        logger.exception("Document ingestion failed", document_id=str(document_id), error=str(e))
        doc.status = "failed"
        doc.error = str(e)
        await session.commit()
        return {"status": "failed", "error": str(e)}
