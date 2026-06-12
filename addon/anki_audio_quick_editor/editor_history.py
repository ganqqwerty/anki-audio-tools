"""Undo and redo behavior for editor audio edits."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .audio_state import DEFAULT_EDITOR_HISTORY_SIZE
from .editor_history_snapshot import HistorySnapshot, history_snapshot_for_field
from .editor_reload_status import reload_editor_with_pending_status
from .editor_session import EditorSession, UndoEntry
from .editor_status import (
    redo_status_message,
    restored_status_summary,
    undo_status_message,
)
from .errors import AudioProcessingError
from .i18n import t
from .media_paths import existing_media_file_path
from .sound_refs import (
    replace_sound_reference,
    select_first_sound_reference,
)


def sync_history_availability(editor: Any, session: EditorSession, deps: Any) -> None:
    """Reflect current undo/redo history into the editor toolbar."""
    deps.eval_history_snapshot(editor, session.field_index, history_snapshot(editor, session, deps))


def request_history_availability_after_edit(editor: Any, session: EditorSession, deps: Any) -> None:
    """Retry history sync after the editor remounts controls."""
    deps.request_history_snapshot_after_edit(editor, session.field_index, history_snapshot(editor, session, deps))


def history_snapshot(editor: Any, session: EditorSession, deps: Any) -> HistorySnapshot:
    """Return the current history snapshot for the session field."""
    latest_persistent_undo_item = getattr(deps, "latest_persistent_undo_item", lambda _editor, _field_index: None)
    return history_snapshot_for_field(
        editor,
        field_index=session.field_index,
        session=session,
        history_size=_history_size(editor, deps),
        can_persistent_undo=deps.can_persistent_undo,
        latest_persistent_undo_item=latest_persistent_undo_item,
    )


def _history_size(editor: Any, deps: Any) -> object:
    if not hasattr(deps, "config"):
        return DEFAULT_EDITOR_HISTORY_SIZE
    try:
        config = deps.config(editor)
    except (AttributeError, TypeError):
        return DEFAULT_EDITOR_HISTORY_SIZE
    return config.get("editor_history_size", DEFAULT_EDITOR_HISTORY_SIZE)


def undo(editor: Any, deps: Any) -> None:
    """Restore the previous generated audio reference for the current field."""
    session, _source_path = deps.session_and_source(editor)
    if deps.is_busy(session):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    previous = session.undo_history.pop()
    if previous is None:
        if deps.restore_persistent_undo(editor, session):
            sync_history_availability(editor, session, deps)
            request_history_availability_after_edit(editor, session, deps)
            return
        deps.eval_status(editor, t("editor.status.nothing_to_undo"))
        return
    deps.restore_history_entry(
        editor,
        session,
        previous,
        redo_current=True,
        status=undo_status_message(previous),
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
        status=redo_status_message(next_entry),
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
    session.post_edit_playback_generation += 1
    field_index = deps.current_field_index(editor)
    field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(field_html)
    if selection.selected is None:
        raise AudioProcessingError(deps.current_field_audio_missing)
    current_state = session.state
    current_filename = session.current_filename
    editor.note.fields[field_index] = replace_sound_reference(field_html, selection.selected, entry.filename)
    if redo_current:
        session.redo_history.push(
            current_state,
            current_filename,
            status_summary=session.status_summary,
        )
    else:
        session.undo_history.push(
            current_state,
            current_filename,
            status_summary=session.status_summary,
        )
    session.state = entry.state
    session.current_filename = entry.filename
    session.field_index = field_index
    session.status_summary = restored_status_summary(entry)
    session.next_status_summary = ""
    session.cursor_ms = 0
    session.playback_active = False
    session.playback_paused = False
    restored_path = existing_media_file_path(Path(editor.mw.col.media.dir()), entry.filename)
    session.source_mtime_ns = restored_path.stat().st_mtime_ns if restored_path is not None else None
    deps.request_playback_after_edit(
        editor,
        field_index,
        require_graph_redraw=field_index in session.graph_active_fields,
    )
    reload_editor_with_pending_status(
        editor,
        session,
        field_index,
        message=status,
        deps=deps,
    )
    sync_history_availability(editor, session, deps)
    request_history_availability_after_edit(editor, session, deps)
    deps.eval_playback_state(editor, field_index, "stopped", 0)
    if field_index in session.graph_active_fields:
        deps.request_graph_redraw(editor, entry.filename)

