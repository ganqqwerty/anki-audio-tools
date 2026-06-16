"""Playback request normalization and frontend-owned playback state updates."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .editor_playback_bounds import requested_end_ms
from .editor_session import EditorSession
from .i18n import t
from .prosody_types import clamp_cursor_ms

if TYPE_CHECKING:
    from .editor_deps_protocols import PlaybackDeps

logger = logging.getLogger(__name__)


def playback_request_values(
    session: EditorSession,
    request: Any,
    field_index: int,
    deps: PlaybackDeps,
) -> tuple[str, str, int, int | None, str, str]:
    """Normalize action, engine, cursor, and selected-region end values from a playback payload."""
    if not isinstance(request, dict):
        return "start", "native", session.cursor_ms, None, "full", "user"
    action = str(request.get("action") or "start")
    engine = str(request.get("engine") or "native")
    duration_ms = deps.visualized_duration_for_field(session, field_index, session.current_filename)
    end_ms = requested_end_ms(request.get("endMs"), duration_ms)
    cursor_ms = clamp_cursor_ms(request.get("cursorMs"), end_ms if end_ms is not None else duration_ms)
    region_mode = "selection" if request.get("regionMode") == "selection" else "full"
    raw_source = str(request.get("source") or "")
    source = raw_source if raw_source in {"chorusing", "post_edit"} else "user"
    return action, engine, cursor_ms, end_ms, region_mode, source


def toggle_native_pause_resume(
    editor: Any,
    session: EditorSession,
    field_index: int,
    action: str,
    cursor_ms: int,
    deps: PlaybackDeps,
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
    deps: PlaybackDeps,
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
        deps.eval_status(editor, playback_started_from_message(cursor_ms, source))
    else:
        deps.eval_status(editor, t("editor.playback.playing"))


def playback_started_from_message(cursor_ms: int, source: str) -> str:
    message = t("editor.playback.playing_from", {"seconds": f"{max(0.0, cursor_ms / 1000):.2f}"})
    if source == "chorusing":
        return f"{message}. {t('editor.playback.chorusing_guidance')}"
    return message
