"""Editor-facing persistent undo helpers."""

from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .audio_state import AudioEditState
from .editor_edit_history import UndoEntry
from .editor_history_settings import normalize_editor_history_size
from .editor_reload_status import reload_editor_with_pending_status
from .editor_session import EditorSession
from .editor_status import restored_status_summary, undo_status_message
from .error_codes import AQE_PERSISTENT_UNDO_UNAVAILABLE, coded_error
from .i18n import t
from .media_paths import existing_media_file_path
from .persistent_history import (
    PersistentHistoryAppend,
    PersistentHistoryOperation,
    PersistentHistoryRepository,
    PersistentHistoryUnavailableError,
    audio_edit_state_from_json,
    audio_edit_state_to_json,
    media_fingerprint,
)
from .persistent_undo_chain import (
    build_persistent_undo_chain,
    persistent_undo_menu_items,
    restored_field_html,
)
from .runtime_paths import user_files_dir

if TYPE_CHECKING:
    from .editor_deps_protocols import PersistentUndoDeps

DB_FILENAME = "persistent_undo.sqlite3"
STANDARD_RENDER_OPERATION = "standard-render"
logger = logging.getLogger(__name__)


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
    try:
        operation = _latest_for_field(editor, field_index)
    except PersistentHistoryUnavailableError:
        logger.debug(
            "persistent undo availability false reason=sqlite_unavailable field_index=%s",
            field_index,
        )
        return False
    if operation is None or field_index is None:
        logger.debug(
            "persistent undo availability false reason=no_operation field_index=%s",
            field_index,
        )
        return False
    field_html = editor.note.fields[int(field_index)]
    if not _old_media_available(editor, operation):
        logger.debug(
            "persistent undo availability false reason=old_media_unavailable operation_id=%s field_index=%s old=%s",
            operation.id,
            field_index,
            operation.old_filename,
        )
        return False
    if restored_field_html(field_html, operation) is None:
        logger.debug(
            "persistent undo availability false reason=current_field_not_applicable operation_id=%s field_index=%s new=%s",
            operation.id,
            field_index,
            operation.new_filename,
        )
        return False
    logger.debug(
        "persistent undo availability true operation_id=%s field_index=%s old=%s new=%s",
        operation.id,
        field_index,
        operation.old_filename,
        operation.new_filename,
    )
    return True


def latest_persistent_undo_item(editor: Any, field_index: int | None) -> dict[str, str] | None:
    """Return a frontend menu item for the latest executable persistent undo."""
    items = persistent_undo_items(editor, field_index, 1)
    return items[0] if items else None


def persistent_undo_items(editor: Any, field_index: int | None, history_size: object) -> list[dict[str, str]]:
    """Return frontend menu items for the executable persistent undo chain."""
    try:
        operations = _undo_chain_for_field(editor, field_index, history_size)
    except PersistentHistoryUnavailableError:
        return []
    return persistent_undo_menu_items(
        operations,
        empty_label=t("editor.history.undo_empty_label"),
    )


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
        logger.debug("persistent undo record skipped reason=no_note_id field_index=%s", field_index)
        return
    media_dir = Path(editor.mw.col.media.dir())
    old_path = existing_media_file_path(media_dir, old_filename)
    new_path = existing_media_file_path(media_dir, new_filename)
    if old_path is None or new_path is None:
        logger.debug(
            "persistent undo record skipped reason=missing_media note_id=%s field_index=%s old_exists=%s new_exists=%s old=%s new=%s",
            note_id,
            field_index,
            old_path is not None,
            new_path is not None,
            old_filename,
            new_filename,
        )
        return
    old_fingerprint = media_fingerprint(old_path)
    new_fingerprint = media_fingerprint(new_path)
    operation_id = repository_for_editor(editor).append_operation(
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
    logger.debug(
        "persistent undo record stored operation_id=%s note_id=%s field_index=%s old=%s new=%s",
        operation_id,
        note_id,
        field_index,
        old_filename,
        new_filename,
    )


def restore_persistent_undo(editor: Any, session: EditorSession, deps: PersistentUndoDeps) -> bool:
    """Restore the latest persistent undo operation for the current field."""
    return restore_persistent_undo_steps(editor, session, 1, deps)


def restore_persistent_undo_steps(editor: Any, session: EditorSession, steps: int, deps: PersistentUndoDeps) -> bool:
    """Restore a selected depth from persistent undo history."""
    field_index = int(deps.current_field_index(editor))
    try:
        operations = _undo_chain_for_field(editor, field_index, steps)
    except PersistentHistoryUnavailableError:
        logger.debug("persistent undo restore unavailable reason=sqlite_unavailable field_index=%s", field_index)
        _show_persistent_undo_unavailable(editor, deps)
        return True
    if len(operations) < steps:
        logger.debug(
            "persistent undo restore skipped reason=insufficient_chain field_index=%s requested_steps=%s available_steps=%s",
            field_index,
            steps,
            len(operations),
        )
        return False

    field_html = editor.note.fields[field_index]
    restored_html = field_html
    for operation in operations[:steps]:
        next_field_html = restored_field_html(restored_html, operation)
        if next_field_html is None:
            logger.debug(
                "persistent undo restore skipped reason=chain_became_inapplicable field_index=%s operation_id=%s new=%s",
                field_index,
                operation.id,
                operation.new_filename,
            )
            return False
        restored_html = next_field_html

    operation = operations[steps - 1]
    state = audio_edit_state_from_json(operation.old_state_json) or AudioEditState(operation.old_filename)
    entry = UndoEntry(state, operation.old_filename, status_summary=operation.status_summary)
    deps.stop_session_playback(session)
    session.post_edit_playback.generation += 1
    editor.note.fields[field_index] = restored_html
    repository = repository_for_editor(editor)
    undone_at_ms = _now_ms()
    for restored_operation in operations[:steps]:
        repository.mark_undone(restored_operation.id, undone_at_ms=undone_at_ms)
    session.state = state
    session.current_filename = operation.old_filename
    session.field_index = field_index
    session.status_summary = restored_status_summary(entry)
    session.processing.next_status_summary = ""
    session.cursor_ms = 0
    session.playback.active = False
    session.playback.paused = False
    deps.request_playback_after_edit(
        editor,
        field_index,
        require_graph_redraw=field_index in session.analysis.graph_active_fields,
    )
    reload_editor_with_pending_status(
        editor,
        session,
        field_index,
        message=undo_status_message(entry),
        deps=deps,
    )
    deps.eval_playback_state(editor, field_index, "stopped", 0)
    logger.debug(
        "persistent undo restored operation_id=%s note_id=%s field_index=%s old=%s new=%s steps=%s",
        operation.id,
        operation.note_id,
        field_index,
        operation.old_filename,
        operation.new_filename,
        steps,
    )
    return True


def _latest_for_field(editor: Any, field_index: int | None) -> PersistentHistoryOperation | None:
    note_id = getattr(getattr(editor, "note", None), "id", None)
    if field_index is None or note_id is None:
        logger.debug(
            "persistent undo latest skipped reason=%s field_index=%s note_id=%s",
            "no_field_index" if field_index is None else "no_note_id",
            field_index,
            note_id,
        )
        return None
    return repository_for_editor(editor).latest_undoable(
        collection_id_for_editor(editor),
        int(note_id),
        int(field_index),
    )


def _recent_for_field(
    editor: Any,
    field_index: int | None,
    history_size: object,
) -> list[PersistentHistoryOperation]:
    note_id = getattr(getattr(editor, "note", None), "id", None)
    if field_index is None or note_id is None:
        logger.debug(
            "persistent undo recent skipped reason=%s field_index=%s note_id=%s",
            "no_field_index" if field_index is None else "no_note_id",
            field_index,
            note_id,
        )
        return []
    return repository_for_editor(editor).recent_undoable(
        collection_id_for_editor(editor),
        int(note_id),
        int(field_index),
        limit=normalize_editor_history_size(history_size),
    )


def _undo_chain_for_field(
    editor: Any,
    field_index: int | None,
    history_size: object,
) -> list[PersistentHistoryOperation]:
    if field_index is None:
        return []
    try:
        field_html = editor.note.fields[int(field_index)]
    except (AttributeError, IndexError, TypeError, ValueError):
        return []
    result = build_persistent_undo_chain(
        current_field_html=field_html,
        operations=_recent_for_field(editor, field_index, history_size),
        old_media_available=lambda operation: _old_media_available(editor, operation),
    )
    if result.break_reason is not None:
        logger.debug(
            "persistent undo chain stopped reason=%s field_index=%s operation_id=%s",
            result.break_reason,
            field_index,
            result.break_operation_id,
        )
    return result.operations


def _show_persistent_undo_unavailable(editor: Any, deps: PersistentUndoDeps) -> None:
    deps.eval_status(
        editor,
        coded_error(
            AQE_PERSISTENT_UNDO_UNAVAILABLE,
            t("editor.status.persistent_undo_unavailable"),
        ),
        kind="error",
    )


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
