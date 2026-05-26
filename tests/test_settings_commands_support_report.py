from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from anki_audio_quick_editor.settings.commands import (
    handle_settings_command,
)
from anki_audio_quick_editor.support import (
    clear_latest_pause_pipeline_support_incident,
    clear_latest_rnnoise_support_incident,
    clear_latest_spleeter_support_incident,
    record_latest_pause_pipeline_support_incident,
    record_latest_rnnoise_support_incident,
    record_latest_spleeter_support_incident,
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


def test_async_support_report_returns_incident_and_log_tail(tmp_path: Path) -> None:
    from aqt import mw

    clear_latest_pause_pipeline_support_incident()
    clear_latest_rnnoise_support_incident()
    clear_latest_spleeter_support_incident()
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
    record_latest_spleeter_support_incident(
        operation="voice_only",
        media_filename="voice.mp3",
        source_path="/media/voice.mp3",
        user_message="Voice Only extraction failed.",
        exception_type="AudioProcessingError",
        ffmpeg_path="/bin/ffmpeg",
        spleeter_path="/bin/sherpa-spleeter",
        vocals_model_path="/models/vocals.fp16.onnx",
        accompaniment_model_path="/models/accompaniment.fp16.onnx",
        attempted_commands=[
            {"command": "/bin/sherpa-spleeter --json", "returncode": 5, "stdout": "", "stderr": "boom", "launch_error": ""},
        ],
    )
    addon_dir = tmp_path / "addon"
    addon_dir.mkdir()
    log_path = addon_dir / "anki_audio_quick_editor.log"
    log_path.write_text("line-1\nline-2\n", encoding="utf-8")
    (addon_dir / "release_info.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "commit_hash": "b" * 40,
                "commit_message": "Ship release diagnostics",
            }
        ),
        encoding="utf-8",
    )
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = {"id": "job-1", "op": "support_report", "payload": {"config": _full_config()}}

    with (
        patch("threading.Thread", _ImmediateThread),
        patch.object(mw.addonManager, "addonsFolder", return_value=str(addon_dir)),
        patch("anki_audio_quick_editor.diagnostics.build_deep_filter_health", return_value={"available": True, "path": "/bin/deep-filter", "version": "0.5.6", "error": ""}),
        patch("anki_audio_quick_editor.diagnostics.build_rnnoise_health", return_value={"available": True, "path": "/bin/rnnoise-cli", "version": "0.2", "error": ""}),
        patch("anki_audio_quick_editor.diagnostics.build_dpdfnet_health", return_value={"available": True, "path": "/bin/dpdfnet", "version": "0.1.0", "error": ""}),
        patch("anki_audio_quick_editor.diagnostics.build_spleeter_health", return_value={"available": True, "path": "/bin/sherpa-spleeter", "version": "1.13.2", "error": ""}),
    ):
        handle_settings_command(_bridge_command("settings.async", payload), eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    report_text = result["result"]["reportText"]
    assert "Anki Audio Quick Editor Support Report" in report_text
    assert "DeepFilterNet pause analysis failed." in report_text
    assert "RNNoise denoise failed." in report_text
    assert "Voice Only extraction failed." in report_text
    assert "/bin/rnnoise-cli denoise --input in.s16le" in report_text
    assert "/bin/sherpa-spleeter --json" in report_text
    assert "0.2" in report_text
    assert "0.1.0" in report_text
    assert "Release commit: " + "b" * 40 in report_text
    assert "Release message: Ship release diagnostics" in report_text
    assert "/addon/aqe_artifacts/clip__run/manifest.json" in report_text
    assert "line-1" in report_text
    assert str(log_path) in report_text



def test_copy_support_report_updates_clipboard() -> None:
    clipboard = MagicMock()
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    payload = {"text": "support text"}

    with patch("aqt.qt.QApplication.clipboard", return_value=clipboard):
        assert handle_settings_command(_bridge_command("support.copy_report", payload), eval_fn, dialog) is True

    clipboard.setText.assert_called_once_with("support text")


def test_copy_support_report_logs_invalid_payload_without_clipboard(caplog: pytest.LogCaptureFixture) -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    caplog.set_level(logging.WARNING, logger="anki_audio_quick_editor.settings.commands")

    with patch("aqt.qt.QApplication.clipboard") as clipboard:
        assert handle_settings_command(_bridge_command("support.copy_report", "not-a-report"), eval_fn, dialog) is True

    clipboard.assert_not_called()
    assert "support.copy_report: invalid payload" in caplog.text


def test_copy_support_report_logs_missing_text_without_clipboard(caplog: pytest.LogCaptureFixture) -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    caplog.set_level(logging.WARNING, logger="anki_audio_quick_editor.settings.commands")

    with patch("aqt.qt.QApplication.clipboard") as clipboard:
        assert handle_settings_command(_bridge_command("support.copy_report", {}), eval_fn, dialog) is True

    clipboard.assert_not_called()
    assert "support.copy_report: missing text payload" in caplog.text


def test_copy_support_report_logs_unavailable_clipboard(caplog: pytest.LogCaptureFixture) -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    caplog.set_level(logging.WARNING, logger="anki_audio_quick_editor.settings.commands")
    payload = {"text": "support text"}

    with patch("aqt.qt.QApplication.clipboard", return_value=None):
        assert handle_settings_command(_bridge_command("support.copy_report", payload), eval_fn, dialog) is True
