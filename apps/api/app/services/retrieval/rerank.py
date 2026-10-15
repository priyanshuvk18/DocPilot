"""
Reranking service for top hybrid search candidates.
"""
from __future__ import annotations

import structlog

from app.providers.embeddings import get_reranker
from app.services.retrieval.hybrid import RetrievedChunk

logger = structlog.get_logger(__name__)


async def rerank_chunks(
    query: str,
    chunks: list[RetrievedChunk],
    top_k: int = 6,
) -> list[RetrievedChunk]:
    """
    Rerank hybrid retrieval candidates using Voyage AI reranker or fallback ranker.
    """
    if not chunks:
        return []

    docs = [c.content for c in chunks]
    reranker = get_reranker()
    try:
        results = await reranker.rerank(query=query, documents=docs, top_k=top_k)
        reranked: list[RetrievedChunk] = []
        for r in results:
            orig = chunks[r["index"]]
            reranked.append(
                RetrievedChunk(
                    chunk_id=orig.chunk_id,
                    document_id=orig.document_id,
                    filename=orig.filename,
                    page=orig.page,
                    heading=orig.heading,
                    content=orig.content,
                    score=r["relevance_score"],
                )
            )
        return reranked
    except Exception as e:
        logger.warning("Reranking failed, preserving original hybrid order", error=str(e))
        return chunks[:top_k]
