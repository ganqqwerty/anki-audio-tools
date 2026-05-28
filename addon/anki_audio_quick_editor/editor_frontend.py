"""Webview evaluation helpers for the editor frontend."""

from __future__ import annotations

import json
from typing import Any

from .error_codes import (
    AQE_AUDIO_PROCESSING_FAILED,
    AQE_GRAPH_ANALYSIS_FAILED,
    coded_error,
)

UserStatusPayload = str | dict[str, str]


def dispose_editor_frontend_controls(editor: Any) -> None:
    """Dispose the mounted editor frontend controls."""
    editor.web.eval("window.__aqeEditorDispose && window.__aqeEditorDispose()")


def eval_status(editor: Any, message: UserStatusPayload, kind: str = "info") -> None:
    """Update the global editor status message."""
    payload = json.dumps(_coded_error_payload(message, kind, AQE_AUDIO_PROCESSING_FAILED))
    kind_payload = json.dumps(kind)
    editor.web.eval(f"window.__aqeSetStatus && window.__aqeSetStatus({payload}, {kind_payload})")


def eval_visualizer_status(editor: Any, message: UserStatusPayload, kind: str = "info") -> None:
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
    message: UserStatusPayload,
    kind: str = "info",
) -> None:
    """Update visualizer status for a specific editor field."""
    display_message = _coded_error_payload(message, kind, AQE_GRAPH_ANALYSIS_FAILED)
    editor.web.eval(
        "window.__aqeSetVisualizerStatus && window.__aqeSetVisualizerStatus("
        f"{json.dumps(int(field_index))}, {json.dumps(display_message)}, {json.dumps(kind)})"
    )


def _coded_error_payload(
    message: UserStatusPayload,
    kind: str,
    default_code: str,
) -> UserStatusPayload:
    if kind != "error" or isinstance(message, dict) or not message:
        return message
    return coded_error(default_code, message)


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


def eval_history_availability(
    editor: Any,
    field_index: int | None,
    can_undo: bool,
    can_redo: bool,
) -> None:
    """Update undo/redo availability for a specific editor field."""
    if field_index is None:
        return
    editor.web.eval(
        "window.__aqeSetHistoryAvailability && window.__aqeSetHistoryAvailability("
        f"{json.dumps(int(field_index))}, {json.dumps(bool(can_undo))}, {json.dumps(bool(can_redo))})"
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


def request_playback_after_edit(
    editor: Any,
    field_index: int,
    deps: Any,
    *,
    require_graph_redraw: bool = False,
) -> None:
    """Record a playback request for the next frontend ready signal."""
    session = deps.sessions.get(editor)
    if session is None:
        return
    session.pending_post_edit_playback_field_index = int(field_index)
    session.pending_post_edit_playback_generation = session.post_edit_playback_generation
    session.pending_post_edit_playback_requires_graph_redraw = bool(require_graph_redraw)
    session.pending_post_edit_playback_source_filename = session.current_filename


def pending_post_edit_playback_payload(session: Any | None) -> dict[str, object] | None:
    """Return the pending post-edit playback payload for frontend injection."""
    if session is None:
        return None
    field_index = session.pending_post_edit_playback_field_index
    generation = session.pending_post_edit_playback_generation
    if field_index is None or generation is None:
        return None
    return {
        "fieldOrd": int(field_index),
        "generation": int(generation),
        "requireGraphRedraw": bool(session.pending_post_edit_playback_requires_graph_redraw),
        "sourceFilename": session.pending_post_edit_playback_source_filename or "",
    }


def handle_post_edit_playback_ready(editor: Any, payload: Any, deps: Any) -> None:
    """Start pending post-edit playback after the frontend reports readiness."""
    session = deps.sessions.get(editor)
    if not _post_edit_playback_ready_matches(session, payload):
        return

    def _clear_if_started(started: bool) -> None:
        if not started:
            return
        current = deps.sessions.get(editor)
        if _post_edit_playback_ready_matches(current, payload):
            current.pending_post_edit_playback_field_index = None
            current.pending_post_edit_playback_generation = None
            current.pending_post_edit_playback_requires_graph_redraw = False
            current.pending_post_edit_playback_source_filename = None

    deps.eval_with_callback(
        editor,
        deps.playback_after_edit_expression(int(payload.field_ord)),
        _clear_if_started,
    )


def _post_edit_playback_ready_matches(session: Any | None, payload: Any) -> bool:
    if session is None:
        return False
    field_ord = getattr(payload, "field_ord", None)
    generation = getattr(payload, "generation", None)
    source_filename = getattr(payload, "source_filename", None)
    if field_ord is None or generation is None:
        return False
    if session.pending_post_edit_playback_field_index != int(field_ord):
        return False
    if session.pending_post_edit_playback_generation != int(generation):
        return False
    pending_source = session.pending_post_edit_playback_source_filename
    return not pending_source or source_filename == pending_source


def request_history_availability_after_edit(
    editor: Any,
    field_index: int,
    can_undo: bool,
    can_redo: bool,
    deps: Any,
) -> None:
    """Schedule undo/redo availability sync after a field replacement remount."""
    deps.schedule_history_availability_attempt(
        editor,
        int(field_index),
        bool(can_undo),
        bool(can_redo),
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


def schedule_history_availability_attempt(
    editor: Any,
    field_index: int,
    can_undo: bool,
    can_redo: bool,
    *,
    remaining: int,
    delay_ms: int,
    deps: Any,
) -> None:
    """Schedule one delayed undo/redo availability sync attempt."""
    from aqt.qt import QTimer

    def _attempt() -> None:
        if getattr(editor, "note", None) is None:
            return
        try:
            deps.eval_with_callback(
                editor,
                deps.history_availability_expression(field_index, can_undo, can_redo),
                lambda synced: deps.retry_history_availability(
                    editor,
                    field_index,
                    can_undo,
                    can_redo,
                    bool(synced),
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


def history_availability_expression(field_index: int, can_undo: bool, can_redo: bool) -> str:
    """Return the frontend expression that reapplies undo/redo availability."""
    return (
        "(() => {"
        "if (!window.__aqeSetHistoryAvailability) return false;"
        "window.__aqeScan && window.__aqeScan();"
        "window.__aqeSetHistoryAvailability("
        f"{json.dumps(int(field_index))}, {json.dumps(bool(can_undo))}, {json.dumps(bool(can_redo))}"
        ");"
        "return true;"
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


def retry_history_availability(
    editor: Any,
    field_index: int,
    can_undo: bool,
    can_redo: bool,
    synced: bool,
    remaining: int,
    deps: Any,
) -> None:
    """Retry history availability sync when the remounted frontend is not ready."""
    if synced or remaining <= 0:
        return
    deps.schedule_history_availability_attempt(
        editor,
        field_index,
        can_undo,
        can_redo,
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
