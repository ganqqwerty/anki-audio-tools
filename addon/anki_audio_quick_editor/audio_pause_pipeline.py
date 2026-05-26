"""DeepFilter- and Silero-assisted pause speed-up orchestration."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .audio_artifacts import (
    _artifact_record,
    _build_pause_pipeline_manifest,
    _create_pause_pipeline_run_dir,
)
from .audio_commands import (
    WAV_MIME_TYPE,
    build_wav_filter_command,
    build_working_original_filters,
)
from .audio_external import probe_duration_ms
from .audio_pause_pipeline_steps import (
    _render_deep_filter_analysis_pause_speedup_audio,
    _render_silero_vad_pause_speedup_audio,
    _run_pipeline_stage,
)
from .audio_state import AudioEditState, AudioProcessingConfig
from .audio_tools import find_deep_filter, find_silero_vad_bundle
from .audio_types import AudioProcessingResult
from .support import record_latest_pause_pipeline_support_incident


@dataclass(frozen=True)
class _PauseDetectionRuntime:
    deep_filter_path: Path | None = None
    silero_vad_path: Path | None = None
    silero_model_path: Path | None = None


@dataclass(frozen=True)
class _PausePipelinePaths:
    analysis_input: Path
    deep_filter_output_dir: Path
    raw_silence_path: Path
    intervals_path: Path
    timeline_path: Path
    filter_script_path: Path


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
    runtime = _PauseDetectionRuntime()
    run_dir = _create_pause_pipeline_run_dir(source_path, artifact_root)
    manifest_path = run_dir / "manifest.json"
    attempted_commands: list[dict[str, object]] = []
    stages: list[dict[str, object]] = []
    artifacts: list[dict[str, object]] = []
    warnings: list[str] = []
    errors: list[str] = []
    working_original = run_dir / "01_working_original.wav"
    final_copy_path = run_dir / "07_final_output.mp3"
    paths = _pause_pipeline_artifact_paths(run_dir)

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
        runtime = _resolve_pause_detection_runtime(config, manifest)
        write_manifest()
        working_duration_ms = _render_working_original(
            source_path,
            state,
            config,
            ffmpeg_path,
            source_duration_ms,
            working_original,
            stages,
            attempted_commands,
            artifacts,
            on_command,
        )
        manifest["working_duration_ms"] = working_duration_ms
        write_manifest()

        return _render_selected_pause_detection_pipeline(
            state,
            config,
            ffmpeg_path,
            output_path,
            on_command,
            manifest_path=manifest_path,
            manifest=manifest,
            stages=stages,
            attempted_commands=attempted_commands,
            artifacts=artifacts,
            write_manifest=write_manifest,
            run_dir=run_dir,
            working_original=working_original,
            working_duration_ms=working_duration_ms,
            final_copy_path=final_copy_path,
            runtime=runtime,
            analysis_input=paths.analysis_input,
            deep_filter_output_dir=paths.deep_filter_output_dir,
            raw_silence_path=paths.raw_silence_path,
            intervals_path=paths.intervals_path,
            timeline_path=paths.timeline_path,
            filter_script_path=paths.filter_script_path,
        )
    except Exception as exc:
        errors.append(str(exc) or type(exc).__name__)
        manifest["final_output"] = {
            "path": str(output_path),
            "artifact_path": str(final_copy_path),
            "duration_ms": None,
        }
        write_manifest()
        record_latest_pause_pipeline_support_incident(
            operation=str(manifest.get("operation") or "deep_filter_pause_speedup"),
            media_filename=source_path.name,
            source_path=str(source_path.resolve()),
            user_message=str(exc),
            exception_type=type(exc).__name__,
            ffmpeg_path=str(ffmpeg_path),
            deep_filter_path=str(runtime.deep_filter_path) if runtime.deep_filter_path is not None else "",
            silero_vad_path=str(runtime.silero_vad_path) if runtime.silero_vad_path is not None else "",
            manifest_path=str(manifest_path),
            artifact_dir=str(run_dir),
            attempted_commands=attempted_commands,
        )
        raise


def _pause_pipeline_artifact_paths(run_dir: Path) -> _PausePipelinePaths:
    deep_filter_output_dir = run_dir / "03_deep_filter_output"
    deep_filter_output_dir.mkdir(parents=True, exist_ok=True)
    return _PausePipelinePaths(
        analysis_input=run_dir / "02_analysis_input_48k_mono.wav",
        deep_filter_output_dir=deep_filter_output_dir,
        raw_silence_path=run_dir / "04_silencedetect_stderr.txt",
        intervals_path=run_dir / "04_silence_intervals.json",
        timeline_path=run_dir / "05_timeline.json",
        filter_script_path=run_dir / "06_filter_complex.ffscript",
    )


def _resolve_pause_detection_runtime(
    config: AudioProcessingConfig,
    manifest: dict[str, object],
) -> _PauseDetectionRuntime:
    if config.pause_detection_algorithm == "silero_vad":
        silero_vad_path, silero_model_path = find_silero_vad_bundle()
        manifest["operation"] = "silero_vad_pause_speedup"
        manifest["silero_vad_path"] = str(silero_vad_path)
        manifest["silero_vad_model_path"] = str(silero_model_path)
        return _PauseDetectionRuntime(
            silero_vad_path=silero_vad_path,
            silero_model_path=silero_model_path,
        )
    deep_filter_path = find_deep_filter()
    manifest["deep_filter_path"] = str(deep_filter_path)
    return _PauseDetectionRuntime(deep_filter_path=deep_filter_path)


def _render_working_original(
    source_path: Path,
    state: AudioEditState,
    config: AudioProcessingConfig,
    ffmpeg_path: Path,
    source_duration_ms: int,
    working_original: Path,
    stages: list[dict[str, object]],
    attempted_commands: list[dict[str, object]],
    artifacts: list[dict[str, object]],
    on_command: Callable[[tuple[str, ...]], None] | None,
) -> int:
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
    return probe_duration_ms(working_original, config)


def _render_selected_pause_detection_pipeline(
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
    deep_filter_output_dir: Path,
    raw_silence_path: Path,
    intervals_path: Path,
    timeline_path: Path,
    filter_script_path: Path,
    final_copy_path: Path,
    runtime: _PauseDetectionRuntime,
) -> AudioProcessingResult:
    if runtime.silero_vad_path is not None and runtime.silero_model_path is not None:
        return _render_silero_vad_pause_speedup_audio(
            state,
            config,
            ffmpeg_path,
            output_path,
            on_command,
            run_dir=run_dir,
            manifest_path=manifest_path,
            manifest=manifest,
            stages=stages,
            attempted_commands=attempted_commands,
            artifacts=artifacts,
            write_manifest=write_manifest,
            working_original=working_original,
            working_duration_ms=working_duration_ms,
            silero_vad_path=runtime.silero_vad_path,
            silero_model_path=runtime.silero_model_path,
        )
    assert runtime.deep_filter_path is not None
    return _render_deep_filter_analysis_pause_speedup_audio(
        state,
        config,
        ffmpeg_path,
        output_path,
        on_command,
        manifest_path=manifest_path,
        manifest=manifest,
        stages=stages,
        attempted_commands=attempted_commands,
        artifacts=artifacts,
        write_manifest=write_manifest,
        working_original=working_original,
        working_duration_ms=working_duration_ms,
        analysis_input=analysis_input,
        deep_filter_output_dir=deep_filter_output_dir,
        raw_silence_path=raw_silence_path,
        intervals_path=intervals_path,
        timeline_path=timeline_path,
        filter_script_path=filter_script_path,
        final_copy_path=final_copy_path,
        deep_filter_path=runtime.deep_filter_path,
    )
