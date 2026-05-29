"""Backward-compatible facade for audio processing APIs."""
from __future__ import annotations

import shutil
import subprocess  # nosec B404
import tempfile
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from . import audio_commands as _audio_commands
from . import audio_external as _audio_external
from . import audio_noise_reduction as _audio_noise_reduction
from . import audio_output_policy as _audio_output_policy
from . import audio_pause_pipeline as _audio_pause_pipeline
from . import audio_pause_pipeline_stage as _audio_pause_pipeline_stage
from . import audio_pause_pipeline_steps as _audio_pause_pipeline_steps
from . import audio_pitch_hum as _audio_pitch_hum
from . import audio_processor_rendering_portal as _render_portal
from . import audio_rendering as _audio_rendering
from . import audio_tools as _audio_tools
from .audio_processor_runtime import (
    sync_external_dependencies,
    sync_noise_dependencies,
    sync_pause_dependencies,
    sync_pitch_hum_dependencies,
    sync_rendering_dependencies,
    sync_tool_dependencies,
)
from .audio_state import AudioEditState, AudioProcessingConfig
from .audio_types import AudioProcessingResult

_BUNDLED_DEEP_FILTER_VERSION = _audio_tools.BUNDLED_DEEP_FILTER_VERSION
BUNDLED_DEEP_FILTER_VERSION = _audio_tools.BUNDLED_DEEP_FILTER_VERSION
BUNDLED_DPDFNET_VERSION = _audio_tools.BUNDLED_DPDFNET_VERSION
BUNDLED_RNNOISE_VERSION = _audio_tools.BUNDLED_RNNOISE_VERSION
_PACKAGE_DIR = _audio_tools.PACKAGE_DIR
_ORIGINAL_BUNDLED_DEEP_FILTER_PATH = _audio_tools._bundled_deep_filter_path
_ORIGINAL_EXPECTED_BUNDLED_RNNOISE_DIR = _audio_tools.expected_bundled_rnnoise_dir
_ORIGINAL_EXPECTED_BUNDLED_SILERO_VAD_MODEL_PATH = _audio_tools.expected_bundled_silero_vad_model_path
_ORIGINAL_EXPECTED_BUNDLED_SPLEETER_MODEL_PATH = _audio_tools.expected_bundled_spleeter_model_path
_ORIGINAL_EXPECTED_BUNDLED_TOOL_PATH = _audio_tools.expected_bundled_tool_path
_ORIGINAL_MAKE_PLAYBACK_SEGMENT_FILENAME = _audio_rendering.make_playback_segment_filename
_safe_filename_stem = _audio_rendering._safe_filename_stem
build_audio_filters = _audio_commands.build_audio_filters
build_convert_audio_command = _audio_commands.build_convert_audio_command
build_region_delete_plan = _audio_commands.build_region_delete_plan
build_region_keep_plan = _audio_commands.build_region_keep_plan
build_silencedetect_command = _audio_commands.build_silencedetect_command
build_working_original_filters = _audio_commands.build_working_original_filters
format_ffmpeg_command = _audio_commands.format_ffmpeg_command
probe_audio_metadata = _audio_output_policy.probe_audio_metadata
resolve_output_policy = _audio_output_policy.resolve_output_policy
make_output_filename = _render_portal.make_output_filename
make_playback_segment_filename = _render_portal.make_playback_segment_filename
render_audio = _render_portal.render_audio
render_audio_region_deleted = _render_portal.render_audio_region_deleted
render_audio_region_kept = _render_portal.render_audio_region_kept
render_converted_audio = _render_portal.render_converted_audio
render_dpdfnet_audio = _render_portal.render_dpdfnet_audio
render_noise_reduced_audio = _render_portal.render_noise_reduced_audio
render_pitch_hum_audio = _render_portal.render_pitch_hum_audio
render_pitch_tier_hum_audio = _render_portal.render_pitch_tier_hum_audio
render_playback_segment = _render_portal.render_playback_segment
render_rnnoise_audio = _render_portal.render_rnnoise_audio
render_voice_only_audio = _render_portal.render_voice_only_audio
select_deep_filter_output = _audio_noise_reduction.select_deep_filter_output
temp_final_path = _render_portal.temp_final_path
temp_playback_path = _render_portal.temp_playback_path


def _bundled_deep_filter_path() -> Path | None:
    return _ORIGINAL_BUNDLED_DEEP_FILTER_PATH()


def _sync_tool_dependencies() -> None:
    sync_tool_dependencies(
        cast(Any, _audio_tools),
        shutil_module=shutil,
        bundled_deep_filter_path=_bundled_deep_filter_path,
    )


def current_platform_key() -> str | None:
    return _audio_tools.current_platform_key()


def bundled_tool_path(tool_name: str) -> Path | None:
    return _audio_tools.bundled_tool_path(tool_name)


def expected_bundled_tool_path(tool_name: str) -> Path | None:
    return _ORIGINAL_EXPECTED_BUNDLED_TOOL_PATH(tool_name)


def expected_bundled_spleeter_model_path(model_name: str) -> Path | None:
    return _ORIGINAL_EXPECTED_BUNDLED_SPLEETER_MODEL_PATH(model_name)


def expected_bundled_silero_vad_model_path() -> Path | None:
    return _ORIGINAL_EXPECTED_BUNDLED_SILERO_VAD_MODEL_PATH()


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


def find_dpdfnet_bundle() -> Path:
    _sync_tool_dependencies()
    return _audio_tools.find_dpdfnet_bundle()


def find_spleeter_bundle() -> tuple[Path, Path, Path]:
    _sync_tool_dependencies()
    audio_tools = cast(Any, _audio_tools)
    original_tool_path = audio_tools.expected_bundled_tool_path
    original_model_path = audio_tools.expected_bundled_spleeter_model_path
    audio_tools.expected_bundled_tool_path = expected_bundled_tool_path
    audio_tools.expected_bundled_spleeter_model_path = expected_bundled_spleeter_model_path
    try:
        return _audio_tools.find_spleeter_bundle()
    finally:
        audio_tools.expected_bundled_tool_path = original_tool_path
        audio_tools.expected_bundled_spleeter_model_path = original_model_path


def find_silero_vad_bundle() -> tuple[Path, Path]:
    _sync_tool_dependencies()
    audio_tools = cast(Any, _audio_tools)
    original_tool_path = audio_tools.expected_bundled_tool_path
    original_model_path = audio_tools.expected_bundled_silero_vad_model_path
    audio_tools.expected_bundled_tool_path = expected_bundled_tool_path
    audio_tools.expected_bundled_silero_vad_model_path = expected_bundled_silero_vad_model_path
    try:
        return _audio_tools.find_silero_vad_bundle()
    finally:
        audio_tools.expected_bundled_tool_path = original_tool_path
        audio_tools.expected_bundled_silero_vad_model_path = original_model_path


def _sync_external_dependencies() -> None:
    sync_external_dependencies(
        cast(Any, _audio_external),
        subprocess_module=subprocess,
        find_ffmpeg=find_ffmpeg,
        find_ffprobe=find_ffprobe,
    )


def probe_duration_ms(source_path: Path, config: AudioProcessingConfig) -> int:
    _sync_external_dependencies()
    return _audio_external.probe_duration_ms(source_path, config)


def _run_external_command(
    command: tuple[str, ...],
    launch_error_message: str,
    timeout_seconds: float | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    _sync_external_dependencies()
    return _audio_external._run_external_command(command, launch_error_message, timeout_seconds, env)


def _external_command_run_kwargs() -> dict[str, Any]:
    _sync_external_dependencies()
    return _audio_external._external_command_run_kwargs()


def _render_external_error_message(
    result: subprocess.CompletedProcess[str],
    default_message: str,
) -> str:
    return _audio_external._render_external_error_message(result, default_message)


def _sync_pause_dependencies() -> None:
    sync_pause_dependencies(
        cast(Any, _audio_pause_pipeline),
        cast(Any, _audio_pause_pipeline_steps),
        cast(Any, _audio_pause_pipeline_stage),
        find_dpdfnet_bundle=find_dpdfnet_bundle,
        find_silero_vad_bundle=find_silero_vad_bundle,
        probe_duration_ms=probe_duration_ms,
        run_external_command=_run_external_command,
        render_external_error_message=_render_external_error_message,
    )


def _render_pause_removal_pipeline_audio(
    source_path: Path,
    state: AudioEditState,
    config: AudioProcessingConfig,
    ffmpeg_path: Path,
    output_path: Path,
    on_command: Callable[[tuple[str, ...]], None] | None,
    *,
    artifact_root: Path | None,
    source_duration_ms: int,
    codec_args: tuple[str, ...],
    output_mime_type: str,
) -> AudioProcessingResult:
    _sync_pause_dependencies()
    return _audio_pause_pipeline._render_pause_removal_pipeline_audio(
        source_path,
        state,
        config,
        ffmpeg_path,
        output_path,
        on_command,
        artifact_root=artifact_root,
        source_duration_ms=source_duration_ms,
        codec_args=codec_args,
        output_mime_type=output_mime_type,
    )
def _sync_rendering_dependencies() -> None:
    sync_rendering_dependencies(
        cast(Any, _audio_rendering),
        build_audio_filters=build_audio_filters,
        build_convert_audio_command=build_convert_audio_command,
        external_command_run_kwargs=_external_command_run_kwargs,
        find_ffmpeg=find_ffmpeg,
        make_playback_segment_filename=make_playback_segment_filename,
        probe_duration_ms=probe_duration_ms,
        resolve_output_policy=resolve_output_policy,
        render_pause_removal_pipeline_audio=_render_pause_removal_pipeline_audio,
        subprocess_module=subprocess,
        tempfile_module=tempfile,
        uuid_module=uuid,
    )


def _sync_noise_dependencies() -> None:
    sync_noise_dependencies(
        cast(Any, _audio_noise_reduction),
        find_deep_filter=find_deep_filter,
        find_dpdfnet_bundle=find_dpdfnet_bundle,
        find_ffmpeg=find_ffmpeg,
        find_rnnoise_bundle=find_rnnoise_bundle,
        find_spleeter_bundle=find_spleeter_bundle,
        find_silero_vad_bundle=find_silero_vad_bundle,
        probe_duration_ms=probe_duration_ms,
        render_external_error_message=_render_external_error_message,
        run_external_command=_run_external_command,
        shutil_module=shutil,
        tempfile_module=tempfile,
    )


def _sync_pitch_hum_dependencies() -> None:
    sync_pitch_hum_dependencies(
        cast(Any, _audio_pitch_hum),
        find_ffmpeg=find_ffmpeg,
        probe_duration_ms=probe_duration_ms,
        subprocess_module=subprocess,
        tempfile_module=tempfile,
    )
