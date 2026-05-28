"""Editor frontend playback state and post-edit playback helpers."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def eval_playback_state(
    editor: Any,
    field_index: int | None,
    state: str,
    cursor_ms: int,
) -> None:
    """Update playback state for a specific editor field."""
    if field_index is None:
        return
    editor.web.eval(
        "window.__aqeSetPlaybackState && window.__aqeSetPlaybackState("
        f"{json.dumps(int(field_index))}, {json.dumps(state)}, {json.dumps(int(cursor_ms))})"
    )


def request_playback_after_edit(
    editor: Any,
    field_index: int,
    deps: Any,
    *,
    require_graph_redraw: bool = False,
) -> None:
    """Record a playback request for the next frontend ready signal."""
    session = deps.sessions.get(editor)
    if session is None:
        logger.info(
            "post-edit playback request skipped: no editor session | field_index=%s require_graph_redraw=%s",
            field_index,
            require_graph_redraw,
        )
        return
    session.pending_post_edit_playback_field_index = int(field_index)
    session.pending_post_edit_playback_generation = session.post_edit_playback_generation
    session.pending_post_edit_playback_requires_graph_redraw = bool(require_graph_redraw)
    session.pending_post_edit_playback_source_filename = session.current_filename
    logger.info(
        "post-edit playback request recorded | %s",
        _post_edit_playback_session_context(session),
    )


def pending_post_edit_playback_payload(session: Any | None) -> dict[str, object] | None:
    """Return the pending post-edit playback payload for frontend injection."""
    if session is None:
        return None
    field_index = session.pending_post_edit_playback_field_index
    generation = session.pending_post_edit_playback_generation
    if field_index is None or generation is None:
        logger.debug("post-edit playback injection skipped: no pending request")
        return None
    payload = {
        "fieldOrd": int(field_index),
        "generation": int(generation),
        "requireGraphRedraw": bool(session.pending_post_edit_playback_requires_graph_redraw),
        "sourceFilename": session.pending_post_edit_playback_source_filename or "",
    }
    logger.info("post-edit playback injection payload | %s", payload)
    return payload


def handle_post_edit_playback_ready(editor: Any, payload: Any, deps: Any) -> None:
    """Start pending post-edit playback after the frontend reports readiness."""
    session = deps.sessions.get(editor)
    logger.info(
        "post-edit playback ready received | payload=%s pending=%s",
        _post_edit_playback_payload_context(payload),
        _post_edit_playback_session_context(session),
    )
    if not _post_edit_playback_ready_matches(session, payload):
        logger.warning(
            "post-edit playback ready ignored: payload does not match pending request | payload=%s pending=%s",
            _post_edit_playback_payload_context(payload),
            _post_edit_playback_session_context(session),
        )
        return

    def _clear_if_started(started: bool) -> None:
        if not started:
            logger.warning(
                "post-edit playback start was not accepted by frontend | payload=%s pending=%s",
                _post_edit_playback_payload_context(payload),
                _post_edit_playback_session_context(deps.sessions.get(editor)),
            )
            return
        current = deps.sessions.get(editor)
        if _post_edit_playback_ready_matches(current, payload):
            current.pending_post_edit_playback_field_index = None
            current.pending_post_edit_playback_generation = None
            current.pending_post_edit_playback_requires_graph_redraw = False
            current.pending_post_edit_playback_source_filename = None
            logger.info(
                "post-edit playback started; pending request cleared | payload=%s",
                _post_edit_playback_payload_context(payload),
            )
        else:
            logger.warning(
                "post-edit playback started but pending request changed before clear | payload=%s pending=%s",
                _post_edit_playback_payload_context(payload),
                _post_edit_playback_session_context(current),
            )

    deps.eval_with_callback(
        editor,
        deps.playback_after_edit_expression(int(payload.field_ord)),
        _clear_if_started,
    )


def _post_edit_playback_ready_matches(session: Any | None, payload: Any) -> bool:
    if session is None:
        return False
    field_ord = getattr(payload, "field_ord", None)
    generation = getattr(payload, "generation", None)
    source_filename = getattr(payload, "source_filename", None)
    if field_ord is None or generation is None:
        return False
    if session.pending_post_edit_playback_field_index != int(field_ord):
        return False
    if session.pending_post_edit_playback_generation != int(generation):
        return False
    pending_source = session.pending_post_edit_playback_source_filename
    return not pending_source or source_filename == pending_source


def _post_edit_playback_session_context(session: Any | None) -> dict[str, object]:
    if session is None:
        return {"hasSession": False}
    return {
        "hasSession": True,
        "fieldOrd": session.pending_post_edit_playback_field_index,
        "generation": session.pending_post_edit_playback_generation,
        "requireGraphRedraw": bool(session.pending_post_edit_playback_requires_graph_redraw),
        "sourceFilename": session.pending_post_edit_playback_source_filename,
        "currentFilename": session.current_filename,
        "sessionFieldOrd": session.field_index,
    }


def _post_edit_playback_payload_context(payload: Any) -> dict[str, object]:
    return {
        "fieldOrd": getattr(payload, "field_ord", None),
        "generation": getattr(payload, "generation", None),
        "sourceFilename": getattr(payload, "source_filename", None),
    }


def playback_after_edit_expression(field_index: int) -> str:
    """Return the frontend expression that starts playback after an edit."""
    return (
        "(() => {"
        "if (!window.__aqeScan || !window.__aqePlayAfterEdit) return false;"
        "window.__aqeScan();"
        f"return window.__aqePlayAfterEdit({json.dumps(int(field_index))});"
        "})()"
    )
