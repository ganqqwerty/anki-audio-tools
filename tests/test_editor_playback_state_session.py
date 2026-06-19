"""Editor session helpers and state transition tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_note_load_hooks import (
    reset_editor_session_for_note_load,
)
from anki_audio_quick_editor.editor_runtime import SESSIONS
from anki_audio_quick_editor.editor_runtime import is_busy as _is_busy
from anki_audio_quick_editor.editor_session import (
    AnalysisState,
    EditorSession,
    GraphVisualizationState,
    PlaybackState,
    PostEditPlaybackState,
    ProcessingState,
)


def test_note_load_reset_clears_note_specific_session_state(monkeypatch) -> None:
    class Editor:
        pass

    editor = Editor()
    editor.web = MagicMock()
    source_path = Path("/tmp/playback.mp3")
    session = EditorSession(
        note_id=10,
        state=AudioEditState("source.mp3", left_trim_ms=100),
        field_index=2,
        current_filename="generated.mp3",
        source_mtime_ns=123,
        cursor_ms=450,
        processing=ProcessingState(active=True),
        analysis=AnalysisState(
            busy=True,
            busy_fields={2},
            generation=3,
            generations_by_field={2: 3},
            graph_active_fields={2},
        ),
        graph=GraphVisualizationState(
            visualized_filename="generated.mp3",
            visualized_duration_ms=1200,
            filenames_by_field={2: "generated.mp3"},
            durations_by_field={2: 1200},
        ),
        playback=PlaybackState(
            active=True,
            paused=True,
            preparing=True,
            generation=4,
            temp_path=source_path,
        ),
        post_edit_playback=PostEditPlaybackState(
            pending_field_index=2,
            pending_generation=3,
            pending_requires_graph_redraw=True,
            pending_source_filename="generated.mp3",
        ),
    )
    session.undo_history.push(AudioEditState("source.mp3"), "generated.mp3")
    SESSIONS[editor] = session

    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.cleanup_temp_playback",
        lambda current: setattr(current.playback, "temp_path", None),
    )

    reset_editor_session_for_note_load(editor, 11)

    assert session.note_id == 11
    assert session.state is None
    assert session.field_index is None
    assert session.current_filename is None
    assert session.processing.active is False
    assert session.analysis.busy is False
    assert session.analysis.busy_fields == set()
    assert session.source_mtime_ns is None
    assert session.cursor_ms == 0
    assert session.analysis.generation == 4
    assert session.analysis.generations_by_field == {}
    assert session.analysis.graph_active_fields == set()
    assert session.graph.visualized_filename is None
    assert session.graph.visualized_duration_ms is None
    assert session.graph.filenames_by_field == {}
    assert session.graph.durations_by_field == {}
    assert session.playback.active is False
    assert session.playback.paused is False
    assert session.playback.preparing is False
    assert session.playback.generation == 5
    assert session.post_edit_playback.pending_field_index is None
    assert session.post_edit_playback.pending_generation is None
    assert session.post_edit_playback.pending_requires_graph_redraw is False
    assert session.post_edit_playback.pending_source_filename is None
    assert session.playback.temp_path is None
    assert session.undo_history.pop() is None
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any(
        "window.__aqeSetHistoryAvailability && window.__aqeSetHistoryAvailability(ord, false, false)"
        in call
        for call in evals
    )


def test_is_busy_includes_playback_preparation() -> None:
    assert _is_busy(EditorSession(playback=PlaybackState(preparing=True))) is True
    assert _is_busy(EditorSession(analysis=AnalysisState(busy_fields={0}))) is True
    assert _is_busy(EditorSession()) is False
