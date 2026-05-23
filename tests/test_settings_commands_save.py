from __future__ import annotations

import json
from types import SimpleNamespace

from anki_audio_quick_editor.settings.commands import (
    handle_settings_command,
)
from tests.settings_command_fixtures import (
    _capture_eval,
    _full_config,
    _make_dialog,
    _parse_callback,
)


class _ImmediateThread:
    def __init__(self, target, daemon=True):
        self._target = target

    def start(self) -> None:
        self._target()


def test_settings_save_writes_config_and_accepts() -> None:
    from aqt import mw

    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    config = {**_full_config(), "enabled": False, "debug_logging": True, "repeat_pause_seconds": 2.5}

    handle_settings_command(f"settings_save:{json.dumps(config)}", eval_fn, dialog)

    mw.addonManager.writeConfig.assert_called_once()
    saved_config = mw.addonManager.writeConfig.call_args.args[1]
    assert saved_config["enabled"] is True
    assert saved_config["repeat_pause_seconds"] == 2.5
    assert dialog.accepted is True


def test_settings_save_accepts_bridge_envelope() -> None:
    from aqt import mw

    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    config = _full_config()
    command = "bridge:" + json.dumps({"command": "settings.save", "payload": config})

    assert handle_settings_command(command, eval_fn, dialog) is True

    mw.addonManager.writeConfig.assert_called_once()
    assert dialog.accepted is True


def test_settings_save_reports_invalid_json() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()

    handle_settings_command("settings_save:not-json", eval_fn, dialog)

    payload = _parse_callback(calls[0], "onSaveError")
    assert payload["error"] == "Invalid JSON payload"
    assert dialog.accepted is False


def test_settings_cancel_rejects_dialog() -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    assert handle_settings_command("settings_cancel", eval_fn, dialog) is True
    assert dialog.rejected is True


def test_settings_reset_defaults_warns_when_defaults_are_missing() -> None:
    from aqt import mw
    from aqt.qt import QMessageBox

    mw.addonManager.addonConfigDefaults.return_value = None
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    assert handle_settings_command("settings_reset_defaults", eval_fn, dialog) is True

    QMessageBox.warning.assert_called_once_with(dialog, "Reset Failed", "Could not load config defaults.")
    mw.addonManager.writeConfig.assert_not_called()
    assert dialog.rejected is False


def test_settings_reset_defaults_respects_no_confirmation() -> None:
    from aqt import mw
    from aqt.qt import QMessageBox

    QMessageBox.StandardButton = SimpleNamespace(Yes=1, No=2)
    QMessageBox.warning.return_value = QMessageBox.StandardButton.No
    mw.addonManager.addonConfigDefaults.return_value = {"enabled": True}
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    assert handle_settings_command("settings_reset_defaults", eval_fn, dialog) is True

    mw.addonManager.writeConfig.assert_not_called()
    assert dialog.rejected is False


def test_settings_reset_defaults_writes_defaults_and_closes_on_yes(monkeypatch) -> None:
    from aqt import mw
    from aqt.qt import QMessageBox

    defaults = {"enabled": True, "debug_logging": False}
    monkeypatch.setattr(
        "anki_audio_quick_editor.ffmpeg_defaults.default_ffmpeg_path",
        lambda: "/opt/homebrew/bin/ffmpeg",
    )
    QMessageBox.StandardButton = SimpleNamespace(Yes=1, No=2)
    QMessageBox.warning.return_value = QMessageBox.StandardButton.Yes
    mw.addonManager.addonConfigDefaults.return_value = defaults
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    assert handle_settings_command("settings_reset_defaults", eval_fn, dialog) is True

    mw.addonManager.writeConfig.assert_called_once_with(
        "anki_audio_quick_editor",
        {"enabled": True, "debug_logging": False, "ffmpeg_path": "/opt/homebrew/bin/ffmpeg"},
    )
    assert dialog.rejected is True

def test_unknown_command_returns_false() -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    assert handle_settings_command("unknown:command", eval_fn, dialog) is False
