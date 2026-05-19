"""Undo and redo behavior for editor audio edits."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .editor_session import EditorSession, UndoEntry
from .errors import AudioProcessingError
from .i18n import t
from .media_paths import existing_media_file_path
from .sound_refs import (
    replace_sound_reference,
    select_first_sound_reference,
)


def undo(editor: Any, deps: Any) -> None:
    """Restore the previous generated audio reference for the current field."""
    session, _source_path = deps.session_and_source(editor)
    if deps.is_busy(session):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    previous = session.undo_history.pop()
    if previous is None:
        deps.eval_status(editor, t("editor.status.nothing_to_undo"))
        return
    deps.restore_history_entry(
        editor,
        session,
        previous,
        redo_current=True,
        status=f"Undid last edit; restored {previous.filename}",
    )


def redo(editor: Any, deps: Any) -> None:
    """Restore the next generated audio reference for the current field."""
    session, _source_path = deps.session_and_source(editor)
    if deps.is_busy(session):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    next_entry = session.redo_history.pop()
    if next_entry is None:
        deps.eval_status(editor, t("editor.status.nothing_to_redo"))
        return
    deps.restore_history_entry(
        editor,
        session,
        next_entry,
        redo_current=False,
        status=f"Redid edit; restored {next_entry.filename}",
    )


def restore_history_entry(
    editor: Any,
    session: EditorSession,
    entry: UndoEntry,
    *,
    redo_current: bool,
    status: str,
    deps: Any,
) -> None:
    """Replace the current audio field with a history entry."""
    deps.stop_session_playback(session)
    field_index = deps.current_field_index(editor)
    field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(field_html)
    if selection.selected is None:
        raise AudioProcessingError(deps.current_field_audio_missing)
    current_state = session.state
    current_filename = session.current_filename
    deps.dispose_editor_frontend_controls(editor)
    editor.note.fields[field_index] = replace_sound_reference(field_html, selection.selected, entry.filename)
    if redo_current:
        session.redo_history.push(current_state, current_filename)
    else:
        session.undo_history.push(current_state, current_filename)
    session.state = entry.state
    session.current_filename = entry.filename
    session.field_index = field_index
    session.cursor_ms = 0
    session.playback_active = False
    session.playback_paused = False
    restored_path = existing_media_file_path(Path(editor.mw.col.media.dir()), entry.filename)
    session.source_mtime_ns = restored_path.stat().st_mtime_ns if restored_path is not None else None
    editor.loadNote(focusTo=field_index)
    deps.eval_status(editor, status)
    deps.eval_playback_state(editor, field_index, "stopped", 0)
    if field_index in session.graph_active_fields:
        deps.request_graph_redraw(editor)
