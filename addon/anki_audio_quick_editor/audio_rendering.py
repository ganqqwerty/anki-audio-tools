"""Audio render orchestration and output path helpers."""

from __future__ import annotations

import os
import subprocess  # nosec B404
import tempfile
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from .audio_commands import (
    build_audio_filters,
    build_ffmpeg_command,
    build_playback_segment_filters,
    build_region_delete_command,
    build_region_delete_plan,
    build_region_keep_plan,
)
from .audio_external import _external_command_run_kwargs, probe_duration_ms
from .audio_pause_pipeline import _render_deep_filter_pause_speedup_audio
from .audio_state import AudioEditState, AudioProcessingConfig
from .audio_tools import find_ffmpeg
from .audio_types import AudioProcessingResult
from .errors import AudioProcessingError


def render_audio(
    source_path: Path,
    state: AudioEditState,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
    artifact_root: Path | None = None,
) -> AudioProcessingResult:
    """Render ``state`` from ``source_path`` to an MP3 file."""
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    duration_ms = probe_duration_ms(source_path, config)
    state.validate(duration_ms, config)

    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_preview_", suffix=".mp3")[1])

    if state.remove_internal_pauses_enabled:
        return _render_deep_filter_pause_speedup_audio(
            source_path,
            state,
            config,
            ffmpeg_path,
            output_path,
            on_command,
            artifact_root=artifact_root,
            source_duration_ms=duration_ms,
        )

    filters = build_audio_filters(duration_ms, state)
    cmd = build_ffmpeg_command(ffmpeg_path, source_path, filters, output_path)
    if on_command:
        on_command(cmd)
    result = subprocess.run(
        list(cmd),
        capture_output=True,
        text=True,
        check=False,
        **_external_command_run_kwargs(),
    )  # nosec B603
    if result.returncode != 0:
        raise AudioProcessingError(result.stderr.strip() or "Audio processing failed.")
    return AudioProcessingResult(
        output_path=output_path,
        command=cmd,
        duration_ms=probe_duration_ms(output_path, config),
    )


def render_audio_region_deleted(
    source_path: Path,
    selection_start_ms: int,
    selection_end_ms: int,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render an MP3 with one selected region removed from ``source_path``."""
    duration_ms = probe_duration_ms(source_path, config)
    plan = build_region_delete_plan(selection_start_ms, selection_end_ms, duration_ms)

    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_region_delete_", suffix=".mp3")[1])

    return _render_region_filter_complex(source_path, plan.filter_complex, config, output_path, on_command)


def _render_region_filter_complex(
    source_path: Path,
    filter_complex: str,
    config: AudioProcessingConfig,
    output_path: Path,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    cmd = build_region_delete_command(ffmpeg_path, source_path, filter_complex, output_path)
    if on_command:
        on_command(cmd)
    result = subprocess.run(
        list(cmd),
        capture_output=True,
        text=True,
        check=False,
        **_external_command_run_kwargs(),
    )  # nosec B603
    if result.returncode != 0:
        raise AudioProcessingError(result.stderr.strip() or "Audio processing failed.")
    return AudioProcessingResult(
        output_path=output_path,
        command=cmd,
        duration_ms=probe_duration_ms(output_path, config),
    )


def render_audio_region_kept(
    source_path: Path,
    selection_start_ms: int,
    selection_end_ms: int,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render an MP3 with only one selected region kept from ``source_path``."""
    duration_ms = probe_duration_ms(source_path, config)
    plan = build_region_keep_plan(selection_start_ms, selection_end_ms, duration_ms)

    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_region_keep_", suffix=".mp3")[1])

    return _render_region_filter_complex(source_path, plan.filter_complex, config, output_path, on_command)


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
    result = subprocess.run(
        list(cmd),
        capture_output=True,
        text=True,
        check=False,
        **_external_command_run_kwargs(),
    )  # nosec B603
    if result.returncode != 0:
        raise AudioProcessingError(result.stderr.strip() or "Playback segment rendering failed.")
    return AudioProcessingResult(
        output_path=output_path,
        command=cmd,
        duration_ms=probe_duration_ms(output_path, config),
    )


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
    max_stem_length = max(1, 120 - len(suffix))  # pragma: no mutate
    return f"{safe_stem[:max_stem_length]}{suffix}"


def _safe_filename_stem(stem: str) -> str:
    safe = "".join(ch if ch.isascii() and (ch.isalnum() or ch in {"-", "_"}) else "_" for ch in stem)  # pragma: no mutate
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
    token = token or uuid.uuid4().hex[:8]  # pragma: no mutate
    stem = _safe_filename_stem(Path(source_filename).stem or "audio")  # pragma: no mutate
    suffix = f"__from_{max(0, int(start_ms))}ms_{token}.mp3"
    prefix = "aqe_playback_"
    max_stem_length = max(1, 160 - len(prefix) - len(suffix))  # pragma: no mutate
    return f"{prefix}{stem[:max_stem_length]}{suffix}"


def temp_playback_path(source_filename: str, start_ms: int) -> Path:
    """Return a temp path for a cursor-to-end playback segment."""
    temp_dir = Path(tempfile.mkdtemp(prefix="aqe_playback_"))  # pragma: no mutate
    return temp_dir / make_playback_segment_filename(source_filename, start_ms)
