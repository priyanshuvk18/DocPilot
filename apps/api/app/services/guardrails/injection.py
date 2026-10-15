"""
Prompt injection and jailbreak detection heuristics.
Architecture.md §4.5 & §9 (S2).
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class InjectionCheckResult:
    is_safe: bool
    flagged: bool
    reason: str | None


INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|directives)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(an?\s+unrestricted|DAN|a\s+hacker|in\s+developer\s+mode)", re.IGNORECASE),
    re.compile(r"disregard\s+(the\s+)?(system|rules|safety|guidelines)", re.IGNORECASE),
    re.compile(r"print\s+(your\s+)?(system\s+prompt|initial\s+instructions|hidden\s+rules)", re.IGNORECASE),
    re.compile(r"<\s*script\s*>", re.IGNORECASE),
    re.compile(r"reveal\s+(all\s+)?passwords|api\s*keys|secrets", re.IGNORECASE),
]


def check_injection(text: str) -> InjectionCheckResult:
    """Scan query or document passage for prompt injection attempts."""
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            return InjectionCheckResult(
                is_safe=False,
                flagged=True,
                reason=f"Matched suspicious pattern: {pattern.pattern}",
            )
    return InjectionCheckResult(is_safe=True, flagged=False, reason=None)
