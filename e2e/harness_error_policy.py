"""Fail-closed E2E error-channel policy."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence

PLATFORM_NOISE_PATTERNS = (
    r"^1000000002\.editor_bridge: editor frontend: ResizeObserver loop completed with undelivered notifications\. \| ",
)


def unexpected_messages(
    messages: Iterable[str],
    allowed_patterns: Sequence[str],
) -> tuple[str, ...]:
    compiled = tuple(re.compile(pattern) for pattern in (*PLATFORM_NOISE_PATTERNS, *allowed_patterns))
    return tuple(
        message
        for message in messages
        if not any(pattern.search(message) for pattern in compiled)
    )
