"""
Output validation and citation extraction guardrail.
Ensures every citation references a valid retrieved chunk and extracts exact quotes.
Architecture.md §4.5 & §9 (S11).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from app.services.retrieval.hybrid import RetrievedChunk


@dataclass
class ValidatedCitation:
    marker: int
    chunk_id: str
    document_name: str
    page: int | None
    quote: str


def validate_citations(
    text: str,
    retrieved_chunks: Sequence[RetrievedChunk],
) -> tuple[str, list[ValidatedCitation]]:
    """
    Find citation markers like [1], [2] in generated text.
    Ensure marker <= len(retrieved_chunks).
    If valid, maps to chunk and extracts quote snippet.
    If marker is invalid/out-of-bounds, strips it from the text.
    """
    chunk_list = list(retrieved_chunks)
    found_markers = re.findall(r"\[(\d+)\]", text)
    valid_citations: list[ValidatedCitation] = []
    seen_markers: set[int] = set()

    for m_str in found_markers:
        marker = int(m_str)
        if marker in seen_markers:
            continue
        seen_markers.add(marker)

        # 1-indexed marker
        idx = marker - 1
        if 0 <= idx < len(chunk_list):
            chunk = chunk_list[idx]
            # Take first ~150 chars as snippet quote
            quote = chunk.content[:180].strip() + ("..." if len(chunk.content) > 180 else "")
            valid_citations.append(
                ValidatedCitation(
                    marker=marker,
                    chunk_id=str(chunk.chunk_id),
                    document_name=chunk.filename,
                    page=chunk.page,
                    quote=quote,
                )
            )
        else:
            # Strip invalid citation marker from text
            text = re.sub(rf"\[{marker}\]", "", text)

    return text, valid_citations
