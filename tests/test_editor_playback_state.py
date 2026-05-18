"""Editor session and playback callback tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    EditorSession,
    _is_busy,
    _play_with_request,
    _playback_segment_ready,
    _reset_editor_session_for_note_load,
    _set_cursor_from_web,
)


def test_note_load_reset_clears_note_specific_session_state(monkeypatch) -> None:
    class Editor:
        pass

    editor = Editor()
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
        temp_playback_path=source_path,
    )
    session.undo_history.push(AudioEditState("source.mp3"), "generated.mp3")
    _SESSIONS[editor] = session

    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.cleanup_temp_playback", lambda current: setattr(current, "temp_playback_path", None))

    _reset_editor_session_for_note_load(editor, 11)

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
    assert session.temp_playback_path is None
    assert session.undo_history.pop() is None


def test_is_busy_includes_playback_preparation() -> None:
    assert _is_busy(EditorSession(playback_preparing=True)) is True
    assert _is_busy(EditorSession(analysis_busy_fields={0})) is True
    assert _is_busy(EditorSession()) is False


def test_stale_playback_segment_completion_is_ignored_and_cleaned(tmp_path: Path) -> None:
    class Editor:
        pass

    editor = Editor()
    session = EditorSession(playback_generation=2)
    _SESSIONS[editor] = session
    temp_dir = tmp_path / "aqe_playback_stale"
    temp_dir.mkdir()
    segment = temp_dir / "aqe_playback_clip__from_700ms_deadbeef.mp3"
    segment.write_bytes(b"audio")

    _playback_segment_ready(editor, 1, 0, 700, segment)

    assert not temp_dir.exists()
    assert session.temp_playback_path is None


def test_html_playback_request_updates_session_without_native_segment(tmp_path: Path, monkeypatch) -> None:
    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"audio")
    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        source_mtime_ns=source.stat().st_mtime_ns,
        visualized_duration_ms=2000,
    )
    _SESSIONS[editor] = session
    stop_calls: list[str] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.stop_audio_playback",
        lambda: stop_calls.append("stop"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_playback_segment",
        lambda *_args, **_kwargs: pytest.fail("HTML playback should not render a segment"),
    )

    _play_with_request(editor, {"engine": "html", "action": "start", "cursorMs": 700})

    assert session.cursor_ms == 700
    assert session.playback_active is True
    assert session.playback_paused is False
    assert session.playback_preparing is False
    assert stop_calls == ["stop"]
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any("Playing from 0.70s" in call for call in evals)


def test_html_cursor_restart_intent_does_not_start_native_playback(tmp_path: Path, monkeypatch) -> None:
    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"audio")
    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        source_mtime_ns=source.stat().st_mtime_ns,
        visualized_duration_ms=2000,
    )
    _SESSIONS[editor] = session

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._eval_with_callback",
        lambda _editor, _script, callback: callback(
            {"cursorMs": 1400, "restartPlayback": True, "engine": "html"}
        ),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._start_playback_from_cursor",
        lambda *_args, **_kwargs: pytest.fail("HTML cursor restart should not start native playback"),
    )

    _set_cursor_from_web(editor)

    assert session.cursor_ms == 1400
    assert session.playback_active is True
    assert session.playback_paused is False


def test_late_html_playback_request_is_ignored_after_editor_note_is_cleared() -> None:
    editor = SimpleNamespace(note=None, currentField=0, web=MagicMock())

    _play_with_request(editor, {"engine": "html", "action": "start", "cursorMs": 700})

    editor.web.eval.assert_not_called()


def test_late_cursor_intent_is_ignored_after_editor_note_is_cleared(monkeypatch) -> None:
    editor = SimpleNamespace(note=None, currentField=0, web=MagicMock())

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._eval_with_callback",
        lambda _editor, _script, callback: callback(
            {"cursorMs": 700, "restartPlayback": True, "engine": "html"}
        ),
    )

    _set_cursor_from_web(editor)

    editor.web.eval.assert_not_called()
