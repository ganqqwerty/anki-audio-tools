"""Editor session helpers and state transition tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_callbacks import _playback_segment_ready
from anki_audio_quick_editor.editor_note_load_hooks import (
    reset_editor_session_for_note_load,
)
from anki_audio_quick_editor.editor_runtime import SESSIONS
from anki_audio_quick_editor.editor_runtime import is_busy as _is_busy
from anki_audio_quick_editor.editor_session import EditorSession


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
        processing=True,
        analysis_busy=True,
        analysis_busy_fields={2},
        source_mtime_ns=123,
        cursor_ms=450,
        analysis_generation=3,
        analysis_generations_by_field={2: 3},
        graph_active_fields={2},
        visualized_filename="generated.mp3",
        visualized_duration_ms=1200,
        visualized_filenames_by_field={2: "generated.mp3"},
        visualized_durations_by_field={2: 1200},
        playback_active=True,
        playback_paused=True,
        playback_preparing=True,
        playback_generation=4,
        pending_post_edit_playback_field_index=2,
        pending_post_edit_playback_generation=3,
        pending_post_edit_playback_requires_graph_redraw=True,
        pending_post_edit_playback_source_filename="generated.mp3",
        temp_playback_path=source_path,
    )
    session.undo_history.push(AudioEditState("source.mp3"), "generated.mp3")
    SESSIONS[editor] = session

    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.cleanup_temp_playback",
        lambda current: setattr(current, "temp_playback_path", None),
    )

    reset_editor_session_for_note_load(editor, 11)

    assert session.note_id == 11
    assert session.state is None
    assert session.field_index is None
    assert session.current_filename is None
    assert session.processing is False
    assert session.analysis_busy is False
    assert session.analysis_busy_fields == set()
    assert session.source_mtime_ns is None
    assert session.cursor_ms == 0
    assert session.analysis_generation == 4
    assert session.analysis_generations_by_field == {}
    assert session.graph_active_fields == set()
    assert session.visualized_filename is None
    assert session.visualized_duration_ms is None
    assert session.visualized_filenames_by_field == {}
    assert session.visualized_durations_by_field == {}
    assert session.playback_active is False
    assert session.playback_paused is False
    assert session.playback_preparing is False
    assert session.playback_generation == 5
    assert session.pending_post_edit_playback_field_index is None
    assert session.pending_post_edit_playback_generation is None
    assert session.pending_post_edit_playback_requires_graph_redraw is False
    assert session.pending_post_edit_playback_source_filename is None
    assert session.temp_playback_path is None
    assert session.undo_history.pop() is None
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any(
        "window.__aqeSetHistoryAvailability && window.__aqeSetHistoryAvailability(ord, false, false)"
        in call
        for call in evals
    )


def test_is_busy_includes_playback_preparation() -> None:
    assert _is_busy(EditorSession(playback_preparing=True)) is True
    assert _is_busy(EditorSession(analysis_busy_fields={0})) is True
    assert _is_busy(EditorSession()) is False


def test_stale_playback_segment_completion_is_ignored_and_cleaned(tmp_path: Path) -> None:
    class Editor:
        pass

    editor = Editor()
    session = EditorSession(playback_generation=2)
    SESSIONS[editor] = session
    temp_dir = tmp_path / "aqe_playback_stale"
    temp_dir.mkdir()
    segment = temp_dir / "aqe_playback_clip__from_700ms_deadbeef.mp3"
    segment.write_bytes(b"audio")

    _playback_segment_ready(editor, 1, 0, 700, segment)

    assert not temp_dir.exists()
    assert session.temp_playback_path is None
