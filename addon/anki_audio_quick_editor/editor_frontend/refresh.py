"""Editor frontend graph redraw and history availability refresh helpers."""

from __future__ import annotations

import json
from typing import Any


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
