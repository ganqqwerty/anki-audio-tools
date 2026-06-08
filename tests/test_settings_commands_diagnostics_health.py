from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from anki_audio_quick_editor.settings.commands import handle_settings_command
from tests.settings_command_fixtures import (
    _bridge_command,
    _capture_eval,
    _full_config,
    _make_dialog,
    _parse_callback,
)
from tests.test_settings_commands_diagnostics import (
    DEEP_FILTER,
    DPDFNET,
    RNNOISE,
    SILERO_VAD,
    SPLEETER,
    _ImmediateThread,
)


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
    assert "silero_vad" in result["result"]


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
        "path": DEEP_FILTER,
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
        "path": RNNOISE,
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
        "path": DPDFNET,
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
        "path": SPLEETER,
        "source": "bundled",
        "version": "Non-streaming source separation with sherpa-onnx.",
        "error": "",
    }


def test_async_health_check_reports_silero_vad_probe() -> None:
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
            "anki_audio_quick_editor.audio_processor.find_silero_vad_bundle",
            return_value=(
                Path("/addon/bin/macos-arm64/silero-vad"),
                Path("/addon/bin/models/silero-vad/silero_vad.onnx"),
            ),
        ),
        patch("anki_audio_quick_editor.diagnostics.subprocess.run") as run,
    ):
        run.return_value.returncode = 0
        run.return_value.stdout = "VAD in sherpa-onnx.\n"
        run.return_value.stderr = ""
        handle_settings_command(_bridge_command("settings.async", payload), eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["result"]["silero_vad"] == {
        "available": True,
        "path": SILERO_VAD,
        "source": "bundled",
        "version": "VAD in sherpa-onnx.",
        "error": "",
    }
