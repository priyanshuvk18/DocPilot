"""
Heading-aware, recursive text chunker.
Target chunk size: ~500 tokens (~2000 characters), ~80 tokens overlap (~320 characters).
Preserves page numbers, heading context, and ordinal sequence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from app.services.ingestion.parser import ParsedPage


@dataclass
class DocumentChunk:
    ordinal: int
    page: int
    heading: str | None
    content: str
    tokens: int


HEADING_REGEX = re.compile(
    r"^(?:#{1,6}\s+|[0-9]{1,2}(?:\.[0-9]{1,2})*\s+|[A-Z\s]{4,}:?\s*$)(.+)$",
    re.MULTILINE,
)


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def chunk_pages(
    pages: Sequence[ParsedPage],
    target_tokens: int = 500,
    overlap_tokens: int = 80,
) -> list[DocumentChunk]:
    """
    Split pages into chunks respecting heading boundaries and target token sizes.
    """
    target_chars = target_tokens * 4
    overlap_chars = overlap_tokens * 4

    chunks: list[DocumentChunk] = []
    ordinal = 1

    for page in pages:
        text = page.text.strip()
        if not text:
            continue

        # Detect any headings in this page
        current_heading: str | None = None
        paragraphs = text.split("\n\n")

        buffer = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if this paragraph is a heading
            heading_match = HEADING_REGEX.match(para)
            if heading_match and len(para) < 120:
                current_heading = para

            if len(buffer) + len(para) <= target_chars:
                buffer = f"{buffer}\n\n{para}".strip()
            else:
                if buffer:
                    chunks.append(
                        DocumentChunk(
                            ordinal=ordinal,
                            page=page.page_number,
                            heading=current_heading,
                            content=buffer,
                            tokens=_approx_tokens(buffer),
                        )
                    )
                    ordinal += 1

                    # Retain overlap from end of buffer
                    if len(buffer) > overlap_chars:
                        buffer = buffer[-overlap_chars:] + "\n\n" + para
                    else:
                        buffer = para
                else:
                    # Single very long paragraph: hard chunk by character slice
                    for i in range(0, len(para), target_chars - overlap_chars):
                        slice_text = para[i : i + target_chars]
                        chunks.append(
                            DocumentChunk(
                                ordinal=ordinal,
                                page=page.page_number,
                                heading=current_heading,
                                content=slice_text,
                                tokens=_approx_tokens(slice_text),
                            )
                        )
                        ordinal += 1
                    buffer = ""

        if buffer:
            chunks.append(
                DocumentChunk(
                    ordinal=ordinal,
                    page=page.page_number,
                    heading=current_heading,
                    content=buffer,
                    tokens=_approx_tokens(buffer),
                )
            )
            ordinal += 1

    return chunks
