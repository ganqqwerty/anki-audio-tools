"""Backward-compatible facade for audio processing APIs."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from . import audio_external as _audio_external
from . import audio_noise_reduction as _audio_noise_reduction
from . import audio_pause_pipeline as _audio_pause_pipeline
from . import audio_rendering as _audio_rendering
from . import audio_tools as _audio_tools
from .audio_artifacts import (
    _artifact_record,
    _build_pause_pipeline_manifest,
    _create_pause_pipeline_run_dir,
    _pause_pipeline_config_snapshot,
    _sha256_file,
    _source_file_record,
)
from .audio_commands import (
    FFMPEG_AUDIO_CODEC_ARG,
    WAV_MIME_TYPE,
    _atempo_filters,
    build_audio_filters,
    build_deep_filter_command,
    build_deep_filter_prepare_command,
    build_ffmpeg_command,
    build_filter_complex_render_command,
    build_mp3_encode_command,
    build_playback_segment_filters,
    build_region_delete_command,
    build_region_delete_plan,
    build_rnnoise_command,
    build_rnnoise_encode_command,
    build_rnnoise_prepare_command,
    build_silencedetect_command,
    build_wav_filter_command,
    build_working_original_filters,
    format_ffmpeg_command,
)
from .audio_noise_reduction import (
    _record_rnnoise_failure,
    _run_audio_stage,
    _run_recorded_external_command,
    select_deep_filter_output,
)
from .audio_pause_pipeline import _run_pipeline_stage
from .audio_rendering import _safe_filename_stem
from .audio_state import AudioEditState, AudioProcessingConfig
from .audio_types import AudioProcessingResult, RegionDeletePlan

__all__ = [
    "BUNDLED_DEEP_FILTER_VERSION",
    "BUNDLED_RNNOISE_VERSION",
    "FFMPEG_AUDIO_CODEC_ARG",
    "WAV_MIME_TYPE",
    "AudioProcessingResult",
    "RegionDeletePlan",
    "_BUNDLED_DEEP_FILTER_VERSION",
    "_PACKAGE_DIR",
    "_artifact_record",
    "_atempo_filters",
    "_build_pause_pipeline_manifest",
    "_bundled_deep_filter_path",
    "_create_pause_pipeline_run_dir",
    "_pause_pipeline_config_snapshot",
    "_record_rnnoise_failure",
    "_render_deep_filter_pause_speedup_audio",
    "_render_external_error_message",
    "_run_audio_stage",
    "_run_external_command",
    "_run_pipeline_stage",
    "_run_recorded_external_command",
    "_safe_filename_stem",
    "_sha256_file",
    "_source_file_record",
    "build_audio_filters",
    "build_deep_filter_command",
    "build_deep_filter_prepare_command",
    "build_ffmpeg_command",
    "build_filter_complex_render_command",
    "build_mp3_encode_command",
    "build_playback_segment_filters",
    "build_region_delete_command",
    "build_region_delete_plan",
    "build_rnnoise_command",
    "build_rnnoise_encode_command",
    "build_rnnoise_prepare_command",
    "build_silencedetect_command",
    "build_wav_filter_command",
    "build_working_original_filters",
    "bundled_tool_path",
    "current_platform_key",
    "expected_bundled_rnnoise_dir",
    "expected_bundled_tool_path",
    "find_deep_filter",
    "find_ffmpeg",
    "find_ffprobe",
    "find_rnnoise_bundle",
    "format_ffmpeg_command",
    "make_output_filename",
    "make_playback_segment_filename",
    "probe_duration_ms",
    "render_audio",
    "render_audio_region_deleted",
    "render_noise_reduced_audio",
    "render_playback_segment",
    "render_rnnoise_audio",
    "select_deep_filter_output",
    "temp_final_path",
    "temp_playback_path",
    "tool_source_label",
]

_BUNDLED_DEEP_FILTER_VERSION = _audio_tools.BUNDLED_DEEP_FILTER_VERSION
BUNDLED_DEEP_FILTER_VERSION = _audio_tools.BUNDLED_DEEP_FILTER_VERSION
BUNDLED_RNNOISE_VERSION = _audio_tools.BUNDLED_RNNOISE_VERSION
_PACKAGE_DIR = _audio_tools.PACKAGE_DIR
_ORIGINAL_BUNDLED_DEEP_FILTER_PATH = _audio_tools._bundled_deep_filter_path
_ORIGINAL_EXPECTED_BUNDLED_RNNOISE_DIR = _audio_tools.expected_bundled_rnnoise_dir
_ORIGINAL_EXPECTED_BUNDLED_TOOL_PATH = _audio_tools.expected_bundled_tool_path
_ORIGINAL_MAKE_PLAYBACK_SEGMENT_FILENAME = _audio_rendering.make_playback_segment_filename


def _bundled_deep_filter_path() -> Path | None:
    return _ORIGINAL_BUNDLED_DEEP_FILTER_PATH()


def _sync_tool_dependencies() -> None:
    audio_tools = cast(Any, _audio_tools)
    audio_tools.Path = Path
    audio_tools.shutil = shutil
    audio_tools._bundled_deep_filter_path = _bundled_deep_filter_path


def current_platform_key() -> str | None:
    return _audio_tools.current_platform_key()


def bundled_tool_path(tool_name: str) -> Path | None:
    return _audio_tools.bundled_tool_path(tool_name)


def expected_bundled_tool_path(tool_name: str) -> Path | None:
    return _ORIGINAL_EXPECTED_BUNDLED_TOOL_PATH(tool_name)


def tool_source_label(tool_path: Path, *, configured_path: str = "") -> str:
    return _audio_tools.tool_source_label(tool_path, configured_path=configured_path)


def find_ffmpeg(configured_path: str = "") -> Path:  # pragma: no mutate
    _sync_tool_dependencies()
    return _audio_tools.find_ffmpeg(configured_path)


def find_ffprobe(ffmpeg_path: Path) -> Path:
    _sync_tool_dependencies()
    return _audio_tools.find_ffprobe(ffmpeg_path)


def find_deep_filter(configured_path: str = "") -> Path:
    _sync_tool_dependencies()
    return _audio_tools.find_deep_filter(configured_path)


def expected_bundled_rnnoise_dir() -> Path | None:
    return _ORIGINAL_EXPECTED_BUNDLED_RNNOISE_DIR()


def find_rnnoise_bundle() -> Path:
    _sync_tool_dependencies()
    audio_tools = cast(Any, _audio_tools)
    original_dir = audio_tools.expected_bundled_rnnoise_dir
    original_path = audio_tools.expected_bundled_tool_path
    audio_tools.expected_bundled_rnnoise_dir = expected_bundled_rnnoise_dir
    audio_tools.expected_bundled_tool_path = expected_bundled_tool_path
    try:
        return _audio_tools.find_rnnoise_bundle()
    finally:
        audio_tools.expected_bundled_rnnoise_dir = original_dir
        audio_tools.expected_bundled_tool_path = original_path


def _sync_external_dependencies() -> None:
    audio_external = cast(Any, _audio_external)
    audio_external.subprocess = subprocess
    audio_external.find_ffmpeg = find_ffmpeg
    audio_external.find_ffprobe = find_ffprobe


def probe_duration_ms(source_path: Path, config: AudioProcessingConfig) -> int:
    _sync_external_dependencies()
    return _audio_external.probe_duration_ms(source_path, config)


def _run_external_command(
    command: tuple[str, ...],
    launch_error_message: str,
) -> subprocess.CompletedProcess[str]:
    _sync_external_dependencies()
    return _audio_external._run_external_command(command, launch_error_message)


def _render_external_error_message(
    result: subprocess.CompletedProcess[str],
    default_message: str,
) -> str:
    return _audio_external._render_external_error_message(result, default_message)


def _sync_pause_dependencies() -> None:
    audio_pause_pipeline = cast(Any, _audio_pause_pipeline)
    audio_pause_pipeline.find_deep_filter = find_deep_filter
    audio_pause_pipeline.probe_duration_ms = probe_duration_ms
    audio_pause_pipeline._run_external_command = _run_external_command
    audio_pause_pipeline._render_external_error_message = _render_external_error_message


def _render_deep_filter_pause_speedup_audio(
    source_path: Path,
    state: AudioEditState,
    config: AudioProcessingConfig,
    ffmpeg_path: Path,
    output_path: Path,
    on_command: Callable[[tuple[str, ...]], None] | None,
    *,
    artifact_root: Path | None,
    source_duration_ms: int,
) -> AudioProcessingResult:
    _sync_pause_dependencies()
    return _audio_pause_pipeline._render_deep_filter_pause_speedup_audio(
        source_path,
        state,
        config,
        ffmpeg_path,
        output_path,
        on_command,
        artifact_root=artifact_root,
        source_duration_ms=source_duration_ms,
    )


def _sync_rendering_dependencies() -> None:
    audio_rendering = cast(Any, _audio_rendering)
    audio_rendering.find_ffmpeg = find_ffmpeg
    audio_rendering.probe_duration_ms = probe_duration_ms
    audio_rendering.build_audio_filters = build_audio_filters
    audio_rendering._render_deep_filter_pause_speedup_audio = _render_deep_filter_pause_speedup_audio
    audio_rendering.subprocess = subprocess
    audio_rendering.tempfile = tempfile
    audio_rendering.uuid = uuid
    audio_rendering.make_playback_segment_filename = make_playback_segment_filename


def render_audio(
    source_path: Path,
    state: AudioEditState,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
    artifact_root: Path | None = None,
) -> AudioProcessingResult:
    _sync_rendering_dependencies()
    return _audio_rendering.render_audio(
        source_path,
        state,
        config,
        output_path,
        on_command,
        artifact_root,
    )


def render_audio_region_deleted(
    source_path: Path,
    selection_start_ms: int,
    selection_end_ms: int,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    _sync_rendering_dependencies()
    return _audio_rendering.render_audio_region_deleted(
        source_path,
        selection_start_ms,
        selection_end_ms,
        config,
        output_path,
        on_command,
    )


def render_playback_segment(
    source_path: Path,
    start_ms: int,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    _sync_rendering_dependencies()
    return _audio_rendering.render_playback_segment(
        source_path,
        start_ms,
        config,
        output_path,
        on_command,
    )


def make_output_filename(
    source_filename: str,
    now: datetime | None = None,
    token: str | None = None,
) -> str:
    _sync_rendering_dependencies()
    return _audio_rendering.make_output_filename(source_filename, now, token)


def temp_final_path(filename: str) -> Path:
    _sync_rendering_dependencies()
    return _audio_rendering.temp_final_path(filename)


def make_playback_segment_filename(
    source_filename: str,
    start_ms: int,
    token: str | None = None,
) -> str:
    cast(Any, _audio_rendering).uuid = uuid
    return _ORIGINAL_MAKE_PLAYBACK_SEGMENT_FILENAME(source_filename, start_ms, token)


def temp_playback_path(source_filename: str, start_ms: int) -> Path:
    _sync_rendering_dependencies()
    return _audio_rendering.temp_playback_path(source_filename, start_ms)


def _sync_noise_dependencies() -> None:
    audio_noise_reduction = cast(Any, _audio_noise_reduction)
    audio_noise_reduction.find_ffmpeg = find_ffmpeg
    audio_noise_reduction.find_deep_filter = find_deep_filter
    audio_noise_reduction.find_rnnoise_bundle = find_rnnoise_bundle
    audio_noise_reduction.probe_duration_ms = probe_duration_ms
    audio_noise_reduction._run_external_command = _run_external_command
    audio_noise_reduction._render_external_error_message = _render_external_error_message
    audio_noise_reduction.tempfile = tempfile
    audio_noise_reduction.shutil = shutil


def render_noise_reduced_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    _sync_noise_dependencies()
    return _audio_noise_reduction.render_noise_reduced_audio(
        source_path,
        config,
        output_path,
        on_command,
    )


def render_rnnoise_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    _sync_noise_dependencies()
    return _audio_noise_reduction.render_rnnoise_audio(
        source_path,
        config,
        output_path,
        on_command,
    )
