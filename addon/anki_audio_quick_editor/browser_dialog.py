"""Qt dialog for Browser batch audio operations."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

from .audio_operations import (
    BATCH_OPERATIONS,
    OP_GRAPH,
    operation_label,
    requires_target_field,
)
from .batch_operations import BatchRunRequest, FieldGroup
from .browser_report import BatchRunReport
from .i18n import active_context, format_message

logger = logging.getLogger(__name__)


class BatchOperationsDialog:
    """Small composed Qt dialog wrapper for batch audio operations."""

    def __init__(
        self,
        browser: Any,
        note_ids: list[int],
        groups: tuple[FieldGroup, ...],
        run_batch_in_background: Callable[[Any, Any, list[int], BatchRunRequest], None],
    ) -> None:
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
        self._i18n = active_context()
        self._messages = dict(self._i18n["messages"])
        self.cancel_event = threading.Event()
        self._run_batch_in_background = run_batch_in_background
        self._running = False
        self._finished = False
        self._dialog = QDialog(browser)
        self._dialog.setWindowTitle(self.tr("batch.window_title"))
        self._dialog.setMinimumWidth(680)
        self._dialog.setMinimumHeight(520)
        self._status_label = QLabel(self.tr("batch.instructions"))
        self._operation_label = QLabel(self.tr("batch.operation"))
        self._operation_combo = QComboBox()
        self._source_combo = QComboBox()
        self._target_label = QLabel(self.tr("batch.target_field"))
        self._target_combo = QComboBox()
        self._progress = QProgressBar()
        self._log = QPlainTextEdit()
        self._start_button = QPushButton(self.tr("batch.start"))
        self._copy_button = QPushButton(self.tr("batch.copy_log"))
        self._cancel_button = QPushButton(self.tr("batch.cancel"))
        self._build_layout(groups)
        self._connect_buttons()

    def tr(self, key: str, values: dict[str, object] | None = None) -> str:
        """Translate a batch dialog message."""
        return format_message(self._messages, key, values)

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
            self._operation_combo.addItem(operation_label(operation, self._messages), operation)
        row = QHBoxLayout()
        row.addWidget(self._operation_label)
        row.addWidget(self._operation_combo)
        return row

    def _field_row(self, groups: tuple[FieldGroup, ...]) -> Any:
        from aqt.qt import QHBoxLayout, QLabel

        _populate_combo(self._source_combo, groups)
        _populate_combo(self._target_combo, groups)
        field_row = QHBoxLayout()
        field_row.addWidget(QLabel(self.tr("batch.source_field")))
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
        self._status_label.setText(
            self.tr("batch.starting", {"operation": operation_label(request.operation, self._messages)})
        )
        logger.info(
            "batch operation started: notes=%s operation=%s source=%s target=%s",
            len(self.note_ids),
            request.operation,
            request.source_field,
            request.target_field,
        )
        self._run_batch_in_background(
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
        audio = current_audio or self.tr("batch.no_audio")
        self._status_label.setText(
            self.tr(
                "batch.progress",
                {"processed": processed, "total": total, "audio": audio, "failures": failures},
            )
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
        self._cancel_button.setText(self.tr("batch.close"))

    def finish_with_error(self, message: str) -> None:
        """Show an unexpected batch-level failure."""
        self._running = False
        self._finished = True
        self._status_label.setText(message)
        self.append_log(message)
        self._copy_button.setEnabled(True)
        self._cancel_button.setEnabled(True)
        self._cancel_button.setText(self.tr("batch.close"))

    def _cancel_or_close(self) -> None:
        if self._running:
            self.cancel_event.set()
            self.append_log(self.tr("batch.cancel_requested"))
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
