"""Frontend callback wrappers shared by editor modules."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from . import editor_dependencies, editor_frontend


def _frontend_exports() -> SimpleNamespace:
    return SimpleNamespace(
        eval_with_callback=_eval_with_callback,
        graph_redraw_expression=_graph_redraw_expression,
        retry_graph_redraw=_retry_graph_redraw,
        schedule_graph_redraw_attempt=_schedule_graph_redraw_attempt,
        set_busy_for_field=_set_busy_for_field,
    )


def _frontend_deps() -> SimpleNamespace:
    return editor_dependencies.frontend_deps(_frontend_exports())


def _dispose_editor_frontend_controls(editor: Any) -> None:
    editor_frontend.dispose_editor_frontend_controls(editor)


def _eval_status(editor: Any, message: str, kind: str = "info") -> None:
    editor_frontend.eval_status(editor, message, kind=kind)


def _eval_visualizer_status(editor: Any, message: str, kind: str = "info") -> None:
    editor_frontend.eval_visualizer_status(editor, message, kind=kind)


def _eval_visualizer_status_for_field(
    editor: Any,
    field_index: int,
    message: str,
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


def _request_graph_redraw(editor: Any) -> None:
    editor_frontend.request_graph_redraw(editor, _frontend_deps())


def _schedule_graph_redraw_attempt(
    editor: Any,
    field_index: int,
    *,
    remaining: int,
    delay_ms: int,
) -> None:
    editor_frontend.schedule_graph_redraw_attempt(
        editor,
        field_index,
        remaining=remaining,
        delay_ms=delay_ms,
        deps=_frontend_deps(),
    )


def _graph_redraw_expression(field_index: int) -> str:
    return editor_frontend.graph_redraw_expression(field_index)


def _retry_graph_redraw(editor: Any, field_index: int, started: bool, remaining: int) -> None:
    editor_frontend.retry_graph_redraw(
        editor,
        field_index,
        started,
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
