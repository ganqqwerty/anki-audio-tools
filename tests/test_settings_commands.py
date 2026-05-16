"""Tests for the Audio Quick Editor settings command dispatcher."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from anki_audio_quick_editor.settings.commands import handle_settings_command
from anki_audio_quick_editor.support import (
    clear_latest_mp_senet_support_incident,
    clear_latest_sidon_support_incident,
    record_latest_mp_senet_support_incident,
    record_latest_sidon_support_incident,
)


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
    assert "sidon" in result["result"]
    assert "mp_senet" in result["result"]


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


def test_async_health_check_reports_sidon_version() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps(
        {
            "id": "job-1",
            "op": "health_check",
            "payload": {},
        }
    )

    with (
        patch("threading.Thread", _ImmediateThread),
        patch(
            "anki_audio_quick_editor.audio_processor.find_sidon_bundle",
            return_value=(
                Path("/addon/bin/sidon-cli-macos-arm64/bin/sidon-cli"),
                Path("/addon/bin/sidon-cli-macos-arm64/models"),
            ),
        ),
        patch("anki_audio_quick_editor.diagnostics.subprocess.run") as run,
    ):
        run.return_value.returncode = 0
        run.return_value.stdout = "sidon-cli 0.1\n"
        run.return_value.stderr = ""
        handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["result"]["sidon"] == {
        "available": True,
        "path": "/addon/bin/sidon-cli-macos-arm64/bin/sidon-cli",
        "model_dir": "/addon/bin/sidon-cli-macos-arm64/models",
        "version": "sidon-cli 0.1",
        "error": "",
    }


def test_async_health_check_reports_mp_senet_version() -> None:
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps(
        {
            "id": "job-1",
            "op": "health_check",
            "payload": {},
        }
    )

    with (
        patch("threading.Thread", _ImmediateThread),
        patch(
            "anki_audio_quick_editor.audio_processor.find_mp_senet_bundle",
            return_value=(
                Path("/addon/bin/mp-senet-cli-macos-arm64/bin/mp-senet-cli"),
                Path("/addon/bin/mp-senet-cli-macos-arm64/models/mp_senet_vb.torchscript.pt"),
            ),
        ),
        patch("anki_audio_quick_editor.diagnostics.subprocess.run") as run,
    ):
        run.return_value.returncode = 0
        run.return_value.stdout = "mp-senet-cli 0.1\n"
        run.return_value.stderr = ""
        handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["result"]["mp_senet"] == {
        "available": True,
        "path": "/addon/bin/mp-senet-cli-macos-arm64/bin/mp-senet-cli",
        "model_path": "/addon/bin/mp-senet-cli-macos-arm64/models/mp_senet_vb.torchscript.pt",
        "version": "mp-senet-cli 0.1",
        "error": "",
    }


def test_async_support_report_returns_incident_and_log_tail(tmp_path: Path) -> None:
    from aqt import mw

    clear_latest_mp_senet_support_incident()
    clear_latest_sidon_support_incident()
    record_latest_sidon_support_incident(
        operation="sidon_restore",
        media_filename="clip.mp3",
        source_path="/media/clip.mp3",
        user_message="Torch backend is not initialized",
        exception_type="AudioProcessingError",
        ffmpeg_path="/bin/ffmpeg",
        sidon_path="/bin/sidon-cli",
        sidon_model_dir="/addon/models",
        attempted_commands=[
            {"command": "/bin/ffmpeg -y -i clip.mp3", "returncode": 0, "stdout": "", "stderr": "", "launch_error": ""},
            {"command": "/bin/sidon-cli restore --input in.wav", "returncode": 5, "stdout": "", "stderr": "boom", "launch_error": ""},
        ],
    )
    record_latest_mp_senet_support_incident(
        operation="mp_senet_denoise",
        media_filename="clip.mp3",
        source_path="/media/clip.mp3",
        user_message="TorchScript load failed",
        exception_type="AudioProcessingError",
        ffmpeg_path="/bin/ffmpeg",
        mp_senet_path="/bin/mp-senet-cli",
        mp_senet_model_path="/addon/models/mp_senet_vb.torchscript.pt",
        attempted_commands=[
            {"command": "/bin/mp-senet-cli denoise --input in.wav", "returncode": 5, "stdout": "", "stderr": "boom", "launch_error": ""},
        ],
    )
    addon_dir = tmp_path / "addon"
    addon_dir.mkdir()
    log_path = addon_dir / "anki_audio_quick_editor.log"
    log_path.write_text("line-1\nline-2\n", encoding="utf-8")
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps({"id": "job-1", "op": "support_report", "payload": {"config": {}}})

    with (
        patch("threading.Thread", _ImmediateThread),
        patch.object(mw.addonManager, "addonsFolder", return_value=str(addon_dir)),
        patch("anki_audio_quick_editor.diagnostics.build_deep_filter_health", return_value={"available": True, "path": "/bin/deep-filter", "version": "0.5.6", "error": ""}),
        patch("anki_audio_quick_editor.diagnostics.build_sidon_health", return_value={"available": True, "path": "/bin/sidon-cli", "model_dir": "/addon/models", "version": "0.1", "error": ""}),
        patch("anki_audio_quick_editor.diagnostics.build_mp_senet_health", return_value={"available": True, "path": "/bin/mp-senet-cli", "model_path": "/addon/models/mp_senet_vb.torchscript.pt", "version": "0.1", "error": ""}),
    ):
        handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    report_text = result["result"]["reportText"]
    assert "Anki Audio Quick Editor Support Report" in report_text
    assert "Media filename: clip.mp3" in report_text
    assert "Torch backend is not initialized" in report_text
    assert "TorchScript load failed" in report_text
    assert "line-1" in report_text
    assert str(log_path) in report_text


def test_async_support_report_handles_missing_log_file() -> None:
    clear_latest_mp_senet_support_incident()
    clear_latest_sidon_support_incident()
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps({"id": "job-1", "op": "support_report", "payload": {"config": {}}})

    with patch("threading.Thread", _ImmediateThread):
        handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    report_text = result["result"]["reportText"]
    assert "No Sidon failure has been captured in this session." in report_text
    assert "No MP-SENet failure has been captured in this session." in report_text
    assert "Log file not found:" in report_text or "(log file is empty)" in report_text


def test_async_show_log_file_reveals_path(tmp_path: Path) -> None:
    from aqt import mw

    addon_dir = tmp_path / "addon"
    addon_dir.mkdir()
    log_path = addon_dir / "anki_audio_quick_editor.log"
    log_path.write_text("log", encoding="utf-8")
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps({"id": "job-1", "op": "show_log_file", "payload": {}})

    with (
        patch("threading.Thread", _ImmediateThread),
        patch.object(mw.addonManager, "addonsFolder", return_value=str(addon_dir)),
        patch("anki_audio_quick_editor.file_reveal.reveal_file") as reveal_file,
    ):
        handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog)

    reveal_file.assert_called_once_with(
        log_path,
        missing_message="The Audio Quick Editor log file was not found.",
    )
    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["result"] == {"logFilePath": str(log_path)}


def test_copy_support_report_updates_clipboard() -> None:
    clipboard = MagicMock()
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    payload = json.dumps({"text": "support text"})

    with patch("aqt.qt.QApplication.clipboard", return_value=clipboard):
        assert handle_settings_command(f"copy_support_report:{payload}", eval_fn, dialog) is True

    clipboard.setText.assert_called_once_with("support text")


def test_unknown_command_returns_false() -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    assert handle_settings_command("unknown:command", eval_fn, dialog) is False
