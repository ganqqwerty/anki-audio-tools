from __future__ import annotations

from anki_audio_quick_editor.editor_pending_intent import create_pending_editor_intent
from anki_audio_quick_editor.editor_session import (
    EditorSession,
    PendingEditorStatus,
    ProcessingState,
)


def test_begin_processing_invalidates_pending_bootstrap_delivery() -> None:
    session = EditorSession(
        note_id=10,
        field_index=2,
        current_filename="clip.mp3",
        backend_media_generation=4,
    )
    create_pending_editor_intent(
        session,
        2,
        require_graph_redraw=False,
        source_kind="generated_edit",
        expected_duration_ms=None,
    )

    guard = session.begin_processing(
        field_index=2,
        source_filename="clip.mp3",
        next_status_summary="Processing clip",
        bump_post_edit_generation=True,
    )

    assert guard.generation == 1
    assert guard.note_id == 10
    assert guard.field_index == 2
    assert guard.source_filename == "clip.mp3"
    assert session.field_index == 2
    assert session.processing.active is True
    assert session.processing.next_status_summary == "Processing clip"
    assert session.pending_editor_intent is None


def test_finish_processing_without_edit_clears_processing_and_pending_status() -> None:
    session = EditorSession(
        processing=ProcessingState(active=True, next_status_summary="pending"),
        pending_status=PendingEditorStatus(0, message="pending"),
    )

    session.finish_processing_without_edit(clear_pending_status=True)

    assert session.processing.active is False
    assert session.processing.next_status_summary == ""
    assert session.pending_status is None
