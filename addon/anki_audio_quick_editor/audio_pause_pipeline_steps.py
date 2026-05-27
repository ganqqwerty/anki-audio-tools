"""Algorithm-specific steps for pause speed-up rendering."""

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
    build_deep_filter_command,
    build_deep_filter_prepare_command,
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
from .audio_noise_reduction import select_deep_filter_output
from .audio_pipeline import (
    SilenceInterval,
    build_filter_complex_script,
    intervals_to_json,
    parse_silencedetect_intervals,
    parse_silero_vad_speech_intervals,
    plan_pause_timeline,
    speech_intervals_to_silence_intervals,
    timeline_to_json,
)
from .audio_state import AudioEditState, AudioProcessingConfig
from .audio_types import AudioProcessingResult
from .errors import AudioProcessingError
from .support import build_command_record


def _render_deep_filter_analysis_pause_speedup_audio(
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
    working_original: Path,
    working_duration_ms: int,
    analysis_input: Path,
    deep_filter_output_dir: Path,
    raw_silence_path: Path,
    intervals_path: Path,
    timeline_path: Path,
    filter_script_path: Path,
    final_copy_path: Path,
    deep_filter_path: Path,
) -> AudioProcessingResult:
    prepare_cmd = build_deep_filter_prepare_command(ffmpeg_path, working_original, analysis_input)
    _run_pipeline_stage(
        "prepare_deep_filter_input",
        prepare_cmd,
        "Could not start DeepFilterNet analysis preparation.",
        "Could not prepare audio for DeepFilterNet pause analysis.",
        stages,
        attempted_commands,
        on_command,
    )
    artifacts.append(_artifact_record("analysis_input", analysis_input, WAV_MIME_TYPE))
    write_manifest()

    deep_filter_cmd = build_deep_filter_command(
        deep_filter_path,
        analysis_input,
        deep_filter_output_dir,
        post_filter=config.deep_filter_post_filter,
    )
    _run_pipeline_stage(
        "deep_filter_analysis",
        deep_filter_cmd,
        "Could not start DeepFilterNet pause analysis.",
        "DeepFilterNet pause analysis failed.",
        stages,
        attempted_commands,
        on_command,
    )
    cleaned_analysis_wav = select_deep_filter_output(deep_filter_output_dir)
    artifacts.append(_artifact_record("deep_filter_output", cleaned_analysis_wav, WAV_MIME_TYPE))
    write_manifest()

    silence_intervals = _detect_deep_filter_silence_intervals(
        config,
        ffmpeg_path,
        cleaned_analysis_wav,
        working_duration_ms,
        raw_silence_path,
        intervals_path,
        stages,
        attempted_commands,
        on_command,
    )
    manifest["silence_intervals"] = intervals_to_json(silence_intervals)
    artifacts.extend(
        [
            _artifact_record("silencedetect_stderr", raw_silence_path, "text/plain"),
            _artifact_record("silence_intervals", intervals_path, "application/json"),
        ]
    )
    write_manifest()

    _write_pause_timeline_artifacts(
        state,
        config,
        working_duration_ms,
        silence_intervals,
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
        command=deep_filter_cmd,
        duration_ms=final_duration_ms,
        artifact_manifest_path=manifest_path,
    )


def _render_silero_vad_pause_speedup_audio(
    state: AudioEditState,
    config: AudioProcessingConfig,
    ffmpeg_path: Path,
    output_path: Path,
    on_command: Callable[[tuple[str, ...]], None] | None,
    *,
    run_dir: Path,
    manifest_path: Path,
    manifest: dict[str, object],
    stages: list[dict[str, object]],
    attempted_commands: list[dict[str, object]],
    artifacts: list[dict[str, object]],
    write_manifest: Callable[[], None],
    working_original: Path,
    working_duration_ms: int,
    silero_vad_path: Path,
    silero_model_path: Path,
) -> AudioProcessingResult:
    silero_input = run_dir / "02_silero_input_16k_mono.wav"
    silero_output = run_dir / "03_silero_vad_output.wav"
    raw_silero_path = run_dir / "04_silero_vad_stderr.txt"
    speech_intervals_path = run_dir / "04_silero_speech_intervals.json"
    silence_intervals_path = run_dir / "04_silence_intervals.json"
    timeline_path = run_dir / "05_timeline.json"
    filter_script_path = run_dir / "06_filter_complex.ffscript"
    final_copy_path = run_dir / "07_final_output.mp3"

    params = _silero_vad_parameters(config)
    manifest["silero_vad_parameters"] = params
    prepare_cmd = build_silero_vad_prepare_command(ffmpeg_path, working_original, silero_input)
    _run_pipeline_stage(
        "prepare_silero_vad_input",
        prepare_cmd,
        "Could not start Silero VAD preparation.",
        "Could not prepare audio for Silero VAD pause analysis.",
        stages,
        attempted_commands,
        on_command,
    )
    artifacts.append(_artifact_record("silero_vad_input", silero_input, WAV_MIME_TYPE))
    write_manifest()

    silero_cmd = build_silero_vad_command(
        silero_vad_path,
        silero_model_path,
        silero_input,
        silero_output,
        threshold=float(params["threshold"]),
        min_silence_seconds=float(params["min_silence_seconds"]),
        min_speech_seconds=float(params["min_speech_seconds"]),
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
    silence_intervals = speech_intervals_to_silence_intervals(speech_intervals, working_duration_ms)
    speech_intervals_path.write_text(
        json.dumps(intervals_to_json(speech_intervals), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    silence_intervals_path.write_text(
        json.dumps(intervals_to_json(silence_intervals), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    manifest["silero_vad_input_duration_ms"] = working_duration_ms
    manifest["silero_vad_speech_intervals"] = intervals_to_json(speech_intervals)
    manifest["silence_intervals"] = intervals_to_json(silence_intervals)
    artifacts.extend(
        [
            _artifact_record("silero_vad_stderr", raw_silero_path, "text/plain"),
            _artifact_record("silero_speech_intervals", speech_intervals_path, "application/json"),
            _artifact_record("silence_intervals", silence_intervals_path, "application/json"),
        ]
    )
    write_manifest()

    _write_pause_timeline_artifacts(
        state,
        config,
        working_duration_ms,
        silence_intervals,
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
    manifest["working_duration_ms"] = working_duration_ms
    write_manifest()
    return AudioProcessingResult(
        output_path=output_path,
        command=silero_cmd,
        duration_ms=final_duration_ms,
        artifact_manifest_path=manifest_path,
    )


def _detect_deep_filter_silence_intervals(
    config: AudioProcessingConfig,
    ffmpeg_path: Path,
    cleaned_analysis_wav: Path,
    working_duration_ms: int,
    raw_silence_path: Path,
    intervals_path: Path,
    stages: list[dict[str, object]],
    attempted_commands: list[dict[str, object]],
    on_command: Callable[[tuple[str, ...]], None] | None,
) -> tuple[SilenceInterval, ...]:
    silence_cmd = build_silencedetect_command(
        ffmpeg_path,
        cleaned_analysis_wav,
        threshold_db=config.internal_pause_silence_threshold_db,
        min_duration_ms=config.internal_pause_threshold_ms,
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
    silence_intervals = parse_silencedetect_intervals(
        silence_result.stderr,
        working_duration_ms,
    )
    intervals_path.write_text(
        json.dumps(intervals_to_json(silence_intervals), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return silence_intervals


def _write_pause_timeline_artifacts(
    state: AudioEditState,
    config: AudioProcessingConfig,
    duration_ms: int,
    silence_intervals: tuple[SilenceInterval, ...],
    timeline_path: Path,
    filter_script_path: Path,
    manifest: dict[str, object],
    artifacts: list[dict[str, object]],
) -> None:
    timeline = plan_pause_timeline(
        duration_ms,
        silence_intervals,
        min_pause_ms=config.internal_pause_threshold_ms,
        target_gap_ms=config.internal_pause_target_gap_ms,
    )
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


def _silero_vad_parameters(config: AudioProcessingConfig) -> dict[str, float]:
    if config.pause_aggressiveness == "gentle":
        return {"threshold": 0.55, "min_silence_seconds": 0.7, "min_speech_seconds": 0.12}
    if config.pause_aggressiveness == "aggressive":
        return {"threshold": 0.85, "min_silence_seconds": 0.15, "min_speech_seconds": 0.04}
    return {"threshold": 0.5, "min_silence_seconds": 0.45, "min_speech_seconds": 0.1}


def _run_pipeline_stage(
    name: str,
    command: tuple[str, ...],
    launch_error_message: str,
    failure_message: str,
    stages: list[dict[str, object]],
    attempted_commands: list[dict[str, object]],
    on_command: Callable[[tuple[str, ...]], None] | None,
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
        result = _run_external_command(command, launch_error_message)
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
