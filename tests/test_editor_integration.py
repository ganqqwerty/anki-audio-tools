"""Tests for the thin Anki editor bridge layer."""

from __future__ import annotations

import importlib
import logging
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    BRIDGE_COMMANDS,
    EditorSession,
    UndoHistory,
    _analysis_finished,
    _audio_field_indices,
    _handle_bridge_command,
    _is_busy,
    _play_with_request,
    _playback_segment_ready,
    _reset_editor_session_for_note_load,
    _set_busy,
    _set_cursor_from_web,
    register_editor_hooks,
)
from anki_audio_quick_editor.errors import (
    AudioProcessingError,
    MissingDeepFilterError,
    MissingMpSenetError,
)
from anki_audio_quick_editor.file_reveal import reveal_file
from anki_audio_quick_editor.prosody_cache import (
    _ANALYSIS_CACHE,
    analyze_prosody_cached,
    prosody_cache_key,
)
from anki_audio_quick_editor.prosody_types import ProsodyPoint, ProsodyTrack
from anki_audio_quick_editor.support import (
    MP_SENET_SUPPORT_HINT,
    clear_latest_mp_senet_support_incident,
    latest_mp_senet_support_incident,
)


def test_register_editor_hooks() -> None:
    hooks = SimpleNamespace(editor_did_init=MagicMock(), editor_will_load_note=MagicMock())

    register_editor_hooks(hooks)

    hooks.editor_did_init.append.assert_called_once()
    hooks.editor_will_load_note.append.assert_called_once()


def test_entrypoint_registers_editor_startup_hook() -> None:
    import aqt

    import anki_audio_quick_editor

    importlib.reload(anki_audio_quick_editor)

    assert aqt.gui_hooks.main_window_did_init.append.call_count == 6


def test_editor_init_registers_all_bridge_commands(tmp_path: Path) -> None:
    from anki_audio_quick_editor.editor_integration import _on_editor_did_init

    editor = SimpleNamespace(_links={}, mw=MagicMock(), web=MagicMock(), currentField=0)
    editor.mw.col.media.dir.return_value = str(tmp_path)

    _on_editor_did_init(editor)

    assert set(BRIDGE_COMMANDS) <= set(editor._links)


def test_audio_field_indices_are_detected_from_note_fields() -> None:
    note = SimpleNamespace(fields=["plain", "<b>[sound:first.mp3]</b>", "[sound:movie.mp4]"])

    assert _audio_field_indices(note) == [1]


def test_undo_history_restores_last_audio_modification_only() -> None:
    history = UndoHistory()
    original = AudioEditState("source.wav")
    trimmed = original.trim_left(100)

    history.push(original, "source.wav")
    history.push(trimmed, "source__aqe_first.mp3")

    assert history.pop().filename == "source__aqe_first.mp3"
    assert history.pop().filename == "source.wav"
    assert history.pop() is None


def test_editor_undo_and_redo_restore_audio_references_without_processing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    original = media_dir / "clip.mp3"
    generated = media_dir / "clip__aqe_first.mp3"
    original.write_bytes(b"original")
    generated.write_bytes(b"generated")
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip__aqe_first.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    generated_state = AudioEditState("clip.mp3", speed=1.1)
    session = EditorSession(
        state=generated_state,
        field_index=0,
        current_filename="clip__aqe_first.mp3",
        source_mtime_ns=generated.stat().st_mtime_ns,
    )
    session.undo_history.push(AudioEditState("clip.mp3"), "clip.mp3")
    _SESSIONS[editor] = session

    monkeypatch.setattr("anki_audio_quick_editor.editor_integration._stop_audio_playback", lambda: None)

    _handle_bridge_command(editor, "aqe:undo")

    assert editor.note.fields == ["[sound:clip.mp3]"]
    assert session.state == AudioEditState("clip.mp3")
    assert session.current_filename == "clip.mp3"
    assert session.redo_history.pop().filename == "clip__aqe_first.mp3"

    session.redo_history.push(generated_state, "clip__aqe_first.mp3")
    _handle_bridge_command(editor, "aqe:redo")

    assert editor.note.fields == ["[sound:clip__aqe_first.mp3]"]
    assert session.state == generated_state
    assert session.current_filename == "clip__aqe_first.mp3"
    assert session.undo_history.pop().filename == "clip.mp3"
    assert editor.loadNote.call_count == 2


def test_editor_settings_command_opens_settings_and_refreshes_after_save(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"audio")
    callbacks: list[Callable[[], None]] = []
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        analysis_busy=True,
        playback_active=True,
        playback_paused=True,
        playback_preparing=True,
    )
    _SESSIONS[editor] = session

    def fake_settings_opener(callback):
        callbacks.append(callback)

    monkeypatch.setattr("anki_audio_quick_editor.editor_integration._SETTINGS_OPENER", fake_settings_opener)
    monkeypatch.setattr("anki_audio_quick_editor.editor_integration._stop_audio_playback", lambda: None)

    _handle_bridge_command(editor, "aqe:settings")

    assert len(callbacks) == 1
    assert any("Opened settings." in call.args[0] for call in editor.web.eval.call_args_list)

    callbacks[0]()

    assert session.analysis_generation == 1
    assert session.processing is False
    assert session.analysis_busy is False
    assert session.playback_active is False
    assert session.playback_paused is False
    assert session.playback_preparing is False
    assert editor.loadNote.call_args.args == ()
    assert editor.loadNote.call_args.kwargs == {"focusTo": 0}
    assert any("window.__aqeEditorDispose" in call.args[0] for call in editor.web.eval.call_args_list)


def test_prosody_cache_key_uses_path_size_and_mtime(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"one")
    first_key = prosody_cache_key(source)
    source.write_bytes(b"one-two")
    second_key = prosody_cache_key(source)

    assert first_key[0] == str(source)
    assert second_key[0] == str(source)
    assert first_key[1] != second_key[1]
    assert isinstance(first_key[2], int)


def test_prosody_cache_reuses_matching_file_identity(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    track = ProsodyTrack(
        duration_ms=1000,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename=source.name,
        analyzer_name="test",
    )
    calls: list[Path] = []

    def fake_analyze(path: Path, _config: AudioProcessingConfig) -> ProsodyTrack:
        calls.append(path)
        return track

    monkeypatch.setattr("anki_audio_quick_editor.prosody_cache.analyze_prosody", fake_analyze)
    _ANALYSIS_CACHE.clear()

    assert analyze_prosody_cached(source, AudioProcessingConfig()) is track
    assert analyze_prosody_cached(source, AudioProcessingConfig()) is track
    assert calls == [source]


def test_set_busy_falls_back_to_session_field_index() -> None:
    class Editor:
        pass

    editor = Editor()
    editor.currentField = None
    editor.web = MagicMock()
    _SESSIONS[editor] = EditorSession(field_index=2)

    _set_busy(editor, False)

    assert "window.__aqeSetBusy" in editor.web.eval.call_args.args[0]
    assert "(2, false" in editor.web.eval.call_args.args[0]


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

    monkeypatch.setattr("anki_audio_quick_editor.editor_integration._stop_audio_playback", lambda: None)
    monkeypatch.setattr("anki_audio_quick_editor.editor_integration._cleanup_temp_playback", lambda current: setattr(current, "temp_playback_path", None))

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
        "anki_audio_quick_editor.editor_integration._stop_audio_playback",
        lambda: stop_calls.append("stop"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration.render_playback_segment",
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
        "anki_audio_quick_editor.editor_integration._eval_with_callback",
        lambda _editor, _script, callback: callback(
            {"cursorMs": 1400, "restartPlayback": True, "engine": "html"}
        ),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration._start_playback_from_cursor",
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
        "anki_audio_quick_editor.editor_integration._eval_with_callback",
        lambda _editor, _script, callback: callback(
            {"cursorMs": 700, "restartPlayback": True, "engine": "html"}
        ),
    )

    _set_cursor_from_web(editor)

    editor.web.eval.assert_not_called()


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

    monkeypatch.setattr("anki_audio_quick_editor.editor_integration.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration._eval_with_callback",
        lambda _editor, _script, callback: callback({"ord": 1, "sourceFilename": "field-two.mp3"}),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration._analyze_prosody_cached",
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

    monkeypatch.setattr("anki_audio_quick_editor.editor_integration.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration._analyze_prosody_cached",
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
        "anki_audio_quick_editor.editor_integration._eval_with_callback",
        lambda _editor, _script, callback: callback({"ord": 0, "sourceFilename": "old.mp3"}),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration._analyze_prosody_cached",
        lambda *_args, **_kwargs: pytest.fail("stale graph requests should not analyze audio"),
    )

    _handle_bridge_command(editor, "aqe:analyze-field")

    assert session.state == AudioEditState("new.mp3")
    assert [entry.filename for entry in session.undo_history.entries] == ["new.mp3"]
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any("window.__aqeSetBusy && window.__aqeSetBusy(0, false" in call for call in evals)
    assert any("window.__aqeSetVisualizerStatus && window.__aqeSetVisualizerStatus(0" in call for call in evals)


def test_note_load_reset_skips_same_note_reload(monkeypatch) -> None:
    class Editor:
        pass

    editor = Editor()
    session = EditorSession(
        note_id=12,
        state=AudioEditState("source.mp3"),
        field_index=0,
        current_filename="source.mp3",
        analysis_generation=5,
        playback_generation=3,
    )
    _SESSIONS[editor] = session
    stop_calls: list[str] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration._stop_audio_playback",
        lambda: stop_calls.append("stop"),
    )

    _reset_editor_session_for_note_load(editor, 12)

    assert stop_calls == []
    assert session.note_id == 12
    assert session.state == AudioEditState("source.mp3")
    assert session.current_filename == "source.mp3"
    assert session.analysis_generation == 5
    assert session.playback_generation == 3


def test_reveal_file_selects_file_on_macos(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.file_reveal.platform.system", lambda: "Darwin")
    monkeypatch.setattr(
        "anki_audio_quick_editor.file_reveal._run_detached",
        lambda command: commands.append(command),
    )

    reveal_file(source)

    assert commands == [("open", "-R", str(source.resolve()))]


def test_reveal_file_selects_file_on_windows(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.file_reveal.platform.system", lambda: "Windows")
    monkeypatch.setattr(
        "anki_audio_quick_editor.file_reveal._run_detached",
        lambda command: commands.append(command),
    )

    reveal_file(source)

    assert commands == [("explorer", f"/select,{source.resolve()}")]


def test_reveal_file_opens_parent_folder_elsewhere(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    folders: list[Path] = []

    monkeypatch.setattr("anki_audio_quick_editor.file_reveal.platform.system", lambda: "Linux")
    monkeypatch.setattr(
        "anki_audio_quick_editor.file_reveal._open_parent_folder",
        lambda folder: folders.append(folder),
    )

    reveal_file(source)

    assert folders == [source.resolve().parent]


def test_standard_denoise_replaces_current_media_and_resets_state(tmp_path: Path, monkeypatch) -> None:
    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self) -> None:
            self._target()

    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"source")
    rendered: list[Path] = []

    def fake_render_noise_reduced_audio(source_path: Path, _config: AudioProcessingConfig, output_path: Path, **_kwargs) -> None:
        rendered.append(source_path)
        output_path.write_bytes(b"cleaned")

    def fake_write_data(desired_name: str, data: bytes) -> str:
        saved_path = media_dir / desired_name
        saved_path.write_bytes(data)
        return desired_name

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(
                return_value={
                    "deep_filter_path": "/bin/deep-filter",
                    "deep_filter_post_filter": True,
                }
            ),
        ),
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=MagicMock(return_value=str(media_dir)),
                write_data=MagicMock(side_effect=fake_write_data),
            )
        ),
    )
    _SESSIONS[editor] = EditorSession(
        state=AudioEditState("clip.mp3", volume_db=3.0),
        field_index=0,
        current_filename="clip.mp3",
    )
    _SESSIONS[editor].redo_history.push(AudioEditState("clip.mp3"), "redo.mp3")

    monkeypatch.setattr("anki_audio_quick_editor.editor_integration.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration.render_noise_reduced_audio",
        fake_render_noise_reduced_audio,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_integration._stop_audio_playback", lambda: None)

    _handle_bridge_command(editor, "aqe:denoise-standard")

    saved_name = editor.mw.col.media.write_data.call_args.args[0]
    session = _SESSIONS[editor]
    assert rendered == [source]
    assert editor.note.fields == [f"[sound:{saved_name}]"]
    assert session.undo_history.pop().filename == "clip.mp3"
    assert session.redo_history.pop() is None
    assert session.state == AudioEditState(source_file=saved_name)
    assert session.current_filename == saved_name
    assert session.processing is False
    editor.loadNote.assert_called_once_with(focusTo=0)

def test_mp_senet_replaces_current_media_and_resets_state(tmp_path: Path, monkeypatch) -> None:
    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self) -> None:
            self._target()

    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"source")
    rendered: list[Path] = []

    def fake_render_mp_senet_audio(source_path: Path, _config: AudioProcessingConfig, output_path: Path, **_kwargs) -> None:
        rendered.append(source_path)
        output_path.write_bytes(b"denoised")

    def fake_write_data(desired_name: str, data: bytes) -> str:
        saved_path = media_dir / desired_name
        saved_path.write_bytes(data)
        return desired_name

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=MagicMock(return_value=str(media_dir)),
                write_data=MagicMock(side_effect=fake_write_data),
            )
        ),
    )
    _SESSIONS[editor] = EditorSession(
        state=AudioEditState("clip.mp3", volume_db=3.0),
        field_index=0,
        current_filename="clip.mp3",
    )

    monkeypatch.setattr("anki_audio_quick_editor.editor_integration.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration.render_mp_senet_audio",
        fake_render_mp_senet_audio,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_integration._stop_audio_playback", lambda: None)

    _handle_bridge_command(editor, "aqe:mp-senet")

    saved_name = editor.mw.col.media.write_data.call_args.args[0]
    session = _SESSIONS[editor]
    assert rendered == [source]
    assert editor.note.fields == [f"[sound:{saved_name}]"]
    assert session.undo_history.pop().filename == "clip.mp3"
    assert session.state == AudioEditState(source_file=saved_name)
    assert session.current_filename == saved_name
    assert session.processing is False
    editor.loadNote.assert_called_once_with(focusTo=0)


@pytest.mark.parametrize(
    ("failure", "expected_message"),
    [
        (
            MissingDeepFilterError(
                "DeepFilterNet's deep-filter executable is required for Standard denoise and Shorten Pauses."
            ),
            "DeepFilterNet's deep-filter executable is required",
        ),
        (
            PermissionError(13, "Permission denied", "/bin/deep-filter"),
            "Permission denied",
        ),
        (
            AudioProcessingError("error: unexpected argument '--atten-lim'"),
            "unexpected argument '--atten-lim'",
        ),
    ],
)
def test_standard_denoise_failure_logs_renders_error_and_keeps_note(
    failure: Exception,
    expected_message: str,
    tmp_path: Path,
    monkeypatch,
    caplog,
) -> None:
    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self) -> None:
            self._target()

    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"source")

    def fake_render_noise_reduced_audio(*_args, **_kwargs) -> None:
        raise failure

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=MagicMock(return_value=str(media_dir)),
                write_data=MagicMock(),
            )
        ),
    )

    monkeypatch.setattr("anki_audio_quick_editor.editor_integration.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration.render_noise_reduced_audio",
        fake_render_noise_reduced_audio,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_integration._stop_audio_playback", lambda: None)
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.editor_integration")

    _handle_bridge_command(editor, "aqe:denoise-standard")

    assert editor.note.fields == ["[sound:clip.mp3]"]
    assert editor.mw.col.media.write_data.call_count == 0
    assert _SESSIONS[editor].processing is False
    assert any(expected_message in call.args[0] for call in editor.web.eval.call_args_list)
    assert "standard denoise failed" in caplog.text
    assert expected_message in caplog.text


@pytest.mark.parametrize(
    ("failure", "expected_message"),
    [
        (
            MissingMpSenetError("MP-SENet requires the bundled mp-senet-cli runtime and model file."),
            "MP-SENet requires the bundled mp-senet-cli runtime",
        ),
        (
            PermissionError(13, "Permission denied", "/bin/mp-senet-cli"),
            "Permission denied",
        ),
        (
            AudioProcessingError("TorchScript load failed"),
            "TorchScript load failed",
        ),
    ],
)
def test_mp_senet_failure_logs_renders_error_and_keeps_note(
    failure: Exception,
    expected_message: str,
    tmp_path: Path,
    monkeypatch,
    caplog,
) -> None:
    clear_latest_mp_senet_support_incident()

    class ImmediateThread:
        def __init__(self, target, daemon=True):
            self._target = target

        def start(self) -> None:
            self._target()

    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"source")

    def fake_render_mp_senet_audio(*_args, **_kwargs) -> None:
        raise failure

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
        addonManager=SimpleNamespace(
            addonFromModule=MagicMock(return_value="addon"),
            getConfig=MagicMock(return_value={}),
        ),
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=MagicMock(return_value=str(media_dir)),
                write_data=MagicMock(),
            )
        ),
    )

    monkeypatch.setattr("anki_audio_quick_editor.editor_integration.threading.Thread", ImmediateThread)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration.render_mp_senet_audio",
        fake_render_mp_senet_audio,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_integration._stop_audio_playback", lambda: None)
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.editor_integration")

    _handle_bridge_command(editor, "aqe:mp-senet")

    assert editor.note.fields == ["[sound:clip.mp3]"]
    assert editor.mw.col.media.write_data.call_count == 0
    assert _SESSIONS[editor].processing is False
    assert any(
        expected_message in call.args[0] and MP_SENET_SUPPORT_HINT in call.args[0]
        for call in editor.web.eval.call_args_list
    )
    assert "mp-senet denoise failed" in caplog.text
    assert expected_message in caplog.text
    incident = latest_mp_senet_support_incident()
    assert incident is not None
    assert incident["operation"] == "mp_senet_denoise"
    assert incident["media_filename"] == "clip.mp3"
    assert incident["source_path"].endswith("clip.mp3")
    assert expected_message in incident["user_message"]
