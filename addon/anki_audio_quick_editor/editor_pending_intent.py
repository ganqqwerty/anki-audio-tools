"""Retryable generated editor bootstrap intent delivery."""

from __future__ import annotations

import time
from typing import Any

from .contracts_generated import (
    AutoplayKind,
    EditorIntentReceipt,
    EditorLifecycleTarget,
    PendingEditorAutoplay,
    PendingEditorIntent,
    SourceKind,
)

EDITOR_INTENT_SCHEMA_VERSION = 1
EDITOR_INTENT_TTL_MS = 30_000


def create_pending_editor_intent(
    session: Any,
    field_index: int,
    *,
    require_graph_redraw: bool,
    source_kind: str,
    expected_duration_ms: int | None,
    autoplay_kind: AutoplayKind = AutoplayKind.ONCE,
    repeat_pause_ms: int = 0,
    now_epoch_ms: int | None = None,
) -> PendingEditorIntent:
    """Replace any prior delivery with a target-bound one-shot intent."""
    source_filename = session.current_filename
    if not source_filename:
        raise ValueError("pending editor intent requires a bound source")
    backend_media_generation = session.backend_media_generation_for(field_index, source_filename)
    session.editor_intent_sequence += 1
    now = now_epoch_ms if now_epoch_ms is not None else round(time.time() * 1000)
    intent = PendingEditorIntent(
        autoplay=PendingEditorAutoplay(
            kind=autoplay_kind,
            repeat_pause_ms=repeat_pause_ms,
            require_graph_redraw=bool(require_graph_redraw),
            expected_duration_ms=expected_duration_ms,
        ),
        delivery_id=(
            f"editor-{session.editor_session_id}-media-{backend_media_generation}"
            f"-delivery-{session.editor_intent_sequence}"
        ),
        expires_at_epoch_ms=now + EDITOR_INTENT_TTL_MS,
        schema_version=EDITOR_INTENT_SCHEMA_VERSION,
        source_kind=(
            SourceKind.EXISTING_MEDIA
            if source_kind == "existing_media"
            else SourceKind.GENERATED_EDIT
        ),
        target=EditorLifecycleTarget(
            backend_media_generation=backend_media_generation,
            editor_session_id=session.editor_session_id,
            field_ord=int(field_index),
            source_filename=source_filename,
            note_id=session.note_id,
        ),
    )
    session.pending_editor_intent = intent
    return intent


def pending_editor_intent_payload(
    session: Any | None,
    *,
    now_epoch_ms: int | None = None,
) -> dict[str, object] | None:
    """Return a matching unexpired generated delivery for WebView bootstrap."""
    if session is None or session.pending_editor_intent is None:
        return None
    intent: PendingEditorIntent = session.pending_editor_intent
    now = now_epoch_ms if now_epoch_ms is not None else round(time.time() * 1000)
    if (
        intent.schema_version != EDITOR_INTENT_SCHEMA_VERSION
        or intent.expires_at_epoch_ms <= now
        or intent.target.editor_session_id != session.editor_session_id
        or intent.target.note_id != session.note_id
        or intent.target.backend_media_generation != session.backend_media_generation_for(
            intent.target.field_ord,
            intent.target.source_filename,
        )
        or intent.target.source_filename != session.current_filename
    ):
        session.pending_editor_intent = None
        return None
    return intent.to_dict()


def consume_editor_intent_receipt(session: Any | None, receipt: EditorIntentReceipt) -> bool:
    """Retire only the exact replayable delivery acknowledged by its owner."""
    if session is None or receipt.schema_version != EDITOR_INTENT_SCHEMA_VERSION:
        return False
    intent: PendingEditorIntent | None = session.pending_editor_intent
    if (
        intent is None
        or receipt.editor_session_id != session.editor_session_id
        or receipt.delivery_id != intent.delivery_id
    ):
        return False
    session.pending_editor_intent = None
    return True
