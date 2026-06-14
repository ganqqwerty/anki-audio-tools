from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_output_policy import AudioSourceMetadata
from anki_audio_quick_editor.audio_processor import (
    find_dpdfnet_bundle,
    render_dpdfnet_audio,
)
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.errors import AudioProcessingError, MissingDpdfnetError
from anki_audio_quick_editor.support import (
    clear_latest_denoise_support_incident,
    latest_denoise_support_incident,
)
from tests.audio_fixtures import FFMPEG_AVAILABLE, _run_ffmpeg, FFMPEG_SKIP_REASON

DPDFNET = str(Path("/bin/dpdfnet"))
FFMPEG = str(Path("/bin/ffmpeg"))


@pytest.fixture(autouse=True)
def stub_source_metadata(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.probe_audio_metadata",
        lambda source_path, _config: AudioSourceMetadata(
            path=source_path,
            visible_format="mp3",
            codec_name="mp3",
            sample_rate=44100,
            channels=2,
            bit_rate=192000,
            bits_per_raw_sample=None,
            sample_fmt=None,
        ),
    )


def _generate_mono_tone(path: Path, *, duration_s: float = 0.8) -> None:
    _run_ffmpeg(
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={duration_s}",
        "-c:a",
        "libmp3lame",
        str(path),
    )


@pytest.mark.allow_managed_runtime
def test_render_dpdfnet_audio_smoke_uses_managed_dpdfnet_when_available(
    tmp_path: Path,
) -> None:
    if not FFMPEG_AVAILABLE:
        pytest.skip(FFMPEG_SKIP_REASON)

    try:
        dpdfnet_path = find_dpdfnet_bundle()
    except MissingDpdfnetError:
        pytest.skip("dpdfnet not available")

    source = tmp_path / "source.mp3"
    output = tmp_path / "denoised.mp3"
    _generate_mono_tone(source, duration_s=0.8)

    result = render_dpdfnet_audio(source, AudioProcessingConfig(), output_path=output)

    assert result.output_path == output
    assert result.command[0] == str(dpdfnet_path)
    assert result.command[:2] == (str(dpdfnet_path), "enhance")
    assert output.is_file()
    assert result.duration_ms >= 700


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
        env: dict[str, str] | None = None,
        **_kwargs: object,
    ) -> SimpleNamespace:
        assert timeout > 0
        calls.append(cmd)
        if cmd[0] == DPDFNET:
            assert env is not None
            assert env["DPDFNET_FFMPEG"] == FFMPEG
            Path(cmd[5]).write_bytes(b"denoised")
        else:
            assert env is None
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "denoised.mp3"
    result = render_dpdfnet_audio(
        tmp_path / "source.mp3",
        AudioProcessingConfig(dpdfnet_attn_limit_db=18.0),
        output_path=output,
        on_command=commands.append,
    )

    assert calls[0] == [
        DPDFNET,
        "enhance",
        "--attn-limit-db",
        "18",
        str(tmp_path / "source.mp3"),
        calls[0][5],
    ]
    assert calls[1][0:4] == [FFMPEG, "-y", "-i", calls[0][5]]
    assert calls[1][-9:] == ["-codec:a", "libmp3lame", "-b:a", "192k", "-ar", "44100", "-ac", "2", str(output)]
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
    assert incident["ffmpeg_path"] == FFMPEG
    assert incident["dpdfnet_path"] == DPDFNET
    assert len(incident["attempted_commands"]) == 1
    assert incident["attempted_commands"][0]["argv"][:2] == [DPDFNET, "enhance"]
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
    assert incident["attempted_commands"][0]["argv"][:2] == [DPDFNET, "enhance"]
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
        if cmd[0] == DPDFNET:
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
    assert incident["attempted_commands"][1]["argv"][0] == FFMPEG
