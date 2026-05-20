"""Command and ffmpeg filter builders for audio processing."""

from __future__ import annotations

import math
import shlex
from pathlib import Path

from .audio_state import AudioEditState
from .audio_types import RegionDeletePlan, RegionKeepPlan
from .errors import AudioProcessingError

FFMPEG_AUDIO_CODEC_ARG = "-codec:a"
WAV_MIME_TYPE = "audio/wav"

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


def build_deep_filter_prepare_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_wav_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command that prepares a 48 kHz mono WAV for DeepFilterNet."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "48000",
        FFMPEG_AUDIO_CODEC_ARG,
        "pcm_s16le",
        str(output_wav_path),
    )


def build_deep_filter_command(
    deep_filter_path: Path,
    input_wav_path: Path,
    output_dir: Path,
    *,
    post_filter: bool,
) -> tuple[str, ...]:
    """Build the DeepFilterNet command for one prepared WAV file."""
    command = [
        str(deep_filter_path),
        "-D",
    ]
    if post_filter:
        command.append("--pf")
    command.extend(("-o", str(output_dir), str(input_wav_path)))
    return tuple(command)


def build_silencedetect_command(
    ffmpeg_path: Path,
    source_path: Path,
    *,
    threshold_db: int,
    min_duration_ms: int,
) -> tuple[str, ...]:
    """Build an ffmpeg command that emits silencedetect metadata to stderr."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-af",
        f"silencedetect=noise={threshold_db}dB:d={max(1, int(min_duration_ms)) / 1000:.3f}",
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


def build_rnnoise_prepare_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_raw_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command that prepares 48 kHz mono raw PCM for RNNoise."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "48000",
        "-f",
        "s16le",
        FFMPEG_AUDIO_CODEC_ARG,
        "pcm_s16le",
        str(output_raw_path),
    )


def build_rnnoise_command(
    rnnoise_path: Path,
    input_raw_path: Path,
    output_raw_path: Path,
) -> tuple[str, ...]:
    """Build the RNNoise command for one prepared raw PCM file."""
    return (
        str(rnnoise_path),
        "denoise",
        "--input",
        str(input_raw_path),
        "--output",
        str(output_raw_path),
        "--overwrite",
        "--json",
    )


def build_dpdfnet_command(
    dpdfnet_path: Path,
    input_path: Path,
    output_wav_path: Path,
    *,
    attn_limit_db: float,
) -> tuple[str, ...]:
    """Build the DPDFNet command for one source audio file."""
    return (
        str(dpdfnet_path),
        "enhance",
        "--attn-limit-db",
        f"{attn_limit_db:g}",
        str(input_path),
        str(output_wav_path),
    )


def build_rnnoise_encode_command(
    ffmpeg_path: Path,
    source_raw_path: Path,
    output_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command that encodes RNNoise raw PCM output as MP3."""
    return (
        str(ffmpeg_path),
        "-y",
        "-f",
        "s16le",
        "-ar",
        "48000",
        "-ac",
        "1",
        "-i",
        str(source_raw_path),
        "-vn",
        FFMPEG_AUDIO_CODEC_ARG,
        "libmp3lame",
        "-q:a",
        "4",
        str(output_path),
    )


def build_spleeter_prepare_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_wav_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command that prepares 44.1 kHz stereo WAV for Spleeter."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-ac",
        "2",
        "-ar",
        "44100",
        FFMPEG_AUDIO_CODEC_ARG,
        "pcm_s16le",
        str(output_wav_path),
    )


def build_spleeter_command(
    spleeter_path: Path,
    vocals_model_path: Path,
    accompaniment_model_path: Path,
    input_wav_path: Path,
    output_dir: Path,
) -> tuple[str, ...]:
    """Build the Sherpa Spleeter command used for voice-only extraction."""
    return (
        str(spleeter_path),
        f"--spleeter-vocals={vocals_model_path}",
        f"--spleeter-accompaniment={accompaniment_model_path}",
        f"--input-wav={input_wav_path}",
        f"--output-vocals-wav={output_dir / 'vocals.wav'}",
        f"--output-accompaniment-wav={output_dir / 'accompaniment.wav'}",
        "--num-threads=1",
    )


def build_mp3_encode_command(
    ffmpeg_path: Path,
    source_path: Path,
    output_path: Path,
) -> tuple[str, ...]:
    """Build the ffmpeg command used to encode processed WAV output as MP3."""
    return (
        str(ffmpeg_path),
        "-y",
        "-i",
        str(source_path),
        "-vn",
        FFMPEG_AUDIO_CODEC_ARG,
        "libmp3lame",
        "-q:a",
        "4",
        str(output_path),
    )


def build_playback_segment_filters(start_ms: int, end_ms: int | None = None) -> str:
    """Build filters for a temporary native playback segment."""
    start_s = max(0, int(start_ms)) / 1000
    if end_ms is None:
        return f"atrim=start={start_s:.3f},asetpts=PTS-STARTPTS"
    end_s = max(start_s, int(end_ms) / 1000)
    return f"atrim=start={start_s:.3f}:end={end_s:.3f},asetpts=PTS-STARTPTS"


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
    """Build filters for original-derived audio before pause speed-up analysis."""
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
