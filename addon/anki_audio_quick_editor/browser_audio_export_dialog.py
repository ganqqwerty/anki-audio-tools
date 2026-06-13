"""WebView dialog for Browser audio export."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .batch_operation_types import BatchNoteSnapshot, FieldGroup
from .browser_audio_export_runner import run_audio_export_in_background
from .browser_audio_export_state import (
    audio_export_finish_payload,
    audio_export_progress_payload,
    build_audio_export_initial_state,
    request_from_audio_export_start_payload,
)
from .error_codes import AQE_BATCH_INVALID_REQUEST, coded_error
from .external_links import open_trusted_external_url_from_payload
from .frontend_logs import handle_frontend_log_payload
from .i18n import active_context, format_message
from .webview_bridge import WebviewBridgeCommand, decode_webview_bridge_command
from .webview_shell import render_webview_content

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .audio_export_types import AudioExportReport

_BUNDLE_DIR = Path(__file__).parent / "templates" / "batch"
_BUNDLE_JS = _BUNDLE_DIR / "batch_bundle.js"
_BUNDLE_CSS = _BUNDLE_DIR / "batch_bundle.css"


class AudioExportDialog:
    """Small composed WebView dialog wrapper for Browser audio export."""

    def __init__(
        self,
        browser: Any,
        note_ids: list[int],
        groups: tuple[FieldGroup, ...],
        snapshots: tuple[BatchNoteSnapshot, ...],
    ) -> None:
        from aqt.qt import QDialog, QVBoxLayout
        from aqt.webview import AnkiWebView

        self.browser = browser
        self.note_ids = note_ids
        self.snapshots = snapshots
        self._i18n = active_context()
        self._messages = dict(self._i18n["messages"])
        self.cancel_event = threading.Event()
        self._running = False
        self._finished = False
        self._log_lines: list[str] = []
        self._dialog = QDialog(browser)
        self._dialog.setWindowTitle(self.tr("audio_export.window_title"))
        self._dialog.setMinimumWidth(680)
        self._dialog.setMinimumHeight(520)

        layout = QVBoxLayout(self._dialog)
        layout.setContentsMargins(0, 0, 0, 0)

        self._webview = AnkiWebView(parent=self._dialog)
        self._webview.requiresCol = False
        self._webview.set_bridge_command(self._handle_bridge_command, self)
        body, head = _render_audio_export_content(
            build_audio_export_initial_state(
                note_count=len(note_ids),
                groups=groups,
                snapshots=snapshots,
            )
        )
        self._webview.stdHtml(body=body, head=head, context=self)
        layout.addWidget(self._webview)

    def tr(self, key: str, values: dict[str, object] | None = None) -> str:
        """Translate an audio export dialog message."""
        return format_message(self._messages, key, values)

    def exec(self) -> Any:
        """Show the dialog modally."""
        return self._dialog.exec()

    def append_log(self, line: str) -> None:
        """Append a line to the copyable export log."""
        self._log_lines.append(line)
        self._emit("onAudioExportLog", {"line": line})

    def update_progress(self, processed: int, total: int, current_audio: str, failures: int) -> None:
        """Update export progress controls from the main thread."""
        audio = current_audio or self.tr("audio_export.no_audio")
        message = self.tr(
            "audio_export.progress",
            {"processed": processed, "total": total, "audio": audio, "failures": failures},
        )
        self._emit(
            "onAudioExportProgress",
            audio_export_progress_payload(
                processed=processed,
                total=total,
                current_audio=current_audio,
                failures=failures,
                message=message,
            ),
        )

    def finish_with_report(self, report: AudioExportReport) -> None:
        """Switch the dialog into final export report mode."""
        self._running = False
        self._finished = True
        self.append_log(report.summary)
        self._emit("onAudioExportFinish", audio_export_finish_payload(report))

    def finish_with_error(
        self,
        message: str,
        *,
        recoverable: bool = False,
        user_error: dict[str, str] | None = None,
    ) -> None:
        """Show an unexpected export-level failure."""
        self._running = False
        self._finished = not recoverable
        display_error = user_error or coded_error(AQE_BATCH_INVALID_REQUEST, message)
        logger.error(
            "audio export dialog displayed error: %s | recoverable=%s",
            _display_error_log_text(display_error),
            recoverable,
        )
        self.append_log(message)
        self._emit(
            "onAudioExportError",
            {
                "message": message,
                "recoverable": recoverable,
                "user_error": display_error,
            },
        )

    def _emit(self, callback: str, payload: dict[str, Any]) -> None:
        self._webview.eval(f"window.{callback}({json.dumps(payload)})")

    def _handle_bridge_command(self, cmd: str) -> bool:
        try:
            command = decode_webview_bridge_command(cmd)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("invalid audio export bridge command: %s", exc)
            return False

        if command.name == "audio-export.choose-destination":
            return self._handle_choose_destination(command.payload)
        if command.name == "audio-export.start":
            return self._handle_audio_export_start(command)
        if command.name == "audio-export.cancel":
            self._cancel_or_close()
            return True
        if command.name == "audio-export.close":
            self._dialog.reject()
            return True
        if command.name == "audio-export.copy_log":
            _clipboard_set_text("\n".join(self._log_lines))
            return True
        if command.name == "frontend.log":
            _handle_frontend_log(command.payload)
            return True
        if command.name == "webview.open_url":
            open_trusted_external_url_from_payload(command.payload, logger=logger)
            return True
        return False

    def _handle_audio_export_start(self, command: WebviewBridgeCommand) -> bool:
        if self._running:
            return True
        try:
            request = request_from_audio_export_start_payload(command.payload)
        except (AssertionError, TypeError) as exc:
            message = self.tr("audio_export.failed", {"error": "Invalid audio export request"})
            self.finish_with_error(
                message,
                user_error=coded_error(AQE_BATCH_INVALID_REQUEST, message),
            )
            logger.warning("invalid audio export start payload: %s", exc)
            return True
        except ValueError as exc:
            message = str(exc)
            self.finish_with_error(
                message,
                recoverable=True,
                user_error=coded_error(AQE_BATCH_INVALID_REQUEST, message),
            )
            return True

        self._running = True
        self._finished = False
        self.cancel_event.clear()
        self._log_lines.clear()
        self._emit(
            "onAudioExportProgress",
            audio_export_progress_payload(
                processed=0,
                total=0,
                current_audio="",
                failures=0,
                message=self.tr("audio_export.starting"),
            ),
        )
        run_audio_export_in_background(self.browser, self, self.snapshots, request)
        return True

    def _handle_choose_destination(self, raw_payload: object) -> bool:
        mode = "zip"
        if isinstance(raw_payload, dict):
            mode = str(raw_payload.get("mode") or "zip")
        destination = _choose_export_destination(self._dialog, mode)
        if destination:
            self._emit("onAudioExportDestination", {"destination_path": destination})
        return True

    def _cancel_or_close(self) -> None:
        if self._running:
            self.cancel_event.set()
            self.append_log(self.tr("audio_export.cancel_requested"))
            return
        self._dialog.reject()


def _render_audio_export_content(initial_state: dict[str, Any]) -> tuple[str, str]:
    """Render audio export webview body/head fragments for Anki's themed HTML shell."""
    return render_webview_content(
        initial_state_name="__AQE_BATCH_INITIAL_STATE__",
        initial_state=initial_state,
        bundle_js=_BUNDLE_JS,
        bundle_css=_BUNDLE_CSS,
        scope="batch",
    )


def _default_export_filename(mode: str) -> str:
    from datetime import UTC, datetime

    extension = ".mp3" if mode == "combined_mp3" else ".zip"
    return f"anki-audio-export-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}{extension}"


def _choose_export_destination(parent: Any, mode: str) -> str:
    from aqt.qt import QFileDialog

    filename = _default_export_filename(mode)
    filter_text = "MP3 audio (*.mp3)" if mode == "combined_mp3" else "Zip archives (*.zip)"
    selected, _filter = QFileDialog.getSaveFileName(parent, "Export Audio", filename, filter_text)
    if not selected:
        return ""
    path = Path(selected)
    suffix = ".mp3" if mode == "combined_mp3" else ".zip"
    if path.suffix.lower() != suffix:
        path = path.with_suffix(suffix)
    return str(path)


def _clipboard_set_text(text: str) -> None:
    from aqt.qt import QApplication

    clipboard = QApplication.clipboard()
    if clipboard is not None:
        clipboard.setText(text)


def _display_error_log_text(error: dict[str, str]) -> str:
    code = error.get("code", "")
    message = error.get("message", "")
    details = error.get("details", "")
    rendered = f"{code}: {message}" if code else message
    if details:
        return f"{rendered} | details={details}"
    return rendered


def _handle_frontend_log(raw_payload: Any) -> None:
    handle_frontend_log_payload(
        raw_payload,
        logger=logger,
        default_scope="batch",
        boundary="audio_export.frontend",
        log_prefix="audio export frontend",
        invalid_label="audio export frontend_log",
    )
