"""Media and field resolution helpers for the editor bridge."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .editor_session import EditorSession
from .errors import AudioProcessingError, AudioQuickEditorError, MissingMediaError
from .sound_refs import safe_media_basename, select_first_sound_reference

CURRENT_FIELD_AUDIO_MISSING = "No [sound:...] reference found in the current field."
REFERENCED_AUDIO_MISSING = "The referenced audio file was not found in Anki's media folder."


def audio_field_indices(note: Any) -> list[int]:
    """Return field indices containing a supported sound reference."""
    return list(audio_field_sources(note))


def audio_field_sources(note: Any) -> dict[int, str]:
    """Return field indices and first supported sound filename for the note."""
    sources: dict[int, str] = {}
    for index, field_html in enumerate(getattr(note, "fields", [])):
        try:
            selection = select_first_sound_reference(field_html)
        except AudioQuickEditorError:
            continue
        if selection.selected is not None:
            sources[index] = safe_media_basename(selection.selected.filename)
    return sources


def current_field_index(editor: Any) -> int:
    """Return the editor's active field index."""
    if editor.currentField is not None:
        return int(editor.currentField)
    if getattr(editor, "last_field_index", None) is not None:
        return int(editor.last_field_index)
    raise AudioProcessingError(CURRENT_FIELD_AUDIO_MISSING)


def sound_reference_for_field(editor: Any, field_index: int) -> tuple[str, Path]:
    """Return the first supported sound filename and media path for a field."""
    field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(field_html)
    if selection.selected is None:
        raise AudioProcessingError(CURRENT_FIELD_AUDIO_MISSING)
    filename = safe_media_basename(selection.selected.filename)
    return filename, Path(editor.mw.col.media.dir()) / filename


def resolve_requested_field_media(
    editor: Any,
    field_index: int,
    expected_filename: str,
) -> tuple[str, Path] | None:
    """Resolve a frontend-addressed field only if it still matches the expected media."""
    if getattr(editor, "note", None) is None:
        return None
    fields = getattr(editor.note, "fields", [])
    if field_index >= len(fields):
        return None
    try:
        filename, media_path = sound_reference_for_field(editor, field_index)
    except AudioQuickEditorError:
        return None
    return (filename, media_path) if filename == expected_filename else None


def session_original_source_path(
    editor: Any,
    session: EditorSession,
    field_index: int,
    filename: str,
) -> Path | None:
    """Return the original source media path for an active generated edit session."""
    if session.field_index != field_index or session.state is None or session.current_filename != filename:
        return None
    source_path = Path(editor.mw.col.media.dir()) / session.state.source_file
    if not source_path.is_file():
        raise MissingMediaError("The original audio file was not found in Anki's media folder.")
    return source_path


def session_needs_media_reset(
    session: EditorSession,
    field_index: int,
    filename: str,
    mtime: int,
) -> bool:
    """Return whether the mutable session should be reset for the current media."""
    return (
        session.field_index != field_index
        or session.state is None
        or session.source_mtime_ns != mtime
        or session.state.source_file != filename
    )


def visualized_duration_for_field(
    session: EditorSession,
    field_index: int,
    filename: str | None,
) -> int | None:
    """Return the known visualized duration for a field and filename."""
    if filename and session.visualized_filenames_by_field.get(field_index) == filename:
        return session.visualized_durations_by_field.get(field_index)
    if session.field_index == field_index:
        return session.visualized_duration_ms
    return None
