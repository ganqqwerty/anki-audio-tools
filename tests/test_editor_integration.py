"""Core editor integration tests."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    BRIDGE_COMMANDS,
    EditorSession,
    UndoHistory,
    _audio_field_indices,
    _handle_bridge_command,
    _initial_status_by_field,
    _set_busy,
    register_editor_hooks,
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

    assert aqt.gui_hooks.main_window_did_init.append.call_count == 7


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
    reload_statuses: list[dict[int, dict[str, str]]] = []
    editor.loadNote = MagicMock(side_effect=lambda **_kwargs: reload_statuses.append(_initial_status_by_field(session)))
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    generated_state = AudioEditState("clip.mp3", speed=1.1)
    session = EditorSession(
        state=generated_state,
        field_index=0,
        current_filename="clip__aqe_first.mp3",
        status_summary="Increased speed to x1.10.",
        source_mtime_ns=generated.stat().st_mtime_ns,
    )
    session.undo_history.push(AudioEditState("clip.mp3"), "clip.mp3", status_summary="Original audio.")
    _SESSIONS[editor] = session

    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    _handle_bridge_command(editor, "aqe:undo")

    assert editor.note.fields == ["[sound:clip.mp3]"]
    assert session.state == AudioEditState("clip.mp3")
    assert session.current_filename == "clip.mp3"
    assert session.redo_history.pop().filename == "clip__aqe_first.mp3"
    assert reload_statuses[0] == {0: {"kind": "info", "message": "Undid: Original audio."}}

    session.redo_history.push(
        generated_state,
        "clip__aqe_first.mp3",
        status_summary="Increased speed to x1.10.",
    )
    _handle_bridge_command(editor, "aqe:redo")

    assert editor.note.fields == ["[sound:clip__aqe_first.mp3]"]
    assert session.state == generated_state
    assert session.current_filename == "clip__aqe_first.mp3"
    assert session.undo_history.pop().filename == "clip.mp3"
    assert editor.loadNote.call_count == 2
    assert reload_statuses[1] == {0: {"kind": "info", "message": "Redid: Increased speed to x1.10."}}
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any("window.__aqeSetHistoryAvailability && window.__aqeSetHistoryAvailability(0, false, true)" in call for call in evals)
    assert any("window.__aqeSetHistoryAvailability && window.__aqeSetHistoryAvailability(0, true, false)" in call for call in evals)
    assert sum("__aqePlayAfterEdit" in call.args[0] for call in editor.web.evalWithCallback.call_args_list) == 2




def test_editor_settings_command_opens_settings_and_refreshes_after_save(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"audio")
    callbacks: list[object] = []
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    reload_statuses: list[dict[int, dict[str, str]]] = []
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
    editor.loadNote = MagicMock(side_effect=lambda **_kwargs: reload_statuses.append(_initial_status_by_field(session)))
    _SESSIONS[editor] = session

    def fake_settings_opener(callback):
        callbacks.append(callback)

    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.SETTINGS_OPENER", fake_settings_opener)
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)

    _handle_bridge_command(editor, "aqe:settings")

    assert len(callbacks) == 1
    assert any("Opened settings." in call.args[0] for call in editor.web.eval.call_args_list)

    callbacks[0].on_saved()

    assert session.analysis_generation == 1
    assert session.processing is False
    assert session.analysis_busy is False
    assert session.playback_active is False
    assert session.playback_paused is False
    assert session.playback_preparing is False
    assert reload_statuses == [{0: {"kind": "info", "message": "Closed settings."}}]
    assert editor.loadNote.call_args.args == ()
    assert editor.loadNote.call_args.kwargs == {"focusTo": 0}
    assert any("window.__aqeEditorDispose" in call.args[0] for call in editor.web.eval.call_args_list)


def test_editor_settings_command_reports_closed_settings_without_refresh_on_close(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"audio")
    callbacks: list[object] = []

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    _SESSIONS[editor] = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
    )

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.SETTINGS_OPENER",
        lambda callback: callbacks.append(callback),
    )

    _handle_bridge_command(editor, "aqe:settings")
    callbacks[0].on_closed()

    assert any("Opened settings." in call.args[0] for call in editor.web.eval.call_args_list)
    assert any("Closed settings." in call.args[0] for call in editor.web.eval.call_args_list)
    editor.loadNote.assert_not_called()


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
