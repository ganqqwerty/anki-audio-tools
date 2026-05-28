"""Frontend callback wrappers shared by editor modules."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from . import editor_dependencies, editor_frontend


def _frontend_exports() -> SimpleNamespace:
    return SimpleNamespace(
        eval_with_callback=_eval_with_callback,
        graph_redraw_expression=_graph_redraw_expression,
        history_availability_expression=_history_availability_expression,
        playback_after_edit_expression=_playback_after_edit_expression,
        pending_post_edit_playback_payload=_pending_post_edit_playback_payload,
        request_history_availability_after_edit=_request_history_availability_after_edit,
        retry_history_availability=_retry_history_availability,
        retry_graph_redraw=_retry_graph_redraw,
        schedule_graph_redraw_attempt=_schedule_graph_redraw_attempt,
        schedule_history_availability_attempt=_schedule_history_availability_attempt,
        set_busy_for_field=_set_busy_for_field,
    )


def _frontend_deps() -> SimpleNamespace:
    return editor_dependencies.frontend_deps(_frontend_exports())


def _dispose_editor_frontend_controls(editor: Any) -> None:
    editor_frontend.dispose_editor_frontend_controls(editor)


def _eval_status(editor: Any, message: editor_frontend.UserStatusPayload, kind: str = "info") -> None:
    editor_frontend.eval_status(editor, message, kind=kind)


def _eval_visualizer_status(editor: Any, message: editor_frontend.UserStatusPayload, kind: str = "info") -> None:
    editor_frontend.eval_visualizer_status(editor, message, kind=kind)


def _eval_visualizer_status_for_field(
    editor: Any,
    field_index: int,
    message: editor_frontend.UserStatusPayload,
    kind: str = "info",
) -> None:
    editor_frontend.eval_visualizer_status_for_field(editor, field_index, message, kind=kind)


def _eval_playback_state(
    editor: Any,
    field_index: int | None,
    state: str,
    cursor_ms: int,
) -> None:
    editor_frontend.eval_playback_state(editor, field_index, state, cursor_ms)


def _eval_history_availability(
    editor: Any,
    field_index: int | None,
    can_undo: bool,
    can_redo: bool,
) -> None:
    editor_frontend.eval_history_availability(editor, field_index, can_undo, can_redo)


def _request_graph_redraw(editor: Any, expected_filename: str | None = None) -> None:
    editor_frontend.request_graph_redraw(editor, _frontend_deps(), expected_filename)


def _request_playback_after_edit(
    editor: Any,
    field_index: int,
    *,
    require_graph_redraw: bool = False,
) -> None:
    editor_frontend.request_playback_after_edit(
        editor,
        field_index,
        _frontend_deps(),
        require_graph_redraw=require_graph_redraw,
    )


def _pending_post_edit_playback_payload(session: Any | None) -> dict[str, object] | None:
    return editor_frontend.pending_post_edit_playback_payload(session)


def _handle_post_edit_playback_ready(editor: Any, payload: Any) -> None:
    editor_frontend.handle_post_edit_playback_ready(editor, payload, _frontend_deps())


def _request_history_availability_after_edit(
    editor: Any,
    field_index: int,
    can_undo: bool,
    can_redo: bool,
) -> None:
    editor_frontend.request_history_availability_after_edit(
        editor,
        field_index,
        can_undo,
        can_redo,
        _frontend_deps(),
    )


def _schedule_graph_redraw_attempt(
    editor: Any,
    field_index: int,
    *,
    expected_filename: str | None = None,
    remaining: int,
    delay_ms: int,
) -> None:
    editor_frontend.schedule_graph_redraw_attempt(
        editor,
        field_index,
        expected_filename=expected_filename,
        remaining=remaining,
        delay_ms=delay_ms,
        deps=_frontend_deps(),
    )


def _schedule_history_availability_attempt(
    editor: Any,
    field_index: int,
    can_undo: bool,
    can_redo: bool,
    *,
    remaining: int,
    delay_ms: int,
) -> None:
    editor_frontend.schedule_history_availability_attempt(
        editor,
        field_index,
        can_undo,
        can_redo,
        remaining=remaining,
        delay_ms=delay_ms,
        deps=_frontend_deps(),
    )


def _graph_redraw_expression(field_index: int, expected_filename: str | None = None) -> str:
    return editor_frontend.graph_redraw_expression(field_index, expected_filename)


def _playback_after_edit_expression(field_index: int) -> str:
    return editor_frontend.playback_after_edit_expression(field_index)


def _history_availability_expression(field_index: int, can_undo: bool, can_redo: bool) -> str:
    return editor_frontend.history_availability_expression(field_index, can_undo, can_redo)


def _retry_graph_redraw(
    editor: Any,
    field_index: int,
    expected_filename: str | None,
    started: bool,
    remaining: int,
) -> None:
    editor_frontend.retry_graph_redraw(
        editor,
        field_index,
        expected_filename,
        started,
        remaining,
        _frontend_deps(),
    )


def _retry_history_availability(
    editor: Any,
    field_index: int,
    can_undo: bool,
    can_redo: bool,
    synced: bool,
    remaining: int,
) -> None:
    editor_frontend.retry_history_availability(
        editor,
        field_index,
        can_undo,
        can_redo,
        synced,
        remaining,
        _frontend_deps(),
    )


def _set_busy(editor: Any, busy: bool, message: str = "", command: str = "") -> None:
    editor_frontend.set_busy(editor, busy, message, command, _frontend_deps())


def _set_busy_for_field(
    editor: Any,
    field_index: int,
    busy: bool,
    message: str = "",
    command: str = "",
) -> None:
    editor_frontend.set_busy_for_field(editor, field_index, busy, message, command)


def _main(editor: Any, callback: Any) -> None:
    editor_frontend.main(editor, callback)


def _eval_with_callback(editor: Any, expression: str, callback: Any) -> None:
    editor_frontend.eval_with_callback(editor, expression, callback)
