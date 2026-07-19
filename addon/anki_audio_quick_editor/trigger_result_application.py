"""Apply trigger results to notes and persist completion state."""

from __future__ import annotations

import logging
from typing import Any

from .batch_operation_types import BatchNoteResult
from .diagnostics_runtime import capture_exception
from .error_codes import AQE_BATCH_INVALID_REQUEST, format_coded_message
from .trigger_jobs import (
    STALE_TRIGGER_COMPLETION_MESSAGE,
    TRIGGER_UPDATE_INITIATOR,
    TriggerExecutionResult,
    TriggerJob,
    trigger_source_filename,
)
from .trigger_state import TriggerStateStore, mark_failed, mark_succeeded

logger = logging.getLogger(__name__)


def apply_trigger_result(
    col: Any,
    job: TriggerJob,
    result: BatchNoteResult,
) -> TriggerExecutionResult:
    """Persist a written trigger result when the target fields are unchanged."""
    note = col.get_note(result.note_id)
    if _note_source_filename(note, job.rule.source_field) != job.input_filename:
        return TriggerExecutionResult(stale_trigger_result(job))
    conflict = _apply_result_fields(note, result)
    if conflict is not None:
        return TriggerExecutionResult(conflict)
    changes = col.update_note(note)
    return TriggerExecutionResult(result, changes)


def _apply_result_fields(note: Any, result: BatchNoteResult) -> BatchNoteResult | None:
    if result.field_updates is not None:
        for field_name, expected_html in (result.original_field_html or {}).items():
            if _note_field_value(note, field_name) != expected_html:
                return _conflict_result(result, field_name)
        for field_name, html in result.field_updates.items():
            note[field_name] = html
        return None
    assert result.target_field is not None
    assert result.target_html is not None
    if (
        result.original_target_html is not None
        and _note_field_value(note, result.target_field) != result.original_target_html
    ):
        return _conflict_result(result, result.target_field)
    note[result.target_field] = result.target_html
    return None


def complete_trigger_job(job: TriggerJob, result: BatchNoteResult) -> None:
    """Persist latest trigger completion status."""
    store = TriggerStateStore.load(job.state_path)
    if result.written or is_handled_trigger_skip(result):
        mark_succeeded(
            store,
            job.state_key,
            job.generation_token,
            _handled_source_filename(job, result),
            result.written_filename,
        )
    elif not is_stale_trigger_completion(result):
        mark_failed(store, job.state_key, job.generation_token, result.message)
    store.save()


def publish_trigger_changes(mw: Any, changes: Any) -> None:
    """Notify Anki that trigger-initiated note updates completed."""
    if changes is None:
        return
    try:
        from aqt import gui_hooks

        mw.update_undo_actions()
        gui_hooks.operation_did_execute(changes, TRIGGER_UPDATE_INITIATOR)
    except Exception as exc:  # pragma: no cover - UI refresh is best effort
        capture_exception(
            "trigger.refresh_after_update",
            exc,
            operation="trigger.refresh",
            user_message=str(exc),
            context={"has_changes": changes is not None},
            log=logger,
        )


def is_stale_trigger_completion(result: BatchNoteResult) -> bool:
    """Return whether ``result`` represents a superseded generation."""
    return result.status == "skipped" and result.message == STALE_TRIGGER_COMPLETION_MESSAGE


def is_handled_trigger_skip(result: BatchNoteResult) -> bool:
    """Return whether a skipped trigger still handled the current input."""
    return (
        result.status == "skipped"
        and result.audio_filename is not None
        and not is_stale_trigger_completion(result)
    )


def stale_trigger_result(job: TriggerJob) -> BatchNoteResult:
    """Return the canonical skipped result for a stale trigger job."""
    return BatchNoteResult(
        note_id=job.note_id,
        status="skipped",
        message=STALE_TRIGGER_COMPLETION_MESSAGE,
        audio_filename=job.input_filename,
    )


def _conflict_result(result: BatchNoteResult, field_name: str) -> BatchNoteResult:
    return BatchNoteResult(
        note_id=result.note_id,
        status="failed",
        message=format_coded_message(
            AQE_BATCH_INVALID_REQUEST,
            f"target field {field_name!r} changed during trigger processing",
        ),
        target_field=field_name,
        audio_filename=result.audio_filename,
        image_filename=result.image_filename,
        written_filename=result.written_filename,
        field_updates=result.field_updates,
        original_field_html=result.original_field_html,
    )


def _note_field_value(note: Any, field_name: str) -> str:
    try:
        return str(note[field_name])
    except (KeyError, TypeError, AttributeError):
        return ""


def _note_source_filename(note: Any, source_field: str) -> str | None:
    return trigger_source_filename(_note_field_value(note, source_field))


def _handled_source_filename(job: TriggerJob, result: BatchNoteResult) -> str:
    if result.written:
        source_html = None
        if result.field_updates is not None:
            source_html = result.field_updates.get(job.rule.source_field)
        elif result.target_field == job.rule.source_field:
            source_html = result.target_html
        if source_html is not None:
            output_filename = trigger_source_filename(source_html)
            if output_filename is not None:
                return output_filename
    return result.audio_filename or job.input_filename
