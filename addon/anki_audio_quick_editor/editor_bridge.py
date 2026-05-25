"""Bridge command decoding and dispatch for the editor UI."""

from __future__ import annotations

import json
import logging
from typing import Any

from .diagnostics_runtime import (
    capture_exception,
    new_operation_id,
    record_breadcrumb,
)
from .editor_actions import (
    CMD_ANALYZE_FIELD,
    CMD_COMMAND_PAYLOAD,
    CMD_CONVERT,
    CMD_DELETE_REST,
    CMD_DELETE_SELECTION,
    CMD_DENOISE_STANDARD,
    CMD_DPDFNET,
    CMD_OPEN_URL,
    CMD_PITCH_HUM,
    CMD_REDO,
    CMD_RNNOISE,
    CMD_SAVE_SPLIT_DEFAULTS,
    CMD_SETTINGS,
    CMD_SHARE,
    CMD_VOICE_ONLY,
    EditorCommandPayload,
    decode_editor_command_payload,
)
from .errors import AudioQuickEditorError
from .frontend_logs import handle_frontend_log_payload
from .i18n import t

logger = logging.getLogger(__name__)


def handle_bridge_command(editor: Any, command: str, deps: Any) -> None:
    """Decode and dispatch one command from Anki's editor bridge."""
    operation_id = new_operation_id("editor")
    record_breadcrumb(
        "editor.command.received",
        source="editor",
        operation="editor.command",
        operation_id=operation_id,
        boundary="editor.bridge",
        context={"command": command, "field_index": getattr(editor, "currentField", None)},
    )
    if command == CMD_COMMAND_PAYLOAD:
        deps.handle_pending_command_payload(editor)
        return
    payload = decode_editor_command_payload(command)
    try:
        if payload.field_ord is not None:
            editor.currentField = payload.field_ord
        if deps.handle_non_processing_command(editor, payload):
            return
        deps.update_state_and_render(editor, payload)
    except AudioQuickEditorError as exc:
        record_breadcrumb(
            "editor.command.rejected",
            source="editor",
            level="warning",
            operation="editor.command",
            operation_id=operation_id,
            boundary="editor.bridge",
            context={"command": command, "message": str(exc)},
        )
        deps.set_busy(editor, False)
        deps.eval_status(editor, str(exc), kind="error")
    except Exception as exc:  # pragma: no cover - defensive boundary for Anki bridge
        capture_exception(
            "editor.bridge",
            exc,
            operation="editor.command",
            operation_id=operation_id,
            user_message=t("editor.processing_failed_note_unchanged", {"error": exc}),
            context={"command": command, "field_index": getattr(editor, "currentField", None)},
            log=logger,
        )
        deps.set_busy(editor, False)
        deps.eval_status(editor, t("editor.processing_failed_note_unchanged", {"error": exc}), kind="error")


def handle_pending_command_payload(editor: Any, deps: Any) -> None:
    """Pop a rich command payload from the webview and dispatch it."""
    expression = """
    (() => {
      const payload = window.__aqePendingCommandPayload || null;
      window.__aqePendingCommandPayload = null;
      return payload;
    })()
    """

    def _continue(raw_payload: Any) -> None:
        if raw_payload is None:
            deps.set_busy(editor, False)
            return
        deps.handle_bridge_command(editor, json.dumps(raw_payload))

    deps.eval_with_callback(editor, expression, _continue)


def handle_non_processing_command(editor: Any, command: str | EditorCommandPayload, deps: Any) -> bool:
    """Handle commands that do not apply an audio edit state."""
    payload = decode_editor_command_payload(command)
    if payload.command == "aqe:scan":
        deps.eval_status(editor, "")
        editor.web.eval("window.__aqeScan && window.__aqeScan()")
        return True
    if payload.command == "aqe:analyze":
        deps.analyze_current_async(editor, graph_settings=payload.graph_settings)
        return True
    if payload.command == CMD_CONVERT:
        deps.convert_async(editor, payload)
        return True
    if payload.command == CMD_DPDFNET:
        deps.dpdfnet_async(editor, payload)
        return True
    if payload.command == CMD_PITCH_HUM:
        deps.pitch_hum_async(editor, payload)
        return True
    if payload.command == CMD_SHARE:
        deps.share_current_audio_file(editor, payload)
        return True
    if payload.command == CMD_OPEN_URL:
        if payload.url is None:
            deps.eval_status(editor, t("external_link.open_failed"), kind="error")
            return True
        deps.open_external_url(payload.url)
        return True
    handlers = {
        CMD_ANALYZE_FIELD: deps.analyze_field_from_frontend,
        "aqe:set-cursor": deps.set_cursor_from_web,
        "aqe:play": deps.play,
        "aqe:frontend-log": deps.handle_editor_frontend_log,
        CMD_SAVE_SPLIT_DEFAULTS: deps.save_split_defaults_from_frontend,
        "aqe:show-file": deps.show_current_audio_file,
        "aqe:play-ended": deps.play_ended,
        "aqe:undo": deps.undo,
        CMD_REDO: deps.redo,
        CMD_SETTINGS: deps.open_settings_from_editor,
        CMD_DENOISE_STANDARD: deps.denoise_standard_async,
        CMD_RNNOISE: deps.rnnoise_async,
        CMD_VOICE_ONLY: deps.voice_only_async,
        CMD_DELETE_SELECTION: deps.delete_selection_from_frontend,
        CMD_DELETE_REST: deps.delete_selection_from_frontend,
    }
    handler = handlers.get(payload.command)
    if handler is None:
        return False
    handler(editor)
    return True


def handle_editor_frontend_log(editor: Any, deps: Any) -> None:
    """Read and log one frontend diagnostic payload."""
    deps.eval_with_callback(
        editor,
        "window.__aqePopFrontendLog ? window.__aqePopFrontendLog() : null",
        deps.log_editor_frontend_payload,
    )


def log_editor_frontend_payload(raw_payload: Any) -> None:
    """Log a frontend diagnostic payload after contract validation."""
    if raw_payload is None:
        return
    handle_frontend_log_payload(
        raw_payload,
        logger=logger,
        default_scope="editor",
        boundary="editor.frontend",
        log_prefix="editor frontend",
        invalid_label="editor frontend_log",
    )
