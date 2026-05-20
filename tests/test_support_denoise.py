"""Tests for external-denoise support-report helpers."""

from __future__ import annotations

from anki_audio_quick_editor.support import (
    build_command_record,
    build_support_report_text,
    clear_latest_denoise_support_incident,
    format_denoise_support_log_block,
    record_latest_denoise_support_incident,
)


def test_support_report_renders_denoise_incident_and_health() -> None:
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
                build_command_record(
                    ("/bin/rnnoise-cli", "denoise"),
                    returncode=5,
                    stdout='{"error":"invalid raw input"}',
                )
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


def test_support_report_renders_dpdfnet_incident_path_and_health() -> None:
    report = build_support_report_text(
        version="1.2.3",
        addon_dir="/addon",
        log_file_path="/addon/anki_audio_quick_editor.log",
        deep_filter_health={"available": False},
        rnnoise_health={"available": False},
        dpdfnet_health={"available": True, "path": "/bin/dpdfnet", "version": "dpdfnet-lite 0.1.0", "error": ""},
        denoise_incident={
            "timestamp": "2026-05-17T09:08:07+00:00",
            "operation": "dpdfnet_denoise",
            "media_filename": "clip.mp3",
            "source_path": "/media/clip.mp3",
            "user_message": "DPDFNet denoise failed.",
            "exception_type": "AudioProcessingError",
            "ffmpeg_path": "/bin/ffmpeg",
            "dpdfnet_path": "/bin/dpdfnet",
            "attempted_commands": [
                build_command_record(
                    ("/bin/dpdfnet", "enhance", "clip.mp3", "denoised.wav"),
                    returncode=2,
                    stderr="model crashed",
                )
            ],
        },
        pause_pipeline_incident=None,
        log_tail="recent log",
    )

    assert "Latest denoise failure" in report
    assert "DPDFNet path: /bin/dpdfnet" in report
    assert "1. /bin/dpdfnet enhance clip.mp3 denoised.wav" in report
    assert "stderr: model crashed" in report
    assert "Current DPDFNet health" in report
    assert '"version": "dpdfnet-lite 0.1.0"' in report


def test_denoise_support_log_block_renders_optional_command_details() -> None:
    block = format_denoise_support_log_block(
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


def test_denoise_support_log_block_renders_dpdfnet_path() -> None:
    block = format_denoise_support_log_block(
        {
            "operation": "dpdfnet_denoise",
            "media_filename": "clip.mp3",
            "source_path": "/media/clip.mp3",
            "user_message": "model crashed",
            "exception_type": "AudioProcessingError",
            "ffmpeg_path": "/bin/ffmpeg",
            "dpdfnet_path": "/bin/dpdfnet",
        }
    )

    assert "denoise support incident:" in block
    assert "operation: dpdfnet_denoise" in block
    assert "dpdfnet_path: /bin/dpdfnet" in block


def test_denoise_incident_operation_change_resets_algorithm_specific_fields() -> None:
    clear_latest_denoise_support_incident()

    record_latest_denoise_support_incident(
        operation="rnnoise_denoise",
        source_path="/media/rnnoise.mp3",
        user_message="invalid raw input",
        exception_type="AudioProcessingError",
        rnnoise_path="/bin/rnnoise-cli",
        attempted_commands=[build_command_record(("/bin/rnnoise-cli", "denoise"), returncode=1)],
    )
    updated = record_latest_denoise_support_incident(
        operation="dpdfnet_denoise",
        source_path="/media/dpdfnet.mp3",
        user_message="model crashed",
        exception_type="AudioProcessingError",
        dpdfnet_path="/bin/dpdfnet",
        attempted_commands=[],
    )

    assert updated["operation"] == "dpdfnet_denoise"
    assert updated["source_path"] == "/media/dpdfnet.mp3"
    assert updated["attempted_commands"] == []
    assert updated["dpdfnet_path"] == "/bin/dpdfnet"
    assert "rnnoise_path" not in updated


def test_denoise_incident_matching_context_preserves_external_command_details() -> None:
    clear_latest_denoise_support_incident()

    record_latest_denoise_support_incident(
        operation="dpdfnet_denoise",
        source_path="/media/clip.mp3",
        user_message="model crashed",
        exception_type="AudioProcessingError",
        ffmpeg_path="/bin/ffmpeg",
        dpdfnet_path="/bin/dpdfnet",
        attempted_commands=[build_command_record(("/bin/dpdfnet", "enhance"), returncode=2, stderr="crash")],
    )
    updated = record_latest_denoise_support_incident(
        operation="dpdfnet_denoise",
        source_path="/media/clip.mp3",
        user_message="model crashed",
        exception_type="AudioProcessingError",
        ffmpeg_path="",
    )

    assert updated["ffmpeg_path"] == "/bin/ffmpeg"
    assert updated["dpdfnet_path"] == "/bin/dpdfnet"
    assert updated["attempted_commands"][0]["stderr"] == "crash"
