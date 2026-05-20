from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_processor import render_rnnoise_audio
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.errors import AudioProcessingError
from anki_audio_quick_editor.support import (
    clear_latest_denoise_support_incident,
    latest_denoise_support_incident,
)


def test_render_rnnoise_audio_runs_prepare_denoise_and_encode(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_denoise_support_incident()
    calls: list[list[str]] = []
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_ffmpeg",
        lambda _path: Path("/bin/ffmpeg"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_rnnoise_bundle",
        lambda: Path("/bin/rnnoise-cli"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.probe_duration_ms",
        lambda *_args: 1000,
    )

    def fake_run(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: float,
    ) -> SimpleNamespace:
        assert timeout > 0
        calls.append(cmd)
        if cmd[0] == "/bin/rnnoise-cli":
            Path(cmd[cmd.index("--output") + 1]).write_bytes(b"denoised")
            return SimpleNamespace(returncode=0, stdout='{"ok":true}', stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "denoised.mp3"
    result = render_rnnoise_audio(
        tmp_path / "source.mp3",
        AudioProcessingConfig(),
        output_path=output,
        on_command=commands.append,
    )

    assert calls[0] == [
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "source.mp3"),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "48000",
        "-f",
        "s16le",
        "-codec:a",
        "pcm_s16le",
        calls[0][-1],
    ]
    assert calls[1][0] == "/bin/rnnoise-cli"
    assert calls[1][1:] == [
        "denoise",
        "--input",
        calls[1][3],
        "--output",
        calls[1][5],
        "--overwrite",
        "--json",
    ]
    assert calls[2][0:8] == [
        "/bin/ffmpeg",
        "-y",
        "-f",
        "s16le",
        "-ar",
        "48000",
        "-ac",
        "1",
    ]
    assert calls[2][-5:] == ["-codec:a", "libmp3lame", "-q:a", "4", str(output)]
    assert commands == [tuple(call) for call in calls]
    assert result.output_path == output
    assert result.command == tuple(calls[1])
    assert result.duration_ms == 1000
    assert latest_denoise_support_incident() is None


def test_render_rnnoise_audio_reports_denoise_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_denoise_support_incident()
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_ffmpeg",
        lambda _path: Path("/bin/ffmpeg"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_rnnoise_bundle",
        lambda: Path("/bin/rnnoise-cli"),
    )

    def fake_run(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: float,
    ) -> SimpleNamespace:
        assert timeout > 0
        if cmd[0] == "/bin/rnnoise-cli":
            return SimpleNamespace(returncode=5, stdout='{"error":"invalid raw input"}', stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="invalid raw input"):
        render_rnnoise_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "denoised.mp3",
        )
    incident = latest_denoise_support_incident()
    assert incident is not None
    assert incident["operation"] == "rnnoise_denoise"
    assert incident["media_filename"] == "source.mp3"
    assert incident["ffmpeg_path"] == "/bin/ffmpeg"
    assert incident["rnnoise_path"] == "/bin/rnnoise-cli"
    assert len(incident["attempted_commands"]) == 2
    assert incident["attempted_commands"][1]["command"].startswith(
        "/bin/rnnoise-cli denoise"
    )
    assert incident["attempted_commands"][1]["returncode"] == 5
    assert incident["attempted_commands"][1]["stdout"] == '{"error":"invalid raw input"}'


def test_render_rnnoise_audio_reports_launch_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_denoise_support_incident()
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_ffmpeg",
        lambda _path: Path("/bin/ffmpeg"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_rnnoise_bundle",
        lambda: Path("/bin/rnnoise-cli"),
    )

    def fake_run(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: float,
    ) -> SimpleNamespace:
        assert timeout > 0
        if cmd[0] == "/bin/rnnoise-cli":
            raise PermissionError(13, "Permission denied", "/bin/rnnoise-cli")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="Could not start RNNoise denoise"):
        render_rnnoise_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "denoised.mp3",
        )
    incident = latest_denoise_support_incident()
    assert incident is not None
    assert incident["attempted_commands"][1]["launch_error"].startswith(
        "Could not start RNNoise denoise."
    )
