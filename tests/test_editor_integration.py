"""Core editor integration tests."""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_actions import BRIDGE_COMMANDS
from anki_audio_quick_editor.editor_bridge_hooks import on_editor_did_init
from anki_audio_quick_editor.editor_callbacks import _handle_bridge_command, _set_busy
from anki_audio_quick_editor.editor_integration import register_editor_hooks
from anki_audio_quick_editor.editor_media import audio_field_indices
from anki_audio_quick_editor.editor_note_load_hooks import on_editor_will_load_note
from anki_audio_quick_editor.editor_runtime import SESSIONS
from anki_audio_quick_editor.editor_session import (
    EditorSession,
    PendingEditorStatus,
    UndoHistory,
)
from anki_audio_quick_editor.editor_webview_injection import (
    _initial_status_by_field,
    editor_injection_script,
)


def test_register_editor_hooks() -> None:
    hooks = SimpleNamespace(editor_did_init=MagicMock(), editor_will_load_note=MagicMock())

    register_editor_hooks(hooks)

    hooks.editor_did_init.append.assert_called_once()
    hooks.editor_will_load_note.append.assert_called_once()
    assert hooks.editor_did_init.append.call_args.args == (on_editor_did_init,)
    assert hooks.editor_will_load_note.append.call_args.args == (on_editor_will_load_note,)


def test_entrypoint_registers_editor_startup_hook() -> None:
    import aqt

    import anki_audio_quick_editor

    importlib.reload(anki_audio_quick_editor)

    assert aqt.gui_hooks.main_window_did_init.append.call_count == 10


def test_editor_init_registers_all_bridge_commands(tmp_path: Path) -> None:
    editor = SimpleNamespace(_links={}, mw=MagicMock(), web=MagicMock(), currentField=0)
    editor.mw.col.media.dir.return_value = str(tmp_path)

    on_editor_did_init(editor)

    assert set(BRIDGE_COMMANDS) <= set(editor._links)


def test_audio_field_indices_are_detected_from_note_fields() -> None:
    note = SimpleNamespace(fields=["plain", "<b>[sound:first.mp3]</b>", "[sound:movie.mp4]"])

    assert audio_field_indices(note) == [1]


def test_editor_injection_script_never_probes_source_audio_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"audio")

    class Editor:
        pass

    editor = Editor()
    editor.mw = SimpleNamespace(
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
        addonManager=SimpleNamespace(
            addonFromModule=lambda _module: "addon",
            getConfig=lambda _addon: {
                "visible_editor_buttons": ["aqe:reduce-size"],
            },
        ),
    )
    note = SimpleNamespace(fields=["[sound:clip.mp3]"])

    def fail_probe(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("editor injection must not probe source metadata")

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_webview_injection.probe_audio_metadata",
        fail_probe,
        raising=False,
    )

    script = editor_injection_script(editor, note)

    match = re.search(r"window\.__AQE_EDITOR_CONFIG__ = (?P<config>\{.*?\});", script)
    assert match is not None
    config = json.loads(match.group("config"))
    assert config["audioFieldMetadata"] == {}
    assert config["audioFieldSources"] == {"0": "clip.mp3"}


def test_editor_injection_script_does_not_probe_when_compress_audio_hidden(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"audio")

    class Editor:
        pass

    editor = Editor()
    editor.mw = SimpleNamespace(
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
        addonManager=SimpleNamespace(
            addonFromModule=lambda _module: "addon",
            getConfig=lambda _addon: {
                "visible_editor_buttons": ["aqe:slower"],
            },
        ),
    )
    note = SimpleNamespace(fields=["[sound:clip.mp3]"])

    def fail_probe(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("hidden Compress Audio must not probe source metadata")

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_webview_injection.probe_audio_metadata",
        fail_probe,
        raising=False,
    )

    script = editor_injection_script(editor, note)

    match = re.search(r"window\.__AQE_EDITOR_CONFIG__ = (?P<config>\{.*?\});", script)
    assert match is not None
    config = json.loads(match.group("config"))
    assert config["visibleEditorButtons"] == ["aqe:slower"]
    assert config["audioFieldMetadata"] == {}


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
        status_summary="Increased speed to x1.5.",
        source_mtime_ns=generated.stat().st_mtime_ns,
    )
    session.undo_history.push(AudioEditState("clip.mp3"), "clip.mp3", status_summary="Original audio.")
    SESSIONS[editor] = session

    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    _handle_bridge_command(editor, "aqe:undo")

    assert editor.note.fields == ["[sound:clip.mp3]"]
    assert session.state == AudioEditState("clip.mp3")
    assert session.current_filename == "clip.mp3"
    assert session.redo_history.pop().filename == "clip__aqe_first.mp3"
    assert reload_statuses[0] == {0: {"kind": "info", "message": "Undid: Original audio."}}
    assert session.pending_status == PendingEditorStatus(0, message="Undid: Original audio.")

    session.redo_history.push(
        generated_state,
        "clip__aqe_first.mp3",
        status_summary="Increased speed to x1.5.",
    )
    _handle_bridge_command(editor, "aqe:redo")

    assert editor.note.fields == ["[sound:clip__aqe_first.mp3]"]
    assert session.state == generated_state
    assert session.current_filename == "clip__aqe_first.mp3"
    assert session.undo_history.pop().filename == "clip.mp3"
    assert editor.loadNote.call_count == 2
    assert reload_statuses[1] == {0: {"kind": "info", "message": "Redid: Increased speed to x1.5."}}
    assert session.pending_status == PendingEditorStatus(0, message="Redid: Increased speed to x1.5.")
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any("window.__aqeSetHistorySnapshot" in call and '"canUndo": false' in call and '"canRedo": true' in call for call in evals)
    assert any("window.__aqeSetHistorySnapshot" in call and '"canUndo": true' in call and '"canRedo": false' in call for call in evals)
    assert session.pending_post_edit_playback_field_index == 0
    assert session.pending_post_edit_playback_generation == session.post_edit_playback_generation
    assert session.pending_post_edit_playback_source_filename == "clip__aqe_first.mp3"


def _history_editor(tmp_path: Path) -> tuple[object, EditorSession]:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    for name in ["clip0.mp3", "clip1.mp3", "clip2.mp3", "clip3.mp3"]:
        (media_dir / name).write_bytes(name.encode("utf-8"))

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip3.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
        addonManager=SimpleNamespace(
            addonFromModule=lambda _module: "addon",
            getConfig=lambda _addon: {"editor_history_size": 100},
        ),
    )
    session = EditorSession(
        state=AudioEditState("clip3.mp3"),
        field_index=0,
        current_filename="clip3.mp3",
        status_summary="Third edit",
    )
    session.undo_history.push(AudioEditState("clip0.mp3"), "clip0.mp3", status_summary="Original")
    session.undo_history.push(AudioEditState("clip1.mp3"), "clip1.mp3", status_summary="First edit")
    session.undo_history.push(AudioEditState("clip2.mp3"), "clip2.mp3", status_summary="Second edit")
    SESSIONS[editor] = session
    return editor, session


def test_history_jump_undo_restores_selected_depth(tmp_path: Path, monkeypatch) -> None:
    editor, session = _history_editor(tmp_path)
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    _handle_bridge_command(editor, '{"command":"aqe:history-jump","fieldOrd":0,"direction":"undo","steps":2}')

    assert editor.note.fields == ["[sound:clip1.mp3]"]
    assert session.current_filename == "clip1.mp3"
    assert [entry.filename for entry in session.undo_history.entries] == ["clip0.mp3"]
    assert [entry.filename for entry in session.redo_history.entries] == ["clip3.mp3", "clip2.mp3"]


def test_history_jump_rejects_out_of_range_without_partial_restore(tmp_path: Path, monkeypatch) -> None:
    editor, session = _history_editor(tmp_path)
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)

    _handle_bridge_command(editor, '{"command":"aqe:history-jump","fieldOrd":0,"direction":"undo","steps":20}')

    assert editor.note.fields == ["[sound:clip3.mp3]"]
    assert session.current_filename == "clip3.mp3"
    assert [entry.filename for entry in session.undo_history.entries] == ["clip0.mp3", "clip1.mp3", "clip2.mp3"]
    assert session.redo_history.entries == []


def test_history_jump_redo_restores_selected_depth(tmp_path: Path, monkeypatch) -> None:
    editor, session = _history_editor(tmp_path)
    session.undo_history.clear()
    session.redo_history.push(AudioEditState("clip3.mp3"), "clip3.mp3", status_summary="Third edit")
    session.redo_history.push(AudioEditState("clip2.mp3"), "clip2.mp3", status_summary="Second edit")
    editor.note.fields = ["[sound:clip1.mp3]"]
    session.state = AudioEditState("clip1.mp3")
    session.current_filename = "clip1.mp3"
    session.status_summary = "First edit"
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    _handle_bridge_command(editor, '{"command":"aqe:history-jump","fieldOrd":0,"direction":"redo","steps":2}')

    assert editor.note.fields == ["[sound:clip3.mp3]"]
    assert session.current_filename == "clip3.mp3"
    assert [entry.filename for entry in session.undo_history.entries] == ["clip1.mp3", "clip2.mp3"]
    assert session.redo_history.entries == []


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
    SESSIONS[editor] = session

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
    assert session.pending_status == PendingEditorStatus(0, message="Closed settings.")
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
    SESSIONS[editor] = EditorSession(
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
    SESSIONS[editor] = EditorSession(field_index=2)

    _set_busy(editor, False)

    assert "window.__aqeSetBusy" in editor.web.eval.call_args.args[0]
    assert "(2, false" in editor.web.eval.call_args.args[0]
