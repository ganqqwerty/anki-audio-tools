"""Detector input preparation and algorithm-specific pause interval detection."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from . import audio_pause_pipeline_stage as _stage
from .audio_artifacts import _artifact_record
from .audio_commands import (
    WAV_MIME_TYPE,
    build_dpdfnet_command,
    build_silencedetect_command,
    build_silero_vad_command,
    build_silero_vad_prepare_command,
)
from .audio_pause_settings import (
    pause_preprocess_denoise_enabled,
    seconds_to_pause_ms,
)
from .audio_pipeline import (
    SilenceInterval,
    intervals_to_json,
    parse_silencedetect_intervals,
    parse_silero_vad_speech_intervals,
    speech_intervals_to_silence_intervals,
)
from .audio_state import AudioProcessingConfig
from .errors import AudioProcessingError

DENOISE_EXTERNAL_TIMEOUT_SECONDS = 20 * 60


def _analysis_source_for_detection(
    config: AudioProcessingConfig,
    ffmpeg_path: Path,
    working_original: Path,
    denoised_analysis: Path,
    dpdfnet_path: Path | None,
    manifest: dict[str, object],
    stages: list[dict[str, object]],
    attempted_commands: list[dict[str, object]],
    artifacts: list[dict[str, object]],
    write_manifest: Callable[[], None],
    on_command: Callable[[tuple[str, ...]], None] | None,
) -> Path:
    if not pause_preprocess_denoise_enabled(config):
        manifest["pause_preprocessing"] = {
            "enabled": False,
            "analysis_source": str(working_original),
        }
        write_manifest()
        return working_original
    if dpdfnet_path is None:
        raise AudioProcessingError("DPDFNet is required for pause detection preprocessing.")

    dpdfnet_cmd = build_dpdfnet_command(
        dpdfnet_path,
        working_original,
        denoised_analysis,
        attn_limit_db=config.dpdfnet_attn_limit_db,
    )
    _stage.run_pipeline_stage(
        "preprocess_pause_analysis_denoise",
        dpdfnet_cmd,
        "Could not start DPDFNet pause preprocessing.",
        "DPDFNet pause preprocessing failed.",
        stages,
        attempted_commands,
        on_command,
        timeout_seconds=DENOISE_EXTERNAL_TIMEOUT_SECONDS,
        env={"DPDFNET_FFMPEG": str(ffmpeg_path)},
    )
    if not denoised_analysis.is_file():
        raise AudioProcessingError("DPDFNet did not produce a pause analysis WAV output.")
    manifest["pause_preprocessing"] = {
        "enabled": True,
        "implementation": "dpdfnet",
        "analysis_source": str(denoised_analysis),
    }
    artifacts.append(_artifact_record("denoised_analysis", denoised_analysis, WAV_MIME_TYPE))
    write_manifest()
    return denoised_analysis


def _detect_silencedetect_pause_intervals(
    config: AudioProcessingConfig,
    ffmpeg_path: Path,
    analysis_source: Path,
    working_duration_ms: int,
    raw_silence_path: Path,
    detected_intervals_path: Path,
    stages: list[dict[str, object]],
    attempted_commands: list[dict[str, object]],
    artifacts: list[dict[str, object]],
    write_manifest: Callable[[], None],
    on_command: Callable[[tuple[str, ...]], None] | None,
) -> tuple[tuple[SilenceInterval, ...], tuple[str, ...]]:
    silence_cmd = build_silencedetect_command(
        ffmpeg_path,
        analysis_source,
        threshold_db=config.pause_silencedetect_threshold_db,
        min_duration_ms=seconds_to_pause_ms(config.pause_silencedetect_min_silence_seconds),
    )
    silence_result = _stage.run_pipeline_stage(
        "detect_silence",
        silence_cmd,
        "Could not start pause detection.",
        "Pause detection failed.",
        stages,
        attempted_commands,
        on_command,
    )
    raw_silence_path.write_text(silence_result.stderr, encoding="utf-8")
    detected_intervals = parse_silencedetect_intervals(
        silence_result.stderr,
        working_duration_ms,
    )
    detected_intervals_path.write_text(
        json.dumps(intervals_to_json(detected_intervals), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    artifacts.extend(
        [
            _artifact_record("silencedetect_stderr", raw_silence_path, "text/plain"),
            _artifact_record("detected_pause_intervals", detected_intervals_path, "application/json"),
        ]
    )
    write_manifest()
    return detected_intervals, silence_cmd


def _detect_silero_pause_intervals(
    config: AudioProcessingConfig,
    ffmpeg_path: Path,
    run_dir: Path,
    analysis_source: Path,
    analysis_input: Path,
    working_duration_ms: int,
    silero_vad_path: Path | None,
    silero_model_path: Path | None,
    stages: list[dict[str, object]],
    attempted_commands: list[dict[str, object]],
    artifacts: list[dict[str, object]],
    write_manifest: Callable[[], None],
    on_command: Callable[[tuple[str, ...]], None] | None,
) -> tuple[tuple[SilenceInterval, ...], tuple[str, ...]]:
    if silero_vad_path is None or silero_model_path is None:
        raise AudioProcessingError("Silero VAD is required for Silero pause detection.")

    silero_output = run_dir / "03_silero_vad_output.wav"
    raw_silero_path = run_dir / "04_silero_vad_stderr.txt"
    speech_intervals_path = run_dir / "04_silero_speech_intervals.json"
    detected_intervals_path = run_dir / "04_detected_pause_intervals.json"
    prepare_cmd = build_silero_vad_prepare_command(ffmpeg_path, analysis_source, analysis_input)
    _stage.run_pipeline_stage(
        "prepare_silero_vad_input",
        prepare_cmd,
        "Could not start Silero VAD preparation.",
        "Could not prepare audio for Silero VAD pause analysis.",
        stages,
        attempted_commands,
        on_command,
    )
    artifacts.append(_artifact_record("silero_vad_input", analysis_input, WAV_MIME_TYPE))
    write_manifest()

    silero_cmd = build_silero_vad_command(
        silero_vad_path,
        silero_model_path,
        analysis_input,
        silero_output,
        threshold=config.pause_silero_threshold,
        min_silence_seconds=config.pause_silero_min_silence_seconds,
        min_speech_seconds=config.pause_silero_min_speech_seconds,
    )
    silero_result = _stage.run_pipeline_stage(
        "silero_vad_analysis",
        silero_cmd,
        "Could not start Silero VAD pause analysis.",
        "Silero VAD pause analysis failed.",
        stages,
        attempted_commands,
        on_command,
    )
    artifacts.append(_artifact_record("silero_vad_output", silero_output, WAV_MIME_TYPE))
    raw_silero_path.write_text(silero_result.stderr.strip(), encoding="utf-8")
    speech_intervals = parse_silero_vad_speech_intervals(silero_result.stderr, working_duration_ms)
    detected_intervals = speech_intervals_to_silence_intervals(speech_intervals, working_duration_ms)
    speech_intervals_path.write_text(
        json.dumps(intervals_to_json(speech_intervals), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    detected_intervals_path.write_text(
        json.dumps(intervals_to_json(detected_intervals), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    artifacts.extend(
        [
            _artifact_record("silero_vad_stderr", raw_silero_path, "text/plain"),
            _artifact_record("silero_speech_intervals", speech_intervals_path, "application/json"),
            _artifact_record("detected_pause_intervals", detected_intervals_path, "application/json"),
        ]
    )
    write_manifest()
    return detected_intervals, silero_cmd
