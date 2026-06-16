"""Undo and redo behavior for editor audio edits."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .editor_history_settings import (
    DEFAULT_EDITOR_HISTORY_SIZE,
    normalize_editor_history_size,
)
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

if TYPE_CHECKING:
    from .editor_deps_protocols import HistoryDeps


def sync_history_availability(editor: Any, session: EditorSession, deps: HistoryDeps) -> None:
    """Reflect current undo/redo history into the editor toolbar."""
    deps.eval_history_snapshot(editor, session.field_index, history_snapshot(editor, session, deps))


def request_history_availability_after_edit(editor: Any, session: EditorSession, deps: HistoryDeps) -> None:
    """Retry history sync after the editor remounts controls."""
    deps.request_history_snapshot_after_edit(editor, session.field_index, history_snapshot(editor, session, deps))


def history_snapshot(editor: Any, session: EditorSession, deps: HistoryDeps) -> HistorySnapshot:
    """Return the current history snapshot for the session field."""
    latest_persistent_undo_item = getattr(deps, "latest_persistent_undo_item", lambda _editor, _field_index: None)
    persistent_undo_items = getattr(deps, "persistent_undo_items", None)
    return history_snapshot_for_field(
        editor,
        field_index=session.field_index,
        session=session,
        history_size=_history_size(editor, deps),
        can_persistent_undo=deps.can_persistent_undo,
        latest_persistent_undo_item=latest_persistent_undo_item,
        persistent_undo_items=persistent_undo_items,
    )


def _history_size(editor: Any, deps: HistoryDeps) -> object:
    if not hasattr(deps, "config"):
        return DEFAULT_EDITOR_HISTORY_SIZE
    try:
        config = deps.config(editor)
    except (AttributeError, TypeError):
        return DEFAULT_EDITOR_HISTORY_SIZE
    return config.get("editor_history_size", DEFAULT_EDITOR_HISTORY_SIZE)


def undo(editor: Any, deps: HistoryDeps) -> None:
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


def redo(editor: Any, deps: HistoryDeps) -> None:
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


def history_jump(editor: Any, payload: Any, deps: HistoryDeps) -> None:
    """Restore a selected undo/redo history depth."""
    session, _source_path = deps.session_and_source(editor)
    if deps.is_busy(session):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    direction, steps = _history_jump_request(editor, payload, deps)
    if direction is None or steps is None:
        deps.eval_status(editor, t("editor.status.history_selection_unavailable"))
        return
    entries = _history_jump_entries(session, direction, steps)
    if entries is None:
        if _restore_persistent_history_jump(editor, session, direction, steps, deps):
            return
        deps.eval_status(editor, t("editor.status.history_selection_unavailable"))
        return
    for entry in entries:
        deps.restore_history_entry(
            editor,
            session,
            entry,
            redo_current=direction == "undo",
            status=undo_status_message(entry) if direction == "undo" else redo_status_message(entry),
        )


def _restore_persistent_history_jump(
    editor: Any,
    session: EditorSession,
    direction: str,
    steps: int,
    deps: HistoryDeps,
) -> bool:
    if direction != "undo" or session.undo_history.entries:
        return False
    restore_persistent_steps = getattr(deps, "restore_persistent_undo_steps", None)
    if not callable(restore_persistent_steps) or not restore_persistent_steps(editor, session, steps):
        return False
    sync_history_availability(editor, session, deps)
    request_history_availability_after_edit(editor, session, deps)
    return True


def _history_jump_request(editor: Any, payload: Any, deps: HistoryDeps) -> tuple[str | None, int | None]:
    field_ord = getattr(payload, "field_ord", None)
    if field_ord is None or int(field_ord) != int(deps.current_field_index(editor)):
        return None, None
    direction = getattr(payload, "history_direction", None)
    steps = getattr(payload, "history_steps", None)
    max_steps = normalize_editor_history_size(_history_size(editor, deps))
    if direction not in {"undo", "redo"} or not isinstance(steps, int) or steps < 1 or steps > max_steps:
        return None, None
    return direction, steps


def _history_jump_entries(
    session: EditorSession,
    direction: str,
    steps: int,
) -> list[UndoEntry] | None:
    stack = session.undo_history if direction == "undo" else session.redo_history
    if len(stack.entries) < steps:
        return None
    entries: list[UndoEntry] = []
    for _index in range(steps):
        entry = stack.pop()
        if entry is None:
            return None
        entries.append(entry)
    return entries


def restore_history_entry(
    editor: Any,
    session: EditorSession,
    entry: UndoEntry,
    *,
    redo_current: bool,
    status: str,
    deps: HistoryDeps,
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
