"""Algorithm-specific steps for pause removal rendering."""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess  # nosec B404
import time
from collections.abc import Callable
from pathlib import Path

from .audio_artifacts import _artifact_record
from .audio_commands import (
    WAV_MIME_TYPE,
    build_dpdfnet_command,
    build_filter_complex_render_command,
    build_silencedetect_command,
    build_silero_vad_command,
    build_silero_vad_prepare_command,
)
from .audio_external import (
    _render_external_error_message,
    _run_external_command,
    probe_duration_ms,
)
from .audio_pause_settings import (
    active_pause_detection_params,
    pause_preprocess_denoise_enabled,
    seconds_to_pause_ms,
)
from .audio_pipeline import (
    SilenceInterval,
    build_filter_complex_script,
    filter_silence_intervals_by_duration,
    intervals_to_json,
    merge_short_speech_gaps,
    parse_silencedetect_intervals,
    parse_silero_vad_speech_intervals,
    plan_pause_removal_timeline,
    speech_intervals_to_silence_intervals,
    timeline_to_json,
)
from .audio_state import AudioEditState, AudioProcessingConfig
from .audio_types import AudioProcessingResult
from .errors import AudioProcessingError
from .support import build_command_record

DENOISE_EXTERNAL_TIMEOUT_SECONDS = 20 * 60


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
    )
    _run_pipeline_stage(
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
    artifacts.append(_artifact_record("final_output", final_copy_path, "audio/mpeg"))
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
    _run_pipeline_stage(
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
    silence_result = _run_pipeline_stage(
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
    _run_pipeline_stage(
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
    silero_result = _run_pipeline_stage(
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


def _run_pipeline_stage(
    name: str,
    command: tuple[str, ...],
    launch_error_message: str,
    failure_message: str,
    stages: list[dict[str, object]],
    attempted_commands: list[dict[str, object]],
    on_command: Callable[[tuple[str, ...]], None] | None,
    *,
    timeout_seconds: float | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    if on_command:
        on_command(command)
    started = time.monotonic()
    stage: dict[str, object] = {
        "name": name,
        "argv": list(command),
        "command": shlex.join(command),
    }
    try:
        result = _run_external_command(
            command,
            launch_error_message,
            timeout_seconds=timeout_seconds,
            env=env,
        )
    except AudioProcessingError as exc:
        stage["duration_seconds"] = round(time.monotonic() - started, 6)
        stage["launch_error"] = str(exc)
        stages.append(stage)
        attempted_commands.append(build_command_record(command, launch_error=str(exc)))
        raise

    stage.update(
        {
            "duration_seconds": round(time.monotonic() - started, 6),
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    )
    stages.append(stage)
    attempted_commands.append(
        build_command_record(
            command,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    )
    if result.returncode != 0:
        raise AudioProcessingError(_render_external_error_message(result, failure_message))
    return result
