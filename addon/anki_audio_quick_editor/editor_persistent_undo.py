"""Editor-facing persistent undo helpers."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

from .audio_state import AudioEditState
from .editor_session import EditorSession, PendingEditorStatus, UndoEntry
from .editor_status import restored_status_summary, undo_status_message
from .errors import AudioQuickEditorError
from .media_paths import existing_media_file_path, media_filenames_match
from .persistent_history import (
    PersistentHistoryAppend,
    PersistentHistoryOperation,
    PersistentHistoryRepository,
    audio_edit_state_from_json,
    audio_edit_state_to_json,
    media_fingerprint,
)
from .runtime_paths import user_files_dir
from .sound_refs import replace_sound_reference, select_first_sound_reference

DB_FILENAME = "persistent_undo.sqlite3"
STANDARD_RENDER_OPERATION = "standard-render"


def history_db_path_for_editor(editor: Any) -> Path:
    """Return the add-on-owned persistent undo DB path for an editor."""
    addon_id = editor.mw.addonManager.addonFromModule(__name__)
    addon_dir = Path(editor.mw.addonManager.addonsFolder(addon_id))
    return user_files_dir(addon_dir) / DB_FILENAME


def repository_for_editor(editor: Any) -> PersistentHistoryRepository:
    """Return a persistent history repository for an editor."""
    return PersistentHistoryRepository(history_db_path_for_editor(editor))


def collection_id_for_editor(editor: Any) -> str:
    """Return a stable collection identity for add-on persistent undo rows."""
    media_dir = Path(editor.mw.col.media.dir()).resolve()
    return hashlib.sha256(str(media_dir).encode("utf-8")).hexdigest()


def can_persistent_undo(editor: Any, field_index: int | None) -> bool:
    """Return whether a persistent undo operation can currently be restored."""
    operation = _latest_for_field(editor, field_index)
    return operation is not None and _old_media_available(editor, operation)


def record_standard_persistent_undo(
    editor: Any,
    *,
    field_index: int,
    old_field_html: str,
    new_field_html: str,
    old_filename: str,
    new_filename: str,
    old_state: AudioEditState | None,
    new_state: AudioEditState,
    status_summary: str,
) -> None:
    """Append a persistent undo row for a standard editor render."""
    note_id = getattr(getattr(editor, "note", None), "id", None)
    if note_id is None:
        return
    media_dir = Path(editor.mw.col.media.dir())
    old_path = existing_media_file_path(media_dir, old_filename)
    new_path = existing_media_file_path(media_dir, new_filename)
    if old_path is None or new_path is None:
        return
    old_fingerprint = media_fingerprint(old_path)
    new_fingerprint = media_fingerprint(new_path)
    repository_for_editor(editor).append_operation(
        PersistentHistoryAppend(
            collection_id=collection_id_for_editor(editor),
            note_id=int(note_id),
            field_index=int(field_index),
            operation_type=STANDARD_RENDER_OPERATION,
            old_field_html=old_field_html,
            new_field_html=new_field_html,
            old_filename=old_filename,
            new_filename=new_filename,
            old_state_json=audio_edit_state_to_json(old_state),
            new_state_json=audio_edit_state_to_json(new_state),
            old_media_sha256=old_fingerprint.sha256,
            old_media_size=old_fingerprint.size,
            new_media_sha256=new_fingerprint.sha256,
            new_media_size=new_fingerprint.size,
            status_summary=status_summary,
            created_at_ms=_now_ms(),
        )
    )


def restore_persistent_undo(editor: Any, session: EditorSession, deps: Any) -> bool:
    """Restore the latest persistent undo operation for the current field."""
    field_index = int(deps.current_field_index(editor))
    operation = _latest_for_field(editor, field_index)
    if operation is None or not _old_media_available(editor, operation):
        return False

    field_html = editor.note.fields[field_index]
    restored_field_html = _restored_field_html(field_html, operation)
    if restored_field_html is None:
        return False

    state = audio_edit_state_from_json(operation.old_state_json) or AudioEditState(operation.old_filename)
    entry = UndoEntry(state, operation.old_filename, status_summary=operation.status_summary)
    deps.stop_session_playback(session)
    session.post_edit_playback_generation += 1
    deps.dispose_editor_frontend_controls(editor)
    editor.note.fields[field_index] = restored_field_html
    repository_for_editor(editor).mark_undone(operation.id, undone_at_ms=_now_ms())
    session.state = state
    session.current_filename = operation.old_filename
    session.field_index = field_index
    session.status_summary = restored_status_summary(entry)
    session.next_status_summary = ""
    session.pending_status = PendingEditorStatus(field_index, message=undo_status_message(entry))
    session.cursor_ms = 0
    session.playback_active = False
    session.playback_paused = False
    deps.request_playback_after_edit(
        editor,
        field_index,
        require_graph_redraw=field_index in session.graph_active_fields,
    )
    editor.loadNote(focusTo=field_index)
    session.pending_status = None
    deps.eval_playback_state(editor, field_index, "stopped", 0)
    return True


def _latest_for_field(editor: Any, field_index: int | None) -> PersistentHistoryOperation | None:
    note_id = getattr(getattr(editor, "note", None), "id", None)
    if field_index is None or note_id is None:
        return None
    return repository_for_editor(editor).latest_undoable(
        collection_id_for_editor(editor),
        int(note_id),
        int(field_index),
    )


def _restored_field_html(field_html: str, operation: PersistentHistoryOperation) -> str | None:
    if field_html == operation.new_field_html:
        return operation.old_field_html
    try:
        selection = select_first_sound_reference(field_html)
    except AudioQuickEditorError:
        return None
    if selection.selected is not None and media_filenames_match(selection.selected.filename, operation.new_filename):
        return replace_sound_reference(field_html, selection.selected, operation.old_filename)
    return None


def _old_media_available(editor: Any, operation: PersistentHistoryOperation) -> bool:
    media_dir = Path(editor.mw.col.media.dir())
    old_path = existing_media_file_path(media_dir, operation.old_filename)
    if old_path is None:
        return False
    return _media_matches(old_path, operation.old_media_sha256, operation.old_media_size)


def _media_matches(path: Path, sha256: str, size: int) -> bool:
    try:
        fingerprint = media_fingerprint(path)
    except OSError:
        return False
    return fingerprint.sha256 == sha256 and fingerprint.size == size


def _now_ms() -> int:
    return int(time.time() * 1000)
