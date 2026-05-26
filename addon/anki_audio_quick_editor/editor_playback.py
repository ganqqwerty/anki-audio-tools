"""Playback behavior for the editor bridge."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from .audio_state import AudioProcessingConfig
from .diagnostics_runtime import capture_exception, new_operation_id, record_breadcrumb
from .editor_session import EditorSession
from .i18n import t
from .media_paths import existing_media_file_path
from .permission_guidance import message_with_permission_guidance
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
    session.preserve_status_during_playback = False
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
    preserve_status = False
    if session:
        field_index = session.field_index if session.field_index is not None else 0
        cursor_ms = session.cursor_ms
        preserve_status = session.preserve_status_during_playback
        deps.stop_session_playback(session)
        deps.eval_playback_state(editor, field_index, "stopped", cursor_ms)
    else:
        deps.stop_audio_playback()
    if not preserve_status:
        deps.eval_status(editor, "")


def play_with_request(editor: Any, request: Any, deps: Any) -> None:
    """Apply a frontend playback request."""
    if getattr(editor, "note", None) is None:
        return
    session, source_path = deps.session_and_source(editor)
    field_index = deps.current_field_index(editor)
    action, engine, cursor_ms, end_ms, region_mode, source = playback_request_values(session, request, field_index, deps)
    if deps.is_busy(session):
        if source != "post_edit":
            deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    session.cursor_ms = cursor_ms
    if engine == "html":
        apply_html_playback_request(editor, session, field_index, action, cursor_ms, source, deps)
        return
    if toggle_native_pause_resume(editor, session, field_index, action, cursor_ms, deps):
        return

    selected_end_ms = end_ms if region_mode == "selection" else None
    deps.start_playback_from_cursor(
        editor,
        session,
        source_path,
        field_index,
        cursor_ms,
        selected_end_ms,
        source=source,
    )


def playback_request_values(
    session: EditorSession,
    request: Any,
    field_index: int,
    deps: Any,
) -> tuple[str, str, int, int | None, str, str]:
    """Normalize action, engine, cursor, and selected-region end values from a playback payload."""
    if not isinstance(request, dict):
        return "start", "native", session.cursor_ms, None, "full", "user"
    action = str(request.get("action") or "start")
    engine = str(request.get("engine") or "native")
    duration_ms = deps.visualized_duration_for_field(session, field_index, session.current_filename)
    end_ms = _requested_end_ms(request.get("endMs"), duration_ms)
    cursor_ms = clamp_cursor_ms(request.get("cursorMs"), end_ms if end_ms is not None else duration_ms)
    region_mode = "selection" if request.get("regionMode") == "selection" else "full"
    source = "post_edit" if request.get("source") == "post_edit" else "user"
    return action, engine, cursor_ms, end_ms, region_mode, source


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
        deps.eval_status(editor, t("editor.playback.pause_unavailable"), kind="warning")
        return True
    session.playback_paused = action == "pause"
    state = "paused" if session.playback_paused else "playing"
    deps.eval_playback_state(editor, field_index, state, cursor_ms)
    deps.eval_status(editor, t("editor.playback.paused") if session.playback_paused else t("editor.playback.playing"))
    return True


def apply_html_playback_request(
    editor: Any,
    session: EditorSession,
    field_index: int,
    action: str,
    cursor_ms: int,
    source: str,
    deps: Any,
) -> None:
    """Update backend state for frontend-owned HTML audio playback."""
    if action == "pause":
        session.cursor_ms = cursor_ms
        session.playback_preparing = False
        session.playback_active = True
        session.playback_paused = True
        session.preserve_status_during_playback = False
        deps.set_busy(editor, False)
        deps.eval_status(editor, t("editor.playback.paused"))
        return
    if action == "start":
        deps.stop_session_playback(session)
    session.cursor_ms = cursor_ms
    session.field_index = field_index
    session.playback_preparing = False
    session.playback_active = True
    session.playback_paused = False
    session.preserve_status_during_playback = source == "post_edit"
    deps.set_busy(editor, False)
    if session.preserve_status_during_playback:
        return
    if cursor_ms > 0 and action == "start":
        deps.eval_status(editor, t("editor.playback.playing_from", {"seconds": f"{max(0.0, cursor_ms / 1000):.2f}"}))
    else:
        deps.eval_status(editor, t("editor.playback.playing"))


def start_playback_from_cursor(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    field_index: int,
    cursor_ms: int,
    end_ms: int | None,
    deps: Any,
    source: str = "user",
) -> None:
    """Start native playback, rendering a temporary segment when seeking or trimming is needed."""
    from anki.sound import SoundOrVideoTag
    from aqt.sound import av_player
    operation_id = new_operation_id("playback")
    filename = session.current_filename or source_path.name
    play_path = existing_media_file_path(Path(editor.mw.col.media.dir()), filename) or source_path
    deps.stop_session_playback(session)
    source_duration_ms = deps.visualized_duration_for_field(session, field_index, filename)
    playback_end_ms = _native_playback_end_ms(end_ms, source_duration_ms)
    session.cursor_ms = clamp_cursor_ms(cursor_ms, playback_end_ms if playback_end_ms is not None else source_duration_ms)
    offset_seconds = max(0.0, session.cursor_ms / 1000)
    bounded_to_selection = playback_end_ms is not None and (
        source_duration_ms is None or playback_end_ms < max(0, source_duration_ms - 20)
    )
    if offset_seconds <= 0 and not bounded_to_selection:
        record_breadcrumb(
            "editor.playback.native_started",
            source="editor",
            operation="editor.playback",
            operation_id=operation_id,
            context={"filename": str(play_path), "field_index": field_index, "cursor_ms": session.cursor_ms},
        )
        av_player.play_tags([SoundOrVideoTag(str(play_path))])
        session.playback_active = True
        session.playback_paused = False
        session.preserve_status_during_playback = source == "post_edit"
        deps.eval_playback_state(editor, field_index, "playing", session.cursor_ms)
        if not session.preserve_status_during_playback:
            deps.eval_status(editor, t("editor.playback.playing"))
        return

    config = AudioProcessingConfig.from_config(deps.config(editor))
    session.playback_generation += 1
    generation = session.playback_generation
    session.playback_preparing = True
    session.playback_active = True
    session.playback_paused = False
    session.preserve_status_during_playback = source == "post_edit"
    playback_cursor_ms = session.cursor_ms
    playback_end_context = playback_end_ms
    if not session.preserve_status_during_playback:
        deps.set_busy(editor, True, t("editor.playback.preparing"))
    deps.eval_playback_state(editor, field_index, "stopped", session.cursor_ms)
    record_breadcrumb(
        "editor.playback.segment_render_started",
        source="editor",
        operation="editor.playback",
        operation_id=operation_id,
        context={
            "filename": str(play_path),
            "field_index": field_index,
            "cursor_ms": playback_cursor_ms,
            "end_ms": playback_end_context,
        },
        flush=True,
    )

    def _run() -> None:
        try:

            def _show_command(command: tuple[str, ...]) -> None:
                rendered = deps.format_ffmpeg_command(command)
                status_message = t("editor.playback.preparing_ffmpeg")
                command_text = ""
                if config.show_ffmpeg_commands:
                    status_message = f"{status_message}: {rendered}"
                    command_text = rendered
                if not session.preserve_status_during_playback:
                    deps.main(editor, lambda: deps.set_busy(editor, True, status_message, command_text))

            result = deps.render_playback_segment(
                play_path,
                playback_cursor_ms,
                config,
                on_command=_show_command,
                end_ms=playback_end_context,
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
            message = message_with_permission_guidance(str(exc), exc)
            capture_exception(
                "editor.worker.playback_segment",
                exc,
                operation="editor.playback",
                operation_id=operation_id,
                user_message=message or t("editor.playback.prepare_failed"),
                context={
                    "filename": str(play_path),
                    "field_index": field_index,
                    "cursor_ms": playback_cursor_ms,
                    "end_ms": playback_end_context,
                },
                log=logger,
            )
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
    if not session.preserve_status_during_playback:
        deps.set_busy(editor, False)
    deps.eval_playback_state(editor, field_index, "playing", cursor_ms)
    if session.preserve_status_during_playback:
        return
    if cursor_ms > 0:
        deps.eval_status(editor, t("editor.playback.playing_from", {"seconds": f"{max(0.0, cursor_ms / 1000):.2f}"}))
    else:
        deps.eval_status(editor, t("editor.playback.playing"))


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
    deps.eval_status(editor, message or t("editor.playback.prepare_failed"), kind="error")


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
            end_ms = (
                _requested_end_ms(value.get("endMs"), duration_ms)
                if value.get("regionMode") == "selection" and value.get("endMs") is not None
                else None
            )
            deps.start_playback_from_cursor(editor, session, source_path, field_index, session.cursor_ms, end_ms)

    deps.eval_with_callback(
        editor,
        "window.__aqeGetCursorIntent ? window.__aqeGetCursorIntent() : "
        "(window.__aqeGetCursorMs ? window.__aqeGetCursorMs() : 0)",
        _apply,
    )


def _requested_end_ms(value: Any, duration_ms: int | None) -> int | None:
    if value is None:
        return duration_ms
    try:
        requested_end_ms = int(round(float(value)))
    except (TypeError, ValueError):
        requested_end_ms = 0
    upper_ms = duration_ms if duration_ms is not None else requested_end_ms
    return clamp_cursor_ms(requested_end_ms, upper_ms)


def _native_playback_end_ms(end_ms: int | None, source_duration_ms: int | None) -> int | None:
    if end_ms is None:
        return None
    upper = source_duration_ms if source_duration_ms is not None else max(0, int(end_ms))
    return clamp_cursor_ms(end_ms, upper)
