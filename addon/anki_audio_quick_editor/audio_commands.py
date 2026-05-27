"""Command and ffmpeg filter builders for audio processing."""

from __future__ import annotations

import math
import shlex
from pathlib import Path

from . import audio_commands_runtime as _runtime
from .audio_formats import OutputFormat, validate_target_format
from .audio_state import AudioEditState
from .audio_types import RegionDeletePlan, RegionKeepPlan
from .errors import AudioProcessingError

FFMPEG_AUDIO_CODEC_ARG = "-codec:a"
WAV_MIME_TYPE = "audio/wav"

_CONVERT_CODEC_ARGS: dict[OutputFormat, tuple[str, ...]] = {
    "mp3": (FFMPEG_AUDIO_CODEC_ARG, "libmp3lame", "-q:a", "4"),
    "m4a": (FFMPEG_AUDIO_CODEC_ARG, "aac", "-b:a", "192k"),
    "wav": (FFMPEG_AUDIO_CODEC_ARG, "pcm_s16le"),
    "flac": (FFMPEG_AUDIO_CODEC_ARG, "flac", "-compression_level", "5"),
}


def conversion_codec_args(target_format: object) -> tuple[str, ...]:
    """Return ffmpeg codec arguments for a supported conversion target."""
    return _CONVERT_CODEC_ARGS[validate_target_format(target_format)]


def build_convert_audio_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_path: Path,
    target_format: object,
) -> tuple[str, ...]:
    """Build an ffmpeg command that converts audio without applying edit filters."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        *conversion_codec_args(target_format),
        str(output_path),
    )


def build_region_delete_plan(
    selection_start_ms: int,
    selection_end_ms: int,
    duration_ms: int,
) -> RegionDeletePlan:
    """Return a concat/trim plan for deleting one region from a clip."""
    duration = max(0, int(round(duration_ms)))
    start = max(0, min(int(round(selection_start_ms)), duration))
    end = max(0, min(int(round(selection_end_ms)), duration))
    if end <= start:
        raise AudioProcessingError("Select a region before deleting it.")
    if start <= 0 and end >= duration:
        raise AudioProcessingError("Cannot delete the whole audio clip.")

    start_s = start / 1000
    end_s = end / 1000
    duration_s = duration / 1000
    if start <= 0:
        filter_complex = f"[0:a]atrim=start={end_s:.3f},asetpts=PTS-STARTPTS[out]"
    elif end >= duration:
        filter_complex = f"[0:a]atrim=end={start_s:.3f},asetpts=PTS-STARTPTS[out]"
    else:
        filter_complex = (
            f"[0:a]atrim=start=0.000:end={start_s:.3f},asetpts=PTS-STARTPTS[a0];"
            f"[0:a]atrim=start={end_s:.3f}:end={duration_s:.3f},asetpts=PTS-STARTPTS[a1];"
            "[a0][a1]concat=n=2:v=0:a=1[out]"
        )
    return RegionDeletePlan(start, end, duration, filter_complex)


def build_region_keep_plan(
    selection_start_ms: int,
    selection_end_ms: int,
    duration_ms: int,
) -> RegionKeepPlan:
    """Return a trim plan for keeping one selected region from a clip."""
    duration = max(0, int(round(duration_ms)))
    start = max(0, min(int(round(selection_start_ms)), duration))
    end = max(0, min(int(round(selection_end_ms)), duration))
    if end <= start:
        raise AudioProcessingError("Select a region before deleting the rest.")
    if start <= 0 and end >= duration:
        raise AudioProcessingError("Selection already covers the whole audio clip.")

    start_s = start / 1000
    end_s = end / 1000
    filter_complex = f"[0:a]atrim=start={start_s:.3f}:end={end_s:.3f},asetpts=PTS-STARTPTS[out]"
    return RegionKeepPlan(start, end, duration, filter_complex)


def build_ffmpeg_command(
    ffmpeg_path: Path,
    source_path: Path,
    filters: str,
    output_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command used to render a processed MP3."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-filter:a",
        filters,
        FFMPEG_AUDIO_CODEC_ARG,
        "libmp3lame",
        "-q:a",
        "4",
        str(output_path),
    )


def build_wav_filter_command(
    ffmpeg_path: Path,
    source_path: Path,
    filters: str,
    output_path: Path,
) -> tuple[str, ...]:
    """Build an ffmpeg command that renders filtered PCM WAV output."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-filter:a",
        filters,
        FFMPEG_AUDIO_CODEC_ARG,
        "pcm_s16le",
        str(output_path),
    )


def build_silencedetect_command(
    ffmpeg_path: Path,
    source_path: Path,
    *,
    threshold_db: float,
    min_duration_ms: int,
) -> tuple[str, ...]:
    """Build an ffmpeg command that emits silencedetect metadata to stderr."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-af",
        f"silencedetect=noise={threshold_db:g}dB:d={max(1, int(min_duration_ms)) / 1000:.3f}",
        "-f",
        "null",
        "-",
    )


def build_filter_complex_render_command(
    ffmpeg_path: Path,
    source_path: Path,
    filter_script_path: Path,
    output_path: Path,
) -> tuple[str, ...]:
    """Build an ffmpeg command that renders from a filter_complex script."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-filter_complex_script",
        str(filter_script_path),
        "-map",
        "[out]",
        FFMPEG_AUDIO_CODEC_ARG,
        "libmp3lame",
        "-q:a",
        "4",
        str(output_path),
    )


def build_region_delete_command(
    ffmpeg_path: Path,
    source_path: Path,
    filter_complex: str,
    output_path: Path,
) -> tuple[str, ...]:
    """Build an ffmpeg command that removes one selected audio region."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        FFMPEG_AUDIO_CODEC_ARG,
        "libmp3lame",
        "-q:a",
        "4",
        str(output_path),
    )


def format_ffmpeg_command(command: tuple[str, ...]) -> str:
    """Return a shell-style ffmpeg command string for user-facing diagnostics."""
    return shlex.join(command)


def build_audio_filters(
    duration_ms: int,
    state: AudioEditState,
) -> str:
    """Build the ffmpeg audio filter chain for an edit state."""
    filters = build_working_original_filters(duration_ms, state).split(",")

    if not math.isclose(state.volume_db, 0.0):
        filters.append(f"volume={state.volume_db:.2f}dB")

    if not math.isclose(state.speed, 1.0):
        filters.extend(_atempo_filters(state.speed))
    return ",".join(filters)


def build_working_original_filters(
    duration_ms: int,
    state: AudioEditState,
) -> str:
    """Build filters for original-derived audio before pause detection and rendering."""
    filters: list[str] = []
    start_s = state.left_trim_ms / 1000
    end_s = (duration_ms - state.right_trim_ms) / 1000
    filters.append(f"atrim=start={start_s:.3f}:end={end_s:.3f}")
    filters.append("asetpts=PTS-STARTPTS")

    return ",".join(filters)


def _atempo_filters(speed: float) -> list[str]:
    remaining = speed
    filters: list[str] = []
    while remaining > 2.0:
        filters.append("atempo=2.000")
        remaining /= 2.0  # pragma: no mutate
    while remaining < 0.5:
        filters.append("atempo=0.500")
        remaining /= 0.5  # pragma: no mutate
    filters.append(f"atempo={remaining:.3f}")
    return filters


build_deep_filter_prepare_command = _runtime.build_deep_filter_prepare_command
build_deep_filter_command = _runtime.build_deep_filter_command
build_silero_vad_prepare_command = _runtime.build_silero_vad_prepare_command
build_silero_vad_command = _runtime.build_silero_vad_command
build_rnnoise_prepare_command = _runtime.build_rnnoise_prepare_command
build_rnnoise_command = _runtime.build_rnnoise_command
build_dpdfnet_command = _runtime.build_dpdfnet_command
build_rnnoise_encode_command = _runtime.build_rnnoise_encode_command
build_spleeter_prepare_command = _runtime.build_spleeter_prepare_command
build_spleeter_command = _runtime.build_spleeter_command
build_mp3_encode_command = _runtime.build_mp3_encode_command
build_playback_segment_filters = _runtime.build_playback_segment_filters
