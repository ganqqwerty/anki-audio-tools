"""Browser menu integration for batch audio operations."""

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
    FieldGroup,
    field_groups_for_notes,
    first_audio_filename,
    process_note_batch_operation,
    unique_note_ids,
)
from .browser_dialog import BatchOperationsDialog
from .browser_report import BatchRunReport, format_result_line
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .i18n import active_context, format_message

logger = logging.getLogger(__name__)

ACTION_LABEL = "Run Audio Batch Operation..."
UNDO_LABEL = "Batch Audio Operation"

def register_browser_hooks(gui_hooks: Any) -> None:
    """Register Browser menu and context-menu hooks."""
    gui_hooks.browser_menus_did_init.append(
        _browser_hook_boundary("browser_menus_did_init", _on_browser_menus_did_init)
    )
    gui_hooks.browser_will_show_context_menu.append(
        _browser_hook_boundary("browser_will_show_context_menu", _on_browser_will_show_context_menu)
    )


def _browser_hook_boundary(name: str, func: Any) -> Any:
    def _wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            capture_exception(f"browser.hook.{name}", exc, operation=f"browser.hook.{name}", log=logger)
            raise

    return _wrapped


def _on_browser_menus_did_init(browser: Any) -> None:
    from aqt.qt import qconnect

    action = browser.form.menu_Cards.addAction(_tr("batch.action"))
    assert action is not None
    qconnect(action.triggered, lambda _checked=False, b=browser: _open_batch_dialog(b))


def _on_browser_will_show_context_menu(browser: Any, menu: Any) -> None:
    from aqt.qt import qconnect

    menu.addSeparator()
    action = menu.addAction(_tr("batch.action"))
    assert action is not None
    qconnect(action.triggered, lambda _checked=False, b=browser: _open_batch_dialog(b))


def _open_batch_dialog(browser: Any) -> None:
    from aqt.utils import showWarning

    note_ids = unique_note_ids(browser.selected_notes())
    if not note_ids:
        showWarning(_tr("batch.no_cards_selected"), parent=browser)
        return

    snapshots = _snapshots_for_note_ids(browser.mw.col, note_ids)
    groups = field_groups_for_notes(snapshots)
    if not groups:
        showWarning(_tr("batch.no_fields"), parent=browser)
        return

    dialog = _create_dialog(browser, note_ids, groups)
    dialog.exec()


def _snapshots_for_note_ids(col: Any, note_ids: list[int]) -> list[BatchNoteSnapshot]:
    snapshots: list[BatchNoteSnapshot] = []
    for note_id in note_ids:
        snapshots.append(_snapshot_from_note(col.get_note(note_id)))
    return snapshots


def _snapshot_from_note(note: Any) -> BatchNoteSnapshot:
    notetype = note.note_type()
    notetype_name = str(notetype.get("name", "Unknown")) if isinstance(notetype, dict) else "Unknown"
    return BatchNoteSnapshot(
        note_id=int(note.id),
        notetype_name=notetype_name,
        fields={str(name): str(value) for name, value in note.items()},
    )


def _create_dialog(browser: Any, note_ids: list[int], groups: tuple[FieldGroup, ...]) -> Any:
    return BatchOperationsDialog(browser, note_ids, groups, _run_batch_in_background)



def _run_batch_in_background(
    browser: Any,
    dialog: Any,
    note_ids: list[int],
    request: BatchRunRequest,
) -> None:
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
        return _run_batch(
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
            capture_exception(
                "browser.batch.worker",
                exc,
                operation="browser.batch",
                operation_id=operation_id,
                user_message=_tr("batch.failed", {"error": exc}),
                context={"note_count": len(note_ids), "operation": request.operation},
                log=logger,
            )
            dialog.finish_with_error(_tr("batch.failed", {"error": exc}))
            return
        _publish_collection_changes(browser, report.changes)
        logger.info("batch operation finished: %s", report.summary)
        dialog.finish_with_report(report)

    mw.taskman.run_in_background(task, done, uses_collection=True)


def _run_batch(
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

        note_result = _process_note(
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
        note_result = _apply_result(
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


def _tr(key: str, values: dict[str, object] | None = None) -> str:
    return format_message(dict(active_context()["messages"]), key, values)


def _process_note(
    col: Any,
    note_id: int,
    request: BatchRunRequest,
    media_dir: Path,
    config: AudioProcessingConfig,
    artifact_root: Path | None = None,
) -> BatchNoteResult:
    try:
        note = col.get_note(note_id)
        snapshot = _snapshot_from_note(note)
    except Exception as exc:
        capture_exception(
            "browser.batch.note_load",
            exc,
            operation=f"browser.batch.{request.operation}",
            user_message=str(exc) or "note load failed",
            context={"note_id": note_id, "source_field": request.source_field},
            log=logger,
        )
        return BatchNoteResult(note_id=note_id, status="failed", message=str(exc) or "note load failed")

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
        )
    return result


def _apply_result(
    col: Any,
    report: BatchRunReport,
    result: BatchNoteResult,
    fallback_field: str,
) -> BatchNoteResult:
    if result.written:
        try:
            note = col.get_note(result.note_id)
            assert result.target_field is not None
            assert result.target_html is not None
            note[result.target_field] = result.target_html
            col.update_note(note)
            report.written += 1
        except Exception as exc:
            capture_exception(
                "browser.batch.apply_result",
                exc,
                operation=f"browser.batch.{result.status}",
                user_message=str(exc) or f"failed to update target field {fallback_field!r}",
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
                message=str(exc) or f"failed to update target field {fallback_field!r}",
                target_field=result.target_field,
                target_html=result.target_html,
                audio_filename=result.audio_filename,
                image_filename=result.image_filename,
                written_filename=result.written_filename,
            )
        return result
    if result.failure:
        report.failures += 1
    else:
        report.skipped += 1
    return result



def _publish_collection_changes(browser: Any, changes: Any) -> None:
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
