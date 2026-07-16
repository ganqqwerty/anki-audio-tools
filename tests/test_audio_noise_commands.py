"""Noise-reduction command builder tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_commands import (
    _atempo_filters,
    build_deep_filter_command,
    build_deep_filter_prepare_command,
    build_dpdfnet_command,
    build_mp3_encode_command,
    build_rnnoise_command,
    build_rnnoise_encode_command,
    build_rnnoise_prepare_command,
    build_spleeter_command,
    build_spleeter_prepare_command,
)
from anki_audio_quick_editor.errors import AudioProcessingError

DEEP_FILTER = str(Path("/bin/deep-filter"))
DPDFNET = str(Path("/bin/dpdfnet"))
FFMPEG = str(Path("/bin/ffmpeg"))
RNNOISE = str(Path("/bin/rnnoise-cli"))
SPLEETER = str(Path("/bin/sherpa-spleeter"))


def test_build_deep_filter_prepare_command_uses_48khz_mono_pcm(tmp_path: Path) -> None:
    assert build_deep_filter_prepare_command(Path("/bin/ffmpeg"), tmp_path / "source.mp3", tmp_path / "input.wav") == (
        FFMPEG,
        "-y",
        "-i",
        str(tmp_path / "source.mp3"),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "48000",
        "-codec:a",
        "pcm_s16le",
        str(tmp_path / "input.wav"),
    )


def test_build_deep_filter_prepare_command_rejects_non_wav_intermediate_output(tmp_path: Path) -> None:
    with pytest.raises(AudioProcessingError, match="WAV output"):
        build_deep_filter_prepare_command(Path("/bin/ffmpeg"), tmp_path / "source.mp3", tmp_path / "input.mp3")


def test_build_deep_filter_command_includes_post_filter_when_enabled(tmp_path: Path) -> None:
    assert build_deep_filter_command(Path("/bin/deep-filter"), tmp_path / "input.wav", tmp_path / "out", post_filter=True) == (
        DEEP_FILTER,
        "-D",
        "--pf",
        "-o",
        str(tmp_path / "out"),
        str(tmp_path / "input.wav"),
    )


def test_build_deep_filter_command_omits_post_filter_when_disabled(tmp_path: Path) -> None:
    command = build_deep_filter_command(Path("/bin/deep-filter"), tmp_path / "input.wav", tmp_path / "out", post_filter=False)
    assert "--pf" not in command
    assert command == (DEEP_FILTER, "-D", "-o", str(tmp_path / "out"), str(tmp_path / "input.wav"))


def test_build_rnnoise_prepare_command_uses_48khz_mono_raw_pcm(tmp_path: Path) -> None:
    assert build_rnnoise_prepare_command(Path("/bin/ffmpeg"), tmp_path / "source.mp3", tmp_path / "input.s16le") == (
        FFMPEG,
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
        str(tmp_path / "input.s16le"),
    )


def test_build_rnnoise_prepare_command_rejects_non_raw_pcm_intermediate_output(tmp_path: Path) -> None:
    with pytest.raises(AudioProcessingError, match="raw PCM output"):
        build_rnnoise_prepare_command(Path("/bin/ffmpeg"), tmp_path / "source.mp3", tmp_path / "input.wav")


def test_build_rnnoise_command_includes_json_and_overwrite(tmp_path: Path) -> None:
    assert build_rnnoise_command(Path("/bin/rnnoise-cli"), tmp_path / "input.s16le", tmp_path / "denoised.s16le") == (
        RNNOISE,
        "denoise",
        "--input",
        str(tmp_path / "input.s16le"),
        "--output",
        str(tmp_path / "denoised.s16le"),
        "--overwrite",
        "--json",
    )


def test_build_dpdfnet_command_uses_enhance_subcommand(tmp_path: Path) -> None:
    assert build_dpdfnet_command(
        Path("/bin/dpdfnet"),
        tmp_path / "source.mp3",
        tmp_path / "denoised.wav",
        attn_limit_db=12.0,
    ) == (
        DPDFNET,
        "enhance",
        "--attn-limit-db",
        "12",
        str(tmp_path / "source.mp3"),
        str(tmp_path / "denoised.wav"),
    )


def test_build_rnnoise_encode_command_reads_raw_pcm(tmp_path: Path) -> None:
    assert build_rnnoise_encode_command(Path("/bin/ffmpeg"), tmp_path / "denoised.s16le", tmp_path / "denoised.mp3") == (
        FFMPEG,
        "-y",
        "-f",
        "s16le",
        "-ar",
        "48000",
        "-ac",
        "1",
        "-i",
        str(tmp_path / "denoised.s16le"),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(tmp_path / "denoised.mp3"),
    )


def test_build_spleeter_prepare_command_uses_44k1_stereo_wav(tmp_path: Path) -> None:
    assert build_spleeter_prepare_command(Path("/bin/ffmpeg"), tmp_path / "source.mp3", tmp_path / "input.wav") == (
        FFMPEG,
        "-y",
        "-i",
        str(tmp_path / "source.mp3"),
        "-vn",
        "-ac",
        "2",
        "-ar",
        "44100",
        "-codec:a",
        "pcm_s16le",
        str(tmp_path / "input.wav"),
    )


def test_build_spleeter_prepare_command_rejects_non_wav_intermediate_output(tmp_path: Path) -> None:
    with pytest.raises(AudioProcessingError, match="WAV output"):
        build_spleeter_prepare_command(Path("/bin/ffmpeg"), tmp_path / "source.mp3", tmp_path / "input.mp3")


def test_build_spleeter_command_uses_sherpa_source_separation_flags(tmp_path: Path) -> None:
    assert build_spleeter_command(
        Path("/bin/sherpa-spleeter"),
        tmp_path / "vocals.fp16.onnx",
        tmp_path / "accompaniment.fp16.onnx",
        tmp_path / "input.wav",
        tmp_path / "out",
    ) == (
        SPLEETER,
        f"--spleeter-vocals={tmp_path / 'vocals.fp16.onnx'}",
        f"--spleeter-accompaniment={tmp_path / 'accompaniment.fp16.onnx'}",
        f"--input-wav={tmp_path / 'input.wav'}",
        f"--output-vocals-wav={tmp_path / 'out' / 'vocals.wav'}",
        f"--output-accompaniment-wav={tmp_path / 'out' / 'accompaniment.wav'}",
        "--num-threads=1",
    )


def test_build_mp3_encode_command_uses_existing_output_policy(tmp_path: Path) -> None:
    assert build_mp3_encode_command(Path("/bin/ffmpeg"), tmp_path / "cleaned.wav", tmp_path / "cleaned.mp3") == (
        FFMPEG,
        "-y",
        "-i",
        str(tmp_path / "cleaned.wav"),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(tmp_path / "cleaned.mp3"),
    )


def test_atempo_filters_preserve_exact_boundary_values() -> None:
    assert _atempo_filters(2.0) == ["atempo=2.000"]
    assert _atempo_filters(2.5) == ["atempo=2.000", "atempo=1.250"]
    assert _atempo_filters(0.5) == ["atempo=0.500"]
    assert _atempo_filters(4.0) == ["atempo=2.000", "atempo=2.000"]
    assert _atempo_filters(0.25) == ["atempo=0.500", "atempo=0.500"]
    assert _atempo_filters(0.1) == ["atempo=0.500", "atempo=0.500", "atempo=0.500", "atempo=0.800"]
