from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_processor import render_dpdfnet_audio
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.errors import AudioProcessingError
from anki_audio_quick_editor.support import (
    clear_latest_denoise_support_incident,
    latest_denoise_support_incident,
)


def test_render_dpdfnet_audio_runs_denoise_and_encode(
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
        "anki_audio_quick_editor.audio_processor.find_dpdfnet_bundle",
        lambda: Path("/bin/dpdfnet"),
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
        if cmd[0] == "/bin/dpdfnet":
            Path(cmd[5]).write_bytes(b"denoised")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "denoised.mp3"
    result = render_dpdfnet_audio(
        tmp_path / "source.mp3",
        AudioProcessingConfig(dpdfnet_attn_limit_db=8.5),
        output_path=output,
        on_command=commands.append,
    )

    assert calls[0] == [
        "/bin/dpdfnet",
        "enhance",
        "--attn-limit-db",
        "8.5",
        str(tmp_path / "source.mp3"),
        calls[0][5],
    ]
    assert calls[1][0:4] == ["/bin/ffmpeg", "-y", "-i", calls[0][5]]
    assert calls[1][-5:] == ["-codec:a", "libmp3lame", "-q:a", "4", str(output)]
    assert commands == [tuple(call) for call in calls]
    assert result.output_path == output
    assert result.command == tuple(calls[0])
    assert result.duration_ms == 1000
    assert latest_denoise_support_incident() is None


def test_render_dpdfnet_audio_reports_denoise_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_denoise_support_incident()
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_ffmpeg",
        lambda _path: Path("/bin/ffmpeg"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_dpdfnet_bundle",
        lambda: Path("/bin/dpdfnet"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=2, stdout="", stderr="bad model"),
    )

    with pytest.raises(AudioProcessingError, match="bad model"):
        render_dpdfnet_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "denoised.mp3",
        )
    incident = latest_denoise_support_incident()
    assert incident is not None
    assert incident["operation"] == "dpdfnet_denoise"
    assert incident["media_filename"] == "source.mp3"
    assert incident["ffmpeg_path"] == "/bin/ffmpeg"
    assert incident["dpdfnet_path"] == "/bin/dpdfnet"
    assert len(incident["attempted_commands"]) == 1
    assert incident["attempted_commands"][0]["command"].startswith("/bin/dpdfnet enhance")
    assert incident["attempted_commands"][0]["returncode"] == 2


def test_render_dpdfnet_audio_reports_launch_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_denoise_support_incident()
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_ffmpeg",
        lambda _path: Path("/bin/ffmpeg"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_dpdfnet_bundle",
        lambda: Path("/bin/dpdfnet"),
    )

    def fake_run(*_args, **_kwargs) -> SimpleNamespace:
        raise PermissionError(13, "Permission denied", "/bin/dpdfnet")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="Could not start DPDFNet denoise"):
        render_dpdfnet_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "denoised.mp3",
        )
    incident = latest_denoise_support_incident()
    assert incident is not None
    assert incident["attempted_commands"][0]["launch_error"].startswith(
        "Could not start DPDFNet denoise."
    )


def test_render_dpdfnet_audio_reports_timeout_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_denoise_support_incident()
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_ffmpeg",
        lambda _path: Path("/bin/ffmpeg"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_dpdfnet_bundle",
        lambda: Path("/bin/dpdfnet"),
    )

    def fake_run(cmd: list[str], *_args, timeout: float, **_kwargs) -> SimpleNamespace:
        raise subprocess.TimeoutExpired(cmd, timeout=timeout)

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="Timed out"):
        render_dpdfnet_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "denoised.mp3",
        )
    incident = latest_denoise_support_incident()
    assert incident is not None
    assert incident["operation"] == "dpdfnet_denoise"
    assert len(incident["attempted_commands"]) == 1
    assert incident["attempted_commands"][0]["command"].startswith("/bin/dpdfnet enhance")
    assert "Timed out" in incident["attempted_commands"][0]["launch_error"]


def test_render_dpdfnet_audio_reports_missing_wav_output(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_denoise_support_incident()
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_ffmpeg",
        lambda _path: Path("/bin/ffmpeg"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_dpdfnet_bundle",
        lambda: Path("/bin/dpdfnet"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    with pytest.raises(AudioProcessingError, match="DPDFNet did not produce a WAV output"):
        render_dpdfnet_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "denoised.mp3",
        )


def test_render_dpdfnet_audio_reports_encode_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_denoise_support_incident()
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_ffmpeg",
        lambda _path: Path("/bin/ffmpeg"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_dpdfnet_bundle",
        lambda: Path("/bin/dpdfnet"),
    )

    def fake_run(cmd: list[str], *_args, **_kwargs) -> SimpleNamespace:
        if cmd[0] == "/bin/dpdfnet":
            Path(cmd[5]).write_bytes(b"denoised")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="encode failed")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="encode failed"):
        render_dpdfnet_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "denoised.mp3",
        )
    incident = latest_denoise_support_incident()
    assert incident is not None
    assert len(incident["attempted_commands"]) == 2
    assert incident["attempted_commands"][1]["command"].startswith("/bin/ffmpeg")
