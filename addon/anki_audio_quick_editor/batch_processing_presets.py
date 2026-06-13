"""Preset processing for Browser batch operations."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .audio_processing_preset_runner import (
    ProcessingPresetRunResult,
    run_processing_preset,
)
from .audio_state import AudioProcessingConfig
from .batch_operation_processing import BatchOperationDeps, batch_preset_runner_adapters
from .batch_operation_types import BatchNoteResult, BatchNoteSnapshot, BatchRunRequest
from .batch_operations_helpers import skipped_batch_note
from .sound_refs import SoundReference, replace_sound_reference

MediaWriter = Callable[[str, bytes], str]
AppendImageReference = Callable[[str, str], str]


@dataclass(frozen=True)
class _PresetFieldWrites:
    field_updates: dict[str, str]
    original_field_html: dict[str, str]
    written_audio_name: str | None
    written_graph_name: str | None


def process_preset_operation(
    note: BatchNoteSnapshot,
    *,
    request: BatchRunRequest,
    source_html: str,
    source_path: Path,
    selection: SoundReference,
    audio_filename: str,
    config: AudioProcessingConfig,
    media_writer: MediaWriter,
    artifact_root: Path | None,
    append_image_reference: AppendImageReference,
    deps: BatchOperationDeps,
) -> BatchNoteResult:
    assert request.preset is not None
    result: ProcessingPresetRunResult | None = None
    missing_target = _missing_configured_preset_target_result(note, request)
    if missing_target is not None:
        return missing_target
    try:
        result = _run_batch_processing_preset(
            request,
            source_path=source_path,
            audio_filename=audio_filename,
            config=config,
            artifact_root=artifact_root,
            deps=deps,
        )
        writes = _write_preset_field_updates(
            note,
            request=request,
            result=result,
            source_html=source_html,
            selection=selection,
            media_writer=media_writer,
            append_image_reference=append_image_reference,
        )
    except Exception as exc:
        return BatchNoteResult(
            note_id=note.note_id,
            status="failed",
            message=str(exc) or f"preset {request.preset.name!r} failed",
            audio_filename=audio_filename,
        )
    finally:
        _cleanup_preset_run(result)

    return _preset_batch_result(note, request, writes, audio_filename)


def _missing_configured_preset_target_result(
    note: BatchNoteSnapshot,
    request: BatchRunRequest,
) -> BatchNoteResult | None:
    assert request.preset is not None
    if request.preset.has_transforms:
        audio_target_field = request.audio_target_field
        assert audio_target_field is not None
        if audio_target_field not in note.fields:
            return skipped_batch_note(note.note_id, f"missing target field {audio_target_field!r}")
    if request.preset.graph.enabled:
        graph_target_field = request.graph_target_field
        assert graph_target_field is not None
        if graph_target_field not in note.fields:
            return skipped_batch_note(note.note_id, f"missing target field {graph_target_field!r}")
    return None


def _run_batch_processing_preset(
    request: BatchRunRequest,
    *,
    source_path: Path,
    audio_filename: str,
    config: AudioProcessingConfig,
    artifact_root: Path | None,
    deps: BatchOperationDeps,
) -> ProcessingPresetRunResult:
    assert request.preset is not None
    return run_processing_preset(
        request.preset,
        source_path=source_path,
        source_filename=audio_filename,
        config=config,
        adapters=batch_preset_runner_adapters(deps),
        artifact_root=artifact_root,
    )

def _write_preset_field_updates(
    note: BatchNoteSnapshot,
    *,
    request: BatchRunRequest,
    result: ProcessingPresetRunResult,
    source_html: str,
    selection: SoundReference,
    media_writer: MediaWriter,
    append_image_reference: AppendImageReference,
) -> _PresetFieldWrites:
    field_updates: dict[str, str] = {}
    original_field_html: dict[str, str] = {}
    written_audio_name = _write_preset_audio_update(
        note,
        request=request,
        result=result,
        source_html=source_html,
        selection=selection,
        media_writer=media_writer,
        field_updates=field_updates,
        original_field_html=original_field_html,
    )
    written_graph_name = _write_preset_graph_update(
        note,
        request=request,
        result=result,
        media_writer=media_writer,
        field_updates=field_updates,
        original_field_html=original_field_html,
        append_image_reference=append_image_reference,
    )
    return _PresetFieldWrites(
        field_updates=field_updates,
        original_field_html=original_field_html,
        written_audio_name=written_audio_name,
        written_graph_name=written_graph_name,
    )


def _write_preset_audio_update(
    note: BatchNoteSnapshot,
    *,
    request: BatchRunRequest,
    result: ProcessingPresetRunResult,
    source_html: str,
    selection: SoundReference,
    media_writer: MediaWriter,
    field_updates: dict[str, str],
    original_field_html: dict[str, str],
) -> str | None:
    if result.final_audio_path is None or result.final_audio_name is None:
        return None
    audio_target_field = request.audio_target_field
    assert audio_target_field is not None
    with result.final_audio_path.open("rb") as file:
        written_audio_name = media_writer(result.final_audio_name, file.read())
    original_field_html[audio_target_field] = note.fields[audio_target_field]
    field_updates[audio_target_field] = replace_sound_reference(
        source_html,
        selection,
        written_audio_name,
    )
    return written_audio_name


def _write_preset_graph_update(
    note: BatchNoteSnapshot,
    *,
    request: BatchRunRequest,
    result: ProcessingPresetRunResult,
    media_writer: MediaWriter,
    field_updates: dict[str, str],
    original_field_html: dict[str, str],
    append_image_reference: AppendImageReference,
) -> str | None:
    if result.graph_svg is None or result.graph_name is None:
        return None
    graph_target_field = request.graph_target_field
    assert graph_target_field is not None
    written_graph_name = media_writer(result.graph_name, result.graph_svg)
    base_html = field_updates.get(graph_target_field, note.fields[graph_target_field])
    original_field_html.setdefault(graph_target_field, note.fields[graph_target_field])
    field_updates[graph_target_field] = append_image_reference(base_html, written_graph_name)
    return written_graph_name


def _preset_batch_result(
    note: BatchNoteSnapshot,
    request: BatchRunRequest,
    writes: _PresetFieldWrites,
    audio_filename: str,
) -> BatchNoteResult:
    assert request.preset is not None
    if not writes.field_updates:
        return BatchNoteResult(
            note_id=note.note_id,
            status="skipped",
            message="nothing to change",
            audio_filename=audio_filename,
        )
    return BatchNoteResult(
        note_id=note.note_id,
        status="written",
        message=f"ran preset {request.preset.name}",
        target_field=next(iter(writes.field_updates)),
        target_html=next(iter(writes.field_updates.values())),
        audio_filename=audio_filename,
        image_filename=writes.written_graph_name,
        written_filename=writes.written_audio_name or writes.written_graph_name,
        field_updates=writes.field_updates,
        original_field_html=writes.original_field_html,
    )


def _cleanup_preset_run(result: ProcessingPresetRunResult | None) -> None:
    if result is not None and result.final_audio_path is not None:
        shutil.rmtree(result.final_audio_path.parent, ignore_errors=True)
