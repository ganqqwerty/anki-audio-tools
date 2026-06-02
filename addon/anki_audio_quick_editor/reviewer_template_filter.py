"""Import-safe rendering helpers for Reviewer template audio-panel filters."""

from __future__ import annotations

import re
from typing import Any

from .reviewer_audio_targets import (
    AQE_REVIEW_TRIGGER_CLASS,
    audio_panel_trigger_html,
)
from .sound_refs import is_supported_audio_filename, safe_media_basename

_SOUND_RE = re.compile(r"\[sound:([^\]]+)\]", re.IGNORECASE)


def audio_panel_filter_html(
    field_text: str,
    field_name: str,
    ctx: Any,
    *,
    label: str,
) -> str:
    """Render the Reviewer audio-panel trigger for one Anki template filter."""
    if AQE_REVIEW_TRIGGER_CLASS in field_text:
        return field_text
    filename = _first_sound_filename(field_text)
    if filename is None:
        return ""
    field_index = _template_field_index(ctx, field_name)
    if field_index is None:
        return ""
    return audio_panel_trigger_html(field_index, filename, label=label)


def _first_sound_filename(text: str) -> str | None:
    match = _SOUND_RE.search(text)
    if match is None:
        return None
    filename = safe_media_basename(match.group(1))
    return filename if is_supported_audio_filename(filename) else None


def _template_field_index(ctx: Any, field_name: str) -> int | None:
    note = _template_note(ctx)
    if isinstance(field_name, str):
        ordinal = _field_index_by_name(note, field_name)
        if ordinal is not None:
            return ordinal
    ordinal = getattr(ctx, "field_ordinal", None)
    if isinstance(ordinal, int):
        return ordinal
    return None


def _template_note(ctx: Any) -> Any | None:
    note = getattr(ctx, "note", None)
    if callable(note):
        try:
            return note()
        except TypeError:
            return None
    return note


def _field_index_by_name(note: Any, field_name: str) -> int | None:
    keys = getattr(note, "keys", None)
    if callable(keys):
        try:
            return list(keys()).index(field_name)
        except ValueError:
            return None
    fields = getattr(note, "fields", None)
    field_names = getattr(note, "field_names", None)
    if isinstance(fields, list) and isinstance(field_names, list):
        try:
            return field_names.index(field_name)
        except ValueError:
            return None
    return None
