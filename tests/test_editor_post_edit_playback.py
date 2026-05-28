"""Editor post-edit playback tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor import editor_frontend
from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    EditorSession,
    _replace_current_field_after_render,
)


def test_standard_render_replacement_records_pending_post_edit_playback(
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

    session = _SESSIONS[editor]
    assert editor.note.fields == ["[sound:clip__aqe.mp3]"]
    assert any(
        "__aqeSetHistoryAvailability(0, true, false)" in call.args[0]
        for call in editor.web.evalWithCallback.call_args_list
    )
    assert session.pending_post_edit_playback_field_index == 0
    assert session.pending_post_edit_playback_generation == session.post_edit_playback_generation
    assert session.pending_post_edit_playback_requires_graph_redraw is False
    assert session.pending_post_edit_playback_source_filename == "clip__aqe.mp3"


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

    session = _SESSIONS[editor]
    assert editor.note.fields == ["[sound:first.mp3]", "[sound:second__aqe.mp3]"]
    assert editor.loadNote.call_args.kwargs == {"focusTo": 1}
    assert any(
        "__aqeSetHistoryAvailability(1, true, false)" in call.args[0]
        for call in editor.web.evalWithCallback.call_args_list
    )
    assert session.pending_post_edit_playback_field_index == 1
    assert session.pending_post_edit_playback_generation == session.post_edit_playback_generation
    assert session.pending_post_edit_playback_requires_graph_redraw is False
    assert session.pending_post_edit_playback_source_filename == "second__aqe.mp3"


def test_stale_post_edit_playback_ready_event_is_ignored() -> None:
    class Editor:
        pass

    editor = Editor()
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    _SESSIONS[editor] = EditorSession(
        post_edit_playback_generation=3,
        pending_post_edit_playback_field_index=0,
        pending_post_edit_playback_generation=3,
        pending_post_edit_playback_source_filename="clip.mp3",
    )
    payload = SimpleNamespace(field_ord=0, generation=2, source_filename="clip.mp3")
    deps = SimpleNamespace(
        sessions=_SESSIONS,
        eval_with_callback=MagicMock(),
        playback_after_edit_expression=editor_frontend.playback_after_edit_expression,
    )

    editor_frontend.handle_post_edit_playback_ready(editor, payload, deps)

    deps.eval_with_callback.assert_not_called()


def test_post_edit_playback_request_records_frontend_ready_payload() -> None:
    class Editor:
        pass

    editor = Editor()
    _SESSIONS[editor] = EditorSession(
        current_filename="clip__aqe.mp3",
        post_edit_playback_generation=7,
    )
    deps = SimpleNamespace(
        sessions=_SESSIONS,
    )

    editor_frontend.request_playback_after_edit(editor, 2, deps)

    session = _SESSIONS[editor]
    assert editor_frontend.pending_post_edit_playback_payload(session) == {
        "fieldOrd": 2,
        "generation": 7,
        "requireGraphRedraw": False,
        "sourceFilename": "clip__aqe.mp3",
    }


def test_matching_post_edit_playback_ready_event_starts_once_and_clears_pending() -> None:
    class Editor:
        pass

    editor = Editor()
    _SESSIONS[editor] = EditorSession(
        pending_post_edit_playback_field_index=1,
        pending_post_edit_playback_generation=4,
        pending_post_edit_playback_source_filename="clip__aqe.mp3",
    )
    payload = SimpleNamespace(field_ord=1, generation=4, source_filename="clip__aqe.mp3")

    def eval_with_callback(_editor, expression, callback):
        assert "__aqePlayAfterEdit(1)" in expression
        callback(True)

    deps = SimpleNamespace(
        sessions=_SESSIONS,
        eval_with_callback=eval_with_callback,
        playback_after_edit_expression=editor_frontend.playback_after_edit_expression,
    )

    editor_frontend.handle_post_edit_playback_ready(editor, payload, deps)

    session = _SESSIONS[editor]
    assert session.pending_post_edit_playback_field_index is None
    assert session.pending_post_edit_playback_generation is None
    assert session.pending_post_edit_playback_requires_graph_redraw is False
    assert session.pending_post_edit_playback_source_filename is None
