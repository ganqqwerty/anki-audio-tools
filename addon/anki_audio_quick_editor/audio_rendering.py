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
    build_convert_audio_command,
    build_ffmpeg_command,
    build_playback_segment_filters,
    build_region_delete_command,
    build_region_delete_plan,
    build_region_keep_plan,
)
from .audio_external import (
    _external_command_run_kwargs,
    _render_external_error_message,
    probe_duration_ms,
)
from .audio_formats import (
    DEFAULT_OUTPUT_FORMAT,
    normalize_output_format,
    output_extension,
    validate_target_format,
    visible_extension,
)
from .audio_output_policy import (
    PRESERVABLE_SOURCE_FORMATS,
    AudioOutputPolicy,
    codec_args_for_output_policy,
    resolve_output_policy,
    resolve_output_policy_from_metadata,
    synthetic_audio_metadata,
)
from .audio_pause_pipeline import _render_pause_removal_pipeline_audio
from .audio_state import AudioEditState, AudioProcessingConfig
from .audio_tools import find_ffmpeg
from .audio_types import AudioProcessingResult
from .errors import AudioProcessingError
from .permission_guidance import launch_error_message


def render_audio(
    source_path: Path,
    state: AudioEditState,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
    artifact_root: Path | None = None,
) -> AudioProcessingResult:
    """Render ``state`` from ``source_path`` to a final audio file."""
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    duration_ms = probe_duration_ms(source_path, config)
    state.validate(duration_ms, config)


    if state.remove_internal_pauses_enabled:
        output_policy = _resolve_filename_output_policy(source_path, config, output_path)
        if output_path is None:
            output_path = Path(tempfile.mkstemp(prefix="aqe_preview_", suffix=output_policy.extension)[1])
        return _render_pause_removal_pipeline_audio(
            source_path,
            state,
            config,
            ffmpeg_path,
            output_path,
            on_command,
            artifact_root=artifact_root,
            source_duration_ms=duration_ms,
            codec_args=codec_args_for_output_policy(output_policy),
            output_mime_type=output_policy.mime_type,
        )

    output_policy = resolve_output_policy(source_path, config, output_path=output_path)
    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_preview_", suffix=output_policy.extension)[1])

    filters = build_audio_filters(duration_ms, state)
    cmd = build_ffmpeg_command(
        ffmpeg_path,
        source_path,
        filters,
        output_path,
        codec_args_for_output_policy(output_policy),
    )
    if on_command:
        on_command(cmd)
    result = _run_render_command(cmd, "Could not start audio processing.")
    if result.returncode != 0:
        raise AudioProcessingError(
            _render_external_error_message(result, "Audio processing failed.")
        )
    return AudioProcessingResult(
        output_path=output_path,
        command=cmd,
        duration_ms=probe_duration_ms(output_path, config),
    )


def render_converted_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    target_format: object,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Convert ``source_path`` to a supported output format without edit filters."""
    target = validate_target_format(target_format)
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    output_policy = resolve_output_policy(
        source_path,
        config,
        requested_format=target,
        output_path=output_path,
    )
    if output_path is None:
        output_path = Path(
            tempfile.mkstemp(prefix="aqe_convert_", suffix=output_policy.extension)[1]
        )

    cmd = build_convert_audio_command(
        ffmpeg_path,
        source_path,
        output_path,
        target,
        codec_args_for_output_policy(output_policy),
    )
    if on_command:
        on_command(cmd)
    result = _run_render_command(cmd, "Could not start audio conversion.")
    if result.returncode != 0:
        raise AudioProcessingError(
            _render_external_error_message(result, "Audio conversion failed.")
        )
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
    """Render final audio with one selected region removed from ``source_path``."""
    duration_ms = probe_duration_ms(source_path, config)
    plan = build_region_delete_plan(selection_start_ms, selection_end_ms, duration_ms)
    output_policy = resolve_output_policy(source_path, config, output_path=output_path)

    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_region_delete_", suffix=output_policy.extension)[1])

    return _render_region_filter_complex(
        source_path,
        plan.filter_complex,
        config,
        output_path,
        codec_args_for_output_policy(output_policy),
        on_command,
    )


def _render_region_filter_complex(
    source_path: Path,
    filter_complex: str,
    config: AudioProcessingConfig,
    output_path: Path,
    codec_args: tuple[str, ...],
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    cmd = build_region_delete_command(ffmpeg_path, source_path, filter_complex, output_path, codec_args)
    if on_command:
        on_command(cmd)
    result = _run_render_command(cmd, "Could not start selected-region rendering.")
    if result.returncode != 0:
        raise AudioProcessingError(
            _render_external_error_message(result, "Audio processing failed.")
        )
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
    """Render final audio with only one selected region kept from ``source_path``."""
    duration_ms = probe_duration_ms(source_path, config)
    plan = build_region_keep_plan(selection_start_ms, selection_end_ms, duration_ms)
    output_policy = resolve_output_policy(source_path, config, output_path=output_path)

    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_region_keep_", suffix=output_policy.extension)[1])

    return _render_region_filter_complex(
        source_path,
        plan.filter_complex,
        config,
        output_path,
        codec_args_for_output_policy(output_policy),
        on_command,
    )


def render_playback_segment(
    source_path: Path,
    start_ms: int,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
    end_ms: int | None = None,
) -> AudioProcessingResult:
    """Render a temporary segment for deterministic native playback."""
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    duration_ms = probe_duration_ms(source_path, config)
    clamped_start_ms = max(0, min(int(start_ms), duration_ms))
    clamped_end_ms = duration_ms if end_ms is None else max(0, min(int(end_ms), duration_ms))
    if clamped_start_ms >= max(0, clamped_end_ms - 20):
        raise AudioProcessingError("Cursor is at the end of the audio.")

    if output_path is None:
        output_path = temp_playback_path(source_path.name, clamped_start_ms)

    filters = build_playback_segment_filters(clamped_start_ms, None if end_ms is None else clamped_end_ms)
    cmd = build_ffmpeg_command(ffmpeg_path, source_path, filters, output_path)
    if on_command:
        on_command(cmd)
    result = _run_render_command(cmd, "Could not start playback segment rendering.")
    if result.returncode != 0:
        raise AudioProcessingError(
            _render_external_error_message(result, "Playback segment rendering failed.")
        )
    return AudioProcessingResult(
        output_path=output_path,
        command=cmd,
        duration_ms=probe_duration_ms(output_path, config),
    )


def make_output_filename(
    source_filename: str,
    now: datetime | None = None,
    token: str | None = None,
    *,
    output_format: object = DEFAULT_OUTPUT_FORMAT,
) -> str:
    """Return the preferred generated filename for a final save."""
    now = now or datetime.now()
    token = token or uuid.uuid4().hex[:8]
    stem = Path(source_filename).stem or "audio"
    safe_stem = _safe_filename_stem(stem)
    suffix = f"__aqe_{now:%Y%m%d_%H%M%S_%f}_{token}{_output_extension_for_filename(source_filename, output_format)}"
    max_stem_length = max(1, 120 - len(suffix))  # pragma: no mutate
    return f"{safe_stem[:max_stem_length]}{suffix}"


def _run_render_command(command: tuple[str, ...], launch_error: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
            **_external_command_run_kwargs(),
        )  # nosec B603
    except OSError as exc:
        raise AudioProcessingError(launch_error_message(launch_error, exc)) from exc


def _safe_filename_stem(stem: str) -> str:
    safe = "".join(ch if ch.isascii() and (ch.isalnum() or ch in {"-", "_"}) else "_" for ch in stem)  # pragma: no mutate
    safe = "_".join(part for part in safe.split("_") if part)
    return safe or "audio"


def _output_extension_for_filename(source_filename: str, output_format: object) -> str:
    if normalize_output_format(output_format) == DEFAULT_OUTPUT_FORMAT:
        source_extension = visible_extension(source_filename)
        if source_extension in PRESERVABLE_SOURCE_FORMATS:
            return f".{source_extension}"
        return ".mp3"
    return output_extension(output_format)


def _resolve_filename_output_policy(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None,
) -> AudioOutputPolicy:
    return resolve_output_policy_from_metadata(
        synthetic_audio_metadata(
            source_path,
            output_path=output_path or source_path,
            codec_name=None,
            sample_rate=None,
            channels=None,
        ),
        requested_format=config.output_format,
        output_path=output_path,
    )


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
