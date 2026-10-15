"""
PII detection and redaction service for queries and logs.
Architecture.md §4.5 & §9 (S5).
"""
from __future__ import annotations

import re

EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
PHONE_REGEX = re.compile(r"\b(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})\b")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")


def redact_pii(text: str) -> tuple[str, dict[str, int]]:
    """
    Redact sensitive PII tokens from string.
    Returns (redacted_text, count_by_type).
    """
    counts: dict[str, int] = {}

    def replace_and_count(pattern: re.Pattern, repl: str, s: str, pii_type: str) -> str:
        matches = len(pattern.findall(s))
        if matches > 0:
            counts[pii_type] = counts.get(pii_type, 0) + matches
        return pattern.sub(repl, s)

    text = replace_and_count(SSN_REGEX, "[REDACTED_SSN]", text, "ssn")
    text = replace_and_count(CREDIT_CARD_REGEX, "[REDACTED_CARD]", text, "credit_card")
    text = replace_and_count(EMAIL_REGEX, "[REDACTED_EMAIL]", text, "email")
    text = replace_and_count(PHONE_REGEX, "[REDACTED_PHONE]", text, "phone")

    return text, counts
