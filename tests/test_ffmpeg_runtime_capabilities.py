from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts.ffmpeg_runtime_capabilities import (
    REQUIRED_AUDIO_OUTPUT_CAPABILITY_PROFILE,
    FfmpegCapabilities,
    collect_ffmpeg_capabilities,
    parse_ffmpeg_table,
    validate_required_audio_output_capabilities,
    verify_ffmpeg_binary,
)


def test_parse_ffmpeg_table_extracts_names_from_encoder_and_muxer_tables() -> None:
    output = """
Encoders:
 A..... aac                  AAC (Advanced Audio Coding)
 A..... libopus              libopus Opus
Muxers:
  E mp3             MP3 (MPEG audio layer 3)
  E webm            WebM
"""

    assert parse_ffmpeg_table(output) == {"aac", "libopus", "mp3", "webm"}


def test_complete_source_audio_capability_profile_passes() -> None:
    report = validate_required_audio_output_capabilities(
        FfmpegCapabilities(
            encoders=set(REQUIRED_AUDIO_OUTPUT_CAPABILITY_PROFILE["encoders"]),
            muxers=set(REQUIRED_AUDIO_OUTPUT_CAPABILITY_PROFILE["muxers"]),
        )
    )

    assert report.ok is True
    assert report.messages == []


@pytest.mark.parametrize(
    ("missing_encoder", "expected_message"),
    [
        ("libopus", ".opus and .webm preservation requires FFmpeg encoder libopus"),
        ("libvorbis", ".ogg and .oga preservation requires FFmpeg encoder libvorbis"),
        ("pcm_s24le", "24-bit WAV preservation requires FFmpeg encoder pcm_s24le"),
    ],
)
def test_missing_required_encoder_reports_blocked_source_formats(
    missing_encoder: str,
    expected_message: str,
) -> None:
    encoders = set(REQUIRED_AUDIO_OUTPUT_CAPABILITY_PROFILE["encoders"])
    encoders.remove(missing_encoder)

    report = validate_required_audio_output_capabilities(
        FfmpegCapabilities(
            encoders=encoders,
            muxers=set(REQUIRED_AUDIO_OUTPUT_CAPABILITY_PROFILE["muxers"]),
        )
    )

    assert report.ok is False
    assert expected_message in "\n".join(report.messages)


def test_missing_raw_aac_muxer_reports_blocked_source_format() -> None:
    muxers = set(REQUIRED_AUDIO_OUTPUT_CAPABILITY_PROFILE["muxers"])
    muxers.remove("adts")

    report = validate_required_audio_output_capabilities(
        FfmpegCapabilities(
            encoders=set(REQUIRED_AUDIO_OUTPUT_CAPABILITY_PROFILE["encoders"]),
            muxers=muxers,
        )
    )

    assert report.ok is False
    assert "raw .aac preservation requires FFmpeg muxer adts" in "\n".join(report.messages)


def test_collect_ffmpeg_capabilities_runs_encoder_and_muxer_commands(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs: object) -> SimpleNamespace:
        calls.append(cmd)
        if cmd[-1] == "-encoders":
            return SimpleNamespace(returncode=0, stdout=" A..... libmp3lame\n A..... aac\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="  E mp3\n  E mp4\n", stderr="")

    monkeypatch.setattr("scripts.ffmpeg_runtime_capabilities.subprocess.run", fake_run)

    capabilities = collect_ffmpeg_capabilities(tmp_path / "ffmpeg")

    assert capabilities.encoders == {"libmp3lame", "aac"}
    assert capabilities.muxers == {"mp3", "mp4"}
    assert calls == [
        [str(tmp_path / "ffmpeg"), "-hide_banner", "-encoders"],
        [str(tmp_path / "ffmpeg"), "-hide_banner", "-muxers"],
    ]


def test_verify_ffmpeg_binary_raises_with_missing_profile_details(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "scripts.ffmpeg_runtime_capabilities.collect_ffmpeg_capabilities",
        lambda _path: FfmpegCapabilities(encoders={"aac"}, muxers={"mp3"}),
    )

    with pytest.raises(RuntimeError, match="aqe-source-audio-v1"):
        verify_ffmpeg_binary(tmp_path / "ffmpeg")
