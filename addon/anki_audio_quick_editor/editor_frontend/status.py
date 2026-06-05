"""Status and basic webview state evaluation helpers."""

from __future__ import annotations

import json
import logging
from typing import Any

from ..error_codes import (
    AQE_AUDIO_PROCESSING_FAILED,
    AQE_GRAPH_ANALYSIS_FAILED,
    coded_error,
)
from .types import UserStatusPayload

logger = logging.getLogger(__name__)


def dispose_editor_frontend_controls(editor: Any) -> None:
    """Dispose the mounted editor frontend controls."""
    editor.web.eval("window.__aqeEditorDispose && window.__aqeEditorDispose()")


def eval_status(editor: Any, message: UserStatusPayload, kind: str = "info") -> None:
    """Update the global editor status message."""
    display_message = _coded_error_payload(message, kind, AQE_AUDIO_PROCESSING_FAILED)
    _log_displayed_error("editor status", display_message, kind)
    payload = json.dumps(display_message)
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
    _log_displayed_error(f"editor visualizer status field={int(field_index)}", display_message, kind)
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


def _log_displayed_error(surface: str, message: UserStatusPayload, kind: str) -> None:
    if kind != "error" or not message:
        return
    logger.error("%s displayed error: %s", surface, _status_log_text(message))


def _status_log_text(message: UserStatusPayload) -> str:
    if not isinstance(message, dict):
        return message
    code = message.get("code", "")
    text = message.get("message", "")
    details = message.get("details", "")
    rendered = f"{code}: {text}" if code else text
    if details:
        return f"{rendered} | details={details}"
    return rendered
