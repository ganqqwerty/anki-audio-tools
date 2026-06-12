"""Shared editor history size limits and normalization."""

from __future__ import annotations

MIN_EDITOR_HISTORY_SIZE = 1
MAX_EDITOR_HISTORY_SIZE = 100
DEFAULT_EDITOR_HISTORY_SIZE = 100


def normalize_editor_history_size(value: object) -> int:
    """Return a supported per-field editor history size."""
    if isinstance(value, bool):
        return DEFAULT_EDITOR_HISTORY_SIZE
    if not isinstance(value, str | int | float):
        return DEFAULT_EDITOR_HISTORY_SIZE
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return DEFAULT_EDITOR_HISTORY_SIZE
    return min(MAX_EDITOR_HISTORY_SIZE, max(MIN_EDITOR_HISTORY_SIZE, parsed))
