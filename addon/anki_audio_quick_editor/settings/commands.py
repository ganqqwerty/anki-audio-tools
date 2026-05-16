"""Settings bridge command dispatcher for Anki Audio Quick Editor."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from collections.abc import Callable
from typing import Any, cast

logger = logging.getLogger(__name__)


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
        config = json.loads(payload_str)
    except json.JSONDecodeError:
        payload = json.dumps({"error": "Invalid JSON payload"})
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
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.error("async_cmd: invalid JSON payload")
        return

    job_id = payload.get("id", str(uuid.uuid4()))
    op = payload.get("op", "")
    op_payload = payload.get("payload", {})

    def _main_eval(js: str) -> None:
        mw.taskman.run_on_main(lambda: eval_fn(js))

    def _progress(pct: int, message: str) -> None:
        data = json.dumps({"id": job_id, "progress": pct, "message": message})
        _main_eval(f"window.onAsyncProgress({data})")

    def _run() -> None:
        try:
            result = _dispatch_op(op, op_payload, _progress)
            data = json.dumps({"id": job_id, "ok": True, "result": result})
            _main_eval(f"window.onAsyncDone({data})")
        except Exception as exc:  # pragma: no cover - tested via public callback path
            logger.exception("async operation failed: %s", op)
            data = json.dumps({"id": job_id, "ok": False, "error": str(exc)})
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
    from ..diagnostics import build_deep_filter_health, build_sidon_health

    progress_fn(20, "Inspecting collection")
    report = build_health_report(mw.col)
    progress_fn(60, "Checking DeepFilterNet")
    raw_config = payload.get("config")
    config = cast(dict[str, Any], raw_config) if isinstance(raw_config, dict) else {}
    report["deep_filter"] = build_deep_filter_health(config)
    progress_fn(80, "Checking Sidon")
    report["sidon"] = build_sidon_health()
    progress_fn(100, "Done")
    return report


def _op_support_report(
    payload: dict[str, Any],
    progress_fn: Callable[[int, str], None],
) -> Any:
    from aqt import mw

    from .._version import __version__
    from ..diagnostics import build_deep_filter_health, build_sidon_health
    from ..support import (
        addon_log_path,
        build_support_report_text,
        latest_sidon_support_incident,
        read_log_tail,
    )

    progress_fn(20, "Collecting environment")
    raw_config = payload.get("config")
    config = cast(dict[str, Any], raw_config) if isinstance(raw_config, dict) else {}
    addon_id = mw.addonManager.addonFromModule(__name__)
    addon_dir = mw.addonManager.addonsFolder(addon_id)
    log_path = addon_log_path(addon_dir)
    progress_fn(50, "Checking external tools")
    deep_filter_health = build_deep_filter_health(config)
    sidon_health = build_sidon_health()
    progress_fn(75, "Reading recent logs")
    report_text = build_support_report_text(
        version=__version__,
        addon_dir=addon_dir,
        log_file_path=str(log_path),
        deep_filter_health=deep_filter_health,
        sidon_health=sidon_health,
        incident=latest_sidon_support_incident(),
        log_tail=read_log_tail(log_path),
    )
    progress_fn(100, "Done")
    return {"reportText": report_text}


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
    return {"logFilePath": str(log_path)}


def _handle_frontend_log(payload_str: str) -> None:
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.warning("frontend_log: invalid payload")
        return

    level = str(payload.get("level", "info")).lower()
    message = str(payload.get("message", ""))
    context = payload.get("context")
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
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.warning("copy_support_report: invalid payload")
        return

    text = payload.get("text")
    if not isinstance(text, str):
        logger.warning("copy_support_report: missing text payload")
        return
    clipboard = QApplication.clipboard()
    if clipboard is None:
        logger.warning("copy_support_report: clipboard unavailable")
        return
    clipboard.setText(text)
