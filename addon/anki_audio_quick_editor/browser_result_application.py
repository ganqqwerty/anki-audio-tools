"""Apply Browser batch note results to the Anki collection."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .batch_operation_types import BatchNoteResult
from .browser_report import BatchRunReport
from .diagnostics_runtime import capture_exception
from .error_codes import AQE_BATCH_INVALID_REQUEST, format_coded_message

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _FieldConflict:
    field_name: str
    expected_html: str


def apply_result(
    col: Any,
    report: BatchRunReport,
    result: BatchNoteResult,
    fallback_field: str,
) -> BatchNoteResult:
    """Apply one batch note result to the collection and report counters."""
    if result.written:
        return _apply_written_result(col, report, result, fallback_field)
    if result.failure:
        report.failures += 1
    else:
        report.skipped += 1
    return result


def _apply_written_result(
    col: Any,
    report: BatchRunReport,
    result: BatchNoteResult,
    fallback_field: str,
) -> BatchNoteResult:
    try:
        note = col.get_note(result.note_id)
        if result.field_updates is not None:
            return _apply_multi_field_result(col, report, result, note)
        return _apply_single_field_result(col, report, result, note)
    except Exception as exc:
        return _failed_apply_result(report, result, fallback_field, exc)


def _apply_multi_field_result(
    col: Any,
    report: BatchRunReport,
    result: BatchNoteResult,
    note: Any,
) -> BatchNoteResult:
    conflict = _multi_field_conflict(note, result)
    if conflict is not None:
        report.failures += 1
        return _field_conflict_result(result, conflict)
    assert result.field_updates is not None
    for field_name, html in result.field_updates.items():
        note[field_name] = html
    col.update_note(note)
    report.written += 1
    return result


def _multi_field_conflict(note: Any, result: BatchNoteResult) -> _FieldConflict | None:
    for field_name, expected_html in (result.original_field_html or {}).items():
        if _note_field_value(note, field_name) != expected_html:
            return _FieldConflict(field_name=field_name, expected_html=expected_html)
    return None


def _apply_single_field_result(
    col: Any,
    report: BatchRunReport,
    result: BatchNoteResult,
    note: Any,
) -> BatchNoteResult:
    assert result.target_field is not None
    assert result.target_html is not None
    conflict = _single_field_conflict(note, result)
    if conflict is not None:
        report.failures += 1
        return _field_conflict_result(result, conflict)
    note[result.target_field] = result.target_html
    col.update_note(note)
    report.written += 1
    return result


def _single_field_conflict(note: Any, result: BatchNoteResult) -> _FieldConflict | None:
    if result.original_target_html is None:
        return None
    assert result.target_field is not None
    current_html = _note_field_value(note, result.target_field)
    if current_html != result.original_target_html:
        return _FieldConflict(
            field_name=result.target_field,
            expected_html=result.original_target_html,
        )
    return None


def _field_conflict_result(
    result: BatchNoteResult,
    conflict: _FieldConflict,
) -> BatchNoteResult:
    message = format_coded_message(
        AQE_BATCH_INVALID_REQUEST,
        f"target field {conflict.field_name!r} changed during batch processing",
    )
    return BatchNoteResult(
        note_id=result.note_id,
        status="failed",
        message=message,
        target_field=conflict.field_name,
        target_html=_target_html_for_conflict(result, conflict.field_name),
        audio_filename=result.audio_filename,
        image_filename=result.image_filename,
        written_filename=result.written_filename,
        original_target_html=conflict.expected_html,
        field_updates=result.field_updates,
        original_field_html=result.original_field_html,
    )


def _target_html_for_conflict(result: BatchNoteResult, field_name: str) -> str | None:
    if result.field_updates is None:
        return result.target_html
    return result.field_updates.get(field_name)


def _failed_apply_result(
    report: BatchRunReport,
    result: BatchNoteResult,
    fallback_field: str,
    exc: Exception,
) -> BatchNoteResult:
    message = format_coded_message(
        AQE_BATCH_INVALID_REQUEST,
        str(exc) or f"failed to update target field {fallback_field!r}",
    )
    capture_exception(
        "browser.batch.apply_result",
        exc,
        operation=f"browser.batch.{result.status}",
        user_message=message,
        context={
            "note_id": result.note_id,
            "target_field": result.target_field,
            "fallback_field": fallback_field,
            "audio_filename": result.audio_filename,
            "written_filename": result.written_filename,
        },
        log=logger,
    )
    report.failures += 1
    return BatchNoteResult(
        note_id=result.note_id,
        status="failed",
        message=message,
        target_field=result.target_field,
        target_html=result.target_html,
        audio_filename=result.audio_filename,
        image_filename=result.image_filename,
        written_filename=result.written_filename,
        original_target_html=result.original_target_html,
    )


def _note_field_value(note: Any, field_name: str) -> str:
    try:
        return str(note[field_name])
    except (KeyError, TypeError, AttributeError):
        fields = getattr(note, "fields", None)
        if isinstance(fields, dict):
            return str(fields[field_name])
        raise
