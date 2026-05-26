"""Import-safe batch operation planning and per-note execution."""

from __future__ import annotations

import html
import logging
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path

from .audio_operations import OP_GRAPH, is_transform_operation
from .audio_processor import (
    render_audio,
    render_converted_audio,
    render_dpdfnet_audio,
    render_noise_reduced_audio,
    render_rnnoise_audio,
    render_voice_only_audio,
)
from .audio_state import AudioProcessingConfig
from .batch_operation_processing import (
    process_graph_operation,
    process_transform_operation,
)
from .batch_operation_types import (
    BatchNoteResult,
    BatchNoteSnapshot,
    BatchRunRequest,
    FieldGroup,
)
from .batch_operations_helpers import skipped_batch_note
from .diagnostics_runtime import new_operation_id, record_breadcrumb
from .errors import AudioQuickEditorError
from .media_paths import existing_media_file_path
from .prosody_cache import analyze_prosody_cached
from .sound_refs import (
    safe_media_basename,
    select_first_sound_reference,
)

MediaWriter = Callable[[str, bytes], str]
NowProvider = Callable[[], datetime]
logger = logging.getLogger(__name__)
__all__ = [
    "BatchNoteResult",
    "BatchNoteSnapshot",
    "BatchRunRequest",
    "FieldGroup",
    "MediaWriter",
    "NowProvider",
    "analyze_prosody_cached",
    "append_image_reference",
    "field_groups_for_notes",
    "first_audio_filename",
    "process_note_batch_operation",
    "render_audio",
    "render_converted_audio",
    "render_dpdfnet_audio",
    "render_noise_reduced_audio",
    "render_rnnoise_audio",
    "render_voice_only_audio",
    "unique_note_ids",
]


def unique_note_ids(note_ids: Sequence[int]) -> list[int]:
    """Return note IDs once, preserving first-seen order."""
    seen: set[int] = set()
    deduped: list[int] = []
    for note_id in note_ids:
        value = int(note_id)
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def field_groups_for_notes(notes: Sequence[BatchNoteSnapshot]) -> tuple[FieldGroup, ...]:
    """Return field choices grouped by note type from selected note snapshots."""
    grouped: dict[str, list[str]] = {}
    for note in notes:
        fields = grouped.setdefault(note.notetype_name, [])
        for field_name in note.fields:
            if field_name not in fields:
                fields.append(field_name)
    return tuple(
        FieldGroup(notetype_name=name, fields=tuple(fields))
        for name, fields in sorted(grouped.items(), key=lambda item: item[0].casefold())
    )


def append_image_reference(field_html: str, image_filename: str) -> str:
    """Append an Anki image media reference on a new visual line."""
    image_tag = f'<img src="{html.escape(image_filename, quote=True)}">'
    return f"{field_html}<br>{image_tag}" if field_html else image_tag


def first_audio_filename(note: BatchNoteSnapshot, source_field: str) -> str | None:
    """Return the selected source audio filename for progress display, if available."""
    if source_field not in note.fields:
        return None
    try:
        selection = select_first_sound_reference(note.fields[source_field])
    except AudioQuickEditorError:
        return None
    if selection.selected is None:
        return None
    return safe_media_basename(selection.selected.filename)


def process_note_batch_operation(
    note: BatchNoteSnapshot,
    *,
    request: BatchRunRequest,
    media_dir: Path,
    config: AudioProcessingConfig,
    media_writer: MediaWriter,
    artifact_root: Path | None = None,
    now_provider: NowProvider | None = None,
) -> BatchNoteResult:
    """Process one batch operation for ``note``."""
    operation_id = new_operation_id("batch-note")
    record_breadcrumb(
        "browser.batch.note_started",
        source="browser",
        operation="browser.batch",
        operation_id=operation_id,
        context={
            "note_id": note.note_id,
            "operation": request.operation,
            "source_field": request.source_field,
            "target_field": request.target_field,
        },
    )
    if request.source_field not in note.fields:
        return skipped_batch_note(note.note_id, f"missing source field {request.source_field!r}")

    source_html = note.fields[request.source_field]
    try:
        selection = select_first_sound_reference(source_html)
    except AudioQuickEditorError as exc:
        return skipped_batch_note(note.note_id, str(exc))
    if selection.selected is None:
        return skipped_batch_note(
            note.note_id,
            f"source field {request.source_field!r} has no supported sound reference",
        )

    audio_filename = safe_media_basename(selection.selected.filename)
    if request.operation == OP_GRAPH:
        target_field = request.target_field
        assert target_field is not None
        if target_field not in note.fields:
            return skipped_batch_note(note.note_id, f"missing target field {target_field!r}")
    source_path = existing_media_file_path(media_dir, audio_filename)
    if source_path is None:
        return BatchNoteResult(
            note_id=note.note_id,
            status="failed",
            message=f"media file not found: {audio_filename}",
            audio_filename=audio_filename,
        )

    if request.operation == OP_GRAPH:
        return process_graph_operation(
            note,
            request=request,
            source_path=source_path,
            audio_filename=audio_filename,
            config=config,
            media_writer=media_writer,
            now_provider=now_provider,
            operation_id=operation_id,
            append_image_reference=append_image_reference,
        )

    if is_transform_operation(request.operation):
        return process_transform_operation(
            note,
            request=request,
            source_html=source_html,
            source_path=source_path,
            selection=selection.selected,
            audio_filename=audio_filename,
            config=config,
            media_writer=media_writer,
            artifact_root=artifact_root,
            operation_id=operation_id,
        )

    raise ValueError(f"Unsupported batch operation: {request.operation}")
