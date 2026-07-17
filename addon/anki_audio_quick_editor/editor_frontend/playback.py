"""Retryable post-edit bootstrap intent publication."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ..contracts_generated import AutoplayKind
from ..editor_pending_intent import (
    create_pending_editor_intent,
)
from ..editor_pending_intent import (
    pending_editor_intent_payload as _pending_editor_intent_payload,
)

if TYPE_CHECKING:
    from ..editor_deps_protocols import FrontendDeps

logger = logging.getLogger(__name__)


def request_playback_after_edit(
    editor: Any,
    field_index: int,
    deps: FrontendDeps,
    *,
    require_graph_redraw: bool = False,
    source_kind: str = "generated_edit",
    expected_duration_ms: int | None = None,
) -> None:
    """Create a retryable bootstrap delivery for frontend-local autoplay."""
    session = deps.sessions.get(editor)
    if session is None or not session.current_filename:
        logger.info("post-edit intent skipped: no bound editor session")
        return
    duration_ms = expected_duration_ms or _expected_post_edit_duration_ms(session, field_index)
    autoplay = session.post_edit_autoplay_by_field.pop(field_index, None)
    intent = create_pending_editor_intent(
        session,
        field_index,
        require_graph_redraw=require_graph_redraw,
        source_kind=source_kind,
        expected_duration_ms=duration_ms,
        autoplay_kind=autoplay.kind if autoplay is not None else AutoplayKind.ONCE,
        repeat_pause_ms=autoplay.repeat_pause_ms if autoplay is not None else 0,
    )
    logger.info(
        "editor.intent_created | delivery=%s field=%s media_generation=%s",
        intent.delivery_id,
        intent.target.field_ord,
        intent.target.backend_media_generation,
    )


def pending_editor_intent_payload(session: Any | None) -> dict[str, object] | None:
    """Return the generated pending intent for matching WebView bootstrap."""
    return _pending_editor_intent_payload(session)


def _expected_post_edit_duration_ms(session: Any, field_index: int) -> int | None:
    source_filename = session.current_filename
    graph = getattr(session, "graph", None)
    if graph is None:
        return None
    if source_filename and graph.filenames_by_field.get(field_index) == source_filename:
        duration = graph.durations_by_field.get(field_index)
        return int(duration) if isinstance(duration, (int, float)) else None
    if session.field_index == field_index and graph.visualized_filename == source_filename:
        duration = graph.visualized_duration_ms
        return int(duration) if isinstance(duration, (int, float)) else None
    return None
