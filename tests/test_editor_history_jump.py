"""Tests for editor history jump operations."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_callbacks import handle_bridge_command
from anki_audio_quick_editor.editor_runtime import SESSIONS
from anki_audio_quick_editor.editor_session import (
    EditorSession,
)


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
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    handle_bridge_command(editor, '{"command":"aqe:history-jump","fieldOrd":0,"direction":"undo","steps":2}')

    assert editor.note.fields == ["[sound:clip1.mp3]"]
    assert session.current_filename == "clip1.mp3"
    assert [entry.filename for entry in session.undo_history.entries] == ["clip0.mp3"]
    assert [entry.filename for entry in session.redo_history.entries] == ["clip3.mp3", "clip2.mp3"]


def test_history_jump_rejects_out_of_range_without_partial_restore(tmp_path: Path, monkeypatch) -> None:
    editor, session = _history_editor(tmp_path)

    handle_bridge_command(editor, '{"command":"aqe:history-jump","fieldOrd":0,"direction":"undo","steps":20}')

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
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    handle_bridge_command(editor, '{"command":"aqe:history-jump","fieldOrd":0,"direction":"redo","steps":2}')

    assert editor.note.fields == ["[sound:clip3.mp3]"]
    assert session.current_filename == "clip3.mp3"
    assert [entry.filename for entry in session.undo_history.entries] == ["clip1.mp3", "clip2.mp3"]
    assert session.redo_history.entries == []
