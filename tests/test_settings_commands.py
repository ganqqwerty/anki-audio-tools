"""Tests for the Audio Quick Editor settings command dispatcher."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from anki_audio_quick_editor.settings.commands import handle_settings_command


class _ImmediateThread:
    def __init__(self, target, daemon=True):
        self._target = target

    def start(self) -> None:
        self._target()


def _make_dialog() -> MagicMock:
    dialog = MagicMock()
    dialog.accepted = False
    dialog.rejected = False
    dialog.accept.side_effect = lambda: setattr(dialog, "accepted", True)
    dialog.reject.side_effect = lambda: setattr(dialog, "rejected", True)
    return dialog


def _capture_eval() -> tuple[list[str], callable]:
    calls: list[str] = []

    def eval_fn(js: str) -> None:
        calls.append(js)

    return calls, eval_fn


def _parse_callback(js: str, name: str) -> dict:
    prefix = f"window.{name}("
    assert js.startswith(prefix)
    return json.loads(js[len(prefix):-1])


def test_settings_save_writes_config_and_accepts() -> None:
    from aqt import mw

    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    config = {"enabled": False, "debug_logging": True}

    handle_settings_command(f"settings_save:{json.dumps(config)}", eval_fn, dialog)

    mw.addonManager.writeConfig.assert_called_once()
    saved_config = mw.addonManager.writeConfig.call_args.args[1]
    assert saved_config["enabled"] is True
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


def test_frontend_log_handles_invalid_json() -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    assert handle_settings_command("frontend_log:not-json", eval_fn, dialog) is True


def test_async_health_check_reports_result() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps({"id": "job-1", "op": "health_check", "payload": {}})

    with patch("threading.Thread", _ImmediateThread):
        handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    assert done_calls
    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["ok"] is True
    assert "card_count" in result["result"]
    assert "deep_filter" in result["result"]


def test_async_health_check_reports_deep_filter_version() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps(
        {
            "id": "job-1",
            "op": "health_check",
            "payload": {"config": {"deep_filter_path": "/custom/deep-filter"}},
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


def test_unknown_command_returns_false() -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    assert handle_settings_command("unknown:command", eval_fn, dialog) is False
