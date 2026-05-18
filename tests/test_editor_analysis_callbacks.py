"""Editor prosody analysis callback tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    EditorSession,
    _analysis_finished,
    _handle_bridge_command,
    _reset_editor_session_for_note_load,
)
from anki_audio_quick_editor.prosody_types import ProsodyPoint, ProsodyTrack


def test_stale_analysis_completion_is_ignored_after_note_load_reset() -> None:
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    session = EditorSession(
        note_id=10,
        field_index=0,
        analysis_busy=True,
        analysis_busy_fields={0},
        analysis_generation=2,
        analysis_generations_by_field={0: 2},
    )
    _SESSIONS[editor] = session
    track = ProsodyTrack(
        duration_ms=1000,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename="clip.mp3",
        analyzer_name="test",
    )

    _reset_editor_session_for_note_load(editor, 11)
    _analysis_finished(editor, 2, 0, track)

    assert session.analysis_generation == 3
    assert session.visualized_duration_ms is None
    editor.web.eval.assert_not_called()


def test_analysis_completion_renders_requested_field_when_session_tracks_another_field() -> None:
    class Editor:
        pass

    editor = Editor()
    editor.web = MagicMock()
    session = EditorSession(
        field_index=0,
        current_filename="field-one.mp3",
        analysis_busy=True,
        analysis_busy_fields={1},
        analysis_generation=2,
        analysis_generations_by_field={1: 2},
    )
    _SESSIONS[editor] = session
    track = ProsodyTrack(
        duration_ms=900,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename="field-two.mp3",
        analyzer_name="test",
    )

    _analysis_finished(editor, 2, 1, track)

    assert session.analysis_busy is False
    assert session.analysis_busy_fields == set()
    assert session.field_index == 0
    assert session.visualized_durations_by_field[1] == 900
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any("window.__aqeSetVisualizer(1," in call for call in evals)


def test_field_addressed_analysis_preserves_edit_session_history(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self) -> None:
            self._target()

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "field-one.mp3").write_bytes(b"one")
    field_two = media_dir / "field-two.mp3"
    field_two.write_bytes(b"two")
    track = ProsodyTrack(
        duration_ms=1200,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename="field-two.mp3",
        analyzer_name="test",
    )
    analyzed: list[Path] = []
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:field-one.mp3]", "[sound:field-two.mp3]"])
    editor.web = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
    )
    session = EditorSession(
        state=AudioEditState("field-one.mp3", speed=1.1),
        field_index=0,
        current_filename="field-one.mp3",
    )
    session.undo_history.push(AudioEditState("field-one.mp3"), "field-one.mp3")
    session.redo_history.push(AudioEditState("field-one.mp3", speed=1.1), "field-one__redo.mp3")
    _SESSIONS[editor] = session

    monkeypatch.setattr("anki_audio_quick_editor.editor_dependencies.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._eval_with_callback",
        lambda _editor, _script, callback: callback({"ord": 1, "sourceFilename": "field-two.mp3"}),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.analyze_prosody_cached",
        lambda path, _config: analyzed.append(path) or track,
    )

    _handle_bridge_command(editor, "aqe:analyze-field")

    assert analyzed == [field_two]
    assert session.state == AudioEditState("field-one.mp3", speed=1.1)
    assert session.field_index == 0
    assert session.current_filename == "field-one.mp3"
    assert [entry.filename for entry in session.undo_history.entries] == ["field-one.mp3"]
    assert [entry.filename for entry in session.redo_history.entries] == ["field-one__redo.mp3"]
    assert session.visualized_durations_by_field[1] == 1200
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any("window.__aqeSetVisualizer(1," in call for call in evals)


def test_manual_analysis_uses_read_only_field_path(tmp_path: Path, monkeypatch) -> None:
    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self) -> None:
            self._target()

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "field-one.mp3").write_bytes(b"one")
    field_two = media_dir / "field-two.mp3"
    field_two.write_bytes(b"two")
    track = ProsodyTrack(
        duration_ms=900,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename="field-two.mp3",
        analyzer_name="test",
    )
    analyzed: list[Path] = []
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 1
    editor.note = SimpleNamespace(fields=["[sound:field-one.mp3]", "[sound:field-two.mp3]"])
    editor.web = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
    )
    session = EditorSession(
        state=AudioEditState("field-one.mp3", volume_db=3.0),
        field_index=0,
        current_filename="field-one.mp3",
    )
    session.undo_history.push(AudioEditState("field-one.mp3"), "field-one.mp3")
    _SESSIONS[editor] = session

    monkeypatch.setattr("anki_audio_quick_editor.editor_dependencies.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.analyze_prosody_cached",
        lambda path, _config: analyzed.append(path) or track,
    )

    _handle_bridge_command(editor, "aqe:analyze")

    assert analyzed == [field_two]
    assert session.state == AudioEditState("field-one.mp3", volume_db=3.0)
    assert session.field_index == 0
    assert session.current_filename == "field-one.mp3"
    assert [entry.filename for entry in session.undo_history.entries] == ["field-one.mp3"]
    assert session.visualized_durations_by_field[1] == 900


def test_stale_field_addressed_analysis_request_is_ignored(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "new.mp3").write_bytes(b"new")
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:new.mp3]"])
    editor.web = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
    )
    session = EditorSession(
        state=AudioEditState("new.mp3"),
        field_index=0,
        current_filename="new.mp3",
    )
    session.undo_history.push(AudioEditState("new.mp3"), "new.mp3")
    _SESSIONS[editor] = session

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._eval_with_callback",
        lambda _editor, _script, callback: callback({"ord": 0, "sourceFilename": "old.mp3"}),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.analyze_prosody_cached",
        lambda *_args, **_kwargs: pytest.fail("stale graph requests should not analyze audio"),
    )

    _handle_bridge_command(editor, "aqe:analyze-field")

    assert session.state == AudioEditState("new.mp3")
    assert [entry.filename for entry in session.undo_history.entries] == ["new.mp3"]
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any("window.__aqeSetBusy && window.__aqeSetBusy(0, false" in call for call in evals)
    assert any("window.__aqeSetVisualizerStatus && window.__aqeSetVisualizerStatus(0" in call for call in evals)
