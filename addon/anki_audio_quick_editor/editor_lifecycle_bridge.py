"""Generated lifecycle-envelope boundary for the inline editor WebView."""

from __future__ import annotations

import logging
from typing import Any

from . import editor_callbacks, editor_runtime
from .contracts_generated import (
    EditorIntentReceipt,
    RecorderCommand,
    RecorderCommandKind,
    SourceMutationCommand,
)
from .editor_actions import EditorCommandOverrides, EditorCommandPayload
from .editor_pending_intent import consume_editor_intent_receipt
from .errors import AudioQuickEditorError
from .webview_bridge import decode_webview_bridge_command

EDITOR_INTENT_RECEIPT = "editor.intent-receipt"
EDITOR_RECORDER_COMMAND = "editor.recorder-command"
EDITOR_SOURCE_MUTATION = "editor.source-mutation"
LIFECYCLE_SCHEMA_VERSION = 1

logger = logging.getLogger(__name__)


def on_editor_lifecycle_message(
    handled: tuple[bool, Any],
    message: str,
    context: Any,
) -> tuple[bool, Any]:
    """Handle one generated editor envelope from Anki's WebView filter hook."""
    if handled[0]:
        return handled
    try:
        command = decode_webview_bridge_command(message)
    except (AssertionError, KeyError, TypeError, ValueError):
        return handled
    if command.name not in {
        EDITOR_INTENT_RECEIPT,
        EDITOR_RECORDER_COMMAND,
        EDITOR_SOURCE_MUTATION,
    }:
        return handled

    try:
        if command.name == EDITOR_INTENT_RECEIPT:
            _handle_intent_receipt(context, EditorIntentReceipt.from_dict(command.payload))
        elif command.name == EDITOR_RECORDER_COMMAND:
            _handle_recorder_command(context, RecorderCommand.from_dict(command.payload))
        else:
            _handle_source_mutation(context, SourceMutationCommand.from_dict(command.payload))
    except (AssertionError, KeyError, TypeError, ValueError) as exc:
        logger.warning("editor lifecycle envelope rejected | command=%s error=%s", command.name, exc)
    return True, None


def _handle_intent_receipt(editor: Any, receipt: EditorIntentReceipt) -> None:
    if not _current_schema(receipt.schema_version):
        return
    consumed = consume_editor_intent_receipt(editor_runtime.SESSIONS.get(editor), receipt)
    logger.debug(
        "editor intent receipt | delivery_id=%s outcome=%s consumed=%s",
        receipt.delivery_id,
        receipt.outcome.value,
        consumed,
    )


def _handle_recorder_command(editor: Any, command: RecorderCommand) -> None:
    if not _current_schema(command.schema_version):
        return
    session = editor_runtime.SESSIONS.get(editor)
    logger.debug(
        "editor recorder command received | kind=%s field=%s current_field=%s "
        "session_field=%s editor_session=%s active_attempt=%s",
        command.kind.value,
        command.field_ord,
        getattr(editor, "currentField", None),
        getattr(session, "field_index", None),
        getattr(session, "editor_session_id", None),
        getattr(getattr(editor_runtime.RECORDER_SERVICE, "active_attempt", None), "attempt_id", None),
    )
    if session is None:
        logger.debug("editor recorder command rejected | reason=session_missing")
        return
    if command.kind is RecorderCommandKind.START:
        editor_callbacks.record_learner_voice(
            editor,
            field_index=command.field_ord,
            graph_settings=command.graph_settings,
            start_cursor_ms=command.start_cursor_ms,
        )
        return
    attempt = editor_runtime.RECORDER_SERVICE.active_attempt
    if (
        attempt is None
        or attempt.target.editor_session_id != session.editor_session_id
        or attempt.target.field_index != command.field_ord
    ):
        logger.debug("editor recorder command rejected | reason=active_attempt_target_mismatch")
        return
    if command.kind is RecorderCommandKind.STOP:
        editor_callbacks.stop_learner_recording(editor)
        return
    reason = command.reason.value if command.reason is not None else "user"
    editor_callbacks.cancel_learner_recording(editor, reason=reason)


def _handle_source_mutation(editor: Any, command: SourceMutationCommand) -> None:
    if not _current_schema(command.schema_version):
        return
    if not _target_matches_current_editor(editor, command):
        session = editor_runtime.SESSIONS.get(editor)
        current_target = (
            session.backend_media_target(command.target.field_ord)
            if session is not None
            else None
        )
        logger.warning(
            "editor source recovery rejected | failure_id=%s "
            "target_editor_session=%s current_editor_session=%s "
            "target_note=%s current_note=%s target_generation=%s current_generation=%s "
            "target_field=%s session_field=%s current_field=%s "
            "target_source=%s current_source=%s recorder_status=%s recorder_busy=%s",
            command.failure.failure_id,
            command.target.editor_session_id,
            getattr(session, "editor_session_id", None),
            command.target.note_id,
            getattr(session, "note_id", None),
            command.target.backend_media_generation,
            getattr(current_target, "generation", None),
            command.target.field_ord,
            getattr(session, "field_index", None),
            getattr(editor, "currentField", None),
            command.target.source_filename,
            getattr(current_target, "source_filename", None),
            getattr(getattr(session, "recorder", None), "status", None),
            editor_runtime.RECORDER_SERVICE.is_busy,
        )
        return
    logger.info(
        "editor source recovery accepted | failure_id=%s attempt_id=%s",
        command.failure.failure_id,
        command.failure.attempt_id,
    )
    editor_callbacks.convert_async(
        editor,
        EditorCommandPayload(
            command="aqe:convert",
            field_ord=command.target.field_ord,
            source_filename=command.target.source_filename,
            overrides=EditorCommandOverrides(target_format="mp3"),
        ),
    )


def _target_matches_current_editor(editor: Any, command: SourceMutationCommand) -> bool:
    session = editor_runtime.SESSIONS.get(editor)
    target = command.target
    if session is None:
        return False
    try:
        current_target = editor_runtime.bind_backend_media_target(
            editor,
            session,
            target.field_ord,
            target.source_filename,
        )
    except (AudioQuickEditorError, OSError):
        return False
    return bool(
        current_target is not None
        and not editor_runtime.RECORDER_SERVICE.is_busy
        and session.recorder.status not in {
            "starting", "recording", "stopping", "finalizing", "analyzing",
        }
        and target.editor_session_id == session.editor_session_id
        and target.note_id == session.note_id
        and target.field_ord == getattr(editor, "currentField", None)
        and target.backend_media_generation == current_target.generation
        and target.source_filename == current_target.source_filename
    )


def _current_schema(value: object) -> bool:
    return type(value) in {int, float} and value == LIFECYCLE_SCHEMA_VERSION
