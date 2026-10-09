"""
Embeddings + reranker provider abstraction.

SCHEMA DEVIATION NOTE:
  Architecture.md specified vector(1024) (for voyage-3 / voyage-large-2).
  We use voyage-3-lite (512-dim) per user request. The DB schema uses vector(512).
  See SCHEMA_DEVIATION.md for rationale and upgrade path.

Current implementation: Voyage AI
  - Embedding model: voyage-3-lite (512 dimensions)
  - Reranker: rerank-2

Usage:
    from app.providers.embeddings import get_embedding_client, get_reranker
    client = get_embedding_client()
    vectors = await client.embed(["text 1", "text 2"])  # list of 512-dim vectors

    reranker = get_reranker()
    ranked = await reranker.rerank(query, documents, top_k=6)
"""
from __future__ import annotations

import abc
from typing import Any

import structlog
import voyageai

from app.core.config import settings

logger = structlog.get_logger(__name__)


# ─── Interfaces ───────────────────────────────────────────────────────────────

class EmbeddingClient(abc.ABC):
    """Abstract embedding provider interface."""

    @abc.abstractmethod
    async def embed(
        self,
        texts: list[str],
        input_type: str = "document",
    ) -> list[list[float]]:
        """
        Embed a batch of texts.

        Args:
            texts: List of strings to embed.
            input_type: "document" for chunks, "query" for user queries.

        Returns:
            List of embedding vectors (each is settings.voyage_embedding_dim floats).
        """
        ...

    @property
    @abc.abstractmethod
    def dim(self) -> int:
        """Embedding vector dimensionality."""
        ...


class RerankerClient(abc.ABC):
    """Abstract reranker provider interface."""

    @abc.abstractmethod
    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 6,
    ) -> list[dict[str, Any]]:
        """
        Rerank documents by relevance to the query.

        Returns list of dicts: {"index": int, "relevance_score": float, "document": str}
        sorted by descending relevance_score, truncated to top_k.
        """
        ...


# ─── Voyage AI implementation ─────────────────────────────────────────────────

class VoyageEmbeddingClient(EmbeddingClient):
    """
    Voyage AI embedding client.

    Uses voyage-3-lite (512-dim) by default.
    Voyage recommends batches of ≤128 texts for optimal throughput.
    """

    _BATCH_SIZE = 128

    def __init__(self) -> None:
        self._client = voyageai.AsyncClient(
            api_key=settings.voyage_api_key.get_secret_value()
        )
        self._model = settings.voyage_embedding_model

    @property
    def dim(self) -> int:
        return settings.voyage_embedding_dim  # 512

    async def embed(
        self,
        texts: list[str],
        input_type: str = "document",
    ) -> list[list[float]]:
        """Embed texts in batches to respect Voyage API limits."""
        if not texts:
            return []

        all_vectors: list[list[float]] = []
        for i in range(0, len(texts), self._BATCH_SIZE):
            batch = texts[i : i + self._BATCH_SIZE]
            logger.debug(
                "Embedding batch",
                model=self._model,
                batch_size=len(batch),
                input_type=input_type,
            )
            result = await self._client.embed(
                batch,
                model=self._model,
                input_type=input_type,
            )
            all_vectors.extend(result.embeddings)

        return all_vectors


class VoyageRerankerClient(RerankerClient):
    """Voyage AI reranker client using rerank-2."""

    def __init__(self) -> None:
        self._client = voyageai.AsyncClient(
            api_key=settings.voyage_api_key.get_secret_value()
        )
        self._model = settings.voyage_rerank_model

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 6,
    ) -> list[dict[str, Any]]:
        logger.debug(
            "Reranking",
            model=self._model,
            n_documents=len(documents),
            top_k=top_k,
        )
        result = await self._client.rerank(
            query=query,
            documents=documents,
            model=self._model,
            top_k=top_k,
        )
        return [
            {
                "index": r.index,
                "relevance_score": r.relevance_score,
                "document": documents[r.index],
            }
            for r in result.results
        ]


# ─── Factories ────────────────────────────────────────────────────────────────

def get_embedding_client() -> EmbeddingClient:
    """Return the configured embedding client."""
    return VoyageEmbeddingClient()


def get_reranker() -> RerankerClient:
    """Return the configured reranker client."""
    return VoyageRerankerClient()
