"""Settings bridge command dispatcher for Anki Audio Quick Editor."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from collections.abc import Callable
from typing import Any

from ..contracts_generated import (
    AsyncCommand,
    AsyncDonePayload,
    AsyncProgressPayload,
    Config,
    CopySupportReportPayload,
    FrontendLogPayload,
    HealthReport,
    ShowLogFileResult,
    SupportReportResult,
)
from ..diagnostics_runtime import (
    capture_exception,
    new_operation_id,
    record_breadcrumb,
    record_frontend_error,
    set_debug_enabled,
    support_report_context,
)
from ..errors import SettingsCommandError

logger = logging.getLogger(__name__)
CONTRACT_DECODE_ERRORS = (AssertionError, TypeError, ValueError)


def handle_settings_command(
    cmd: str,
    eval_fn: Callable[[str], None],
    dialog: Any,
) -> bool:
    """Dispatch a settings command received from the Svelte UI."""
    command_name = cmd.split(":", 1)[0]
    record_breadcrumb(
        "settings.command.received",
        source="settings",
        operation=f"settings.{command_name}",
        operation_id=new_operation_id("settings"),
        context={"command": command_name},
    )
    if cmd == "settings_cancel":
        dialog.reject()
        return True
    if cmd == "settings_reset_defaults":
        _handle_reset_defaults(dialog)
        return True
    if cmd.startswith("settings_save:"):
        _handle_settings_save(cmd[len("settings_save:"):], eval_fn, dialog)
        return True
    if cmd.startswith("async_cmd:"):
        _handle_async_cmd(cmd[len("async_cmd:"):], eval_fn)
        return True
    if cmd.startswith("frontend_log:"):
        _handle_frontend_log(cmd[len("frontend_log:"):])
        return True
    if cmd.startswith("copy_support_report:"):
        _handle_copy_support_report(cmd[len("copy_support_report:"):])
        return True
    return False


def _handle_settings_save(
    payload_str: str,
    eval_fn: Callable[[str], None],
    dialog: Any,
) -> None:
    from aqt import mw

    try:
        raw_config = json.loads(payload_str)
    except json.JSONDecodeError:
        payload = json.dumps({"error": "Invalid JSON payload"})
        eval_fn(f"window.onSaveError({payload})")
        return
    try:
        config = Config.from_dict(raw_config).to_dict()
    except CONTRACT_DECODE_ERRORS:
        payload = json.dumps({"error": "Invalid settings payload"})
        eval_fn(f"window.onSaveError({payload})")
        return

    config["enabled"] = True
    addon_id = mw.addonManager.addonFromModule(__name__)
    mw.addonManager.writeConfig(addon_id, config)

    root_logger = logging.getLogger("anki_audio_quick_editor")
    debug_enabled = bool(config.get("debug_logging", False))
    root_logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)
    set_debug_enabled(debug_enabled)
    record_breadcrumb(
        "settings.saved",
        source="settings",
        operation="settings.save",
        context={"debug_logging": debug_enabled},
        flush=True,
    )
    dialog.accept()


def _handle_reset_defaults(dialog: Any) -> None:
    from aqt import mw
    from aqt.qt import QMessageBox

    addon_id = mw.addonManager.addonFromModule(__name__)
    defaults = mw.addonManager.addonConfigDefaults(addon_id)
    if defaults is None:
        QMessageBox.warning(dialog, "Reset Failed", "Could not load config defaults.")
        return

    result = QMessageBox.warning(
        dialog,
        "Reset Audio Quick Editor Settings",
        "Reset all Audio Quick Editor settings to their defaults?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    if result != QMessageBox.StandardButton.Yes:
        return

    mw.addonManager.writeConfig(addon_id, defaults)
    dialog.reject()


def _handle_async_cmd(payload_str: str, eval_fn: Callable[[str], None]) -> None:
    from aqt import mw

    try:
        raw_payload = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.error("async_cmd: invalid JSON payload")
        return
    raw_job_id = _raw_job_id(raw_payload)

    try:
        command = AsyncCommand.from_dict(raw_payload)
    except CONTRACT_DECODE_ERRORS as invalid_payload_error:
        invalid_done_payload_json = json.dumps(
            AsyncDonePayload(raw_job_id, False, error="Invalid async command payload").to_dict()
        )
        mw.taskman.run_on_main(lambda: eval_fn(f"window.onAsyncDone({invalid_done_payload_json})"))
        logger.warning("async_cmd: invalid payload shape: %s", invalid_payload_error)
        return

    job_id = command.id
    op = command.op
    op_payload = command.payload.to_dict()
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
            result = _dispatch_op(op, op_payload, _progress)
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
            failure_done_payload_json = json.dumps(
                AsyncDonePayload(job_id, False, error=str(async_error)).to_dict()
            )
            _main_eval(f"window.onAsyncDone({failure_done_payload_json})")

    threading.Thread(target=_run, daemon=True).start()


def _dispatch_op(
    op: str,
    payload: dict[str, Any],
    progress_fn: Callable[[int, str], None],
) -> Any:
    if op == "health_check":
        return _op_health_check(payload, progress_fn)
    if op == "support_report":
        return _op_support_report(payload, progress_fn)
    if op == "show_log_file":
        return _op_show_log_file(progress_fn)
    raise SettingsCommandError(f"Unknown async operation: {op}")


def _op_health_check(
    payload: dict[str, Any],
    progress_fn: Callable[[int, str], None],
) -> Any:
    from aqt import mw

    from ..db_helpers import build_health_report
    from ..diagnostics import (
        build_deep_filter_health,
        build_rnnoise_health,
    )

    progress_fn(20, "Inspecting collection")
    report = build_health_report(mw.col)
    progress_fn(60, "Checking DeepFilterNet")
    config = _config_payload(payload)
    report["deep_filter"] = build_deep_filter_health(config)
    progress_fn(90, "Checking RNNoise")
    report["rnnoise"] = build_rnnoise_health()
    progress_fn(100, "Done")
    return HealthReport.from_dict(report).to_dict()


def _op_support_report(
    payload: dict[str, Any],
    progress_fn: Callable[[int, str], None],
) -> Any:
    from aqt import mw

    from .._version import __version__
    from ..diagnostics import (
        build_deep_filter_health,
        build_rnnoise_health,
    )
    from ..support import (
        addon_log_path,
        build_support_report_text,
        latest_pause_pipeline_support_incident,
        latest_rnnoise_support_incident,
        read_log_tail,
    )

    record_breadcrumb("settings.support_report.collect", source="settings", operation="settings.support_report")
    progress_fn(20, "Collecting environment")
    config = _config_payload(payload)
    addon_id = mw.addonManager.addonFromModule(__name__)
    addon_dir = mw.addonManager.addonsFolder(addon_id)
    log_path = addon_log_path(addon_dir)
    progress_fn(50, "Checking external tools")
    deep_filter_health = build_deep_filter_health(config)
    rnnoise_health = build_rnnoise_health()
    progress_fn(75, "Reading recent logs")
    report_text = build_support_report_text(
        version=__version__,
        addon_dir=addon_dir,
        log_file_path=str(log_path),
        deep_filter_health=deep_filter_health,
        rnnoise_health=rnnoise_health,
        rnnoise_incident=latest_rnnoise_support_incident(),
        pause_pipeline_incident=latest_pause_pipeline_support_incident(),
        log_tail=read_log_tail(log_path),
        diagnostics_context=support_report_context(),
    )
    progress_fn(100, "Done")
    return SupportReportResult(report_text).to_dict()


def _op_show_log_file(
    progress_fn: Callable[[int, str], None],
) -> Any:
    from aqt import mw

    from ..file_reveal import reveal_file
    from ..support import addon_log_path

    progress_fn(25, "Locating log file")
    addon_id = mw.addonManager.addonFromModule(__name__)
    addon_dir = mw.addonManager.addonsFolder(addon_id)
    log_path = addon_log_path(addon_dir)
    progress_fn(75, "Opening log file")
    reveal_file(log_path, missing_message="The Audio Quick Editor log file was not found.")
    progress_fn(100, "Done")
    return ShowLogFileResult(str(log_path)).to_dict()


def _handle_frontend_log(payload_str: str) -> None:
    payload = _decode_frontend_log_payload(payload_str)
    if payload is None:
        return

    level = payload.level.value
    message = payload.message
    context = payload.context
    stack = str(getattr(payload, "stack", "") or "")
    scope = str(getattr(payload, "scope", "") or "settings")
    operation_id = str(getattr(payload, "operation_id", "") or "")
    _emit_frontend_log(level, _render_frontend_log("frontend", message, context, stack))
    record_breadcrumb(
        "frontend.log",
        source=scope,
        level="error" if level == "error" else "debug",
        operation="frontend.log",
        operation_id=operation_id,
        context=_frontend_log_context(payload, level),
    )
    if level == "error":
        record_frontend_error(
            "settings.frontend",
            message=message,
            stack=stack,
            source=scope,
            operation="settings.frontend",
            operation_id=operation_id,
            context=context,
        )


def _decode_frontend_log_payload(payload_str: str) -> FrontendLogPayload | None:
    try:
        raw_payload = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.warning("frontend_log: invalid payload")
        return None
    try:
        return FrontendLogPayload.from_dict(raw_payload)
    except CONTRACT_DECODE_ERRORS:
        logger.warning("frontend_log: invalid payload")
        return None


def _render_frontend_log(prefix: str, message: str, context: object, stack: str) -> str:
    rendered = f"{prefix}: {message}"
    if context is not None:
        rendered = f"{rendered} | {context!r}"
    if stack:
        rendered = f"{rendered}\n{stack}"
    return rendered


def _emit_frontend_log(level: str, rendered: str) -> None:
    if level == "debug":
        logger.debug(rendered)
    elif level == "warn":
        logger.warning(rendered)
    elif level == "error":
        logger.error(rendered)
    else:
        logger.info(rendered)


def _frontend_log_context(payload: FrontendLogPayload, level: str) -> dict[str, object]:
    return {
        "level": level,
        "message": payload.message,
        "filename": getattr(payload, "filename", None),
        "lineno": getattr(payload, "lineno", None),
        "colno": getattr(payload, "colno", None),
        "context": payload.context,
    }


def _handle_copy_support_report(payload_str: str) -> None:
    from aqt.qt import QApplication

    try:
        raw_payload = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.warning("copy_support_report: invalid payload")
        return
    try:
        payload = CopySupportReportPayload.from_dict(raw_payload)
    except CONTRACT_DECODE_ERRORS:
        if isinstance(raw_payload, dict) and not isinstance(raw_payload.get("text"), str):
            logger.warning("copy_support_report: missing text payload")
        else:
            logger.warning("copy_support_report: invalid payload")
        return

    clipboard = QApplication.clipboard()
    if clipboard is None:
        logger.warning("copy_support_report: clipboard unavailable")
        return
    clipboard.setText(payload.text)


def _raw_job_id(payload: Any) -> str:
    if isinstance(payload, dict):
        job_id = payload.get("id")
        if isinstance(job_id, str):
            return job_id
    return str(uuid.uuid4())


def _config_payload(payload: dict[str, Any]) -> dict[str, Any]:
    raw_config = payload.get("config")
    if not isinstance(raw_config, dict):
        return {}
    try:
        return Config.from_dict(raw_config).to_dict()
    except CONTRACT_DECODE_ERRORS:
        return {}
