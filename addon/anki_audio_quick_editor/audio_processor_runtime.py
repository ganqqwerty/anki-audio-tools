"""Dependency sync helpers for the audio processor facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def sync_tool_dependencies(audio_tools: Any, *, shutil_module: Any, bundled_deep_filter_path: Any) -> None:
    audio_tools.Path = Path
    audio_tools.shutil = shutil_module
    audio_tools._bundled_deep_filter_path = bundled_deep_filter_path


def sync_external_dependencies(audio_external: Any, *, subprocess_module: Any, find_ffmpeg: Any, find_ffprobe: Any) -> None:
    audio_external.subprocess = subprocess_module
    audio_external.find_ffmpeg = find_ffmpeg
    audio_external.find_ffprobe = find_ffprobe


def sync_pause_dependencies(
    audio_pause_pipeline: Any,
    *,
    find_deep_filter: Any,
    find_silero_vad_bundle: Any,
    probe_duration_ms: Any,
    run_external_command: Any,
    render_external_error_message: Any,
) -> None:
    audio_pause_pipeline.find_deep_filter = find_deep_filter
    audio_pause_pipeline.find_silero_vad_bundle = find_silero_vad_bundle
    audio_pause_pipeline.probe_duration_ms = probe_duration_ms
    audio_pause_pipeline._run_external_command = run_external_command
    audio_pause_pipeline._render_external_error_message = render_external_error_message


def sync_rendering_dependencies(
    audio_rendering: Any,
    *,
    build_audio_filters: Any,
    build_convert_audio_command: Any,
    external_command_run_kwargs: Any,
    find_ffmpeg: Any,
    make_playback_segment_filename: Any,
    probe_duration_ms: Any,
    render_deep_filter_pause_speedup_audio: Any,
    subprocess_module: Any,
    tempfile_module: Any,
    uuid_module: Any,
) -> None:
    audio_rendering.find_ffmpeg = find_ffmpeg
    audio_rendering.probe_duration_ms = probe_duration_ms
    audio_rendering.build_audio_filters = build_audio_filters
    audio_rendering.build_convert_audio_command = build_convert_audio_command
    audio_rendering._render_deep_filter_pause_speedup_audio = render_deep_filter_pause_speedup_audio
    audio_rendering._external_command_run_kwargs = external_command_run_kwargs
    audio_rendering.subprocess = subprocess_module
    audio_rendering.tempfile = tempfile_module
    audio_rendering.uuid = uuid_module
    audio_rendering.make_playback_segment_filename = make_playback_segment_filename


def sync_noise_dependencies(
    audio_noise_reduction: Any,
    *,
    find_deep_filter: Any,
    find_dpdfnet_bundle: Any,
    find_ffmpeg: Any,
    find_rnnoise_bundle: Any,
    find_silero_vad_bundle: Any,
    find_spleeter_bundle: Any,
    probe_duration_ms: Any,
    render_external_error_message: Any,
    run_external_command: Any,
    shutil_module: Any,
    tempfile_module: Any,
) -> None:
    audio_noise_reduction.find_ffmpeg = find_ffmpeg
    audio_noise_reduction.find_deep_filter = find_deep_filter
    audio_noise_reduction.find_rnnoise_bundle = find_rnnoise_bundle
    audio_noise_reduction.find_silero_vad_bundle = find_silero_vad_bundle
    audio_noise_reduction.find_dpdfnet_bundle = find_dpdfnet_bundle
    audio_noise_reduction.find_spleeter_bundle = find_spleeter_bundle
    audio_noise_reduction.probe_duration_ms = probe_duration_ms
    audio_noise_reduction._run_external_command = run_external_command
    audio_noise_reduction._render_external_error_message = render_external_error_message
    audio_noise_reduction.tempfile = tempfile_module
    audio_noise_reduction.shutil = shutil_module
    bundled = getattr(audio_noise_reduction, "_bundled", None)
    if bundled is not None:
        bundled.find_ffmpeg = find_ffmpeg
        bundled.find_rnnoise_bundle = find_rnnoise_bundle
        bundled.find_silero_vad_bundle = find_silero_vad_bundle
        bundled.find_dpdfnet_bundle = find_dpdfnet_bundle
        bundled.find_spleeter_bundle = find_spleeter_bundle
        bundled.probe_duration_ms = probe_duration_ms
        bundled._run_external_command = run_external_command
        bundled._render_external_error_message = render_external_error_message
        bundled.tempfile = tempfile_module
        bundled.shutil = shutil_module


def sync_pitch_hum_dependencies(audio_pitch_hum: Any, *, find_ffmpeg: Any, probe_duration_ms: Any, subprocess_module: Any, tempfile_module: Any) -> None:
    audio_pitch_hum.find_ffmpeg = find_ffmpeg
    audio_pitch_hum.probe_duration_ms = probe_duration_ms
    audio_pitch_hum.subprocess = subprocess_module
    audio_pitch_hum.tempfile = tempfile_module
