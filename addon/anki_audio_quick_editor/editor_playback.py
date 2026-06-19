"""Playback behavior for the editor bridge."""

from __future__ import annotations

import logging
import shutil
from typing import TYPE_CHECKING, Any

from .editor_playback_request import (
    apply_html_playback_request,
    playback_request_values,
)
from .editor_session import EditorSession
from .error_codes import (
    AQE_AUDIO_PROCESSING_FAILED,
    AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING,
    AQE_MEDIA_REFERENCED_AUDIO_MISSING,
    coded_error,
)
from .errors import AudioQuickEditorError
from .prosody_types import clamp_cursor_ms

if TYPE_CHECKING:
    from .editor_deps_protocols import PlaybackDeps

logger = logging.getLogger(__name__)

__all__ = [
    "apply_html_playback_request",
    "cleanup_temp_playback",
    "play",
    "play_ended",
    "play_with_request",
    "playback_request_values",
    "set_cursor_from_web",
    "stop_audio_playback",
    "stop_playback",
    "stop_session_playback",
]


def stop_audio_playback() -> None:
    """Compatibility hook retained for callers that clear playback state."""


def stop_session_playback(session: EditorSession, deps: PlaybackDeps) -> None:
    """Stop playback and clear transient playback state for an editor session."""
    session.playback.stop()
    deps.stop_audio_playback()
    deps.cleanup_temp_playback(session)


def cleanup_temp_playback(session: EditorSession) -> None:
    """Remove the generated temporary playback segment, if one exists."""
    temp_path = session.playback.temp_path
    session.playback.temp_path = None
    if temp_path is None:
        return
    try:
        if temp_path.parent.name.startswith("aqe_playback_"):
            shutil.rmtree(temp_path.parent, ignore_errors=True)
        else:
            temp_path.unlink(missing_ok=True)
    except OSError as exc:
        logger.info("temporary playback cleanup failed: %s", exc)


def play(editor: Any, deps: PlaybackDeps) -> None:
    """Ask the frontend for a playback request and apply it."""
    deps.eval_with_callback(
        editor,
        "window.__aqeGetPlaybackRequest ? window.__aqeGetPlaybackRequest() : "
        "({ action: 'start', cursorMs: 0 })",
        lambda request: deps.play_with_request(editor, request),
    )


def play_ended(editor: Any, deps: PlaybackDeps) -> None:
    """Handle the frontend playback-ended callback."""
    preserve_status = stop_playback(editor, deps)
    if not preserve_status:
        deps.eval_status(editor, "")


def stop_playback(editor: Any, deps: PlaybackDeps) -> bool:
    """Stop active playback without clearing editor status text."""
    session = deps.sessions.get(editor)
    preserve_status = False
    if session:
        field_index = session.field_index if session.field_index is not None else 0
        cursor_ms = session.cursor_ms
        preserve_status = session.playback.preserve_status
        learner_was_active = session.learner_recording.playback_status != "stopped"
        deps.stop_session_playback(session)
        deps.eval_playback_state(editor, field_index, "stopped", cursor_ms)
        if learner_was_active:
            deps.eval_learner_recording_state(editor, session.learner_recording)
    else:
        deps.stop_audio_playback()
    return preserve_status


def play_with_request(editor: Any, request: Any, deps: PlaybackDeps) -> None:
    """Apply a frontend playback request."""
    if getattr(editor, "note", None) is None:
        return
    try:
        if _unsupported_playback_engine(request):
            logger.info(
                "ignoring unsupported playback engine request for field %s",
                getattr(editor, "currentField", None),
            )
            return
        session, _source_path = deps.session_and_source(editor)
        field_index = deps.current_field_index(editor)
        action, engine, cursor_ms, end_ms, region_mode, source = playback_request_values(
            session,
            request,
            field_index,
            deps,
        )
        del end_ms, region_mode
        if engine not in {"", "html"}:
            logger.info("ignoring unsupported playback engine request for field %s", field_index)
            return
        if deps.is_busy(session):
            if source != "post_edit":
                deps.eval_status(editor, deps.still_processing_message, kind="processing")
            return
        session.cursor_ms = cursor_ms
        apply_html_playback_request(editor, session, field_index, action, cursor_ms, source, deps)
    except AudioQuickEditorError as exc:
        deps.set_busy(editor, False)
        deps.eval_status(editor, _coded_playback_error(str(exc), deps), kind="error")


def _coded_playback_error(message: str, deps: PlaybackDeps) -> dict[str, str]:
    if message == deps.current_field_audio_missing:
        return coded_error(AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING, message)
    if message == deps.referenced_audio_missing:
        return coded_error(AQE_MEDIA_REFERENCED_AUDIO_MISSING, message)
    return coded_error(AQE_AUDIO_PROCESSING_FAILED, message)


def _unsupported_playback_engine(request: Any) -> bool:
    return isinstance(request, dict) and str(request.get("engine") or "html") not in {"", "html"}


def set_cursor_from_web(editor: Any, deps: PlaybackDeps) -> None:
    """Update the session cursor from frontend state."""

    def _apply(value: Any) -> None:
        if getattr(editor, "note", None) is None:
            return
        session, _source_path = deps.session_and_source(editor)
        cursor_value = value.get("cursorMs") if isinstance(value, dict) else value
        field_index = deps.current_field_index(editor)
        duration_ms = deps.visualized_duration_for_field(session, field_index, session.current_filename)
        session.cursor_ms = clamp_cursor_ms(cursor_value, duration_ms)
        if isinstance(value, dict) and value.get("restartPlayback"):
            if _unsupported_playback_engine(value):
                logger.info("ignoring unsupported playback engine cursor restart for field %s", field_index)
                return
            session.playback.active = True
            session.playback.paused = False

    deps.eval_with_callback(
        editor,
        "window.__aqeGetCursorIntent ? window.__aqeGetCursorIntent() : "
        "(window.__aqeGetCursorMs ? window.__aqeGetCursorMs() : 0)",
        _apply,
    )
