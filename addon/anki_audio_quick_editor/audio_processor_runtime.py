"""Dependency sync helpers for the audio processor facade."""

from __future__ import annotations

import subprocess  # nosec B404
from typing import Any

from .audio_deps import AudioModuleDeps


def sync_tool_dependencies(audio_tools: Any, deps: AudioModuleDeps) -> None:
    audio_tools._bundled_deep_filter_path = deps.bundled_deep_filter_path


def sync_external_dependencies(audio_external: Any, deps: AudioModuleDeps) -> None:
    audio_external.subprocess = subprocess
    audio_external.find_ffmpeg = deps.find_ffmpeg
    audio_external.find_ffprobe = deps.find_ffprobe


def sync_pause_dependencies(
    audio_pause_pipeline: Any,
    audio_pause_pipeline_steps: Any,
    audio_pause_pipeline_stage: Any,
    deps: AudioModuleDeps,
) -> None:
    audio_pause_pipeline.find_dpdfnet_bundle = deps.find_dpdfnet_bundle
    audio_pause_pipeline.find_silero_vad_bundle = deps.find_silero_vad_bundle
    audio_pause_pipeline.probe_duration_ms = deps.probe_duration_ms
    audio_pause_pipeline.resolve_output_policy = deps.resolve_output_policy
    audio_pause_pipeline_steps.probe_duration_ms = deps.probe_duration_ms
    audio_pause_pipeline_stage.run_external_command = deps.run_external_command
    audio_pause_pipeline_stage.render_external_error_message = deps.render_external_error_message


def sync_rendering_dependencies(audio_rendering: Any, deps: AudioModuleDeps) -> None:
    audio_rendering.find_ffmpeg = deps.find_ffmpeg
    audio_rendering.probe_duration_ms = deps.probe_duration_ms
    audio_rendering.probe_audio_metadata = deps.probe_audio_metadata
    audio_rendering.build_audio_filters = deps.build_audio_filters
    audio_rendering.build_convert_audio_command = deps.build_convert_audio_command
    audio_rendering.build_size_reduction_audio_command = deps.build_size_reduction_audio_command
    audio_rendering.resolve_output_policy = deps.resolve_output_policy
    audio_rendering.render_pause_removal_pipeline_audio = deps.render_pause_removal_pipeline_audio
    audio_rendering.external_command_run_kwargs = deps.external_command_run_kwargs
    audio_rendering.make_playback_segment_filename = deps.make_playback_segment_filename


def sync_noise_dependencies(audio_noise_reduction: Any, deps: AudioModuleDeps) -> None:
    audio_noise_reduction.find_ffmpeg = deps.find_ffmpeg
    audio_noise_reduction.find_deep_filter = deps.find_deep_filter
    audio_noise_reduction.find_rnnoise_bundle = deps.find_rnnoise_bundle
    audio_noise_reduction.find_silero_vad_bundle = deps.find_silero_vad_bundle
    audio_noise_reduction.find_dpdfnet_bundle = deps.find_dpdfnet_bundle
    audio_noise_reduction.find_spleeter_bundle = deps.find_spleeter_bundle
    audio_noise_reduction.probe_audio_metadata = deps.probe_audio_metadata
    audio_noise_reduction.probe_duration_ms = deps.probe_duration_ms
    audio_noise_reduction.run_external_command = deps.run_external_command
    audio_noise_reduction.render_external_error_message = deps.render_external_error_message
    bundled = getattr(audio_noise_reduction, "_bundled", None)
    if bundled is not None:
        bundled.find_ffmpeg = deps.find_ffmpeg
        bundled.find_rnnoise_bundle = deps.find_rnnoise_bundle
        bundled.find_silero_vad_bundle = deps.find_silero_vad_bundle
        bundled.find_dpdfnet_bundle = deps.find_dpdfnet_bundle
        bundled.find_spleeter_bundle = deps.find_spleeter_bundle
        bundled.probe_audio_metadata = deps.probe_audio_metadata
        bundled.probe_duration_ms = deps.probe_duration_ms
        bundled.run_external_command = deps.run_external_command
        bundled.render_external_error_message = deps.render_external_error_message


def sync_pitch_hum_dependencies(audio_pitch_hum: Any, deps: AudioModuleDeps) -> None:
    audio_pitch_hum.find_ffmpeg = deps.find_ffmpeg
    audio_pitch_hum.probe_duration_ms = deps.probe_duration_ms
