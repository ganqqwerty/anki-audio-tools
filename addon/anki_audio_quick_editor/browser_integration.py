"""Browser menu integration for batch audio operations."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .audio_operations import (
    BATCH_OPERATIONS,
    OP_GRAPH,
    OPERATION_LABELS,
    requires_target_field,
)
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

logger = logging.getLogger(__name__)

ACTION_LABEL = "Run Audio Batch Operation..."
UNDO_LABEL = "Batch Audio Operation"


@dataclass
class BatchRunReport:
    """Summary returned from a completed batch run."""

    total: int
    processed: int = 0
    written: int = 0
    skipped: int = 0
    failures: int = 0
    canceled: bool = False
    log_lines: list[str] = field(default_factory=list)
    changes: Any = None

    def add(self, line: str) -> None:
        """Append one human-readable log line."""
        self.log_lines.append(line)

    @property
    def summary(self) -> str:
        """Return the final user-facing summary."""
        state = "Canceled" if self.canceled else "Completed"
        return (
            f"{state}: {self.processed}/{self.total} notes processed, "
            f"{self.written} written, {self.skipped} skipped, {self.failures} failures."
        )


def register_browser_hooks(gui_hooks: Any) -> None:
    """Register Browser menu and context-menu hooks."""
    gui_hooks.browser_menus_did_init.append(_on_browser_menus_did_init)
    gui_hooks.browser_will_show_context_menu.append(_on_browser_will_show_context_menu)


def _on_browser_menus_did_init(browser: Any) -> None:
    from aqt.qt import qconnect

    action = browser.form.menu_Cards.addAction(ACTION_LABEL)
    assert action is not None
    qconnect(action.triggered, lambda _checked=False, b=browser: _open_batch_dialog(b))


def _on_browser_will_show_context_menu(browser: Any, menu: Any) -> None:
    from aqt.qt import qconnect

    menu.addSeparator()
    action = menu.addAction(ACTION_LABEL)
    assert action is not None
    qconnect(action.triggered, lambda _checked=False, b=browser: _open_batch_dialog(b))


def _open_batch_dialog(browser: Any) -> None:
    from aqt.utils import showWarning

    note_ids = unique_note_ids(browser.selected_notes())
    if not note_ids:
        showWarning("No cards are selected.", parent=browser)
        return

    snapshots = _snapshots_for_note_ids(browser.mw.col, note_ids)
    groups = field_groups_for_notes(snapshots)
    if not groups:
        showWarning("The selected cards do not expose any note fields.", parent=browser)
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
    return BatchOperationsDialog(browser, note_ids, groups)


class BatchOperationsDialog:
    """Small composed Qt dialog wrapper for batch audio operations."""

    def __init__(self, browser: Any, note_ids: list[int], groups: tuple[FieldGroup, ...]) -> None:
        from aqt.qt import (
            QComboBox,
            QDialog,
            QLabel,
            QPlainTextEdit,
            QProgressBar,
            QPushButton,
        )

        self.browser = browser
        self.note_ids = note_ids
        self.cancel_event = threading.Event()
        self._running = False
        self._finished = False
        self._dialog = QDialog(browser)
        self._dialog.setWindowTitle("Run Audio Batch Operation")
        self._dialog.setMinimumWidth(680)
        self._dialog.setMinimumHeight(520)
        self._status_label = QLabel("Choose an operation and fields for the selected notes.")
        self._operation_label = QLabel("Operation")
        self._operation_combo = QComboBox()
        self._source_combo = QComboBox()
        self._target_label = QLabel("Target field")
        self._target_combo = QComboBox()
        self._progress = QProgressBar()
        self._log = QPlainTextEdit()
        self._start_button = QPushButton("Start")
        self._copy_button = QPushButton("Copy Log")
        self._cancel_button = QPushButton("Cancel")
        self._build_layout(groups)
        self._connect_buttons()

    def exec(self) -> Any:
        """Show the dialog modally."""
        return self._dialog.exec()

    def _build_layout(self, groups: tuple[FieldGroup, ...]) -> None:
        from aqt.qt import QHBoxLayout, QVBoxLayout

        layout = QVBoxLayout(self._dialog)
        layout.addWidget(self._status_label)
        layout.addLayout(self._operation_row())
        layout.addLayout(self._field_row(groups))
        self._progress.setMinimum(0)
        self._progress.setMaximum(len(self.note_ids))
        self._progress.setValue(0)
        layout.addWidget(self._progress)
        self._log.setReadOnly(True)
        layout.addWidget(self._log)
        button_row = QHBoxLayout()
        self._copy_button.setEnabled(False)
        button_row.addWidget(self._start_button)
        button_row.addWidget(self._copy_button)
        button_row.addWidget(self._cancel_button)
        layout.addLayout(button_row)
        self._sync_target_visibility()

    def _operation_row(self) -> Any:
        from aqt.qt import QHBoxLayout

        for operation in BATCH_OPERATIONS:
            self._operation_combo.addItem(OPERATION_LABELS[operation], operation)
        row = QHBoxLayout()
        row.addWidget(self._operation_label)
        row.addWidget(self._operation_combo)
        return row

    def _field_row(self, groups: tuple[FieldGroup, ...]) -> Any:
        from aqt.qt import QHBoxLayout, QLabel

        _populate_combo(self._source_combo, groups)
        _populate_combo(self._target_combo, groups)
        field_row = QHBoxLayout()
        field_row.addWidget(QLabel("Source field"))
        field_row.addWidget(self._source_combo)
        field_row.addWidget(self._target_label)
        field_row.addWidget(self._target_combo)
        return field_row

    def _connect_buttons(self) -> None:
        from aqt.qt import qconnect

        qconnect(self._operation_combo.currentIndexChanged, lambda _index: self._sync_target_visibility())
        qconnect(self._start_button.clicked, self._start)
        qconnect(self._copy_button.clicked, self._copy_log)
        qconnect(self._cancel_button.clicked, self._cancel_or_close)

    def _start(self) -> None:
        operation = self._operation_combo.currentData()
        source_field = self._source_combo.currentData()
        target_field = self._target_combo.currentData() if requires_target_field(str(operation)) else None
        try:
            request = BatchRunRequest(
                operation=str(operation),
                source_field=str(source_field or ""),
                target_field=str(target_field) if target_field else None,
            )
        except ValueError as exc:
            self.append_log(str(exc))
            return
        self._running = True
        self._operation_combo.setEnabled(False)
        self._source_combo.setEnabled(False)
        self._target_combo.setEnabled(False)
        self._start_button.setEnabled(False)
        self._status_label.setText(f"Starting {OPERATION_LABELS[request.operation]} batch...")
        logger.info(
            "batch operation started: notes=%s operation=%s source=%s target=%s",
            len(self.note_ids),
            request.operation,
            request.source_field,
            request.target_field,
        )
        _run_batch_in_background(
            self.browser,
            self,
            self.note_ids,
            request,
        )

    def append_log(self, line: str) -> None:
        """Append a line to the copyable report."""
        self._log.appendPlainText(line)

    def update_progress(self, processed: int, total: int, current_audio: str, failures: int) -> None:
        """Update progress controls from the main thread."""
        self._progress.setMaximum(total)
        self._progress.setValue(processed)
        audio = current_audio or "no audio"
        self._status_label.setText(
            f"Processed {processed}/{total} notes. Current audio: {audio}. Failures: {failures}."
        )

    def finish_with_report(self, report: BatchRunReport) -> None:
        """Switch the dialog into final report mode."""
        self._running = False
        self._finished = True
        self._progress.setMaximum(report.total)
        self._progress.setValue(report.processed)
        self._status_label.setText(report.summary)
        self.append_log(report.summary)
        self._copy_button.setEnabled(True)
        self._cancel_button.setEnabled(True)
        self._cancel_button.setText("Close")

    def finish_with_error(self, message: str) -> None:
        """Show an unexpected batch-level failure."""
        self._running = False
        self._finished = True
        self._status_label.setText(message)
        self.append_log(message)
        self._copy_button.setEnabled(True)
        self._cancel_button.setEnabled(True)
        self._cancel_button.setText("Close")

    def _cancel_or_close(self) -> None:
        if self._running:
            self.cancel_event.set()
            self.append_log("Cancel requested; stopping after the current note.")
            self._cancel_button.setEnabled(False)
            return
        self._dialog.reject()

    def _copy_log(self) -> None:
        from aqt.qt import QApplication

        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._log.toPlainText())

    def _sync_target_visibility(self) -> None:
        operation = str(self._operation_combo.currentData() or OP_GRAPH)
        needs_target = requires_target_field(operation)
        self._target_label.setVisible(needs_target)
        self._target_combo.setVisible(needs_target)
        self._target_combo.setEnabled(needs_target and not self._running)


def _populate_combo(combo: Any, groups: tuple[FieldGroup, ...]) -> None:
    for group in groups:
        for field_name in group.fields:
            combo.addItem(f"{group.notetype_name} / {field_name}", field_name)


def _run_batch_in_background(
    browser: Any,
    dialog: Any,
    note_ids: list[int],
    request: BatchRunRequest,
) -> None:
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
            logger.exception("batch operation failed")
            dialog.finish_with_error(f"Batch operation failed: {exc}")
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
    report = BatchRunReport(total=len(note_ids))
    undo_entry: int | None = None
    last_audio = ""

    report.add(
        f"Starting batch: {len(note_ids)} notes, operation={request.operation!r}, "
        f"source={request.source_field!r}, target={request.target_field!r}."
    )
    on_log(report.log_lines[-1])

    for note_id in note_ids:
        if cancel_event.is_set():
            report.canceled = True
            report.add("Canceled before starting the next note.")
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
            undo_entry = col.add_custom_undo_entry(UNDO_LABEL)
        note_result = _apply_result(
            col,
            report,
            note_result,
            request.target_field or request.source_field,
        )
        report.processed += 1
        line = _format_result_line(note_result)
        report.add(line)
        on_log(line)
        on_progress(report.processed, report.total, last_audio, report.failures)

    if undo_entry is not None:
        report.changes = col.merge_undo_entries(undo_entry)

    report.add(report.summary)
    return report


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


def _format_result_line(result: BatchNoteResult) -> str:
    prefix = {
        "written": "WROTE",
        "skipped": "SKIP",
        "failed": "FAIL",
    }.get(result.status, result.status.upper())
    audio = f" ({result.audio_filename})" if result.audio_filename else ""
    return f"{prefix} note {result.note_id}{audio}: {result.message}"


def _publish_collection_changes(browser: Any, changes: Any) -> None:
    if changes is None:
        return
    try:
        from aqt import gui_hooks

        browser.mw.update_undo_actions()
        gui_hooks.operation_did_execute(changes, browser)
    except Exception as exc:  # pragma: no cover - UI refresh is best effort
        logger.info("browser refresh after batch visualization failed: %s", exc)
