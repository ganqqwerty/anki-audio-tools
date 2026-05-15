"""ffmpeg-backed rendering for preview and final audio files."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tempfile
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .audio_state import AudioEditState, AudioProcessingConfig
from .errors import AudioProcessingError, MissingFfmpegError


@dataclass(frozen=True)
class AudioProcessingResult:
    """Rendered audio metadata."""

    output_path: Path
    command: tuple[str, ...]
    duration_ms: int | None = None


def find_ffmpeg(configured_path: str = "") -> Path:
    """Return an ffmpeg executable path, honoring an optional config override."""
    if configured_path:
        path = Path(configured_path).expanduser()
        if path.is_file():
            return path
    found = shutil.which("ffmpeg")
    if found:
        return Path(found)
    raise MissingFfmpegError(
        "Audio Quick Editor requires ffmpeg. Please install ffmpeg and make sure it is "
        "available in PATH, or configure its path in the add-on settings."
    )


def find_ffprobe(ffmpeg_path: Path) -> Path:
    """Return ffprobe next to ffmpeg or from PATH."""
    sibling = ffmpeg_path.with_name("ffprobe" + ffmpeg_path.suffix)
    if sibling.is_file():
        return sibling
    found = shutil.which("ffprobe")
    if found:
        return Path(found)
    raise MissingFfmpegError(
        "Audio Quick Editor requires ffprobe alongside ffmpeg to inspect audio duration."
    )


def probe_duration_ms(source_path: Path, config: AudioProcessingConfig) -> int:
    """Inspect an audio file duration with ffprobe."""
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    ffprobe_path = find_ffprobe(ffmpeg_path)
    cmd = [
        str(ffprobe_path),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(source_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # nosec B603
    if result.returncode != 0:
        raise AudioProcessingError(result.stderr.strip() or "Could not inspect audio duration.")
    try:
        seconds = float(json.loads(result.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise AudioProcessingError("Could not parse audio duration.") from exc
    return max(0, round(seconds * 1000))


def render_audio(
    source_path: Path,
    state: AudioEditState,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render ``state`` from ``source_path`` to an MP3 file."""
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    duration_ms = probe_duration_ms(source_path, config)
    state.validate(duration_ms, config)

    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_preview_", suffix=".mp3")[1])

    filters = build_audio_filters(duration_ms, state, config)
    cmd = build_ffmpeg_command(ffmpeg_path, source_path, filters, output_path)
    if on_command:
        on_command(cmd)
    result = subprocess.run(list(cmd), capture_output=True, text=True, check=False)  # nosec B603
    if result.returncode != 0:
        raise AudioProcessingError(result.stderr.strip() or "Audio processing failed.")
    return AudioProcessingResult(
        output_path=output_path,
        command=cmd,
        duration_ms=probe_duration_ms(output_path, config),
    )


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
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(output_path),
    )


def render_playback_segment(
    source_path: Path,
    start_ms: int,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render a temporary cursor-to-end segment for deterministic playback."""
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    duration_ms = probe_duration_ms(source_path, config)
    clamped_start_ms = max(0, min(int(start_ms), duration_ms))
    if clamped_start_ms >= max(0, duration_ms - 20):
        raise AudioProcessingError("Cursor is at the end of the audio.")

    if output_path is None:
        output_path = temp_playback_path(source_path.name, clamped_start_ms)

    filters = build_playback_segment_filters(clamped_start_ms)
    cmd = build_ffmpeg_command(ffmpeg_path, source_path, filters, output_path)
    if on_command:
        on_command(cmd)
    result = subprocess.run(list(cmd), capture_output=True, text=True, check=False)  # nosec B603
    if result.returncode != 0:
        raise AudioProcessingError(result.stderr.strip() or "Playback segment rendering failed.")
    return AudioProcessingResult(
        output_path=output_path,
        command=cmd,
        duration_ms=probe_duration_ms(output_path, config),
    )


def build_playback_segment_filters(start_ms: int) -> str:
    """Build filters for a temporary cursor-to-end playback segment."""
    start_s = max(0, int(start_ms)) / 1000
    return f"atrim=start={start_s:.3f},asetpts=PTS-STARTPTS"


def format_ffmpeg_command(command: tuple[str, ...]) -> str:
    """Return a shell-style ffmpeg command string for user-facing diagnostics."""
    return shlex.join(command)


def build_audio_filters(
    duration_ms: int,
    state: AudioEditState,
    config: AudioProcessingConfig,
) -> str:
    """Build the ffmpeg audio filter chain for an edit state."""
    filters: list[str] = []
    start_s = state.left_trim_ms / 1000
    end_s = (duration_ms - state.right_trim_ms) / 1000
    filters.append(f"atrim=start={start_s:.3f}:end={end_s:.3f}")
    filters.append("asetpts=PTS-STARTPTS")

    threshold = f"{config.edge_silence_threshold_db}dB"
    if state.edge_trim_enabled:
        edge_s = config.edge_silence_min_ms / 1000
        filters.append(
            "silenceremove="
            f"start_periods=1:start_duration={edge_s:.3f}:start_threshold={threshold}:"
            f"stop_periods=1:stop_duration={edge_s:.3f}:stop_threshold={threshold}"
        )

    if state.remove_internal_pauses_enabled:
        pause_s = config.internal_pause_threshold_ms / 1000
        gap_s = config.internal_pause_target_gap_ms / 1000
        filters.append(
            "silenceremove="
            f"stop_periods=-1:stop_duration={pause_s:.3f}:stop_threshold={threshold}:"
            f"stop_silence={gap_s:.3f}"
        )

    if state.speed != 1.0:
        filters.extend(_atempo_filters(state.speed))
    return ",".join(filters)


def make_output_filename(
    source_filename: str,
    now: datetime | None = None,
    token: str | None = None,
) -> str:
    """Return the preferred generated MP3 filename for a final save."""
    now = now or datetime.now()
    token = token or uuid.uuid4().hex[:8]
    stem = Path(source_filename).stem or "audio"
    safe_stem = _safe_filename_stem(stem)
    suffix = f"__aqe_{now:%Y%m%d_%H%M%S_%f}_{token}.mp3"
    max_stem_length = max(1, 120 - len(suffix))
    return f"{safe_stem[:max_stem_length]}{suffix}"


def _safe_filename_stem(stem: str) -> str:
    safe = "".join(ch if ch.isascii() and (ch.isalnum() or ch in {"-", "_"}) else "_" for ch in stem)
    safe = "_".join(part for part in safe.split("_") if part)
    return safe or "audio"


def temp_final_path(filename: str) -> Path:
    """Return a temp path preserving a final desired basename for diagnostics."""
    temp_dir = Path(tempfile.mkdtemp(prefix="aqe_final_"))
    return temp_dir / os.path.basename(filename)


def make_playback_segment_filename(
    source_filename: str,
    start_ms: int,
    token: str | None = None,
) -> str:
    """Return a debuggable temp filename for cursor playback segments."""
    token = token or uuid.uuid4().hex[:8]
    stem = _safe_filename_stem(Path(source_filename).stem or "audio")
    suffix = f"__from_{max(0, int(start_ms))}ms_{token}.mp3"
    prefix = "aqe_playback_"
    max_stem_length = max(1, 160 - len(prefix) - len(suffix))
    return f"{prefix}{stem[:max_stem_length]}{suffix}"


def temp_playback_path(source_filename: str, start_ms: int) -> Path:
    """Return a temp path for a cursor-to-end playback segment."""
    temp_dir = Path(tempfile.mkdtemp(prefix="aqe_playback_"))
    return temp_dir / make_playback_segment_filename(source_filename, start_ms)


def _atempo_filters(speed: float) -> list[str]:
    remaining = speed
    filters: list[str] = []
    while remaining > 2.0:
        filters.append("atempo=2.000")
        remaining /= 2.0
    while remaining < 0.5:
        filters.append("atempo=0.500")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.3f}")
    return filters
