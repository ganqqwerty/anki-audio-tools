from __future__ import annotations

from anki_audio_quick_editor.editor_session import (
    EditorSession,
    PendingEditorStatus,
    PlaybackState,
    PostEditPlaybackState,
    ProcessingState,
)


def test_begin_processing_clears_incompatible_playback_state() -> None:
    session = EditorSession(
        note_id=10,
        current_filename="clip.mp3",
        playback=PlaybackState(active=True, paused=True),
        post_edit_playback=PostEditPlaybackState(generation=4),
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
    assert session.playback.active is False
    assert session.playback.paused is False
    assert session.post_edit_playback.generation == 5


def test_finish_processing_without_edit_clears_processing_playback_and_pending_status() -> None:
    session = EditorSession(
        processing=ProcessingState(active=True, next_status_summary="pending"),
        playback=PlaybackState(active=True, paused=True),
        pending_status=PendingEditorStatus(0, message="pending"),
    )

    session.finish_processing_without_edit(clear_pending_status=True)

    assert session.processing.active is False
    assert session.processing.next_status_summary == ""
    assert session.playback.active is False
    assert session.playback.paused is False
    assert session.pending_status is None


def test_post_edit_playback_request_and_clear_pending() -> None:
    state = PostEditPlaybackState(generation=3)

    state.request(1, "clip__aqe.mp3", require_graph_redraw=True)

    assert state.pending_field_index == 1
    assert state.pending_generation == 3
    assert state.pending_requires_graph_redraw is True
    assert state.pending_source_filename == "clip__aqe.mp3"
    assert state.pending_source_kind == "generated_edit"

    state.clear_pending()

    assert state.pending_field_index is None
    assert state.pending_generation is None
    assert state.pending_requires_graph_redraw is False
    assert state.pending_source_filename is None
    assert state.pending_source_kind == "generated_edit"
    assert state.pending_expected_duration_ms is None
