"""Status and basic webview state evaluation helpers."""

from __future__ import annotations

import json
from typing import Any

from ..error_codes import (
    AQE_AUDIO_PROCESSING_FAILED,
    AQE_GRAPH_ANALYSIS_FAILED,
    coded_error,
)
from .types import UserStatusPayload


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
