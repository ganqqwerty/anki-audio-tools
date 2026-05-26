"""WebView dialog for Browser batch audio operations."""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .audio_operations import operation_label
from .batch_operations import BatchRunRequest, FieldGroup
from .browser_dialog_state import (
    batch_error_payload,
    batch_finish_payload,
    batch_progress_payload,
    build_batch_initial_state,
    request_from_batch_start_payload,
)
from .browser_report import BatchRunReport
from .frontend_logs import handle_frontend_log_payload
from .i18n import active_context, format_message
from .webview_bridge import (
    WebviewBridgeCommand,
    decode_webview_bridge_command,
    legacy_json_payload,
)
from .webview_shell import render_webview_content

if TYPE_CHECKING:
    from .audio_state import AudioProcessingConfig

logger = logging.getLogger(__name__)

_BUNDLE_DIR = Path(__file__).parent / "templates" / "batch"
_BUNDLE_JS = _BUNDLE_DIR / "batch_bundle.js"
_BUNDLE_CSS = _BUNDLE_DIR / "batch_bundle.css"


class BatchOperationsDialog:
    """Small composed WebView dialog wrapper for batch audio operations."""

    def __init__(
        self,
        browser: Any,
        note_ids: list[int],
        groups: tuple[FieldGroup, ...],
        config: AudioProcessingConfig,
        run_batch_in_background: Callable[[Any, Any, list[int], BatchRunRequest], None],
    ) -> None:
        from aqt.qt import QDialog, QVBoxLayout
        from aqt.webview import AnkiWebView

        self.browser = browser
        self.note_ids = note_ids
        self._i18n = active_context()
        self._messages = dict(self._i18n["messages"])
        self.cancel_event = threading.Event()
        self._run_batch_in_background = run_batch_in_background
        self._running = False
        self._finished = False
        self._log_lines: list[str] = []
        self._dialog = QDialog(browser)
        self._dialog.setWindowTitle(self.tr("batch.window_title"))
        self._dialog.setMinimumWidth(680)
        self._dialog.setMinimumHeight(520)

        layout = QVBoxLayout(self._dialog)
        layout.setContentsMargins(0, 0, 0, 0)

        self._webview = AnkiWebView(parent=self._dialog)
        self._webview.requiresCol = False
        self._webview.set_bridge_command(self._handle_bridge_command, self)
        body, head = _render_batch_content(
            build_batch_initial_state(note_count=len(note_ids), groups=groups, config=config)
        )
        self._webview.stdHtml(body=body, head=head, context=self)
        layout.addWidget(self._webview)

    def tr(self, key: str, values: dict[str, object] | None = None) -> str:
        """Translate a batch dialog message."""
        return format_message(self._messages, key, values)

    def exec(self) -> Any:
        """Show the dialog modally."""
        return self._dialog.exec()

    def append_log(self, line: str) -> None:
        """Append a line to the copyable report."""
        self._log_lines.append(line)
        self._emit("onBatchLog", {"line": line})

    def update_progress(self, processed: int, total: int, current_audio: str, failures: int) -> None:
        """Update progress controls from the main thread."""
        audio = current_audio or self.tr("batch.no_audio")
        message = self.tr(
            "batch.progress",
            {"processed": processed, "total": total, "audio": audio, "failures": failures},
        )
        self._emit(
            "onBatchProgress",
            batch_progress_payload(
                processed=processed,
                total=total,
                current_audio=current_audio,
                failures=failures,
                message=message,
            ),
        )

    def finish_with_report(self, report: BatchRunReport) -> None:
        """Switch the dialog into final report mode."""
        self._running = False
        self._finished = True
        self.append_log(report.summary)
        self._emit("onBatchFinish", batch_finish_payload(report))

    def finish_with_error(self, message: str, *, recoverable: bool = False) -> None:
        """Show an unexpected batch-level failure."""
        self._running = False
        self._finished = not recoverable
        self.append_log(message)
        self._emit("onBatchError", batch_error_payload(message, recoverable=recoverable))

    def _emit(self, callback: str, payload: dict[str, Any]) -> None:
        self._webview.eval(f"window.{callback}({json.dumps(payload)})")

    def _handle_bridge_command(self, cmd: str) -> bool:
        try:
            command = decode_webview_bridge_command(cmd)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("invalid batch bridge command: %s", exc)
            return False

        if command.name in {"batch.start", "batch_start"}:
            return self._handle_batch_start(command)
        if command.name in {"batch.cancel", "batch_cancel"}:
            self._cancel_or_close()
            return True
        if command.name in {"batch.close", "batch_close"}:
            self._dialog.reject()
            return True
        if command.name in {"batch.copy_log", "batch_copy_log"}:
            _clipboard_set_text("\n".join(self._log_lines))
            return True
        if command.name in {"frontend.log", "frontend_log"}:
            _handle_frontend_log(command.legacy_payload if command.is_legacy else command.payload)
            return True
        return False

    def _handle_batch_start(self, command: WebviewBridgeCommand) -> bool:
        if self._running:
            return True
        try:
            raw_payload = legacy_json_payload(command)
            request = request_from_batch_start_payload(raw_payload)
        except (json.JSONDecodeError, AssertionError, TypeError) as exc:
            message = self.tr("batch.failed", {"error": "Invalid batch request"})
            self.finish_with_error(message)
            logger.warning("invalid batch start payload: %s", exc)
            return True
        except ValueError as exc:
            self.finish_with_error(str(exc), recoverable=True)
            return True

        self._running = True
        self._finished = False
        self._log_lines.clear()
        operation = str(getattr(request, "operation", "") or "")
        operation_name = operation_label(operation, self._messages) if operation else ""
        self._emit(
            "onBatchProgress",
            batch_progress_payload(
                processed=0,
                total=len(self.note_ids),
                current_audio="",
                failures=0,
                message=self.tr("batch.starting", {"operation": operation_name}),
            ),
        )
        self._run_batch_in_background(self.browser, self, self.note_ids, request)
        return True

    def _cancel_or_close(self) -> None:
        if self._running:
            self.cancel_event.set()
            self.append_log(self.tr("batch.cancel_requested"))
            return
        self._dialog.reject()


def _render_batch_content(initial_state: dict[str, Any]) -> tuple[str, str]:
    """Render batch webview body/head fragments for Anki's themed HTML shell."""
    return render_webview_content(
        initial_state_name="__AQE_BATCH_INITIAL_STATE__",
        initial_state=initial_state,
        bundle_js=_BUNDLE_JS,
        bundle_css=_BUNDLE_CSS,
        scope="batch",
    )


def _clipboard_set_text(text: str) -> None:
    from aqt.qt import QApplication

    clipboard = QApplication.clipboard()
    if clipboard is not None:
        clipboard.setText(text)


def _handle_frontend_log(raw_payload: Any) -> None:
    handle_frontend_log_payload(
        raw_payload,
        logger=logger,
        default_scope="batch",
        boundary="batch.frontend",
        log_prefix="batch frontend",
        invalid_label="batch frontend_log",
    )
