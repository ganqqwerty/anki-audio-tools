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


def request_graph_redraw(editor: Any, deps: Any) -> None:
    """Schedule graph redraw attempts after field contents are reloaded."""
    field_index = getattr(editor, "currentField", None)
    if field_index is None:
        field_index = getattr(editor, "last_field_index", None)
    if field_index is None:
        session = deps.sessions.get(editor)
        field_index = session.field_index if session else 0
    deps.schedule_graph_redraw_attempt(editor, int(field_index or 0), remaining=12, delay_ms=150)


def schedule_graph_redraw_attempt(
    editor: Any,
    field_index: int,
    *,
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
                deps.graph_redraw_expression(field_index),
                lambda started: deps.retry_graph_redraw(editor, field_index, bool(started), remaining - 1),
            )
        except RuntimeError:
            return

    QTimer.singleShot(delay_ms, _attempt)


def graph_redraw_expression(field_index: int) -> str:
    """Return the frontend expression that restarts graph rendering."""
    return (
        "(() => {"
        "if (!window.__aqeScan || !window.__aqeResetGraphAfterEdit) return false;"
        "window.__aqeScan();"
        f"return window.__aqeResetGraphAfterEdit({json.dumps(int(field_index))});"
        "})()"
    )


def retry_graph_redraw(editor: Any, field_index: int, started: bool, remaining: int, deps: Any) -> None:
    """Retry graph redraw when the frontend was not ready."""
    if started or remaining <= 0:
        return
    deps.schedule_graph_redraw_attempt(editor, field_index, remaining=remaining, delay_ms=100)


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
