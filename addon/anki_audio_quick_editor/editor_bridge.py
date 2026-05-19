"""Bridge command decoding and dispatch for the editor UI."""

from __future__ import annotations

import json
import logging
from typing import Any

from .contracts_generated import FrontendLogPayload
from .diagnostics_runtime import (
    capture_exception,
    new_operation_id,
    record_breadcrumb,
    record_frontend_error,
)
from .editor_actions import (
    CMD_ANALYZE_FIELD,
    CMD_COMMAND_PAYLOAD,
    CMD_DELETE_REST,
    CMD_DELETE_SELECTION,
    CMD_DENOISE_STANDARD,
    CMD_REDO,
    CMD_RNNOISE,
    CMD_SETTINGS,
    decode_editor_command_payload,
)
from .errors import AudioQuickEditorError
from .i18n import t

logger = logging.getLogger(__name__)
CONTRACT_DECODE_ERRORS = (AssertionError, TypeError, ValueError)


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
        if deps.handle_non_processing_command(editor, payload.command):
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


def handle_non_processing_command(editor: Any, command: str, deps: Any) -> bool:
    """Handle commands that do not apply an audio edit state."""
    if command == "aqe:scan":
        deps.eval_status(editor, "")
        editor.web.eval("window.__aqeScan && window.__aqeScan()")
        return True
    handlers = {
        "aqe:analyze": deps.analyze_current_async,
        CMD_ANALYZE_FIELD: deps.analyze_field_from_frontend,
        "aqe:set-cursor": deps.set_cursor_from_web,
        "aqe:play": deps.play,
        "aqe:frontend-log": deps.handle_editor_frontend_log,
        "aqe:show-file": deps.show_current_audio_file,
        "aqe:play-ended": deps.play_ended,
        "aqe:undo": deps.undo,
        CMD_REDO: deps.redo,
        CMD_SETTINGS: deps.open_settings_from_editor,
        CMD_DENOISE_STANDARD: deps.denoise_standard_async,
        CMD_RNNOISE: deps.rnnoise_async,
        CMD_DELETE_SELECTION: deps.delete_selection_from_frontend,
        CMD_DELETE_REST: deps.delete_selection_from_frontend,
    }
    handler = handlers.get(command)
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
    payload = _decode_frontend_log_payload(raw_payload)
    if payload is None:
        return

    level = payload.level.value
    stack = str(getattr(payload, "stack", "") or "")
    _log_frontend(level, _render_frontend_log("editor frontend", payload.message, payload.context, stack))
    scope = str(getattr(payload, "scope", "") or "editor")
    operation_id = str(getattr(payload, "operation_id", "") or "")
    record_breadcrumb(
        "frontend.log",
        source=scope,
        level=_breadcrumb_level(level),
        operation="frontend.log",
        operation_id=operation_id,
        boundary="editor.frontend",
        context=_frontend_log_context(payload, level),
    )
    if level == "error":
        record_frontend_error(
            "editor.frontend",
            message=payload.message,
            stack=stack,
            source=scope,
            operation="editor.frontend",
            operation_id=operation_id,
            context=payload.context,
        )

def _decode_frontend_log_payload(raw_payload: Any) -> FrontendLogPayload | None:
    try:
        return FrontendLogPayload.from_dict(raw_payload)
    except CONTRACT_DECODE_ERRORS:
        logger.warning("editor frontend_log: invalid payload")
        return None


def _render_frontend_log(prefix: str, message: str, context: Any, stack: str) -> str:
    rendered = f"{prefix}: {message}"
    if context is not None:
        rendered = f"{rendered} | {context!r}"
    return f"{rendered}\n{stack}" if stack else rendered


def _log_frontend(level: str, rendered: str) -> None:
    log_fn = {
        "debug": logger.debug,
        "warn": logger.warning,
        "error": logger.error,
    }.get(level, logger.info)
    log_fn(rendered)


def _breadcrumb_level(level: str) -> str:
    return "error" if level == "error" else "debug"


def _frontend_log_context(payload: FrontendLogPayload, level: str) -> dict[str, Any]:
    return {
        "level": level,
        "message": payload.message,
        "filename": getattr(payload, "filename", None),
        "lineno": getattr(payload, "lineno", None),
        "colno": getattr(payload, "colno", None),
        "context": payload.context,
    }
