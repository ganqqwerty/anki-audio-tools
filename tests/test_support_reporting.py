"""Support-report rendering tests."""

from __future__ import annotations

from anki_audio_quick_editor.support import (
    build_command_record,
    build_support_report_text,
    format_spleeter_support_log_block,
)


def test_support_report_renders_pause_pipeline_command_details() -> None:
    report = build_support_report_text(
        version="1.2.3",
        addon_dir="/addon",
        log_file_path="/addon/anki_audio_quick_editor.log",
        deep_filter_health={"available": False},
        rnnoise_health={"available": False},
        denoise_incident=None,
        pause_pipeline_incident={
            "timestamp": "2026-05-17T09:08:07+00:00",
            "operation": "pause_removal",
            "media_filename": "clip.mp3",
            "source_path": "/media/clip.mp3",
            "user_message": "No space left on device",
            "exception_type": "AudioProcessingError",
            "ffmpeg_path": "/bin/ffmpeg",
            "deep_filter_path": "/bin/deep-filter",
            "artifact_dir": "/addon/aqe_artifacts/clip",
            "manifest_path": "/addon/aqe_artifacts/clip/manifest.json",
            "attempted_commands": [
                build_command_record(
                    ("/bin/ffmpeg", "-y", "-i", "clip.mp3"),
                    returncode=None,
                    stdout="partial stdout",
                    stderr="partial stderr",
                    launch_error="No space left on device",
                )
            ],
        },
        log_tail="recent log",
    )
    assert "Latest pause-shortening failure" in report
    assert "1. /bin/ffmpeg -y -i clip.mp3" in report
    assert "returncode: None" in report
    assert "launch_error: No space left on device" in report
    assert "stdout: partial stdout" in report
    assert "stderr: partial stderr" in report
    assert "/addon/aqe_artifacts/clip/manifest.json" in report


def test_support_report_renders_empty_pause_pipeline_command_report() -> None:
    report = build_support_report_text(
        version="1.2.3",
        addon_dir="/addon",
        log_file_path="/addon/anki_audio_quick_editor.log",
        deep_filter_health={"available": False},
        rnnoise_health={"available": False},
        denoise_incident=None,
        pause_pipeline_incident={"operation": "pause_removal"},
        log_tail="recent log",
    )
    assert "(no external commands were captured)" in report


def test_support_report_renders_latest_error_recent_events_and_crash_forensics() -> None:
    report = build_support_report_text(
        version="1.2.3",
        addon_dir="/addon",
        log_file_path="/addon/anki_audio_quick_editor.log",
        deep_filter_health={"available": False},
        rnnoise_health={"available": False},
        denoise_incident=None,
        pause_pipeline_incident=None,
        log_tail="recent log",
        diagnostics_context={
            "latest_error": {
                "timestamp": "2026-05-19T10:00:00+00:00",
                "session_id": "session-1",
                "operation": "editor.render",
                "operation_id": "op-1",
                "boundary": "editor.worker.render",
                "exception_type": "RuntimeError",
                "user_message": "render failed",
                "context": {"field_index": 0},
                "traceback": "Traceback (most recent call last):\nRuntimeError: render failed",
            },
            "recent_events": [
                {
                    "seq": 1,
                    "timestamp": "2026-05-19T09:59:59+00:00",
                    "source": "editor",
                    "event": "editor.render.started",
                    "operation": "editor.render",
                    "operation_id": "op-1",
                    "boundary": "",
                    "context": {"source_filename": "clip.mp3"},
                }
            ],
            "crash_forensics": {
                "session_id": "session-1",
                "debug_enabled": True,
                "event_log_path": "/addon/anki_audio_quick_editor_events.jsonl",
                "crash_log_path": "/addon/anki_audio_quick_editor_crash.log",
                "session_marker_path": "/addon/anki_audio_quick_editor_session.json",
                "previous_dirty_session": {"session_id": "previous", "clean_exit": False},
            },
        },
    )
    assert "Latest captured error" in report
    assert "Boundary: editor.worker.render" in report
    assert "RuntimeError: render failed" in report
    assert "Recent event sequence" in report
    assert "editor:editor.render.started" in report
    assert "Crash forensics" in report
    assert "Previous session ended cleanly: no" in report
    assert "/addon/anki_audio_quick_editor_events.jsonl" in report


def test_support_report_renders_rnnoise_incident_and_health() -> None:
    report = build_support_report_text(
        version="1.2.3",
        addon_dir="/addon",
        log_file_path="/addon/anki_audio_quick_editor.log",
        deep_filter_health={"available": False},
        rnnoise_health={"available": True, "path": "/bin/rnnoise-cli", "version": "rnnoise-cli 0.2", "error": ""},
        denoise_incident={
            "timestamp": "2026-05-17T09:08:07+00:00",
            "operation": "rnnoise_denoise",
            "media_filename": "clip.mp3",
            "source_path": "/media/clip.mp3",
            "user_message": "invalid raw input",
            "exception_type": "AudioProcessingError",
            "ffmpeg_path": "/bin/ffmpeg",
            "rnnoise_path": "/bin/rnnoise-cli",
            "attempted_commands": [
                build_command_record(("/bin/rnnoise-cli", "denoise"), returncode=5, stdout='{"error":"invalid raw input"}')
            ],
        },
        pause_pipeline_incident=None,
        log_tail="recent log",
    )
    assert "Latest denoise failure" in report
    assert "RNNoise path: /bin/rnnoise-cli" in report
    assert "1. /bin/rnnoise-cli denoise" in report
    assert "Current RNNoise health" in report
    assert '"version": "rnnoise-cli 0.2"' in report


def test_support_report_renders_spleeter_incident_and_health() -> None:
    report = build_support_report_text(
        version="1.2.3",
        addon_dir="/addon",
        log_file_path="/addon/anki_audio_quick_editor.log",
        deep_filter_health={"available": False},
        rnnoise_health={"available": False},
        denoise_incident=None,
        spleeter_health={"available": True, "path": "/bin/sherpa-spleeter", "version": "sherpa-spleeter 1.0", "error": ""},
        spleeter_incident={
            "timestamp": "2026-05-17T09:08:07+00:00",
            "operation": "voice_only",
            "media_filename": "clip.mp3",
            "source_path": "/media/clip.mp3",
            "user_message": "invalid wav",
            "exception_type": "AudioProcessingError",
            "ffmpeg_path": "/bin/ffmpeg",
            "spleeter_path": "/bin/sherpa-spleeter",
            "vocals_model_path": "/models/vocals.fp16.onnx",
            "accompaniment_model_path": "/models/accompaniment.fp16.onnx",
            "attempted_commands": [
                build_command_record(("/bin/sherpa-spleeter", "--json"), returncode=5, stdout='{"error":"invalid wav"}')
            ],
        },
        pause_pipeline_incident=None,
        log_tail="recent log",
    )
    assert "Latest Voice Only failure" in report
    assert "Sherpa Spleeter path: /bin/sherpa-spleeter" in report
    assert "Vocals model path: /models/vocals.fp16.onnx" in report
    assert "Accompaniment model path: /models/accompaniment.fp16.onnx" in report
    assert "1. /bin/sherpa-spleeter --json" in report
    assert "Current Sherpa Spleeter health" in report
    assert '"version": "sherpa-spleeter 1.0"' in report


def test_rnnoise_support_log_block_renders_optional_command_details() -> None:
    from anki_audio_quick_editor.support import format_rnnoise_support_log_block

    block = format_rnnoise_support_log_block(
        {
            "timestamp": "2026-05-17T09:08:07+00:00",
            "operation": "rnnoise_denoise",
            "media_filename": "clip.mp3",
            "source_path": "/media/clip.mp3",
            "user_message": "invalid raw input",
            "exception_type": "AudioProcessingError",
            "ffmpeg_path": "/bin/ffmpeg",
            "rnnoise_path": "/bin/rnnoise-cli",
            "attempted_commands": [
                build_command_record(
                    ("/bin/rnnoise-cli", "denoise"),
                    returncode=None,
                    stdout="partial stdout",
                    stderr="partial stderr",
                    launch_error="permission denied",
                )
            ],
        }
    )
    assert "denoise support incident:" in block
    assert "command_1: /bin/rnnoise-cli denoise" in block
    assert "returncode: None" in block
    assert "launch_error: permission denied" in block
    assert "stdout: partial stdout" in block
    assert "stderr: partial stderr" in block


def test_spleeter_support_log_block_renders_optional_command_details() -> None:
    block = format_spleeter_support_log_block(
        {
            "timestamp": "2026-05-17T09:08:07+00:00",
            "operation": "voice_only",
            "media_filename": "clip.mp3",
            "source_path": "/media/clip.mp3",
            "user_message": "invalid wav",
            "exception_type": "AudioProcessingError",
            "ffmpeg_path": "/bin/ffmpeg",
            "spleeter_path": "/bin/sherpa-spleeter",
            "vocals_model_path": "/models/vocals.fp16.onnx",
            "accompaniment_model_path": "/models/accompaniment.fp16.onnx",
            "attempted_commands": [
                build_command_record(
                    ("/bin/sherpa-spleeter", "--json"),
                    returncode=None,
                    stdout="partial stdout",
                    stderr="partial stderr",
                    launch_error="permission denied",
                )
            ],
        }
    )
    assert "sherpa spleeter support incident:" in block
    assert "command_1: /bin/sherpa-spleeter --json" in block
    assert "returncode: None" in block
    assert "launch_error: permission denied" in block
    assert "stdout: partial stdout" in block
    assert "stderr: partial stderr" in block
