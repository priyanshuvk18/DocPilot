"""
Query rewriter using history context to generate standalone search queries.
"""
from __future__ import annotations

import structlog

from app.providers.llm import get_llm_client

logger = structlog.get_logger(__name__)


async def rewrite_query(query: str, history: list[dict[str, str]] | None = None) -> str:
    """
    Rewrite follow-up questions into standalone queries using conversation context.
    If no history or standalone question, returns original query.
    """
    if not history:
        return query.strip()

    # Cheap model for rewrite
    llm = get_llm_client(cheap=True)
    system_prompt = (
        "You are an AI assistant. Given a chat history and a follow-up question, "
        "rewrite the follow-up question into a single clear, standalone search query. "
        "Do not answer the question; output only the rewritten query. "
        "If it is already standalone, return it as-is."
    )
    formatted_messages = []
    for msg in history[-4:]:
        formatted_messages.append({"role": msg["role"], "content": msg["content"]})
    formatted_messages.append({"role": "user", "content": f"Follow-up: {query}"})

    try:
        resp = await llm.chat(messages=formatted_messages, system=system_prompt, max_tokens=100)
        if hasattr(resp, "content") and resp.content:
            first_block = resp.content[0]
            if hasattr(first_block, "text"):
                rewritten = first_block.text.strip().strip('"')
                if rewritten:
                    return rewritten
    except Exception as e:
        logger.warning("Query rewrite error, using original query", error=str(e))

    return query.strip()
