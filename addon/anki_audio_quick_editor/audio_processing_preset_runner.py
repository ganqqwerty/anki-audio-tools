"""Shared staged execution for processing presets."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Protocol

from .audio_formats import (
    CONCRETE_OUTPUT_FORMATS,
    format_label,
    is_same_visible_format,
    visible_extension,
)
from .audio_operation_params import effective_config_for_operation
from .audio_operations import (
    OP_CONVERT,
    OP_DENOISE,
    OP_REDUCE_SIZE,
    apply_audio_operation,
)
from .audio_processing_presets import (
    AudioProcessingPreset,
    AudioProcessingPresetGraph,
    AudioProcessingPresetStep,
)
from .audio_state import AudioEditState, AudioProcessingConfig


class AudioOutputNameFactory(Protocol):
    """Build the generated audio filename used for one preset step."""

    def __call__(
        self,
        source_filename: str,
        *,
        output_format: str | None = None,
    ) -> str:
        ...


@dataclass(frozen=True)
class ProcessingPresetStepResult:
    """Status for one executed preset step."""

    step_id: str
    operation: str
    status: str
    message: str


@dataclass(frozen=True)
class ProcessingPresetRunResult:
    """Staged outputs produced by a processing preset run."""

    final_audio_path: Path | None
    final_audio_name: str | None
    graph_svg: bytes | None
    graph_name: str | None
    steps: tuple[ProcessingPresetStepResult, ...]
    changed: bool


@dataclass(frozen=True)
class ProcessingPresetRunnerAdapters:
    """Side-effect hooks used by the import-safe preset runner."""

    make_audio_output_filename: AudioOutputNameFactory
    make_graph_output_filename: Callable[[str], str]
    temp_output_path: Callable[[str], Path]
    render_audio: Callable[[Path, AudioEditState, AudioProcessingConfig, Path, Path | None], None]
    render_converted_audio: Callable[[Path, AudioProcessingConfig, str, Path], None]
    render_size_reduced_audio: Callable[[Path, AudioProcessingConfig, Path], None]
    render_denoise_audio: Callable[[Path, AudioProcessingConfig, Path], None]
    analyze_prosody: Callable[[Path, AudioProcessingConfig], Any]
    render_graph_svg: Callable[[Any], bytes]


def run_processing_preset(
    preset: AudioProcessingPreset,
    *,
    source_path: Path,
    source_filename: str,
    config: AudioProcessingConfig,
    adapters: ProcessingPresetRunnerAdapters,
    artifact_root: Path | None = None,
    render_graph: bool = True,
) -> ProcessingPresetRunResult:
    """Run ``preset`` against one source file and return staged outputs."""
    owned_paths: list[Path] = []
    current_path = source_path
    current_filename = source_filename
    final_audio_path: Path | None = None
    final_audio_name: str | None = None
    step_results: list[ProcessingPresetStepResult] = []
    completed = False
    try:
        for step in preset.steps:
            step_output = _run_transform_step(
                step,
                current_path=current_path,
                current_filename=current_filename,
                source_filename=source_filename,
                config=config,
                adapters=adapters,
                artifact_root=artifact_root,
            )
            step_results.append(step_output.result)
            if step_output.output_path is None:
                continue
            if current_path in owned_paths:
                _remove_temp_parent(current_path)
                owned_paths.remove(current_path)
            owned_paths.append(step_output.output_path)
            current_path = step_output.output_path
            current_filename = step_output.output_name or current_filename
            final_audio_path = step_output.output_path
            final_audio_name = step_output.output_name

        graph_svg: bytes | None = None
        graph_name: str | None = None
        if preset.graph.enabled and render_graph:
            graph_config = _graph_config(config, preset.graph)
            track = adapters.analyze_prosody(current_path, graph_config)
            graph_svg = adapters.render_graph_svg(track)
            graph_name = adapters.make_graph_output_filename(current_filename)

        result = ProcessingPresetRunResult(
            final_audio_path=final_audio_path,
            final_audio_name=final_audio_name,
            graph_svg=graph_svg,
            graph_name=graph_name,
            steps=tuple(step_results),
            changed=final_audio_path is not None or graph_svg is not None,
        )
        completed = True
        return result
    finally:
        if not completed:
            for path in owned_paths:
                _remove_temp_parent(path)


@dataclass(frozen=True)
class _StepOutput:
    result: ProcessingPresetStepResult
    output_path: Path | None
    output_name: str | None


def _run_transform_step(
    step: AudioProcessingPresetStep,
    *,
    current_path: Path,
    current_filename: str,
    source_filename: str,
    config: AudioProcessingConfig,
    adapters: ProcessingPresetRunnerAdapters,
    artifact_root: Path | None,
) -> _StepOutput:
    effective_config = effective_config_for_operation(step.operation, config, step.parameters)
    if step.operation == OP_CONVERT:
        return _run_convert_step(
            step,
            current_path,
            current_filename,
            source_filename,
            effective_config,
            adapters,
        )
    desired_name = _step_output_name(step.operation, source_filename, current_filename, adapters)
    output_path = adapters.temp_output_path(desired_name)
    completed = False
    try:
        if step.operation == OP_DENOISE:
            adapters.render_denoise_audio(current_path, effective_config, output_path)
        elif step.operation == OP_REDUCE_SIZE:
            adapters.render_size_reduced_audio(current_path, effective_config, output_path)
        else:
            updated_state = apply_audio_operation(
                step.operation,
                AudioEditState(source_file=current_filename),
                effective_config,
            )
            adapters.render_audio(
                current_path,
                updated_state,
                effective_config,
                output_path,
                artifact_root,
            )
        completed = True
    finally:
        if not completed:
            _remove_temp_parent(output_path)
    return _StepOutput(
        result=ProcessingPresetStepResult(
            step_id=step.id,
            operation=step.operation,
            status="rendered",
            message=f"rendered {desired_name}",
        ),
        output_path=output_path,
        output_name=desired_name,
    )


def _run_convert_step(
    step: AudioProcessingPresetStep,
    current_path: Path,
    current_filename: str,
    source_filename: str,
    effective_config: AudioProcessingConfig,
    adapters: ProcessingPresetRunnerAdapters,
) -> _StepOutput:
    target_format = effective_config.output_format
    if is_same_visible_format(current_filename, target_format):
        return _StepOutput(
            result=ProcessingPresetStepResult(
                step_id=step.id,
                operation=step.operation,
                status="skipped",
                message=f"already in {format_label(target_format)} format",
            ),
            output_path=None,
            output_name=None,
        )
    desired_name = adapters.make_audio_output_filename(
        source_filename,
        output_format=target_format,
    )
    output_path = adapters.temp_output_path(desired_name)
    completed = False
    try:
        adapters.render_converted_audio(current_path, effective_config, target_format, output_path)
        completed = True
    finally:
        if not completed:
            _remove_temp_parent(output_path)
    return _StepOutput(
        result=ProcessingPresetStepResult(
            step_id=step.id,
            operation=step.operation,
            status="rendered",
            message=f"rendered {desired_name}",
        ),
        output_path=output_path,
        output_name=desired_name,
    )


def _step_output_name(
    operation: str,
    source_filename: str,
    current_filename: str,
    adapters: ProcessingPresetRunnerAdapters,
) -> str:
    if operation == OP_REDUCE_SIZE:
        return adapters.make_audio_output_filename(source_filename, output_format="mp3")
    current_format = visible_extension(current_filename)
    if current_format in CONCRETE_OUTPUT_FORMATS:
        return adapters.make_audio_output_filename(source_filename, output_format=current_format)
    return adapters.make_audio_output_filename(source_filename)


def _graph_config(
    config: AudioProcessingConfig,
    graph: AudioProcessingPresetGraph,
) -> AudioProcessingConfig:
    parameters = graph.parameters
    return replace(
        config,
        graph_voice_range=parameters.graph_voice_range,
        graph_recording_condition=parameters.graph_recording_condition,
        graph_smoothness=parameters.graph_smoothness,
        graph_connect_short_dropouts_ms=parameters.graph_connect_short_dropouts_ms,
        graph_voice_lock=parameters.graph_voice_lock,
    )


def _remove_temp_parent(path: Path) -> None:
    shutil.rmtree(path.parent, ignore_errors=True)
