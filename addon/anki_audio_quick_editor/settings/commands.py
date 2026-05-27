"""Settings bridge command dispatcher for Anki Audio Quick Editor."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from ..contracts_generated import (
    Config,
    CopySupportReportPayload,
    VisibleEditorButton,
)
from ..diagnostics_runtime import (
    new_operation_id,
    record_breadcrumb,
    set_debug_enabled,
)
from ..frontend_logs import handle_frontend_log_payload
from ..webview_bridge import (
    WebviewBridgeCommand,
    decode_webview_bridge_command,
)
from .async_commands import handle_async_settings_command

logger = logging.getLogger(__name__)
CONTRACT_DECODE_ERRORS = (AssertionError, TypeError, ValueError)


def handle_settings_command(
    cmd: str,
    eval_fn: Callable[[str], None],
    dialog: Any,
) -> bool:
    """Dispatch a settings command received from the Svelte UI."""
    try:
        command = decode_webview_bridge_command(cmd)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("settings bridge: invalid command: %s", exc)
        return False

    command_name = command.name
    record_breadcrumb(
        "settings.command.received",
        source="settings",
        operation=f"settings.{command_name}",
        operation_id=new_operation_id("settings"),
        context={"command": command_name},
    )
    if command_name == "settings.cancel":
        dialog.reject()
        return True
    if command_name == "settings.reset_defaults":
        _handle_reset_defaults(dialog)
        return True
    if command_name == "settings.save":
        _handle_settings_save(command, eval_fn, dialog)
        return True
    if command_name == "settings.check_media":
        _handle_check_media()
        return True
    if command_name == "settings.async":
        handle_async_settings_command(command, eval_fn)
        return True
    if command_name == "frontend.log":
        _handle_frontend_log(command.payload)
        return True
    if command_name == "support.copy_report":
        _handle_copy_support_report(command)
        return True
    return False


def _handle_settings_save(
    command: WebviewBridgeCommand,
    eval_fn: Callable[[str], None],
    dialog: Any,
) -> None:
    from aqt import mw

    raw_config = command.payload
    _sanitize_settings_payload(raw_config)
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


def _sanitize_settings_payload(raw_config: Any) -> None:
    if not isinstance(raw_config, dict):
        return
    visible_buttons = raw_config.get("visible_editor_buttons")
    if isinstance(visible_buttons, list):
        allowed_buttons = {button.value for button in VisibleEditorButton}
        raw_config["visible_editor_buttons"] = [
            button for button in visible_buttons if button in allowed_buttons
        ]


def _handle_reset_defaults(dialog: Any) -> None:
    from aqt import mw
    from aqt.qt import QMessageBox

    from ..ffmpeg_defaults import with_platform_ffmpeg_default
    from ..i18n import t

    addon_id = mw.addonManager.addonFromModule(__name__)
    defaults = mw.addonManager.addonConfigDefaults(addon_id)
    if defaults is None:
        QMessageBox.warning(
            dialog,
            t("settings.reset_failed.title"),
            t("settings.reset_failed.defaults_missing"),
        )
        return

    result = QMessageBox.warning(
        dialog,
        t("settings.footer.reset_defaults"),
        t("settings.reset_confirm.message"),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    if result != QMessageBox.StandardButton.Yes:
        return

    mw.addonManager.writeConfig(addon_id, with_platform_ffmpeg_default(defaults))
    dialog.reject()


def _handle_check_media() -> None:
    from aqt import mw
    from aqt.mediacheck import check_media_db

    check_media_db(mw)


def _handle_frontend_log(raw_payload: Any) -> None:
    handle_frontend_log_payload(
        raw_payload,
        logger=logger,
        default_scope="settings",
        boundary="settings.frontend",
        log_prefix="frontend",
        invalid_label="frontend_log",
    )


def _handle_copy_support_report(command: WebviewBridgeCommand) -> None:
    from aqt.qt import QApplication

    raw_payload = command.payload
    try:
        payload = CopySupportReportPayload.from_dict(raw_payload)
    except CONTRACT_DECODE_ERRORS:
        if isinstance(raw_payload, dict) and not isinstance(raw_payload.get("text"), str):
            logger.warning("support.copy_report: missing text payload")
        else:
            logger.warning("support.copy_report: invalid payload")
        return

    clipboard = QApplication.clipboard()
    if clipboard is None:
        logger.warning("support.copy_report: clipboard unavailable")
        return
    clipboard.setText(payload.text)

