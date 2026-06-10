"""Shared primitives for editor media replacement workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from .errors import AudioProcessingError
from .sound_refs import replace_sound_reference, select_first_sound_reference


def persist_generated_media(
    editor: Any,
    saved_name: str,
    output_path: Path | None,
    deps: Any,
) -> str:
    """Persist generated media when a worker returned a temp path."""
    if output_path is None:
        return saved_name
    return cast(str, deps.write_generated_media(editor, saved_name, output_path))


def replace_first_sound_reference_in_field(
    editor: Any,
    *,
    field_index: int,
    saved_name: str,
    missing_message: str,
) -> tuple[str, str, str]:
    """Replace the first sound reference in a field and return old/new details."""
    old_field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(old_field_html)
    if selection.selected is None:
        raise AudioProcessingError(missing_message)
    old_filename = selection.selected.filename
    editor.note.fields[field_index] = replace_sound_reference(
        old_field_html,
        selection.selected,
        saved_name,
    )
    return old_field_html, editor.note.fields[field_index], old_filename
