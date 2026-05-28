"""Browser batch operation execution and persistence."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

from .audio_state import AudioProcessingConfig
from .batch_operations import (
    BatchNoteResult,
    BatchNoteSnapshot,
    BatchRunRequest,
    first_audio_filename,
    process_note_batch_operation,
)
from .browser_report import BatchRunReport, format_result_line
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .error_codes import AQE_BATCH_INVALID_REQUEST, coded_error, format_coded_message
from .i18n import active_context, format_message

logger = logging.getLogger(__name__)


def snapshot_from_note(note: Any) -> BatchNoteSnapshot:
    """Return the batch snapshot for an Anki note."""
    notetype = note.note_type()
    notetype_name = str(notetype.get("name", "Unknown")) if isinstance(notetype, dict) else "Unknown"
    return BatchNoteSnapshot(
        note_id=int(note.id),
        notetype_name=notetype_name,
        fields={str(name): str(value) for name, value in note.items()},
    )


def run_batch_in_background(
    browser: Any,
    dialog: Any,
    note_ids: list[int],
    request: BatchRunRequest,
) -> None:
    """Schedule a browser batch run in Anki's background task manager."""
    operation_id = new_operation_id("batch")
    mw = browser.mw
    config = AudioProcessingConfig.from_config(
        mw.addonManager.getConfig(mw.addonManager.addonFromModule(__name__)) or {}
    )
    media_dir = Path(mw.col.media.dir())
    artifact_root = Path(
        mw.addonManager.addonsFolder(mw.addonManager.addonFromModule(__name__))
    ) / "aqe_artifacts"

    def on_log(line: str) -> None:
        logger.info("batch operation: %s", line)
        mw.taskman.run_on_main(lambda value=line: dialog.append_log(value))

    def on_progress(processed: int, total: int, current_audio: str, failures: int) -> None:
        mw.taskman.run_on_main(
            lambda: dialog.update_progress(processed, total, current_audio, failures)
        )

    def task() -> BatchRunReport:
        record_breadcrumb(
            "browser.batch.started",
            source="browser",
            operation="browser.batch",
            operation_id=operation_id,
            context={
                "note_count": len(note_ids),
                "operation": request.operation,
                "source_field": request.source_field,
                "target_field": request.target_field,
            },
            flush=True,
        )
        return run_batch(
            mw.col,
            note_ids,
            request,
            media_dir,
            config,
            dialog.cancel_event,
            on_log,
            on_progress,
            artifact_root=artifact_root,
        )

    def done(future: Any) -> None:
        try:
            report = future.result()
        except Exception as exc:
            message = _tr("batch.failed", {"error": exc})
            capture_exception(
                "browser.batch.worker",
                exc,
                operation="browser.batch",
                operation_id=operation_id,
                user_message=format_coded_message(AQE_BATCH_INVALID_REQUEST, message),
                context={"note_count": len(note_ids), "operation": request.operation},
                log=logger,
            )
            dialog.finish_with_error(
                message,
                user_error=coded_error(AQE_BATCH_INVALID_REQUEST, message),
            )
            return
        publish_collection_changes(browser, report.changes)
        logger.info("batch operation finished: %s", report.summary)
        dialog.finish_with_report(report)

    mw.taskman.run_in_background(task, done, uses_collection=True)


def run_batch(
    col: Any,
    note_ids: list[int],
    request: BatchRunRequest,
    media_dir: Path,
    config: AudioProcessingConfig,
    cancel_event: threading.Event,
    on_log: Any,
    on_progress: Any,
    artifact_root: Path | None = None,
) -> BatchRunReport:
    """Run a browser batch operation against a selected note id list."""
    messages = dict(active_context()["messages"])
    report = BatchRunReport(total=len(note_ids), messages=messages)
    undo_entry: int | None = None
    last_audio = ""

    report.add(
        format_message(
            messages,
            "batch.log.starting",
            {
                "total": len(note_ids),
                "operation": repr(request.operation),
                "source": repr(request.source_field),
                "target": repr(request.target_field),
                "parameters": _format_parameters(request),
            },
        )
    )
    on_log(report.log_lines[-1])

    for note_id in note_ids:
        if cancel_event.is_set():
            report.canceled = True
            report.add(format_message(messages, "batch.log.canceled"))
            on_log(report.log_lines[-1])
            break

        note_result = process_note(
            col,
            int(note_id),
            request,
            media_dir,
            config,
            artifact_root,
        )
        last_audio = note_result.audio_filename or last_audio
        if note_result.written and undo_entry is None:
            undo_entry = col.add_custom_undo_entry(format_message(messages, "batch.undo_label"))
        note_result = apply_result(
            col,
            report,
            note_result,
            request.target_field or request.source_field,
        )
        report.processed += 1
        line = format_result_line(note_result, messages)
        report.add(line)
        on_log(line)
        on_progress(report.processed, report.total, last_audio, report.failures)

    if undo_entry is not None:
        report.changes = col.merge_undo_entries(undo_entry)

    report.add(report.summary)
    return report


def process_note(
    col: Any,
    note_id: int,
    request: BatchRunRequest,
    media_dir: Path,
    config: AudioProcessingConfig,
    artifact_root: Path | None = None,
) -> BatchNoteResult:
    """Process one note snapshot for a browser batch request."""
    try:
        note = col.get_note(note_id)
        snapshot = snapshot_from_note(note)
    except Exception as exc:
        message = format_coded_message(
            AQE_BATCH_INVALID_REQUEST,
            str(exc) or "note load failed",
        )
        capture_exception(
            "browser.batch.note_load",
            exc,
            operation=f"browser.batch.{request.operation}",
            user_message=message,
            context={"note_id": note_id, "source_field": request.source_field},
            log=logger,
        )
        return BatchNoteResult(note_id=note_id, status="failed", message=message)

    current_audio = first_audio_filename(snapshot, request.source_field) or ""
    result = process_note_batch_operation(
        snapshot,
        request=request,
        media_dir=media_dir,
        config=config,
        media_writer=col.media.write_data,
        artifact_root=artifact_root,
    )
    if current_audio and result.audio_filename is None:
        return BatchNoteResult(
            note_id=result.note_id,
            status=result.status,
            message=result.message,
            target_field=result.target_field,
            target_html=result.target_html,
            audio_filename=current_audio,
            image_filename=result.image_filename,
            written_filename=result.written_filename,
            original_target_html=result.original_target_html,
        )
    return result


def apply_result(
    col: Any,
    report: BatchRunReport,
    result: BatchNoteResult,
    fallback_field: str,
) -> BatchNoteResult:
    """Apply one batch note result to the collection and report counters."""
    if result.written:
        try:
            note = col.get_note(result.note_id)
            assert result.target_field is not None
            assert result.target_html is not None
            if result.original_target_html is not None:
                current_html = _note_field_value(note, result.target_field)
                if current_html != result.original_target_html:
                    report.failures += 1
                    message = format_coded_message(
                        AQE_BATCH_INVALID_REQUEST,
                        f"target field {result.target_field!r} changed during batch processing",
                    )
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
            note[result.target_field] = result.target_html
            col.update_note(note)
            report.written += 1
        except Exception as exc:
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
        return result
    if result.failure:
        report.failures += 1
    else:
        report.skipped += 1
    return result


def publish_collection_changes(browser: Any, changes: Any) -> None:
    """Notify Anki that collection changes were produced by the batch run."""
    if changes is None:
        return
    try:
        from aqt import gui_hooks

        browser.mw.update_undo_actions()
        gui_hooks.operation_did_execute(changes, browser)
    except Exception as exc:  # pragma: no cover - UI refresh is best effort
        capture_exception(
            "browser.refresh_after_batch",
            exc,
            operation="browser.batch.refresh",
            user_message=str(exc),
            context={"has_changes": changes is not None},
            log=logger,
        )


def _format_parameters(request: BatchRunRequest) -> str:
    params = request.parameters
    values: list[str] = []
    if request.operation in {"slower", "faster"} and params.speed_step is not None:
        values.append(f"speed_step={params.speed_step}")
    if request.operation in {"volume_down", "volume_up"} and params.volume_step_db is not None:
        values.append(f"volume_step_db={params.volume_step_db}")
    if request.operation == "remove_pauses" and params.pause_aggressiveness is not None:
        values.append(f"pause_aggressiveness={params.pause_aggressiveness}")
    if request.operation == "remove_pauses" and params.pause_detection_algorithm is not None:
        values.append(f"pause_detection_algorithm={params.pause_detection_algorithm}")
    return ", ".join(values) if values else "defaults"


def _note_field_value(note: Any, field_name: str) -> str:
    try:
        return str(note[field_name])
    except (KeyError, TypeError, AttributeError):
        fields = getattr(note, "fields", None)
        if isinstance(fields, dict):
            return str(fields[field_name])
        raise


def _tr(key: str, values: dict[str, object] | None = None) -> str:
    return format_message(dict(active_context()["messages"]), key, values)
