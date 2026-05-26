"""Cursor and selection bounds for editor playback requests."""

from __future__ import annotations

from typing import Any

from .prosody_types import clamp_cursor_ms


def requested_end_ms(value: Any, duration_ms: int | None) -> int | None:
    if value is None:
        return duration_ms
    try:
        requested_end = int(round(float(value)))
    except (TypeError, ValueError):
        requested_end = 0
    upper_ms = duration_ms if duration_ms is not None else requested_end
    return clamp_cursor_ms(requested_end, upper_ms)


def native_playback_end_ms(end_ms: int | None, source_duration_ms: int | None) -> int | None:
    if end_ms is None:
        return None
    upper = source_duration_ms if source_duration_ms is not None else max(0, int(end_ms))
    return clamp_cursor_ms(end_ms, upper)
