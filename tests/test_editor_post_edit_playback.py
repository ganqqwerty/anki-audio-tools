"""Editor post-edit playback tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    EditorSession,
    _replace_current_field_after_render,
)


def test_standard_render_replacement_schedules_post_edit_playback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"source")

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
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    _replace_current_field_after_render(editor, AudioEditState("clip.mp3", volume_db=3.0), "clip__aqe.mp3")

    assert editor.note.fields == ["[sound:clip__aqe.mp3]"]
    assert any(
        "__aqeSetHistoryAvailability(0, true, false)" in call.args[0]
        for call in editor.web.evalWithCallback.call_args_list
    )
    assert "__aqePlayAfterEdit(0)" in editor.web.evalWithCallback.call_args.args[0]


def test_standard_render_replacement_uses_session_field_when_focus_changes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "first.mp3").write_bytes(b"first")
    (media_dir / "second.mp3").write_bytes(b"second")

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:first.mp3]", "[sound:second.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    _SESSIONS[editor] = EditorSession(
        state=AudioEditState("second.mp3"),
        field_index=1,
        current_filename="second.mp3",
    )
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    _replace_current_field_after_render(editor, AudioEditState("second.mp3", left_trim_ms=100), "second__aqe.mp3")

    assert editor.note.fields == ["[sound:first.mp3]", "[sound:second__aqe.mp3]"]
    assert editor.loadNote.call_args.kwargs == {"focusTo": 1}
    assert any(
        "__aqeSetHistoryAvailability(1, true, false)" in call.args[0]
        for call in editor.web.evalWithCallback.call_args_list
    )
    assert "__aqePlayAfterEdit(1)" in editor.web.evalWithCallback.call_args.args[0]


def test_stale_post_edit_playback_attempt_is_ignored(monkeypatch) -> None:
    from anki_audio_quick_editor import editor_frontend_callbacks

    class Editor:
        pass

    scheduled: list[Callable[[], None]] = []
    editor = Editor()
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    _SESSIONS[editor] = EditorSession(
        field_index=0,
        post_edit_playback_generation=3,
    )
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: scheduled.append(callback))

    editor_frontend_callbacks._request_playback_after_edit(editor, 0)
    _SESSIONS[editor].post_edit_playback_generation += 1
    scheduled[0]()

    editor.web.evalWithCallback.assert_not_called()
