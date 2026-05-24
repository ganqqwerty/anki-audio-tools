"""Shared editor-processing helpers."""

from __future__ import annotations

from typing import Any

from .editor_session import EditorSession


def sync_history_availability(editor: Any, session: EditorSession | None, deps: Any) -> None:
    if session is None:
        return
    deps.eval_history_availability(
        editor,
        session.field_index,
        bool(session.undo_history.entries),
        bool(session.redo_history.entries),
    )


def request_history_availability_after_edit(editor: Any, session: EditorSession | None, deps: Any) -> None:
    if session is None:
        return
    deps.request_history_availability_after_edit(
        editor,
        session.field_index,
        bool(session.undo_history.entries),
        bool(session.redo_history.entries),
    )


def cancel_graph_analysis_for_processing(editor: Any, session: EditorSession, deps: Any) -> None:
    if not (session.analysis_busy or session.analysis_busy_fields):
        return
    busy_fields = set(session.analysis_busy_fields)
    session.analysis_generation += 1
    session.analysis_generations_by_field.clear()
    session.analysis_busy_fields.clear()
    session.analysis_busy = False
    for field_index in busy_fields:
        deps.set_busy_for_field(editor, field_index, False)


def resolved_field_index(session: EditorSession | None, editor: Any, deps: Any) -> int:
    if session is not None and session.field_index is not None:
        return int(session.field_index)
    return int(deps.current_field_index(editor))


def reset_session_visualized_graph(session: EditorSession, field_index: int) -> None:
    session.visualized_filename = None
    session.visualized_duration_ms = None
    session.visualized_filenames_by_field.pop(field_index, None)
    session.visualized_durations_by_field.pop(field_index, None)
