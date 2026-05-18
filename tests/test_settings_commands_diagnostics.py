from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from anki_audio_quick_editor.errors import SettingsCommandError
from anki_audio_quick_editor.settings.commands import (
    _dispatch_op,
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


def test_frontend_log_handles_invalid_json(caplog: pytest.LogCaptureFixture) -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    caplog.set_level(logging.WARNING, logger="anki_audio_quick_editor.settings.commands")

    assert handle_settings_command("frontend_log:not-json", eval_fn, dialog) is True
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
    payload = json.dumps({"level": level, "message": "loaded", "context": {"tab": "diagnostics"}})

    assert handle_settings_command(f"frontend_log:{payload}", eval_fn, dialog) is True

    record = caplog.records[-1]
    assert record.levelno == expected_level
    assert record.message == "frontend: loaded | {'tab': 'diagnostics'}"


def test_async_command_logs_invalid_json_without_callback(caplog: pytest.LogCaptureFixture) -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.settings.commands")

    assert handle_settings_command("async_cmd:not-json", eval_fn, dialog) is True

    assert calls == []
    assert "async_cmd: invalid JSON payload" in caplog.text


def test_async_command_reports_unknown_operation() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps({"id": "job-unknown", "op": "explode", "payload": {}})

    with patch("threading.Thread", _ImmediateThread):
        assert handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog) is True

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
    payload = json.dumps({"id": "job-1", "op": "health_check", "payload": {"config": "/not/a/dict"}})

    assert handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog) is True

    result = _parse_callback(calls[-1], "onAsyncDone")
    assert result == {
        "id": "job-1",
        "ok": False,
        "error": "Invalid async command payload",
    }


def test_async_health_check_reports_result() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps({"id": "job-1", "op": "health_check", "payload": {"config": _full_config()}})

    with patch("threading.Thread", _ImmediateThread):
        handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    assert done_calls
    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["ok"] is True
    assert "card_count" in result["result"]
    assert "deep_filter" in result["result"]
    assert ("si" + "don") not in result["result"]
    assert "rnnoise" in result["result"]


def test_async_health_check_reports_deep_filter_version() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps(
        {
            "id": "job-1",
            "op": "health_check",
            "payload": {"config": {**_full_config(), "deep_filter_path": "/custom/deep-filter"}},
        }
    )

    with (
        patch("threading.Thread", _ImmediateThread),
        patch(
            "anki_audio_quick_editor.audio_processor.find_deep_filter",
            return_value=Path("/custom/deep-filter"),
        ),
        patch("anki_audio_quick_editor.diagnostics.subprocess.run") as run,
    ):
        run.return_value.returncode = 0
        run.return_value.stdout = "deep-filter 0.5.6\n"
        run.return_value.stderr = ""
        handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["result"]["deep_filter"] == {
        "available": True,
        "path": "/custom/deep-filter",
        "version": "deep-filter 0.5.6",
        "error": "",
    }


def test_async_health_check_reports_rnnoise_version() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps(
        {
            "id": "job-1",
            "op": "health_check",
            "payload": {"config": _full_config()},
        }
    )

    with (
        patch("threading.Thread", _ImmediateThread),
        patch(
            "anki_audio_quick_editor.audio_processor.find_rnnoise_bundle",
            return_value=Path("/addon/bin/rnnoise-cli-macos-arm64/bin/rnnoise-cli"),
        ),
        patch("anki_audio_quick_editor.diagnostics.subprocess.run") as run,
    ):
        run.return_value.returncode = 0
        run.return_value.stdout = "rnnoise-cli 0.2\n"
        run.return_value.stderr = ""
        handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["result"]["rnnoise"] == {
        "available": True,
        "path": "/addon/bin/rnnoise-cli-macos-arm64/bin/rnnoise-cli",
        "version": "rnnoise-cli 0.2",
        "error": "",
    }


