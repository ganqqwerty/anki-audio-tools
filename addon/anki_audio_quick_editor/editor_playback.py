"""Playback behavior for the editor bridge."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from .audio_state import AudioProcessingConfig
from .editor_session import EditorSession
from .media_paths import existing_media_file_path
from .prosody_types import clamp_cursor_ms

logger = logging.getLogger(__name__)


def stop_audio_playback() -> None:
    """Stop Anki audio playback on a best-effort basis."""
    try:
        from aqt.sound import av_player

        av_player.stop_and_clear_queue()
    except Exception as exc:  # pragma: no cover - depends on active Anki audio backend
        logger.info("audio stop failed: %s", exc)


def stop_session_playback(session: EditorSession, deps: Any) -> None:
    """Stop playback and clear transient playback state for an editor session."""
    session.playback_generation += 1
    session.playback_preparing = False
    session.playback_active = False
    session.playback_paused = False
    deps.stop_audio_playback()
    deps.cleanup_temp_playback(session)


def cleanup_temp_playback(session: EditorSession) -> None:
    """Remove the generated temporary playback segment, if one exists."""
    temp_path = session.temp_playback_path
    session.temp_playback_path = None
    if temp_path is None:
        return
    try:
        if temp_path.parent.name.startswith("aqe_playback_"):
            shutil.rmtree(temp_path.parent, ignore_errors=True)
        else:
            temp_path.unlink(missing_ok=True)
    except OSError as exc:
        logger.info("temporary playback cleanup failed: %s", exc)


def play(editor: Any, deps: Any) -> None:
    """Ask the frontend for a playback request and apply it."""
    deps.eval_with_callback(
        editor,
        "window.__aqeGetPlaybackRequest ? window.__aqeGetPlaybackRequest() : "
        "({ action: 'start', cursorMs: 0 })",
        lambda request: deps.play_with_request(editor, request),
    )


def play_ended(editor: Any, deps: Any) -> None:
    """Handle the frontend/native playback-ended callback."""
    session = deps.sessions.get(editor)
    if session:
        deps.stop_session_playback(session)
    else:
        deps.stop_audio_playback()
    deps.eval_status(editor, "")


def play_with_request(editor: Any, request: Any, deps: Any) -> None:
    """Apply a frontend playback request."""
    if getattr(editor, "note", None) is None:
        return
    session, source_path = deps.session_and_source(editor)
    if deps.is_busy(session):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    field_index = deps.current_field_index(editor)
    action, engine, cursor_ms = playback_request_values(session, request, field_index, deps)
    session.cursor_ms = cursor_ms
    if engine == "html":
        apply_html_playback_request(editor, session, field_index, action, cursor_ms, deps)
        return
    if toggle_native_pause_resume(editor, session, field_index, action, cursor_ms, deps):
        return

    deps.start_playback_from_cursor(editor, session, source_path, field_index, cursor_ms)


def playback_request_values(
    session: EditorSession,
    request: Any,
    field_index: int,
    deps: Any,
) -> tuple[str, str, int]:
    """Normalize action, engine, and cursor values from a playback payload."""
    if not isinstance(request, dict):
        return "start", "native", session.cursor_ms
    action = str(request.get("action") or "start")
    engine = str(request.get("engine") or "native")
    duration_ms = request.get("endMs")
    if duration_ms is None:
        duration_ms = deps.visualized_duration_for_field(session, field_index, session.current_filename)
    cursor_ms = clamp_cursor_ms(request.get("cursorMs"), duration_ms)
    return action, engine, cursor_ms


def toggle_native_pause_resume(
    editor: Any,
    session: EditorSession,
    field_index: int,
    action: str,
    cursor_ms: int,
    deps: Any,
) -> bool:
    """Toggle native playback pause/resume when possible."""
    if action not in {"pause", "resume"} or not session.playback_active:
        return False
    from aqt.sound import av_player

    try:
        av_player.toggle_pause()
    except Exception as exc:  # pragma: no cover - depends on active Anki audio backend
        logger.info("audio pause/resume failed: %s", exc)
        deps.eval_status(editor, "Pause/resume was not available.", kind="warning")
        return True
    session.playback_paused = action == "pause"
    state = "paused" if session.playback_paused else "playing"
    deps.eval_playback_state(editor, field_index, state, cursor_ms)
    deps.eval_status(editor, "Paused" if session.playback_paused else "Playing")
    return True


def apply_html_playback_request(
    editor: Any,
    session: EditorSession,
    field_index: int,
    action: str,
    cursor_ms: int,
    deps: Any,
) -> None:
    """Update backend state for frontend-owned HTML audio playback."""
    if action == "pause":
        session.cursor_ms = cursor_ms
        session.playback_preparing = False
        session.playback_active = True
        session.playback_paused = True
        deps.set_busy(editor, False)
        deps.eval_status(editor, "Paused")
        return

    if action == "start":
        deps.stop_session_playback(session)

    session.cursor_ms = cursor_ms
    session.field_index = field_index
    session.playback_preparing = False
    session.playback_active = True
    session.playback_paused = False
    deps.set_busy(editor, False)
    if cursor_ms > 0 and action == "start":
        deps.eval_status(editor, f"Playing from {max(0.0, cursor_ms / 1000):.2f}s")
    else:
        deps.eval_status(editor, "Playing")


def start_playback_from_cursor(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    field_index: int,
    cursor_ms: int,
    deps: Any,
) -> None:
    """Start native playback, rendering a temporary segment when seeking is needed."""
    from anki.sound import SoundOrVideoTag
    from aqt.sound import av_player

    filename = session.current_filename or source_path.name
    play_path = existing_media_file_path(Path(editor.mw.col.media.dir()), filename) or source_path
    deps.stop_session_playback(session)
    session.cursor_ms = clamp_cursor_ms(cursor_ms, session.visualized_duration_ms)
    offset_seconds = max(0.0, session.cursor_ms / 1000)
    if offset_seconds <= 0:
        av_player.play_tags([SoundOrVideoTag(str(play_path))])
        session.playback_active = True
        session.playback_paused = False
        deps.eval_playback_state(editor, field_index, "playing", session.cursor_ms)
        deps.eval_status(editor, "Playing")
        return

    config = AudioProcessingConfig.from_config(deps.config(editor))
    session.playback_generation += 1
    generation = session.playback_generation
    session.playback_preparing = True
    session.playback_active = True
    session.playback_paused = False
    playback_cursor_ms = session.cursor_ms
    deps.set_busy(editor, True, "Preparing playback...")
    deps.eval_playback_state(editor, field_index, "stopped", session.cursor_ms)

    def _run() -> None:
        try:

            def _show_command(command: tuple[str, ...]) -> None:
                rendered = deps.format_ffmpeg_command(command)
                status_message = "Preparing playback with ffmpeg"
                command_text = ""
                if config.show_ffmpeg_commands:
                    status_message = f"{status_message}: {rendered}"
                    command_text = rendered
                deps.main(editor, lambda: deps.set_busy(editor, True, status_message, command_text))

            result = deps.render_playback_segment(
                play_path,
                playback_cursor_ms,
                config,
                on_command=_show_command,
            )
            deps.main(
                editor,
                lambda: deps.playback_segment_ready(
                    editor,
                    generation,
                    field_index,
                    playback_cursor_ms,
                    result.output_path,
                ),
            )
        except Exception as exc:
            message = str(exc)
            deps.main(editor, lambda: deps.playback_segment_failed(editor, generation, message))

    deps.threading.Thread(target=_run, daemon=True).start()


def playback_segment_ready(
    editor: Any,
    generation: int,
    field_index: int,
    cursor_ms: int,
    playback_path: Path,
    deps: Any,
) -> None:
    """Start native playback once an offset playback segment has rendered."""
    session = deps.sessions.get(editor)
    if session is None or generation != session.playback_generation:
        shutil.rmtree(playback_path.parent, ignore_errors=True)
        return
    from anki.sound import SoundOrVideoTag
    from aqt.sound import av_player

    session.playback_preparing = False
    session.temp_playback_path = playback_path
    session.playback_active = True
    session.playback_paused = False
    av_player.stop_and_clear_queue()
    av_player.play_tags([SoundOrVideoTag(str(playback_path))])
    deps.set_busy(editor, False)
    deps.eval_playback_state(editor, field_index, "playing", cursor_ms)
    deps.eval_status(editor, f"Playing from {max(0.0, cursor_ms / 1000):.2f}s")


def playback_segment_failed(editor: Any, generation: int, message: str, deps: Any) -> None:
    """Report playback segment render failure if it belongs to the active generation."""
    session = deps.sessions.get(editor)
    if session is None or generation != session.playback_generation:
        return
    session.playback_preparing = False
    session.playback_active = False
    session.playback_paused = False
    deps.set_busy(editor, False)
    deps.eval_playback_state(editor, session.field_index, "stopped", session.cursor_ms)
    deps.eval_status(editor, message or "Could not prepare playback.", kind="error")


def set_cursor_from_web(editor: Any, deps: Any) -> None:
    """Update the session cursor from frontend state."""

    def _apply(value: Any) -> None:
        if getattr(editor, "note", None) is None:
            return
        session, source_path = deps.session_and_source(editor)
        cursor_value = value.get("cursorMs") if isinstance(value, dict) else value
        field_index = deps.current_field_index(editor)
        duration_ms = deps.visualized_duration_for_field(session, field_index, session.current_filename)
        session.cursor_ms = clamp_cursor_ms(cursor_value, duration_ms)
        if isinstance(value, dict) and value.get("restartPlayback"):
            if value.get("engine") == "html":
                session.playback_active = True
                session.playback_paused = False
                return
            deps.start_playback_from_cursor(editor, session, source_path, field_index, session.cursor_ms)

    deps.eval_with_callback(
        editor,
        "window.__aqeGetCursorIntent ? window.__aqeGetCursorIntent() : "
        "(window.__aqeGetCursorMs ? window.__aqeGetCursorMs() : 0)",
        _apply,
    )
