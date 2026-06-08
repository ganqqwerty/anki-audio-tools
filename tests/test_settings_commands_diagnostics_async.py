from __future__ import annotations

import logging
import sys
import types
from unittest.mock import patch

import pytest

from anki_audio_quick_editor.errors import SettingsCommandError
from anki_audio_quick_editor.settings.async_operations import dispatch_settings_async_op
from anki_audio_quick_editor.settings.commands import handle_settings_command
from tests.settings_command_fixtures import (
    _bridge_command,
    _capture_eval,
    _make_dialog,
    _parse_callback,
)
from tests.test_settings_commands_diagnostics import _ImmediateThread


def test_async_command_reports_invalid_payload(caplog: pytest.LogCaptureFixture) -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    caplog.set_level(logging.WARNING, logger="anki_audio_quick_editor.settings.commands")

    assert handle_settings_command(_bridge_command("settings.async", "not-json"), eval_fn, dialog) is True

    result = _parse_callback(calls[-1], "onAsyncDone")
    assert result["ok"] is False
    assert result["error"] == "Invalid async command payload"
    assert "settings.async: invalid payload shape" in caplog.text


def test_check_media_command_opens_anki_media_checker() -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    mediacheck = types.ModuleType("aqt.mediacheck")
    mediacheck.check_media_db = lambda _mw: None

    with (
        patch.dict(sys.modules, {"aqt.mediacheck": mediacheck}),
        patch("aqt.mediacheck.check_media_db") as check_media_db,
    ):
        assert handle_settings_command(
            'bridge:{"command":"settings.check_media"}',
            eval_fn,
            dialog,
        ) is True

    check_media_db.assert_called_once()
    assert dialog.accepted is False
    assert dialog.rejected is False


def test_open_runtime_installer_command_returns_refreshed_status() -> None:
    dialog = _make_dialog()
    dialog.open_runtime_installer.return_value = {
        "phase": "ready",
        "runtime_manifest_id": "runtime-test",
        "platform": "macos-arm64",
        "runtime_root": "/runtime",
        "progress": 100,
        "message": "Runtime is ready.",
        "error": "",
    }
    calls, eval_fn = _capture_eval()

    assert handle_settings_command(
        _bridge_command("settings.open_runtime_installer"),
        eval_fn,
        dialog,
    ) is True

    dialog.open_runtime_installer.assert_called_once_with()
    assert _parse_callback(calls[-1], "onRuntimeInstallerClosed") == {
        "error": "",
        "message": "Runtime is ready.",
        "phase": "ready",
        "platform": "macos-arm64",
        "progress": 100,
        "runtime_manifest_id": "runtime-test",
        "runtime_root": "/runtime",
    }


def test_async_command_reports_unknown_operation() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = {"id": "job-unknown", "op": "explode", "payload": {}}

    with patch("threading.Thread", _ImmediateThread):
        assert handle_settings_command(_bridge_command("settings.async", payload), eval_fn, dialog) is True

    result = _parse_callback(calls[-1], "onAsyncDone")
    assert result == {
        "id": "job-unknown",
        "ok": False,
        "error": "Unknown async operation: explode",
        "user_error": {
            "code": "AQE-FRONTEND-002",
            "message": "Unknown async operation: explode",
        },
    }


def test_unknown_async_operation_uses_settings_command_error() -> None:
    with pytest.raises(SettingsCommandError, match="Unknown async operation: explode"):
        dispatch_settings_async_op("explode", {}, lambda _pct, _message: None)


def test_async_health_check_rejects_non_dict_payload_config() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = {"id": "job-1", "op": "health_check", "payload": {"config": "/not/a/dict"}}

    assert handle_settings_command(_bridge_command("settings.async", payload), eval_fn, dialog) is True

    result = _parse_callback(calls[-1], "onAsyncDone")
    assert result == {
        "id": "job-1",
        "ok": False,
        "error": "Invalid async command payload",
        "user_error": {
            "code": "AQE-FRONTEND-002",
            "message": "Invalid async command payload",
        },
    }

