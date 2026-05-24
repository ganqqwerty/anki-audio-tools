"""DeepFilter-assisted pause speed-up orchestration."""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess  # nosec B404
import time
from collections.abc import Callable
from pathlib import Path

from .audio_artifacts import (
    _artifact_record,
    _build_pause_pipeline_manifest,
    _create_pause_pipeline_run_dir,
)
from .audio_commands import (
    WAV_MIME_TYPE,
    build_deep_filter_command,
    build_deep_filter_prepare_command,
    build_filter_complex_render_command,
    build_silencedetect_command,
    build_wav_filter_command,
    build_working_original_filters,
)
from .audio_external import (
    _render_external_error_message,
    _run_external_command,
    probe_duration_ms,
)
from .audio_noise_reduction import select_deep_filter_output
from .audio_pipeline import (
    build_filter_complex_script,
    intervals_to_json,
    parse_silencedetect_intervals,
    plan_pause_timeline,
    timeline_to_json,
)
from .audio_state import AudioEditState, AudioProcessingConfig
from .audio_tools import find_deep_filter
from .audio_types import AudioProcessingResult
from .errors import AudioProcessingError
from .support import build_command_record, record_latest_pause_pipeline_support_incident


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
    deep_filter_path: Path | None = None
    run_dir = _create_pause_pipeline_run_dir(source_path, artifact_root)
    manifest_path = run_dir / "manifest.json"
    attempted_commands: list[dict[str, object]] = []
    stages: list[dict[str, object]] = []
    artifacts: list[dict[str, object]] = []
    warnings: list[str] = []
    errors: list[str] = []
    final_duration_ms: int | None = None
    working_original = run_dir / "01_working_original.wav"
    analysis_input = run_dir / "02_analysis_input_48k_mono.wav"
    deep_filter_output_dir = run_dir / "03_deep_filter_output"
    raw_silence_path = run_dir / "04_silencedetect_stderr.txt"
    intervals_path = run_dir / "04_silence_intervals.json"
    timeline_path = run_dir / "05_timeline.json"
    filter_script_path = run_dir / "06_filter_complex.ffscript"
    final_copy_path = run_dir / "07_final_output.mp3"
    deep_filter_output_dir.mkdir(parents=True, exist_ok=True)

    manifest = _build_pause_pipeline_manifest(
        run_dir,
        source_path,
        state,
        config,
        source_duration_ms,
        stages=stages,
        artifacts=artifacts,
        warnings=warnings,
        errors=errors,
    )

    def write_manifest() -> None:
        manifest["stages"] = stages
        manifest["artifacts"] = artifacts
        manifest["warnings"] = warnings
        manifest["errors"] = errors
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    artifacts.append(_artifact_record("source", source_path, "input"))
    artifacts.append({"id": "manifest", "path": str(manifest_path), "kind": "manifest", "exists": True})
    try:
        deep_filter_path = find_deep_filter()
        manifest["deep_filter_path"] = str(deep_filter_path)
        write_manifest()
        working_filters = build_working_original_filters(source_duration_ms, state)
        working_cmd = build_wav_filter_command(
            ffmpeg_path,
            source_path,
            working_filters,
            working_original,
        )
        _run_pipeline_stage(
            "render_working_original",
            working_cmd,
            "Could not start working-audio preparation.",
            "Could not prepare working audio for pause shortening.",
            stages,
            attempted_commands,
            on_command,
        )
        artifacts.append(_artifact_record("working_original", working_original, WAV_MIME_TYPE))
        working_duration_ms = probe_duration_ms(working_original, config)
        manifest["working_duration_ms"] = working_duration_ms
        write_manifest()

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
        intervals_json = intervals_to_json(silence_intervals)
        intervals_path.write_text(
            json.dumps(intervals_json, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        manifest["silence_intervals"] = intervals_json
        artifacts.extend(
            [
                _artifact_record("silencedetect_stderr", raw_silence_path, "text/plain"),
                _artifact_record("silence_intervals", intervals_path, "application/json"),
            ]
        )
        write_manifest()

        timeline = plan_pause_timeline(
            working_duration_ms,
            silence_intervals,
            min_pause_ms=config.internal_pause_threshold_ms,
            target_gap_ms=config.internal_pause_target_gap_ms,
        )
        timeline_json = timeline_to_json(timeline)
        timeline_path.write_text(
            json.dumps(timeline_json, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        filter_script = build_filter_complex_script(
            timeline,
            volume_db=state.volume_db,
            speed=state.speed,
        )
        filter_script_path.write_text(filter_script, encoding="utf-8")
        manifest["timeline"] = timeline_json
        artifacts.extend(
            [
                _artifact_record("timeline", timeline_path, "application/json"),
                _artifact_record("filter_complex_script", filter_script_path, "text/plain"),
            ]
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
    except Exception as exc:
        errors.append(str(exc) or type(exc).__name__)
        manifest["final_output"] = {
            "path": str(output_path),
            "artifact_path": str(final_copy_path),
            "duration_ms": final_duration_ms,
        }
        write_manifest()
        record_latest_pause_pipeline_support_incident(
            operation="deep_filter_pause_speedup",
            media_filename=source_path.name,
            source_path=str(source_path.resolve()),
            user_message=str(exc),
            exception_type=type(exc).__name__,
            ffmpeg_path=str(ffmpeg_path),
            deep_filter_path=str(deep_filter_path) if deep_filter_path is not None else "",
            manifest_path=str(manifest_path),
            artifact_dir=str(run_dir),
            attempted_commands=attempted_commands,
        )
        raise


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
