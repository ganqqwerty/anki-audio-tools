"""Tests for support-report helpers."""

from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.support import (
    build_command_record,
    build_support_report_text,
    clear_latest_pause_pipeline_support_incident,
    clear_latest_rnnoise_support_incident,
    latest_pause_pipeline_support_incident,
    latest_rnnoise_support_incident,
    read_log_tail,
    record_latest_pause_pipeline_support_incident,
    record_latest_rnnoise_support_incident,
)


def test_pause_pipeline_incident_ignores_empty_updates_and_keeps_valid_fields() -> None:
    clear_latest_pause_pipeline_support_incident()
    record_latest_pause_pipeline_support_incident(
        operation="deep_filter_pause_speedup",
        media_filename="clip.mp3",
        user_message="first failure",
        attempted_commands=[build_command_record(("/bin/ffmpeg", "-version"), returncode=0)],
    )

    updated = record_latest_pause_pipeline_support_incident(
        operation="",
        media_filename=None,
        user_message="updated failure",
        attempted_commands=[],
        extra={},
    )

    assert updated["operation"] == "deep_filter_pause_speedup"
    assert updated["media_filename"] == "clip.mp3"
    assert updated["user_message"] == "updated failure"
    assert updated["attempted_commands"] == [
        {
            "argv": ["/bin/ffmpeg", "-version"],
            "command": "/bin/ffmpeg -version",
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "launch_error": "",
        }
    ]


def test_latest_pause_pipeline_incident_returns_deep_copy() -> None:
    clear_latest_pause_pipeline_support_incident()
    incident = record_latest_pause_pipeline_support_incident(
        operation="deep_filter_pause_speedup",
        attempted_commands=[build_command_record(("/bin/deep-filter", "-D"), returncode=12, stderr="boom")],
    )

    incident["attempted_commands"][0]["stderr"] = "mutated"

    latest = latest_pause_pipeline_support_incident()
    assert latest is not None
    assert latest["attempted_commands"][0]["stderr"] == "boom"


def test_latest_rnnoise_incident_returns_deep_copy() -> None:
    clear_latest_rnnoise_support_incident()
    incident = record_latest_rnnoise_support_incident(
        operation="rnnoise_denoise",
        attempted_commands=[build_command_record(("/bin/rnnoise-cli", "--version"), returncode=1, stderr="boom")],
    )

    incident["attempted_commands"][0]["stderr"] = "mutated"

    latest = latest_rnnoise_support_incident()
    assert latest is not None
    assert latest["attempted_commands"][0]["stderr"] == "boom"


def test_support_report_renders_pause_pipeline_command_details() -> None:
    report = build_support_report_text(
        version="1.2.3",
        addon_dir="/addon",
        log_file_path="/addon/anki_audio_quick_editor.log",
        deep_filter_health={"available": False},
        rnnoise_health={"available": False},
        rnnoise_incident=None,
        pause_pipeline_incident={
            "timestamp": "2026-05-17T09:08:07+00:00",
            "operation": "deep_filter_pause_speedup",
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
        rnnoise_incident=None,
        pause_pipeline_incident={"operation": "deep_filter_pause_speedup"},
        log_tail="recent log",
    )

    assert "(no external commands were captured)" in report


def test_support_report_renders_rnnoise_incident_and_health() -> None:
    report = build_support_report_text(
        version="1.2.3",
        addon_dir="/addon",
        log_file_path="/addon/anki_audio_quick_editor.log",
        deep_filter_health={"available": False},
        rnnoise_health={"available": True, "path": "/bin/rnnoise-cli", "version": "rnnoise-cli 0.2", "error": ""},
        rnnoise_incident={
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

    assert "Latest RNNoise failure" in report
    assert "RNNoise path: /bin/rnnoise-cli" in report
    assert "1. /bin/rnnoise-cli denoise" in report
    assert "Current RNNoise health" in report
    assert '"version": "rnnoise-cli 0.2"' in report


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

    assert "rnnoise support incident:" in block
    assert "command_1: /bin/rnnoise-cli denoise" in block
    assert "returncode: None" in block
    assert "launch_error: permission denied" in block
    assert "stdout: partial stdout" in block
    assert "stderr: partial stderr" in block


def test_incident_recorders_ignore_empty_string_list_and_dict_fields() -> None:
    clear_latest_rnnoise_support_incident()

    record_latest_rnnoise_support_incident(
        operation="rnnoise_denoise",
        media_filename="clip.mp3",
        attempted_commands=[build_command_record(("/bin/rnnoise-cli", "--version"), returncode=0)],
        metadata={"tool": "rnnoise"},
    )
    updated = record_latest_rnnoise_support_incident(
        operation="",
        media_filename="",
        attempted_commands=[],
        metadata={},
        user_message="updated",
    )

    assert updated["operation"] == "rnnoise_denoise"
    assert updated["media_filename"] == "clip.mp3"
    assert updated["attempted_commands"][0]["command"] == "/bin/rnnoise-cli --version"
    assert updated["metadata"] == {"tool": "rnnoise"}
    assert updated["user_message"] == "updated"


def test_read_log_tail_reports_empty_file(tmp_path: Path) -> None:
    log_path = tmp_path / "empty.log"
    log_path.write_text("", encoding="utf-8")

    assert read_log_tail(log_path) == "(log file is empty)"


def test_read_log_tail_returns_only_requested_tail(tmp_path: Path) -> None:
    log_path = tmp_path / "tail.log"
    log_path.write_text("one\ntwo\nthree\n", encoding="utf-8")

    assert read_log_tail(log_path, max_lines=2) == "two\nthree"


def test_read_log_tail_reports_unreadable_file(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "unreadable.log"
    log_path.write_text("secret", encoding="utf-8")

    def fake_read_text(self: Path, encoding: str) -> str:
        assert self == log_path
        assert encoding == "utf-8"
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "read_text", fake_read_text)

    assert read_log_tail(log_path) == f"Could not read log file {log_path}: permission denied"
