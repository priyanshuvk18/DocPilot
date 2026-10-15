"""
Hybrid retrieval combining vector similarity and keyword search with Reciprocal Rank Fusion (RRF).
Works seamlessly on PostgreSQL + pgvector and SQLite.
"""
from __future__ import annotations

import math
import re
import uuid
from dataclasses import dataclass
from typing import Sequence

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chunk, Document
from app.providers.embeddings import get_embedding_client

logger = structlog.get_logger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page: int | None
    heading: str | None
    content: str
    score: float


def _cosine_similarity(v1: Sequence[float], v2: Sequence[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a, b in zip(v1, v2)))
    norm_b = math.sqrt(sum(b * b for a, b in zip(v1, v2)))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def hybrid_search(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    query: str,
    collection_id: uuid.UUID | None = None,
    document_ids: list[uuid.UUID] | None = None,
    top_k: int = 15,
) -> list[RetrievedChunk]:
    """
    Perform hybrid retrieval:
      1. Embed the query
      2. Vector cosine score
      3. Keyword BM25 / token matching
      4. Reciprocal Rank Fusion (RRF): 1 / (60 + r_vector) + 1 / (60 + r_keyword)
    """
    # 1. Fetch candidate chunks for this workspace
    stmt = (
        select(Chunk, Document.filename)
        .join(Document, Chunk.document_id == Document.id)
        .where(Chunk.workspace_id == workspace_id)
        .where(Document.status == "ready")
    )
    if collection_id:
        stmt = stmt.where(Document.collection_id == collection_id)
    if document_ids:
        stmt = stmt.where(Document.id.in_(document_ids))

    result = await session.execute(stmt)
    rows = result.all()
    if not rows:
        return []

    # 2. Query embedding
    embedder = get_embedding_client()
    query_embeddings = await embedder.embed([query], input_type="query")
    q_vec = query_embeddings[0] if query_embeddings else None

    # 3. Vector ranking
    vector_scores: list[tuple[uuid.UUID, float]] = []
    if q_vec:
        for chunk, _ in rows:
            if chunk.embedding:
                sim = _cosine_similarity(q_vec, chunk.embedding)
                vector_scores.append((chunk.id, sim))
    vector_scores.sort(key=lambda x: x[1], reverse=True)
    v_ranks = {cid: rank + 1 for rank, (cid, _) in enumerate(vector_scores)}

    # 4. Keyword ranking
    q_terms = set(re.findall(r"\w+", query.lower()))
    keyword_scores: list[tuple[uuid.UUID, float]] = []
    for chunk, _ in rows:
        c_text = chunk.content.lower()
        c_terms = set(re.findall(r"\w+", c_text))
        if q_terms and c_terms:
            overlap = len(q_terms.intersection(c_terms))
            # Substring match bonus
            bonus = 1.0 if query.lower() in c_text else 0.0
            score = (overlap / (len(q_terms) + 1)) + bonus
        else:
            score = 0.0
        keyword_scores.append((chunk.id, score))
    keyword_scores.sort(key=lambda x: x[1], reverse=True)
    k_ranks = {cid: rank + 1 for rank, (cid, _) in enumerate(keyword_scores)}

    # 5. Reciprocal Rank Fusion (RRF)
    scored_chunks: list[RetrievedChunk] = []
    chunk_map = {chunk.id: (chunk, fname) for chunk, fname in rows}

    for chunk_id, (chunk, fname) in chunk_map.items():
        r_v = v_ranks.get(chunk_id, 100)
        r_k = k_ranks.get(chunk_id, 100)
        rrf_score = (1.0 / (60.0 + r_v)) + (1.0 / (60.0 + r_k))

        scored_chunks.append(
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                filename=fname,
                page=chunk.page,
                heading=chunk.heading,
                content=chunk.content,
                score=rrf_score,
            )
        )

    scored_chunks.sort(key=lambda x: x.score, reverse=True)
    return scored_chunks[:top_k]
