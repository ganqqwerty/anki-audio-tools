"""Characterization tests for EditorSession lifecycle invariants."""

from __future__ import annotations

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_analysis import begin_field_analysis
from anki_audio_quick_editor.editor_processing import (
    _replace_standard_render_session_state,
)
from anki_audio_quick_editor.editor_runtime import is_busy as _is_busy
from anki_audio_quick_editor.editor_session import (
    AnalysisState,
    EditorSession,
    ProcessingState,
    reset_for_note_load,
)

# ---------------------------------------------------------------------------
# Cross-domain busy state (X1, X2)
# ---------------------------------------------------------------------------

def test_is_busy_true_when_processing() -> None:
    session = EditorSession(processing=ProcessingState(active=True))
    assert _is_busy(session) is True


def test_is_busy_true_when_analysis_busy() -> None:
    session = EditorSession(analysis=AnalysisState(busy_fields={0}))
    assert _is_busy(session) is True


def test_is_busy_false_for_default_session() -> None:
    session = EditorSession()
    assert _is_busy(session) is False


def test_replace_standard_render_clears_processing() -> None:
    session = EditorSession(
        state=AudioEditState("source.mp3"),
        current_filename="source.mp3",
        processing=ProcessingState(active=True),
    )

    _replace_standard_render_session_state(
        session, field_index=0, saved_name="output.mp3",
        updated_state=AudioEditState("output.mp3"),
    )

    assert session.processing.active is False


# ---------------------------------------------------------------------------
# Backend media generation (recorder/source identity)
# ---------------------------------------------------------------------------

def test_successful_same_filename_edit_advances_backend_media_generation() -> None:
    session = EditorSession(
        state=AudioEditState("source.mp3"),
        current_filename="source.mp3",
        backend_media_generation=4,
        processing=ProcessingState(active=True),
    )

    session.apply_edit_result(AudioEditState("source.mp3"), "source.mp3", "edited")

    assert session.backend_media_generation == 5


def test_redundant_note_observation_keeps_backend_media_generation_stable() -> None:
    session = EditorSession(note_id=10, backend_media_generation=4)

    assert reset_for_note_load(session, note_id=10) is False
    assert session.backend_media_generation == 4


def test_backend_media_target_reuses_generation_until_source_identity_changes() -> None:
    session = EditorSession(note_id=10, backend_media_generation=4)

    first = session.bind_backend_media_target(0, "source.m4a", 100)
    redundant = session.bind_backend_media_target(0, "source.m4a", 100)
    replaced = session.bind_backend_media_target(0, "source.m4a", 101)

    assert first.generation == 5
    assert redundant is first
    assert replaced.generation == 6


def test_backend_media_targets_are_field_addressed() -> None:
    session = EditorSession(note_id=10)

    first = session.bind_backend_media_target(0, "same.m4a", 100)
    second = session.bind_backend_media_target(1, "same.m4a", 100)

    assert first.generation == 1
    assert second.generation == 2
    assert session.backend_media_generation_for(0, "same.m4a") == 1
    assert session.backend_media_generation_for(1, "same.m4a") == 2


# ---------------------------------------------------------------------------
# Graph active fields accumulation (D5)
# ---------------------------------------------------------------------------

def test_graph_active_fields_accumulate_across_analyses() -> None:
    session = EditorSession()

    begin_field_analysis(session, 0, "file0.mp3")
    begin_field_analysis(session, 1, "file1.mp3")

    assert session.analysis.graph_active_fields == {0, 1}


def test_graph_active_fields_cleared_on_note_load() -> None:
    session = EditorSession(note_id=10)
    begin_field_analysis(session, 0, "file0.mp3")
    begin_field_analysis(session, 1, "file1.mp3")

    reset_for_note_load(session, note_id=11)

    assert session.analysis.graph_active_fields == set()


def test_graph_active_fields_re_added_after_note_load() -> None:
    session = EditorSession(note_id=10)
    begin_field_analysis(session, 0, "file0.mp3")
    reset_for_note_load(session, note_id=11)

    begin_field_analysis(session, 0, "file0.mp3")

    assert session.analysis.graph_active_fields == {0}
