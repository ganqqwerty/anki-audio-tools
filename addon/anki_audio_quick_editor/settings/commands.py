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

logger = logging.getLogger(__name__)
CONTRACT_DECODE_ERRORS = (AssertionError, TypeError, ValueError)


def handle_settings_command(
    cmd: str,
    eval_fn: Callable[[str], None],
    dialog: Any,
) -> bool:
    """Dispatch a settings command received from the Svelte UI."""
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
    root_logger.setLevel(logging.DEBUG if config.get("debug_logging", False) else logging.INFO)
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
    except CONTRACT_DECODE_ERRORS as exc:
        data = json.dumps(
            AsyncDonePayload(raw_job_id, False, error="Invalid async command payload").to_dict()
        )
        mw.taskman.run_on_main(lambda: eval_fn(f"window.onAsyncDone({data})"))
        logger.warning("async_cmd: invalid payload shape: %s", exc)
        return

    job_id = command.id
    op = command.op
    op_payload = command.payload.to_dict()

    def _main_eval(js: str) -> None:
        mw.taskman.run_on_main(lambda: eval_fn(js))

    def _progress(pct: int, message: str) -> None:
        data = json.dumps(AsyncProgressPayload(job_id, message, pct).to_dict())
        _main_eval(f"window.onAsyncProgress({data})")

    def _run() -> None:
        try:
            result = _dispatch_op(op, op_payload, _progress)
            data = json.dumps(AsyncDonePayload(job_id, True, result=result).to_dict())
            _main_eval(f"window.onAsyncDone({data})")
        except Exception as exc:  # pragma: no cover - tested via public callback path
            logger.exception("async operation failed: %s", op)
            data = json.dumps(AsyncDonePayload(job_id, False, error=str(exc)).to_dict())
            _main_eval(f"window.onAsyncDone({data})")

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
    raise RuntimeError(f"Unknown async operation: {op}")


def _op_health_check(
    payload: dict[str, Any],
    progress_fn: Callable[[int, str], None],
) -> Any:
    from aqt import mw

    from ..db_helpers import build_health_report
    from ..diagnostics import (
        build_deep_filter_health,
        build_mp_senet_health,
        build_sidon_health,
    )

    progress_fn(20, "Inspecting collection")
    report = build_health_report(mw.col)
    progress_fn(60, "Checking DeepFilterNet")
    config = _config_payload(payload)
    report["deep_filter"] = build_deep_filter_health(config)
    progress_fn(75, "Checking Sidon")
    report["sidon"] = build_sidon_health()
    progress_fn(90, "Checking MP-SENet")
    report["mp_senet"] = build_mp_senet_health()
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
        build_mp_senet_health,
        build_sidon_health,
    )
    from ..support import (
        addon_log_path,
        build_support_report_text,
        latest_mp_senet_support_incident,
        latest_pause_pipeline_support_incident,
        latest_sidon_support_incident,
        read_log_tail,
    )

    progress_fn(20, "Collecting environment")
    config = _config_payload(payload)
    addon_id = mw.addonManager.addonFromModule(__name__)
    addon_dir = mw.addonManager.addonsFolder(addon_id)
    log_path = addon_log_path(addon_dir)
    progress_fn(50, "Checking external tools")
    deep_filter_health = build_deep_filter_health(config)
    sidon_health = build_sidon_health()
    mp_senet_health = build_mp_senet_health()
    progress_fn(75, "Reading recent logs")
    report_text = build_support_report_text(
        version=__version__,
        addon_dir=addon_dir,
        log_file_path=str(log_path),
        deep_filter_health=deep_filter_health,
        sidon_health=sidon_health,
        mp_senet_health=mp_senet_health,
        sidon_incident=latest_sidon_support_incident(),
        mp_senet_incident=latest_mp_senet_support_incident(),
        pause_pipeline_incident=latest_pause_pipeline_support_incident(),
        log_tail=read_log_tail(log_path),
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
    try:
        raw_payload = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.warning("frontend_log: invalid payload")
        return
    try:
        payload = FrontendLogPayload.from_dict(raw_payload)
    except CONTRACT_DECODE_ERRORS:
        logger.warning("frontend_log: invalid payload")
        return

    level = payload.level.value
    message = payload.message
    context = payload.context
    rendered = f"frontend: {message}"
    if context is not None:
        rendered = f"{rendered} | {context!r}"

    if level == "debug":
        logger.debug(rendered)
    elif level == "warn":
        logger.warning(rendered)
    elif level == "error":
        logger.error(rendered)
    else:
        logger.info(rendered)


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
