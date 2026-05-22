"""Editor adapter for Catbox/Litterbox sharing."""

from __future__ import annotations

import logging
import threading
from typing import Any

from .diagnostics_runtime import capture_exception, new_operation_id
from .editor_actions import EditorCommandPayload, decode_editor_command_payload

logger = logging.getLogger(__name__)


def share_current_audio_file(
    editor: Any,
    command: str | EditorCommandPayload,
    deps: Any,
) -> None:
    """Upload the current editor audio file and copy the resulting URL."""
    payload = decode_editor_command_payload(command)
    if payload.share_target not in {"catbox", "litterbox"}:
        deps.set_busy(editor, False)
        deps.eval_status(editor, deps.t("editor.status.share_invalid_target"), kind="error")
        return

    session, media_path = deps.current_media_path(editor)
    if deps.is_busy(session):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return

    operation_id = new_operation_id("editor-share")
    message_key = (
        "editor.status.sharing_litterbox"
        if payload.share_target == "litterbox"
        else "editor.status.sharing_catbox"
    )
    deps.set_busy(editor, True, deps.t(message_key), payload.command)

    def _run() -> None:
        try:
            url = deps.upload_file(media_path, payload.share_target)
            deps.main(
                editor,
                lambda: deps.finish_shared_audio(
                    editor,
                    payload.share_target,
                    media_path.name,
                    url,
                ),
            )
        except Exception as exc:  # pragma: no cover - worker boundary
            error_message = str(exc)
            capture_exception(
                "editor.worker.share",
                exc,
                operation="editor.share",
                operation_id=operation_id,
                user_message=error_message,
                context={"filename": media_path.name, "share_target": payload.share_target},
                log=logger,
            )
            deps.main(editor, lambda: deps.share_failed(editor, error_message))

    threading.Thread(target=_run, daemon=True).start()


def finish_shared_audio(
    editor: Any,
    share_target: str,
    filename: str,
    url: str,
    deps: Any,
) -> None:
    """Finalize a successful upload on the main thread."""
    from aqt.qt import QApplication

    clipboard = QApplication.clipboard()
    if clipboard is None:
        deps.logger.warning("share_current_audio_file: clipboard unavailable")
        deps.eval_status(
            editor,
            deps.t("editor.status.share_clipboard_unavailable", {"filename": filename, "url": url}),
            kind="warning",
        )
        deps.set_busy(editor, False)
        return

    clipboard.setText(url)
    success_key = (
        "editor.status.shared_litterbox"
        if share_target == "litterbox"
        else "editor.status.shared_catbox"
    )
    deps.eval_status(editor, deps.t(success_key, {"filename": filename}), kind="info")
    deps.set_busy(editor, False)


def share_failed(editor: Any, error: str, deps: Any) -> None:
    """Clear the busy state after a failed upload."""
    deps.set_busy(editor, False)
    deps.eval_status(editor, deps.t("editor.status.share_failed", {"error": error}), kind="error")
