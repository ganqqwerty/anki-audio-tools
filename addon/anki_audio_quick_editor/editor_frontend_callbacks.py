"""Frontend callback wrappers shared by editor modules."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from . import editor_dependencies, editor_frontend


def _frontend_exports() -> SimpleNamespace:
    return SimpleNamespace(
        eval_with_callback=_eval_with_callback,
        graph_redraw_expression=_graph_redraw_expression,
        playback_after_edit_expression=_playback_after_edit_expression,
        retry_playback_after_edit=_retry_playback_after_edit,
        retry_graph_redraw=_retry_graph_redraw,
        schedule_graph_redraw_attempt=_schedule_graph_redraw_attempt,
        schedule_playback_after_edit_attempt=_schedule_playback_after_edit_attempt,
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


def _request_graph_redraw(editor: Any, expected_filename: str | None = None) -> None:
    editor_frontend.request_graph_redraw(editor, _frontend_deps(), expected_filename)


def _request_playback_after_edit(editor: Any, field_index: int) -> None:
    editor_frontend.request_playback_after_edit(editor, field_index, _frontend_deps())


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


def _schedule_playback_after_edit_attempt(
    editor: Any,
    field_index: int,
    generation: int,
    *,
    remaining: int,
    delay_ms: int,
) -> None:
    editor_frontend.schedule_playback_after_edit_attempt(
        editor,
        field_index,
        generation,
        remaining=remaining,
        delay_ms=delay_ms,
        deps=_frontend_deps(),
    )


def _graph_redraw_expression(field_index: int, expected_filename: str | None = None) -> str:
    return editor_frontend.graph_redraw_expression(field_index, expected_filename)


def _playback_after_edit_expression(field_index: int) -> str:
    return editor_frontend.playback_after_edit_expression(field_index)


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


def _retry_playback_after_edit(
    editor: Any,
    field_index: int,
    generation: int,
    started: bool,
    remaining: int,
) -> None:
    editor_frontend.retry_playback_after_edit(
        editor,
        field_index,
        generation,
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
