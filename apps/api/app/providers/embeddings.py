"""
Embeddings + reranker provider abstraction with robust fallback.
"""
from __future__ import annotations

import abc
import hashlib
import math
import re
from typing import Any

import structlog

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
        ...

    @property
    @abc.abstractmethod
    def dim(self) -> int:
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
        ...


# ─── Local Fallback Embedding ─────────────────────────────────────────────────

def _generate_fallback_embedding(text: str, dim: int = 512) -> list[float]:
    """
    Generate a deterministic normalized embedding vector from text using
    hashed character n-grams and token frequencies.
    Produces valid cosine distances for semantic retrieval testing.
    """
    vec = [0.0] * dim
    words = re.findall(r"\w+", text.lower())
    if not words:
        return vec

    for i, word in enumerate(words):
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0 + (1.0 / (i + 1))

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


# ─── Voyage AI implementation ─────────────────────────────────────────────────

class VoyageEmbeddingClient(EmbeddingClient):
    """
    Voyage AI embedding client using voyage-3-lite (512-dim).
    Falls back gracefully to local deterministic embeddings if key is placeholder or offline.
    """

    _BATCH_SIZE = 128

    def __init__(self) -> None:
        self._key = settings.voyage_api_key.get_secret_value()
        self._is_placeholder = not self._key or "placeholder" in self._key or "pa-your-voyage-key" in self._key
        self._model = settings.voyage_embedding_model

    @property
    def dim(self) -> int:
        return settings.voyage_embedding_dim  # 512

    async def embed(
        self,
        texts: list[str],
        input_type: str = "document",
    ) -> list[list[float]]:
        if not texts:
            return []

        if self._is_placeholder:
            return [_generate_fallback_embedding(t, self.dim) for t in texts]

        try:
            import voyageai
            client = voyageai.AsyncClient(api_key=self._key)
            all_vectors: list[list[float]] = []
            for i in range(0, len(texts), self._BATCH_SIZE):
                batch = texts[i : i + self._BATCH_SIZE]
                result = await client.embed(
                    batch,
                    model=self._model,
                    input_type=input_type,
                )
                all_vectors.extend(result.embeddings)
            return all_vectors
        except Exception as e:
            logger.warning("Voyage embed failed, falling back to local deterministic embedding", error=str(e))
            return [_generate_fallback_embedding(t, self.dim) for t in texts]


class VoyageRerankerClient(RerankerClient):
    """
    Voyage AI reranker client using rerank-2.
    Falls back to BM25/keyword scoring if key is placeholder or offline.
    """

    def __init__(self) -> None:
        self._key = settings.voyage_api_key.get_secret_value()
        self._is_placeholder = not self._key or "placeholder" in self._key or "pa-your-voyage-key" in self._key
        self._model = settings.voyage_rerank_model

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 6,
    ) -> list[dict[str, Any]]:
        if not documents:
            return []

        if not self._is_placeholder:
            try:
                import voyageai
                client = voyageai.AsyncClient(api_key=self._key)
                result = await client.rerank(
                    query=query,
                    documents=documents,
                    model=self._model,
                    top_k=min(top_k, len(documents)),
                )
                return [
                    {
                        "index": r.index,
                        "relevance_score": r.relevance_score,
                        "document": documents[r.index],
                    }
                    for r in result.results
                ]
            except Exception as e:
                logger.warning("Voyage rerank failed, falling back to local ranker", error=str(e))

        # Local fallback ranker: token overlap + coverage
        q_tokens = set(re.findall(r"\w+", query.lower()))
        scored = []
        for idx, doc in enumerate(documents):
            d_tokens = set(re.findall(r"\w+", doc.lower()))
            if not q_tokens or not d_tokens:
                score = 0.1
            else:
                overlap = len(q_tokens.intersection(d_tokens))
                score = min(0.99, overlap / (len(q_tokens) + 1) + 0.1)
            scored.append({"index": idx, "relevance_score": round(score, 4), "document": doc})

        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:top_k]


# ─── Factories ────────────────────────────────────────────────────────────────

def get_embedding_client() -> EmbeddingClient:
    return VoyageEmbeddingClient()


def get_reranker() -> RerankerClient:
    return VoyageRerankerClient()
