"""Shared editor-processing helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .editor_history_snapshot import history_snapshot_for_field
from .editor_session import EditorSession

if TYPE_CHECKING:
    from .editor_deps_protocols import ProcessingSharedDeps


def sync_history_availability(editor: Any, session: EditorSession | None, deps: ProcessingSharedDeps) -> None:
    if session is None:
        return
    snapshot = _history_snapshot(editor, session, deps)
    if snapshot is not None and hasattr(deps, "eval_history_snapshot"):
        deps.eval_history_snapshot(editor, session.field_index, snapshot)
        return
    deps.eval_history_availability(
        editor,
        session.field_index,
        bool(session.undo_history.entries),
        bool(session.redo_history.entries),
    )


def request_history_availability_after_edit(
    editor: Any,
    session: EditorSession | None,
    deps: ProcessingSharedDeps,
) -> None:
    if session is None:
        return
    snapshot = _history_snapshot(editor, session, deps)
    if snapshot is not None and hasattr(deps, "request_history_snapshot_after_edit"):
        deps.request_history_snapshot_after_edit(editor, session.field_index, snapshot)
        return
    deps.request_history_availability_after_edit(
        editor,
        session.field_index,
        bool(session.undo_history.entries),
        bool(session.redo_history.entries),
    )


def _history_snapshot(editor: Any, session: EditorSession, deps: ProcessingSharedDeps) -> Any | None:
    try:
        config = deps.config(editor) if hasattr(deps, "config") else {}
        latest_persistent_undo_item = getattr(deps, "latest_persistent_undo_item", lambda _editor, _field_index: None)
        persistent_undo_items = getattr(deps, "persistent_undo_items", None)
        return history_snapshot_for_field(
            editor,
            field_index=session.field_index,
            session=session,
            history_size=config.get("editor_history_size") if isinstance(config, dict) else None,
            can_persistent_undo=deps.can_persistent_undo,
            latest_persistent_undo_item=latest_persistent_undo_item,
            persistent_undo_items=persistent_undo_items,
        )
    except (AttributeError, TypeError):
        return None


def cancel_graph_analysis_for_processing(editor: Any, session: EditorSession, deps: ProcessingSharedDeps) -> None:
    if not (session.analysis.busy or session.analysis.busy_fields):
        return
    busy_fields = set(session.analysis.busy_fields)
    session.analysis.cancel_all()
    for field_index in busy_fields:
        deps.set_busy_for_field(editor, field_index, False)


def resolved_field_index(session: EditorSession | None, editor: Any, deps: ProcessingSharedDeps) -> int:
    if session is not None and session.field_index is not None:
        return int(session.field_index)
    return int(deps.current_field_index(editor))


def reset_session_visualized_graph(session: EditorSession, field_index: int) -> None:
    session.graph.visualized_filename = None
    session.graph.visualized_duration_ms = None
    session.graph.filenames_by_field.pop(field_index, None)
    session.graph.durations_by_field.pop(field_index, None)
