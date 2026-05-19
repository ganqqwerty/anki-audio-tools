"""Import-safe batch operation planning and per-note execution."""

from __future__ import annotations

import html
import logging
import shutil
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .audio_operations import (
    OP_GRAPH,
    apply_audio_operation,
    is_transform_operation,
    requires_target_field,
    validate_operation,
)
from .audio_processor import make_output_filename, render_audio, temp_final_path
from .audio_state import AudioEditState, AudioProcessingConfig
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .errors import AudioQuickEditorError
from .prosody_cache import analyze_prosody_cached
from .prosody_svg import make_visualization_filename, render_prosody_svg
from .sound_refs import (
    SoundReference,
    replace_sound_reference,
    safe_media_basename,
    select_first_sound_reference,
)

MediaWriter = Callable[[str, bytes], str]
NowProvider = Callable[[], datetime]
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BatchRunRequest:
    """One validated batch operation request selected by the Browser UI."""

    operation: str
    source_field: str
    target_field: str | None = None

    def __post_init__(self) -> None:
        operation = validate_operation(self.operation)
        object.__setattr__(self, "operation", operation)
        if not self.source_field:
            raise ValueError("Choose a source field before starting.")
        if requires_target_field(operation) and not self.target_field:
            raise ValueError("Choose a target field before starting.")


@dataclass(frozen=True)
class BatchNoteSnapshot:
    """Minimal note data needed by import-safe batch logic."""

    note_id: int
    notetype_name: str
    fields: dict[str, str]


@dataclass(frozen=True)
class FieldGroup:
    """Fields available on one note type in the current batch selection."""

    notetype_name: str
    fields: tuple[str, ...]


@dataclass(frozen=True)
class BatchNoteResult:
    """Outcome of processing one note snapshot."""

    note_id: int
    status: str
    message: str
    target_field: str | None = None
    target_html: str | None = None
    audio_filename: str | None = None
    image_filename: str | None = None
    written_filename: str | None = None

    @property
    def written(self) -> bool:
        """Return true when the caller should persist ``target_html``."""
        return self.status == "written"

    @property
    def failure(self) -> bool:
        """Return true when this result should increment the failure count."""
        return self.status == "failed"


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
        return _skipped(note, f"missing source field {request.source_field!r}")

    source_html = note.fields[request.source_field]
    try:
        selection = select_first_sound_reference(source_html)
    except AudioQuickEditorError as exc:
        return _skipped(note, str(exc))
    if selection.selected is None:
        return _skipped(
            note,
            f"source field {request.source_field!r} has no supported sound reference",
        )

    audio_filename = safe_media_basename(selection.selected.filename)
    if request.operation == OP_GRAPH:
        target_field = request.target_field
        assert target_field is not None
        if target_field not in note.fields:
            return _skipped(note, f"missing target field {target_field!r}")
    source_path = media_dir / audio_filename
    if not source_path.is_file():
        return BatchNoteResult(
            note_id=note.note_id,
            status="failed",
            message=f"media file not found: {audio_filename}",
            audio_filename=audio_filename,
        )

    if request.operation == OP_GRAPH:
        return _process_graph_operation(
            note,
            request=request,
            source_path=source_path,
            audio_filename=audio_filename,
            config=config,
            media_writer=media_writer,
            now_provider=now_provider,
            operation_id=operation_id,
        )

    if is_transform_operation(request.operation):
        return _process_transform_operation(
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


def _process_graph_operation(
    note: BatchNoteSnapshot,
    *,
    request: BatchRunRequest,
    source_path: Path,
    audio_filename: str,
    config: AudioProcessingConfig,
    media_writer: MediaWriter,
    now_provider: NowProvider | None,
    operation_id: str,
) -> BatchNoteResult:
    target_field = request.target_field
    assert target_field is not None
    try:
        track = analyze_prosody_cached(source_path, config)
        svg_bytes = render_prosody_svg(track)
        desired_name = make_visualization_filename(
            audio_filename,
            now=(now_provider() if now_provider else None),
        )
        saved_name = media_writer(desired_name, svg_bytes)
    except Exception as exc:
        capture_exception(
            "browser.batch.note_graph",
            exc,
            operation="browser.batch.graph",
            operation_id=operation_id,
            user_message=str(exc) or "visualization generation failed",
            context={
                "note_id": note.note_id,
                "source_field": request.source_field,
                "target_field": request.target_field,
                "audio_filename": audio_filename,
            },
            log=logger,
        )
        return BatchNoteResult(
            note_id=note.note_id,
            status="failed",
            message=str(exc) or "visualization generation failed",
            audio_filename=audio_filename,
        )

    return BatchNoteResult(
        note_id=note.note_id,
        status="written",
        message=f"appended {saved_name}",
        target_field=target_field,
        target_html=append_image_reference(note.fields[target_field], saved_name),
        audio_filename=audio_filename,
        image_filename=saved_name,
        written_filename=saved_name,
    )


def _process_transform_operation(
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
    operation_id: str,
) -> BatchNoteResult:
    output_path: Path | None = None
    try:
        updated_state = apply_audio_operation(
            request.operation,
            AudioEditState(source_file=audio_filename),
            config,
        )
        desired_name = make_output_filename(audio_filename)
        output_path = temp_final_path(desired_name)
        render_audio(
            source_path,
            updated_state,
            config,
            output_path=output_path,
            artifact_root=artifact_root,
        )
        with output_path.open("rb") as file:
            saved_name = media_writer(desired_name, file.read())
        replaced_html = replace_sound_reference(source_html, selection, saved_name)
    except Exception as exc:
        capture_exception(
            "browser.batch.note_transform",
            exc,
            operation=f"browser.batch.{request.operation}",
            operation_id=operation_id,
            user_message=str(exc) or "audio transformation failed",
            context={
                "note_id": note.note_id,
                "source_field": request.source_field,
                "audio_filename": audio_filename,
            },
            log=logger,
        )
        return BatchNoteResult(
            note_id=note.note_id,
            status="failed",
            message=str(exc) or "audio transformation failed",
            audio_filename=audio_filename,
        )
    finally:
        if output_path is not None:
            shutil.rmtree(output_path.parent, ignore_errors=True)

    return BatchNoteResult(
        note_id=note.note_id,
        status="written",
        message=f"replaced audio with {saved_name}",
        target_field=request.source_field,
        target_html=replaced_html,
        audio_filename=audio_filename,
        written_filename=saved_name,
    )


def _skipped(note: BatchNoteSnapshot, message: str) -> BatchNoteResult:
    return BatchNoteResult(note_id=note.note_id, status="skipped", message=message)
