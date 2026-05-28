"""Threaded settings async command bridge."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from collections.abc import Callable
from typing import Any

from ..contracts_generated import AsyncCommand, AsyncDonePayload, AsyncProgressPayload
from ..diagnostics_runtime import capture_exception, record_breadcrumb
from ..error_codes import AQE_FRONTEND_UNKNOWN_ASYNC_ERROR, coded_error
from ..webview_bridge import WebviewBridgeCommand
from .async_operations import dispatch_settings_async_op

logger = logging.getLogger("anki_audio_quick_editor.settings.commands")
CONTRACT_DECODE_ERRORS = (AssertionError, TypeError, ValueError)


def handle_async_settings_command(command: WebviewBridgeCommand, eval_fn: Callable[[str], None]) -> None:
    """Decode and run one settings async bridge command."""
    from aqt import mw

    raw_payload = command.payload
    raw_job_id = _raw_job_id(raw_payload)

    try:
        async_command = AsyncCommand.from_dict(raw_payload)
    except CONTRACT_DECODE_ERRORS as invalid_payload_error:
        message = "Invalid async command payload"
        invalid_done_payload_json = json.dumps(
            {
                "id": raw_job_id,
                "ok": False,
                "error": message,
                "user_error": coded_error(AQE_FRONTEND_UNKNOWN_ASYNC_ERROR, message),
            }
        )
        mw.taskman.run_on_main(lambda: eval_fn(f"window.onAsyncDone({invalid_done_payload_json})"))
        logger.warning("settings.async: invalid payload shape: %s", invalid_payload_error)
        return

    job_id = async_command.id
    op = async_command.op
    op_payload = async_command.payload.to_dict()
    operation_id = f"settings-{job_id}"
    record_breadcrumb(
        "settings.async.started",
        source="settings",
        operation=f"settings.{op}",
        operation_id=operation_id,
        context={"op": op},
        flush=True,
    )

    def _main_eval(js: str) -> None:
        mw.taskman.run_on_main(lambda: eval_fn(js))

    def _progress(pct: int, message: str) -> None:
        progress_payload_json = json.dumps(AsyncProgressPayload(job_id, message, pct).to_dict())
        _main_eval(f"window.onAsyncProgress({progress_payload_json})")

    def _run() -> None:
        try:
            result = dispatch_settings_async_op(op, op_payload, _progress)
            success_done_payload_json = json.dumps(
                AsyncDonePayload(job_id, True, result=result).to_dict()
            )
            record_breadcrumb(
                "settings.async.succeeded",
                source="settings",
                operation=f"settings.{op}",
                operation_id=operation_id,
                context={"op": op},
                flush=True,
            )
            _main_eval(f"window.onAsyncDone({success_done_payload_json})")
        except Exception as async_error:  # pragma: no cover - tested via public callback path
            capture_exception(
                "settings.async_worker",
                async_error,
                operation=f"settings.{op}",
                operation_id=operation_id,
                user_message=str(async_error),
                context={"op": op, "job_id": job_id},
                log=logger,
            )
            message = str(async_error)
            failure_done_payload_json = json.dumps(
                {
                    "id": job_id,
                    "ok": False,
                    "error": message,
                    "user_error": coded_error(AQE_FRONTEND_UNKNOWN_ASYNC_ERROR, message),
                }
            )
            _main_eval(f"window.onAsyncDone({failure_done_payload_json})")

    threading.Thread(target=_run, daemon=True).start()


def _raw_job_id(payload: Any) -> str:
    if isinstance(payload, dict):
        job_id = payload.get("id")
        if isinstance(job_id, str):
            return job_id
    return str(uuid.uuid4())
