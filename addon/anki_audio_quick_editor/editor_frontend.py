"""Webview evaluation helpers for the editor frontend."""

from __future__ import annotations

import json
from typing import Any


def dispose_editor_frontend_controls(editor: Any) -> None:
    """Dispose the mounted editor frontend controls."""
    editor.web.eval("window.__aqeEditorDispose && window.__aqeEditorDispose()")


def eval_status(editor: Any, message: str, kind: str = "info") -> None:
    """Update the global editor status message."""
    payload = json.dumps(message)
    kind_payload = json.dumps(kind)
    editor.web.eval(f"window.__aqeSetStatus && window.__aqeSetStatus({payload}, {kind_payload})")


def eval_visualizer_status(editor: Any, message: str, kind: str = "info") -> None:
    """Update visualizer status for the active editor field."""
    field_index = getattr(editor, "currentField", None)
    if field_index is None:
        field_index = getattr(editor, "last_field_index", None)
    if field_index is None:
        return
    eval_visualizer_status_for_field(editor, int(field_index), message, kind=kind)


def eval_visualizer_status_for_field(
    editor: Any,
    field_index: int,
    message: str,
    kind: str = "info",
) -> None:
    """Update visualizer status for a specific editor field."""
    editor.web.eval(
        "window.__aqeSetVisualizerStatus && window.__aqeSetVisualizerStatus("
        f"{json.dumps(int(field_index))}, {json.dumps(message)}, {json.dumps(kind)})"
    )


def eval_playback_state(
    editor: Any,
    field_index: int | None,
    state: str,
    cursor_ms: int,
) -> None:
    """Update playback state for a specific editor field."""
    if field_index is None:
        return
    editor.web.eval(
        "window.__aqeSetPlaybackState && window.__aqeSetPlaybackState("
        f"{json.dumps(int(field_index))}, {json.dumps(state)}, {json.dumps(int(cursor_ms))})"
    )


def request_graph_redraw(editor: Any, deps: Any, expected_filename: str | None = None) -> None:
    """Schedule graph redraw attempts after field contents are reloaded."""
    field_index = getattr(editor, "currentField", None)
    if field_index is None:
        field_index = getattr(editor, "last_field_index", None)
    if field_index is None:
        session = deps.sessions.get(editor)
        field_index = session.field_index if session else 0
    deps.schedule_graph_redraw_attempt(
        editor,
        int(field_index or 0),
        expected_filename=expected_filename,
        remaining=12,
        delay_ms=150,
    )


def request_playback_after_edit(editor: Any, field_index: int, deps: Any) -> None:
    """Schedule playback after a successful audio field replacement."""
    session = deps.sessions.get(editor)
    generation = session.post_edit_playback_generation if session else 0
    deps.schedule_playback_after_edit_attempt(
        editor,
        int(field_index),
        generation,
        remaining=12,
        delay_ms=150,
    )


def schedule_graph_redraw_attempt(
    editor: Any,
    field_index: int,
    *,
    expected_filename: str | None = None,
    remaining: int,
    delay_ms: int,
    deps: Any,
) -> None:
    """Schedule one delayed graph redraw attempt."""
    from aqt.qt import QTimer

    def _attempt() -> None:
        if getattr(editor, "note", None) is None:
            return
        try:
            deps.eval_with_callback(
                editor,
                deps.graph_redraw_expression(field_index, expected_filename),
                lambda started: deps.retry_graph_redraw(
                    editor,
                    field_index,
                    expected_filename,
                    bool(started),
                    remaining - 1,
                ),
            )
        except RuntimeError:
            return

    QTimer.singleShot(delay_ms, _attempt)


def schedule_playback_after_edit_attempt(
    editor: Any,
    field_index: int,
    generation: int,
    *,
    remaining: int,
    delay_ms: int,
    deps: Any,
) -> None:
    """Schedule one delayed playback-after-edit attempt."""
    from aqt.qt import QTimer

    def _attempt() -> None:
        if getattr(editor, "note", None) is None:
            return
        session = deps.sessions.get(editor)
        if session and session.post_edit_playback_generation != generation:
            return
        try:
            deps.eval_with_callback(
                editor,
                deps.playback_after_edit_expression(field_index),
                lambda started: deps.retry_playback_after_edit(
                    editor,
                    field_index,
                    generation,
                    bool(started),
                    remaining - 1,
                ),
            )
        except RuntimeError:
            return

    QTimer.singleShot(delay_ms, _attempt)


def graph_redraw_expression(field_index: int, expected_filename: str | None = None) -> str:
    """Return the frontend expression that restarts graph rendering."""
    return (
        "(() => {"
        "if (!window.__aqeScan || !window.__aqeResetGraphAfterEdit) return false;"
        "window.__aqeScan();"
        "return window.__aqeResetGraphAfterEdit("
        f"{json.dumps(int(field_index))}, {json.dumps(expected_filename)}"
        ");"
        "})()"
    )


def playback_after_edit_expression(field_index: int) -> str:
    """Return the frontend expression that starts playback after an edit."""
    return (
        "(() => {"
        "if (!window.__aqeScan || !window.__aqePlayAfterEdit) return false;"
        "window.__aqeScan();"
        f"return window.__aqePlayAfterEdit({json.dumps(int(field_index))});"
        "})()"
    )


def retry_graph_redraw(
    editor: Any,
    field_index: int,
    expected_filename: str | None,
    started: bool,
    remaining: int,
    deps: Any,
) -> None:
    """Retry graph redraw when the frontend was not ready."""
    if started or remaining <= 0:
        return
    deps.schedule_graph_redraw_attempt(
        editor,
        field_index,
        expected_filename=expected_filename,
        remaining=remaining,
        delay_ms=100,
    )


def retry_playback_after_edit(
    editor: Any,
    field_index: int,
    generation: int,
    started: bool,
    remaining: int,
    deps: Any,
) -> None:
    """Retry playback after edit when the frontend was not ready."""
    if started or remaining <= 0:
        return
    deps.schedule_playback_after_edit_attempt(
        editor,
        field_index,
        generation,
        remaining=remaining,
        delay_ms=100,
    )


def set_busy(editor: Any, busy: bool, message: str, command: str, deps: Any) -> None:
    """Set busy state for the active field."""
    field_index = getattr(editor, "currentField", None)
    if field_index is None:
        field_index = getattr(editor, "last_field_index", None)
    if field_index is None:
        session = deps.sessions.get(editor)
        field_index = session.field_index if session else None
    if field_index is None:
        return
    deps.set_busy_for_field(editor, int(field_index), busy, message, command)


def set_busy_for_field(
    editor: Any,
    field_index: int,
    busy: bool,
    message: str = "",
    command: str = "",
) -> None:
    """Set busy state for a specific editor field."""
    editor.web.eval(
        "window.__aqeSetBusy && window.__aqeSetBusy("
        f"{json.dumps(int(field_index))}, {json.dumps(busy)}, "
        f"{json.dumps(message)}, {json.dumps(command)})"
    )


def main(editor: Any, callback: Any) -> None:
    """Run a callback on Anki's main thread."""
    editor.mw.taskman.run_on_main(callback)


def eval_with_callback(editor: Any, expression: str, callback: Any) -> None:
    """Evaluate JavaScript and deliver the result to a Python callback."""
    if hasattr(editor.web, "evalWithCallback"):
        editor.web.evalWithCallback(expression, callback)
        return
    page = editor.web.page() if hasattr(editor.web, "page") else None
    if page is not None and hasattr(page, "runJavaScript"):
        page.runJavaScript(expression, callback)
