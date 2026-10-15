"""
Text normalization and cleaner for ingested documents.
"""
from __future__ import annotations

import re


def clean_text(text: str) -> str:
    """Clean and normalize raw extracted document text."""
    if not text:
        return ""

    # Replace null bytes and non-printable control chars except \n, \t, \r
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Normalize carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace 3 or more consecutive newlines with 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Normalize multiple consecutive horizontal spaces to a single space
    text = re.sub(r"[ \t]+", " ", text)

    # Strip trailing whitespace on each line
    lines = [line.strip() for line in text.split("\n")]
    cleaned = "\n".join(lines).strip()

    return cleaned
