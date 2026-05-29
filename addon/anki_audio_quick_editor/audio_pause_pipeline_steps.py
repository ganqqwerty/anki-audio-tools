"""Pause-removal render planning and final output stages."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path

from . import audio_pause_pipeline_stage as _stage
from .audio_artifacts import _artifact_record
from .audio_commands import (
    build_filter_complex_render_command,
)
from .audio_external import (
    probe_duration_ms,
)
from .audio_pause_pipeline_detection import (
    _analysis_source_for_detection,
    _detect_silencedetect_pause_intervals,
    _detect_silero_pause_intervals,
)
from .audio_pause_settings import (
    active_pause_detection_params,
    seconds_to_pause_ms,
)
from .audio_pipeline import (
    SilenceInterval,
    build_filter_complex_script,
    filter_silence_intervals_by_duration,
    intervals_to_json,
    merge_short_speech_gaps,
    plan_pause_removal_timeline,
    timeline_to_json,
)
from .audio_state import AudioEditState, AudioProcessingConfig
from .audio_types import AudioProcessingResult


def _render_pause_removal_audio(
    state: AudioEditState,
    config: AudioProcessingConfig,
    ffmpeg_path: Path,
    output_path: Path,
    on_command: Callable[[tuple[str, ...]], None] | None,
    *,
    manifest_path: Path,
    manifest: dict[str, object],
    stages: list[dict[str, object]],
    attempted_commands: list[dict[str, object]],
    artifacts: list[dict[str, object]],
    write_manifest: Callable[[], None],
    run_dir: Path,
    working_original: Path,
    working_duration_ms: int,
    analysis_input: Path,
    denoised_analysis: Path,
    raw_silence_path: Path,
    intervals_path: Path,
    timeline_path: Path,
    filter_script_path: Path,
    final_copy_path: Path,
    dpdfnet_path: Path | None,
    silero_vad_path: Path | None,
    silero_model_path: Path | None,
    codec_args: tuple[str, ...] = ("-codec:a", "libmp3lame", "-q:a", "4"),
    output_mime_type: str = "audio/mpeg",
) -> AudioProcessingResult:
    active_params = active_pause_detection_params(config)
    manifest["pause_detection_parameters"] = {
        "algorithm": config.pause_detection_algorithm,
        "aggressiveness": config.pause_aggressiveness,
        **active_params,
    }
    analysis_source = _analysis_source_for_detection(
        config,
        ffmpeg_path,
        working_original,
        denoised_analysis,
        dpdfnet_path,
        manifest,
        stages,
        attempted_commands,
        artifacts,
        write_manifest,
        on_command,
    )

    if config.pause_detection_algorithm == "silero_vad":
        detected_intervals, detection_cmd = _detect_silero_pause_intervals(
            config,
            ffmpeg_path,
            run_dir,
            analysis_source,
            analysis_input,
            working_duration_ms,
            silero_vad_path,
            silero_model_path,
            stages,
            attempted_commands,
            artifacts,
            write_manifest,
            on_command,
        )
    else:
        detected_intervals, detection_cmd = _detect_silencedetect_pause_intervals(
            config,
            ffmpeg_path,
            analysis_source,
            working_duration_ms,
            raw_silence_path,
            run_dir / "04_detected_pause_intervals.json",
            stages,
            attempted_commands,
            artifacts,
            write_manifest,
            on_command,
        )

    removed_intervals = _removable_pause_intervals(
        detected_intervals,
        working_duration_ms,
        min_silence_seconds=float(active_params["min_silence_seconds"]),
        min_speech_seconds=float(active_params["min_speech_seconds"]),
    )
    _write_pause_interval_artifacts(
        detected_intervals,
        removed_intervals,
        intervals_path,
        manifest,
        artifacts,
    )
    write_manifest()

    _write_pause_timeline_artifacts(
        state,
        working_duration_ms,
        removed_intervals,
        timeline_path,
        filter_script_path,
        manifest,
        artifacts,
    )
    write_manifest()

    render_cmd = build_filter_complex_render_command(
        ffmpeg_path,
        working_original,
        filter_script_path,
        output_path,
        codec_args,
    )
    _stage.run_pipeline_stage(
        "render_final_output",
        render_cmd,
        "Could not start pause-shortened audio rendering.",
        "Could not render pause-shortened audio.",
        stages,
        attempted_commands,
        on_command,
    )
    if output_path.resolve() != final_copy_path.resolve():
        shutil.copyfile(output_path, final_copy_path)
    artifacts.append(_artifact_record("final_output", final_copy_path, output_mime_type))
    final_duration_ms = probe_duration_ms(output_path, config)
    manifest["final_output"] = {
        "path": str(output_path),
        "artifact_path": str(final_copy_path),
        "duration_ms": final_duration_ms,
    }
    write_manifest()
    return AudioProcessingResult(
        output_path=output_path,
        command=detection_cmd,
        duration_ms=final_duration_ms,
        artifact_manifest_path=manifest_path,
    )


def _removable_pause_intervals(
    detected_intervals: tuple[SilenceInterval, ...],
    working_duration_ms: int,
    *,
    min_silence_seconds: float,
    min_speech_seconds: float,
) -> tuple[SilenceInterval, ...]:
    merged_intervals = merge_short_speech_gaps(
        detected_intervals,
        working_duration_ms,
        min_speech_ms=seconds_to_pause_ms(min_speech_seconds),
    )
    return filter_silence_intervals_by_duration(
        merged_intervals,
        min_silence_ms=seconds_to_pause_ms(min_silence_seconds),
    )


def _write_pause_interval_artifacts(
    detected_intervals: tuple[SilenceInterval, ...],
    removed_intervals: tuple[SilenceInterval, ...],
    intervals_path: Path,
    manifest: dict[str, object],
    artifacts: list[dict[str, object]],
) -> None:
    detected_json = intervals_to_json(detected_intervals)
    removed_json = intervals_to_json(removed_intervals)
    intervals_path.write_text(
        json.dumps(removed_json, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    manifest["detected_intervals"] = detected_json
    manifest["removed_intervals"] = removed_json
    manifest["silence_intervals"] = removed_json
    artifacts.append(_artifact_record("removed_intervals", intervals_path, "application/json"))


def _write_pause_timeline_artifacts(
    state: AudioEditState,
    duration_ms: int,
    silence_intervals: tuple[SilenceInterval, ...],
    timeline_path: Path,
    filter_script_path: Path,
    manifest: dict[str, object],
    artifacts: list[dict[str, object]],
) -> None:
    timeline = plan_pause_removal_timeline(duration_ms, silence_intervals)
    timeline_json = timeline_to_json(timeline)
    timeline_path.write_text(
        json.dumps(timeline_json, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    filter_script_path.write_text(
        build_filter_complex_script(
            timeline,
            volume_db=state.volume_db,
            speed=state.speed,
        ),
        encoding="utf-8",
    )
    manifest["timeline"] = timeline_json
    artifacts.extend(
        [
            _artifact_record("timeline", timeline_path, "application/json"),
            _artifact_record("filter_complex_script", filter_script_path, "text/plain"),
        ]
    )
