"""
LLM provider abstraction — swappable interface.

Architecture.md §1: "behind a swappable provider interface"
Techstack.md §5: "a small LLMClient interface so models can be swapped or failed over"

Current implementation: Anthropic Claude (claude-sonnet-4-5 / claude-haiku-4-5)
Fallback: secondary model (same API, different model ID)

Usage:
    from app.providers.llm import get_llm_client
    client = get_llm_client()
    async for chunk in client.stream_chat(messages, system):
        ...
"""
from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from typing import Any

import structlog
from anthropic import AsyncAnthropic
from anthropic.types import Message, MessageStreamEvent

from app.core.config import settings

logger = structlog.get_logger(__name__)


# ─── Provider interface ───────────────────────────────────────────────────────

class LLMClient(abc.ABC):
    """Abstract interface for LLM providers. Implement to swap providers."""

    @abc.abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        system: str,
        max_tokens: int | None = None,
        temperature: float = 0.1,
        tools: list[dict[str, Any]] | None = None,
    ) -> Message:
        """Non-streaming completion."""
        ...

    @abc.abstractmethod
    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        system: str,
        max_tokens: int | None = None,
        temperature: float = 0.1,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[MessageStreamEvent]:
        """Streaming completion — yields SSE-style events."""
        ...

    @property
    @abc.abstractmethod
    def model_name(self) -> str:
        """The model identifier used for this client instance."""
        ...


# ─── Anthropic implementation ─────────────────────────────────────────────────

class AnthropicClient(LLMClient):
    """
    Anthropic Claude client.

    Uses claude-sonnet-4-5 for high-quality answers and claude-haiku-4-5
    for cheap tasks (query rewriting, classification).
    """

    def __init__(self, model: str | None = None) -> None:
        self._model = model or settings.anthropic_model_answer
        self._client = AsyncAnthropic(
            api_key=settings.anthropic_api_key.get_secret_value(),
        )

    @property
    def model_name(self) -> str:
        return self._model

    async def chat(
        self,
        messages: list[dict[str, Any]],
        system: str,
        max_tokens: int | None = None,
        temperature: float = 0.1,
        tools: list[dict[str, Any]] | None = None,
    ) -> Message:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens or settings.anthropic_max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        logger.debug("LLM chat request", model=self._model, message_count=len(messages))
        return await self._client.messages.create(**kwargs)

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        system: str,
        max_tokens: int | None = None,
        temperature: float = 0.1,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[MessageStreamEvent]:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens or settings.anthropic_max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        logger.debug("LLM stream request", model=self._model)
        async with self._client.messages.stream(**kwargs) as stream:
            async for event in stream:
                yield event


# ─── Factory ──────────────────────────────────────────────────────────────────

def get_llm_client(cheap: bool = False) -> LLMClient:
    """
    Return the configured LLM client.

    Args:
        cheap: If True, returns the Haiku-class model for low-cost tasks
               (query rewriting, entity extraction). Default: Sonnet-class.
    """
    model = settings.anthropic_model_cheap if cheap else settings.anthropic_model_answer
    return AnthropicClient(model=model)
