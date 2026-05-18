"""Tests for the Audio Quick Editor settings command dispatcher."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from anki_audio_quick_editor.errors import SettingsCommandError
from anki_audio_quick_editor.settings.commands import (
    _dispatch_op,
    handle_settings_command,
)
from anki_audio_quick_editor.support import (
    clear_latest_mp_senet_support_incident,
    clear_latest_pause_pipeline_support_incident,
    clear_latest_rnnoise_support_incident,
    record_latest_mp_senet_support_incident,
    record_latest_pause_pipeline_support_incident,
    record_latest_rnnoise_support_incident,
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


def _full_config() -> dict[str, object]:
    return {
        "_config_version": 9,
        "enabled": True,
        "debug_logging": False,
        "show_ffmpeg_commands": False,
        "repeat_playback_by_default": False,
        "show_graph_by_default": False,
        "manual_trim_small_ms": 100,
        "manual_trim_large_ms": 500,
        "speed_step": 0.05,
        "min_speed": 0.75,
        "max_speed": 1.5,
        "volume_step_db": 3.0,
        "min_volume_db": -24.0,
        "max_volume_db": 24.0,
        "internal_pause_silence_threshold_db": -45,
        "internal_pause_threshold_ms": 300,
        "internal_pause_target_gap_ms": 100,
        "output_format": "mp3",
        "ffmpeg_path": "",
        "deep_filter_path": "",
        "deep_filter_post_filter": True,
    }


def _parse_callback(js: str, name: str) -> dict:
    prefix = f"window.{name}("
    assert js.startswith(prefix)
    return json.loads(js[len(prefix):-1])


def test_settings_save_writes_config_and_accepts() -> None:
    from aqt import mw

    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    config = {**_full_config(), "enabled": False, "debug_logging": True}

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


def test_settings_reset_defaults_writes_defaults_and_closes_on_yes() -> None:
    from aqt import mw
    from aqt.qt import QMessageBox

    defaults = {"enabled": True, "debug_logging": False}
    QMessageBox.StandardButton = SimpleNamespace(Yes=1, No=2)
    QMessageBox.warning.return_value = QMessageBox.StandardButton.Yes
    mw.addonManager.addonConfigDefaults.return_value = defaults
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    assert handle_settings_command("settings_reset_defaults", eval_fn, dialog) is True

    mw.addonManager.writeConfig.assert_called_once_with("anki_audio_quick_editor", defaults)
    assert dialog.rejected is True


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
    assert "mp_senet" in result["result"]
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


def test_async_health_check_reports_mp_senet_version() -> None:
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


def test_async_support_report_returns_incident_and_log_tail(tmp_path: Path) -> None:
    from aqt import mw

    clear_latest_mp_senet_support_incident()
    clear_latest_pause_pipeline_support_incident()
    clear_latest_rnnoise_support_incident()
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
    record_latest_pause_pipeline_support_incident(
        operation="deep_filter_pause_speedup",
        media_filename="clip.mp3",
        source_path="/media/clip.mp3",
        user_message="DeepFilterNet pause analysis failed.",
        exception_type="AudioProcessingError",
        ffmpeg_path="/bin/ffmpeg",
        deep_filter_path="/bin/deep-filter",
        artifact_dir="/addon/aqe_artifacts/clip__run",
        manifest_path="/addon/aqe_artifacts/clip__run/manifest.json",
        attempted_commands=[
            {"command": "/bin/deep-filter -D -o out in.wav", "returncode": 12, "stdout": "", "stderr": "boom", "launch_error": ""},
        ],
    )
    record_latest_rnnoise_support_incident(
        operation="rnnoise_denoise",
        media_filename="rnnoise.mp3",
        source_path="/media/rnnoise.mp3",
        user_message="RNNoise denoise failed.",
        exception_type="AudioProcessingError",
        ffmpeg_path="/bin/ffmpeg",
        rnnoise_path="/bin/rnnoise-cli",
        attempted_commands=[
            {"command": "/bin/rnnoise-cli denoise --input in.s16le", "returncode": 5, "stdout": "", "stderr": "boom", "launch_error": ""},
        ],
    )
    addon_dir = tmp_path / "addon"
    addon_dir.mkdir()
    log_path = addon_dir / "anki_audio_quick_editor.log"
    log_path.write_text("line-1\nline-2\n", encoding="utf-8")
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps({"id": "job-1", "op": "support_report", "payload": {"config": _full_config()}})

    with (
        patch("threading.Thread", _ImmediateThread),
        patch.object(mw.addonManager, "addonsFolder", return_value=str(addon_dir)),
        patch("anki_audio_quick_editor.diagnostics.build_deep_filter_health", return_value={"available": True, "path": "/bin/deep-filter", "version": "0.5.6", "error": ""}),
        patch("anki_audio_quick_editor.diagnostics.build_mp_senet_health", return_value={"available": True, "path": "/bin/mp-senet-cli", "model_path": "/addon/models/mp_senet_vb.torchscript.pt", "version": "0.1", "error": ""}),
        patch("anki_audio_quick_editor.diagnostics.build_rnnoise_health", return_value={"available": True, "path": "/bin/rnnoise-cli", "version": "0.2", "error": ""}),
    ):
        handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    report_text = result["result"]["reportText"]
    assert "Anki Audio Quick Editor Support Report" in report_text
    assert "Media filename: clip.mp3" in report_text
    assert "TorchScript load failed" in report_text
    assert "DeepFilterNet pause analysis failed." in report_text
    assert "RNNoise denoise failed." in report_text
    assert "/bin/rnnoise-cli denoise --input in.s16le" in report_text
    assert "0.2" in report_text
    assert "/addon/aqe_artifacts/clip__run/manifest.json" in report_text
    assert "line-1" in report_text
    assert str(log_path) in report_text


def test_async_support_report_handles_missing_log_file() -> None:
    clear_latest_mp_senet_support_incident()
    clear_latest_pause_pipeline_support_incident()
    clear_latest_rnnoise_support_incident()
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps({"id": "job-1", "op": "support_report", "payload": {"config": _full_config()}})

    with patch("threading.Thread", _ImmediateThread):
        handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    report_text = result["result"]["reportText"]
    assert "No MP-SENet failure has been captured in this session." in report_text
    assert "No RNNoise failure has been captured in this session." in report_text
    assert "No pause-shortening failure has been captured in this session." in report_text
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


def test_async_show_log_file_reports_reveal_failure(tmp_path: Path) -> None:
    from aqt import mw

    addon_dir = tmp_path / "addon"
    addon_dir.mkdir()
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps({"id": "job-log", "op": "show_log_file", "payload": {}})

    with (
        patch("threading.Thread", _ImmediateThread),
        patch.object(mw.addonManager, "addonsFolder", return_value=str(addon_dir)),
        patch("anki_audio_quick_editor.file_reveal.reveal_file", side_effect=RuntimeError("missing log")),
    ):
        assert handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog) is True

    result = _parse_callback(calls[-1], "onAsyncDone")
    assert result == {
        "id": "job-log",
        "ok": False,
        "error": "missing log",
    }


def test_copy_support_report_updates_clipboard() -> None:
    clipboard = MagicMock()
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    payload = json.dumps({"text": "support text"})

    with patch("aqt.qt.QApplication.clipboard", return_value=clipboard):
        assert handle_settings_command(f"copy_support_report:{payload}", eval_fn, dialog) is True

    clipboard.setText.assert_called_once_with("support text")


def test_copy_support_report_logs_invalid_json_without_clipboard(caplog: pytest.LogCaptureFixture) -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    caplog.set_level(logging.WARNING, logger="anki_audio_quick_editor.settings.commands")

    with patch("aqt.qt.QApplication.clipboard") as clipboard:
        assert handle_settings_command("copy_support_report:not-json", eval_fn, dialog) is True

    clipboard.assert_not_called()
    assert "copy_support_report: invalid payload" in caplog.text


def test_copy_support_report_logs_missing_text_without_clipboard(caplog: pytest.LogCaptureFixture) -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    caplog.set_level(logging.WARNING, logger="anki_audio_quick_editor.settings.commands")

    with patch("aqt.qt.QApplication.clipboard") as clipboard:
        assert handle_settings_command("copy_support_report:{}", eval_fn, dialog) is True

    clipboard.assert_not_called()
    assert "copy_support_report: missing text payload" in caplog.text


def test_copy_support_report_logs_unavailable_clipboard(caplog: pytest.LogCaptureFixture) -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    caplog.set_level(logging.WARNING, logger="anki_audio_quick_editor.settings.commands")
    payload = json.dumps({"text": "support text"})

    with patch("aqt.qt.QApplication.clipboard", return_value=None):
        assert handle_settings_command(f"copy_support_report:{payload}", eval_fn, dialog) is True

    assert "copy_support_report: clipboard unavailable" in caplog.text


def test_unknown_command_returns_false() -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    assert handle_settings_command("unknown:command", eval_fn, dialog) is False
