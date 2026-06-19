"""Editor adapter for Catbox/Litterbox sharing."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Any

from .diagnostics_runtime import capture_exception, new_operation_id
from .editor_actions import EditorCommandPayload, decode_editor_command_payload
from .editor_recording_state import ready_learner_recording_media_path
from .error_codes import (
    AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING,
    AQE_MEDIA_REFERENCED_AUDIO_MISSING,
    AQE_SHARE_FAILED,
    coded_error,
)
from .errors import AudioProcessingError, MissingMediaError

if TYPE_CHECKING:
    from .editor_deps_protocols import ShareDeps

logger = logging.getLogger(__name__)


def share_current_audio_file(
    editor: Any,
    command: str | EditorCommandPayload,
    deps: ShareDeps,
) -> None:
    """Upload the current editor audio file and copy the resulting URL."""
    payload = decode_editor_command_payload(command)
    if payload.share_target not in {"catbox", "litterbox"}:
        reject_invalid_share_target(editor, deps)
        return

    try:
        session, media_path = deps.current_media_path(editor)
    except MissingMediaError as exc:
        deps.set_busy(editor, False)
        deps.eval_status(
            editor,
            coded_error(AQE_MEDIA_REFERENCED_AUDIO_MISSING, str(exc)),
            kind="error",
        )
        return
    except AudioProcessingError as exc:
        deps.set_busy(editor, False)
        deps.eval_status(
            editor,
            coded_error(AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING, str(exc)),
            kind="error",
        )
        return
    share_media_path(editor, payload, session, media_path, deps)


def share_learner_recording_file(
    editor: Any,
    command: str | EditorCommandPayload,
    deps: ShareDeps,
) -> None:
    """Upload the latest learner recording sidecar and copy the resulting URL."""
    payload = decode_editor_command_payload(command)
    if payload.share_target not in {"catbox", "litterbox"}:
        reject_invalid_share_target(editor, deps)
        return

    session = deps.sessions.get(editor)
    media_path = ready_learner_recording_media_path(session)
    if session is None or media_path is None:
        deps.set_busy(editor, False)
        message = deps.t("editor.status.referenced_audio_missing")
        deps.eval_status(editor, coded_error(AQE_MEDIA_REFERENCED_AUDIO_MISSING, message), kind="error")
        return
    share_media_path(editor, payload, session, media_path, deps)


def reject_invalid_share_target(editor: Any, deps: ShareDeps) -> None:
    deps.set_busy(editor, False)
    message = deps.t("editor.status.share_invalid_target")
    deps.eval_status(
        editor,
        coded_error(AQE_SHARE_FAILED, message),
        kind="error",
    )


def share_media_path(
    editor: Any,
    payload: EditorCommandPayload,
    session: Any,
    media_path: Any,
    deps: ShareDeps,
) -> None:
    """Upload one already-resolved media path."""
    if deps.is_busy(session):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return

    operation_id = new_operation_id("editor-share")
    logger.info(
        "Editor share upload start | command=%s target=%s path=%s",
        payload.command,
        payload.share_target,
        media_path,
    )
    message_key = (
        "editor.status.sharing_litterbox"
        if payload.share_target == "litterbox"
        else "editor.status.sharing_catbox"
    )
    deps.set_busy(editor, True, deps.t(message_key), payload.command)

    def _run() -> None:
        try:
            url = deps.upload_file(media_path, payload.share_target)
            logger.info(
                "Editor share upload succeeded | command=%s target=%s filename=%s",
                payload.command,
                payload.share_target,
                media_path.name,
            )
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
    deps: ShareDeps,
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
    deps.eval_status(editor, deps.t(success_key, {"filename": filename, "url": url}), kind="info")
    deps.set_busy(editor, False)


def share_failed(editor: Any, error: str, deps: ShareDeps) -> None:
    """Clear the busy state after a failed upload."""
    deps.set_busy(editor, False)
    message = deps.t("editor.status.share_failed", {"error": error})
    deps.eval_status(
        editor,
        coded_error(AQE_SHARE_FAILED, message),
        kind="error",
    )
