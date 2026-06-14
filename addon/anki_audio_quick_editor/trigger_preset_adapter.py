"""One-note processing preset adapter for trigger automation."""

from __future__ import annotations

from pathlib import Path

from .audio_operations import OP_PRESET
from .audio_processing_presets import AudioProcessingPreset, preset_by_id
from .audio_state import AudioProcessingConfig
from .batch_operation_types import BatchNoteResult, BatchNoteSnapshot, BatchRunRequest
from .batch_operations import MediaWriter
from .batch_operations_helpers import skipped_batch_note
from .batch_processing_presets import process_preset_operation
from .diagnostics_runtime import new_operation_id
from .error_codes import AQE_MEDIA_REFERENCED_AUDIO_MISSING, format_coded_message
from .errors import AudioQuickEditorError
from .media_paths import existing_media_file_path
from .sound_refs import (
    SoundReference,
    safe_media_basename,
    select_first_sound_reference,
)
from .trigger_operation_support import trigger_image_reference, trigger_operation_deps
from .trigger_rules import AudioTriggerRule


def process_trigger_preset(
    note: BatchNoteSnapshot,
    *,
    rule: AudioTriggerRule,
    presets: tuple[AudioProcessingPreset, ...],
    media_dir: Path,
    config: AudioProcessingConfig,
    media_writer: MediaWriter,
    artifact_root: Path | None = None,
) -> BatchNoteResult:
    """Run one preset trigger rule for ``note``."""
    if rule.action_type != "preset" or rule.preset_id is None:
        raise ValueError("process_trigger_preset requires a preset trigger rule")

    preset = _resolved_preset(rule, presets)
    if preset is None:
        return skipped_batch_note(note.note_id, f"missing preset {rule.preset_id!r}")

    request = BatchRunRequest(
        operation=OP_PRESET,
        source_field=rule.source_field,
        preset_id=rule.preset_id,
        preset=preset,
        audio_target_field=rule.source_field if preset.has_transforms else None,
        graph_target_field=rule.target_field if preset.graph.enabled else None,
    )
    prepared = _prepare_preset_source(note, request, media_dir)
    if isinstance(prepared, BatchNoteResult):
        return prepared
    source_html, source_path, selection, audio_filename = prepared

    return process_preset_operation(
        note,
        request=request,
        source_html=source_html,
        source_path=source_path,
        selection=selection,
        audio_filename=audio_filename,
        config=config,
        media_writer=media_writer,
        artifact_root=artifact_root,
        append_image_reference=lambda _field_html, image_filename: trigger_image_reference(
            image_filename
        ),
        deps=trigger_operation_deps(),
        operation_id=new_operation_id("trigger-preset"),
    )


def _resolved_preset(
    rule: AudioTriggerRule,
    presets: tuple[AudioProcessingPreset, ...],
) -> AudioProcessingPreset | None:
    assert rule.preset_id is not None
    try:
        return preset_by_id(presets, rule.preset_id)
    except ValueError:
        return None


def _prepare_preset_source(
    note: BatchNoteSnapshot,
    request: BatchRunRequest,
    media_dir: Path,
) -> tuple[str, Path, SoundReference, str] | BatchNoteResult:
    if request.source_field not in note.fields:
        return skipped_batch_note(note.note_id, f"missing source field {request.source_field!r}")
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
    return (
        note.fields[request.source_field],
        source_path,
        selection.selected,
        audio_filename,
    )
