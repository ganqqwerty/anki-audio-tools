"""Graph and transform processors for Browser batch operations."""

from __future__ import annotations

import logging
import shutil
from collections.abc import Callable
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Any

from .audio_formats import format_label, is_same_visible_format
from .audio_operation_params import effective_config_for_operation
from .audio_operations import OP_CONVERT, OP_DENOISE, apply_audio_operation
from .audio_processor import (
    make_output_filename,
    temp_final_path,
)
from .audio_state import AudioEditState, AudioProcessingConfig
from .batch_operation_types import BatchNoteResult, BatchNoteSnapshot, BatchRunRequest
from .batch_operations_helpers import render_batch_denoise
from .diagnostics_runtime import capture_exception
from .permission_guidance import message_with_permission_guidance
from .prosody_svg import make_visualization_filename, render_prosody_svg
from .sound_refs import SoundReference, replace_sound_reference

logger = logging.getLogger(__name__)


def _facade_attr(name: str) -> Any:
    facade = import_module(".batch_operations", package=__package__)
    return getattr(facade, name)


def process_graph_operation(
    note: BatchNoteSnapshot,
    *,
    request: BatchRunRequest,
    source_path: Path,
    audio_filename: str,
    config: AudioProcessingConfig,
    media_writer: Callable[[str, bytes], str],
    now_provider: Callable[[], datetime] | None,
    operation_id: str,
    append_image_reference: Callable[[str, str], str],
) -> BatchNoteResult:
    target_field = request.target_field
    assert target_field is not None
    try:
        track = _facade_attr("analyze_prosody_cached")(source_path, config)
        svg_bytes = render_prosody_svg(track)
        desired_name = make_visualization_filename(
            audio_filename,
            now=(now_provider() if now_provider else None),
        )
        saved_name = media_writer(desired_name, svg_bytes)
    except Exception as exc:
        raw_message = str(exc)
        message = (
            message_with_permission_guidance(raw_message, exc)
            if raw_message
            else "visualization generation failed"
        )
        capture_exception(
            "browser.batch.note_graph",
            exc,
            operation="browser.batch.graph",
            operation_id=operation_id,
            user_message=message,
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
            message=message,
            audio_filename=audio_filename,
        )

    return BatchNoteResult(
        note_id=note.note_id,
        status="written",
        message=f"appended {saved_name}",
        target_field=target_field,
        target_html=append_image_reference(note.fields[target_field], saved_name),
        original_target_html=note.fields[target_field],
        audio_filename=audio_filename,
        image_filename=saved_name,
        written_filename=saved_name,
    )


def process_transform_operation(
    note: BatchNoteSnapshot,
    *,
    request: BatchRunRequest,
    source_html: str,
    source_path: Path,
    selection: SoundReference,
    audio_filename: str,
    config: AudioProcessingConfig,
    media_writer: Callable[[str, bytes], str],
    artifact_root: Path | None,
    operation_id: str,
) -> BatchNoteResult:
    output_path: Path | None = None
    try:
        effective_config = effective_config_for_operation(
            request.operation,
            config,
            request.parameters,
        )
        if request.operation == OP_CONVERT:
            target_format = effective_config.output_format
            if is_same_visible_format(audio_filename, target_format):
                return BatchNoteResult(
                    note_id=note.note_id,
                    status="skipped",
                    message=f"already in {format_label(target_format)} format",
                    audio_filename=audio_filename,
                )
            desired_name = make_output_filename(audio_filename, output_format=target_format)
            output_path = temp_final_path(desired_name)
            _facade_attr("render_converted_audio")(
                source_path,
                effective_config,
                target_format,
                output_path=output_path,
            )
        else:
            desired_name = make_output_filename(audio_filename)
            output_path = temp_final_path(desired_name)
            if request.operation == OP_DENOISE:
                render_batch_denoise(source_path, effective_config, output_path)
            else:
                updated_state = apply_audio_operation(
                    request.operation,
                    AudioEditState(source_file=audio_filename),
                    effective_config,
                )
                _facade_attr("render_audio")(
                    source_path,
                    updated_state,
                    effective_config,
                    output_path=output_path,
                    artifact_root=artifact_root,
                )
        with output_path.open("rb") as file:
            saved_name = media_writer(desired_name, file.read())
        replaced_html = replace_sound_reference(source_html, selection, saved_name)
    except Exception as exc:
        raw_message = str(exc)
        message = (
            message_with_permission_guidance(raw_message, exc)
            if raw_message
            else "audio transformation failed"
        )
        capture_exception(
            "browser.batch.note_transform",
            exc,
            operation=f"browser.batch.{request.operation}",
            operation_id=operation_id,
            user_message=message,
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
            message=message,
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
        original_target_html=source_html,
        audio_filename=audio_filename,
        written_filename=saved_name,
    )
