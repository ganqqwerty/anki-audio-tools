"""Typed audio processing dependency injection seam."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AudioModuleDeps:
    find_ffmpeg: Callable[..., Path]
    find_ffprobe: Callable[..., Path]
    find_deep_filter: Callable[..., Path]
    find_rnnoise_bundle: Callable[..., Path]
    find_dpdfnet_bundle: Callable[..., Path]
    find_spleeter_bundle: Callable[..., tuple[Path, Path, Path]]
    find_silero_vad_bundle: Callable[..., tuple[Path, Path]]
    probe_duration_ms: Callable[..., int]
    probe_audio_metadata: Callable[..., Any]
    build_audio_filters: Callable[..., Any]
    build_convert_audio_command: Callable[..., Any]
    build_size_reduction_audio_command: Callable[..., Any]
    resolve_output_policy: Callable[..., Any]
    render_external_error_message: Callable[..., str]
    run_external_command: Callable[..., Any]
    external_command_run_kwargs: Callable[..., dict[str, Any]]
    make_playback_segment_filename: Callable[..., Any]
    render_pause_removal_pipeline_audio: Callable[..., Any]
    bundled_deep_filter_path: Callable[..., Path | None]
