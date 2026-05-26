from __future__ import annotations

import logging
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from anki_audio_quick_editor.errors import SettingsCommandError
from anki_audio_quick_editor.settings.commands import (
    _dispatch_op,
    handle_settings_command,
)
from tests.settings_command_fixtures import (
    _bridge_command,
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


def test_frontend_log_handles_invalid_payload(caplog: pytest.LogCaptureFixture) -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    caplog.set_level(logging.WARNING, logger="anki_audio_quick_editor.settings.commands")

    assert handle_settings_command(_bridge_command("frontend.log", "not-json"), eval_fn, dialog) is True
    assert "frontend_log: invalid payload" in caplog.text


@pytest.mark.parametrize(
    ("level", "expected_level"),
    [
        ("debug", logging.DEBUG),
        ("info", logging.INFO),
        ("warn", logging.WARNING),
        ("error", logging.ERROR),
        ("unknown", logging.INFO),
    ],
)
def test_frontend_log_renders_level_message_and_context(
    level: str,
    expected_level: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    caplog.set_level(logging.DEBUG, logger="anki_audio_quick_editor.settings.commands")
    payload = {"level": level, "message": "loaded", "context": {"tab": "diagnostics"}}

    assert handle_settings_command(_bridge_command("frontend.log", payload), eval_fn, dialog) is True

    record = caplog.records[-1]
    assert record.levelno == expected_level
    assert record.message == "frontend: loaded | {'tab': 'diagnostics'}"


def test_frontend_error_payload_records_stack_for_support_report(
    caplog: pytest.LogCaptureFixture,
) -> None:
    from anki_audio_quick_editor.diagnostics_runtime import (
        latest_incident,
        reset_for_tests,
    )

    reset_for_tests()
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.settings.commands")
    payload = {
        "scope": "settings",
        "level": "error",
        "message": "frontend exploded",
        "stack": "Error: frontend exploded\n    at SettingsApp",
        "context": {"tab": "diagnostics"},
    }

    assert handle_settings_command(_bridge_command("frontend.log", payload), eval_fn, dialog) is True

    assert "Error: frontend exploded" in caplog.text
    incident = latest_incident()
    assert incident is not None
    assert incident["boundary"] == "settings.frontend"
    assert incident["traceback"] == "Error: frontend exploded\n    at SettingsApp"


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
    }


def test_unknown_async_operation_uses_settings_command_error() -> None:
    with pytest.raises(SettingsCommandError, match="Unknown async operation: explode"):
        _dispatch_op("explode", {}, lambda _pct, _message: None)


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
    }


def test_async_health_check_reports_result() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = {"id": "job-1", "op": "health_check", "payload": {"config": _full_config()}}

    with patch("threading.Thread", _ImmediateThread):
        handle_settings_command(_bridge_command("settings.async", payload), eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    assert done_calls
    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["ok"] is True
    assert "card_count" in result["result"]
    assert "deep_filter" in result["result"]
    assert ("si" + "don") not in result["result"]
    assert "rnnoise" in result["result"]
    assert "dpdfnet" in result["result"]
    assert "spleeter" in result["result"]


def test_async_health_check_reports_deep_filter_version() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = {
        "id": "job-1",
        "op": "health_check",
        "payload": {"config": _full_config()},
    }

    with (
        patch("threading.Thread", _ImmediateThread),
        patch(
            "anki_audio_quick_editor.audio_processor.find_deep_filter",
            return_value=Path("/addon/bin/deep-filter"),
        ),
        patch("anki_audio_quick_editor.diagnostics.subprocess.run") as run,
    ):
        run.return_value.returncode = 0
        run.return_value.stdout = "deep-filter 0.5.6\n"
        run.return_value.stderr = ""
        handle_settings_command(_bridge_command("settings.async", payload), eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["result"]["deep_filter"] == {
        "available": True,
        "path": "/addon/bin/deep-filter",
        "source": "PATH",
        "version": "deep-filter 0.5.6",
        "error": "",
    }


def test_async_health_check_reports_rnnoise_version() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = {
        "id": "job-1",
        "op": "health_check",
        "payload": {"config": _full_config()},
    }

    with (
        patch("threading.Thread", _ImmediateThread),
        patch(
            "anki_audio_quick_editor.audio_processor.find_rnnoise_bundle",
            return_value=Path("/addon/bin/macos-arm64/rnnoise-cli"),
        ),
        patch("anki_audio_quick_editor.diagnostics.subprocess.run") as run,
    ):
        run.return_value.returncode = 0
        run.return_value.stdout = "rnnoise-cli 0.2\n"
        run.return_value.stderr = ""
        handle_settings_command(_bridge_command("settings.async", payload), eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["result"]["rnnoise"] == {
        "available": True,
        "path": "/addon/bin/macos-arm64/rnnoise-cli",
        "source": "bundled",
        "version": "rnnoise-cli 0.2",
        "error": "",
    }


def test_async_health_check_reports_dpdfnet_version() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = {
        "id": "job-1",
        "op": "health_check",
        "payload": {"config": _full_config()},
    }

    with (
        patch("threading.Thread", _ImmediateThread),
        patch(
            "anki_audio_quick_editor.audio_processor.find_dpdfnet_bundle",
            return_value=Path("/addon/bin/macos-arm64/dpdfnet"),
        ),
        patch("anki_audio_quick_editor.diagnostics.subprocess.run") as run,
    ):
        run.return_value.returncode = 0
        run.return_value.stdout = "dpdfnet-lite 0.1.0\n"
        run.return_value.stderr = ""
        handle_settings_command(_bridge_command("settings.async", payload), eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["result"]["dpdfnet"] == {
        "available": True,
        "path": "/addon/bin/macos-arm64/dpdfnet",
        "source": "bundled",
        "version": "dpdfnet-lite 0.1.0",
        "error": "",
    }


def test_async_health_check_reports_spleeter_probe() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = {
        "id": "job-1",
        "op": "health_check",
        "payload": {"config": _full_config()},
    }

    with (
        patch("threading.Thread", _ImmediateThread),
        patch(
            "anki_audio_quick_editor.audio_processor.find_spleeter_bundle",
            return_value=(
                Path("/addon/bin/macos-arm64/sherpa-spleeter"),
                Path("/addon/bin/models/spleeter-2stems-fp16/vocals.fp16.onnx"),
                Path("/addon/bin/models/spleeter-2stems-fp16/accompaniment.fp16.onnx"),
            ),
        ),
        patch("anki_audio_quick_editor.diagnostics.subprocess.run") as run,
    ):
        run.return_value.returncode = 0
        run.return_value.stdout = "Non-streaming source separation with sherpa-onnx.\n"
        run.return_value.stderr = ""
        handle_settings_command(_bridge_command("settings.async", payload), eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["result"]["spleeter"] == {
        "available": True,
        "path": "/addon/bin/macos-arm64/sherpa-spleeter",
        "source": "bundled",
        "version": "Non-streaming source separation with sherpa-onnx.",
        "error": "",
    }
