"""ffmpeg helpers for combined selected-card audio export."""

from __future__ import annotations

from pathlib import Path

from .audio_commands import conversion_codec_args
from .ffmpeg_output_contracts import validate_final_ffmpeg_output

EXPORT_SAMPLE_RATE_HZ = 44100
EXPORT_CHANNELS = 2


def build_normalize_wav_command(
    *,
    ffmpeg_path: Path,
    source_path: Path,
    output_path: Path,
) -> tuple[str, ...]:
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ar",
        str(EXPORT_SAMPLE_RATE_HZ),
        "-ac",
        str(EXPORT_CHANNELS),
        "-c:a",
        "pcm_s16le",
        str(output_path),
    )


def build_silence_wav_command(
    *,
    ffmpeg_path: Path,
    duration_seconds: float,
    output_path: Path,
) -> tuple[str, ...]:
    return (
        str(ffmpeg_path),
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r={EXPORT_SAMPLE_RATE_HZ}:cl=stereo",
        "-t",
        f"{duration_seconds:.3f}",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    )


def build_concat_list_text(paths: list[Path] | tuple[Path, ...]) -> str:
    return "".join(f"file '{_concat_escape(path)}'\n" for path in paths)


def build_final_mp3_command(
    *,
    ffmpeg_path: Path,
    concat_list_path: Path,
    output_path: Path,
) -> tuple[str, ...]:
    codec_args = conversion_codec_args("mp3")
    validate_final_ffmpeg_output(output_path, codec_args)
    return (
        str(ffmpeg_path),
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list_path),
        "-vn",
        *codec_args,
        str(output_path),
    )


def _concat_escape(path: Path) -> str:
    return str(path).replace("'", "'\\''")
