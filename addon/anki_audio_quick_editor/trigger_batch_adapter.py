"""One-note batch operation adapter for trigger automation."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .audio_operations import OP_GRAPH
from .audio_state import AudioProcessingConfig
from .batch_operation_processing import process_graph_operation
from .batch_operation_types import BatchNoteResult, BatchNoteSnapshot, BatchRunRequest
from .batch_operations import MediaWriter, NowProvider, process_note_batch_operation
from .batch_operations_helpers import skipped_batch_note
from .diagnostics_runtime import new_operation_id
from .error_codes import AQE_MEDIA_REFERENCED_AUDIO_MISSING, format_coded_message
from .errors import AudioQuickEditorError
from .media_paths import existing_media_file_path
from .sound_refs import safe_media_basename, select_first_sound_reference
from .trigger_operation_support import trigger_image_reference, trigger_operation_deps
from .trigger_rules import AudioTriggerRule


def process_trigger_operation(
    note: BatchNoteSnapshot,
    *,
    rule: AudioTriggerRule,
    media_dir: Path,
    config: AudioProcessingConfig,
    media_writer: MediaWriter,
    artifact_root: Path | None = None,
    now_provider: NowProvider | None = None,
) -> BatchNoteResult:
    """Run one single-operation trigger rule for ``note``."""
    if rule.action_type != "operation" or rule.operation is None:
        raise ValueError("process_trigger_operation requires an operation trigger rule")

    request = BatchRunRequest(
        operation=rule.operation,
        source_field=rule.source_field,
        target_field=rule.target_field,
        parameters=rule.parameters,
    )
    if rule.operation != OP_GRAPH:
        return process_note_batch_operation(
            note,
            request=request,
            media_dir=media_dir,
            config=config,
            media_writer=media_writer,
            artifact_root=artifact_root,
            now_provider=now_provider,
        )

    prepared = _prepare_graph_source(note, request, media_dir)
    if isinstance(prepared, BatchNoteResult):
        return prepared

    source_path, audio_filename = prepared
    return process_graph_operation(
        note,
        request=request,
        source_path=source_path,
        audio_filename=audio_filename,
        config=_config_with_graph_parameters(config, rule),
        media_writer=media_writer,
        now_provider=now_provider,
        operation_id=new_operation_id("trigger-graph"),
        append_image_reference=lambda _field_html, image_filename: trigger_image_reference(
            image_filename
        ),
        deps=trigger_operation_deps(),
    )


def _prepare_graph_source(
    note: BatchNoteSnapshot,
    request: BatchRunRequest,
    media_dir: Path,
) -> tuple[Path, str] | BatchNoteResult:
    if request.source_field not in note.fields:
        return skipped_batch_note(note.note_id, f"missing source field {request.source_field!r}")
    target_field = request.target_field
    assert target_field is not None
    if target_field not in note.fields:
        return skipped_batch_note(note.note_id, f"missing target field {target_field!r}")

    try:
        selection = select_first_sound_reference(note.fields[request.source_field])
    except AudioQuickEditorError as exc:
        return skipped_batch_note(note.note_id, str(exc))
    if selection.selected is None:
        return skipped_batch_note(
            note.note_id,
            f"source field {request.source_field!r} has no supported sound reference",
        )

    audio_filename = safe_media_basename(selection.selected.filename)
    source_path = existing_media_file_path(media_dir, audio_filename)
    if source_path is None:
        return BatchNoteResult(
            note_id=note.note_id,
            status="failed",
            message=format_coded_message(
                AQE_MEDIA_REFERENCED_AUDIO_MISSING,
                f"media file not found: {audio_filename}",
            ),
            audio_filename=audio_filename,
        )
    return source_path, audio_filename


def _config_with_graph_parameters(
    config: AudioProcessingConfig,
    rule: AudioTriggerRule,
) -> AudioProcessingConfig:
    graph = rule.graph_parameters
    return replace(
        config,
        graph_voice_range=(
            graph.graph_voice_range
            if graph.graph_voice_range is not None
            else config.graph_voice_range
        ),
        graph_recording_condition=(
            graph.graph_recording_condition
            if graph.graph_recording_condition is not None
            else config.graph_recording_condition
        ),
        graph_smoothness=(
            graph.graph_smoothness
            if graph.graph_smoothness is not None
            else config.graph_smoothness
        ),
        graph_connect_short_dropouts_ms=(
            graph.graph_connect_short_dropouts_ms
            if graph.graph_connect_short_dropouts_ms is not None
            else config.graph_connect_short_dropouts_ms
        ),
        graph_voice_lock=(
            graph.graph_voice_lock
            if graph.graph_voice_lock is not None
            else config.graph_voice_lock
        ),
    )
