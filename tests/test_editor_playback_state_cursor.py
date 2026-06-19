"""Web cursor intent playback tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_callbacks import _set_cursor_from_web
from anki_audio_quick_editor.editor_runtime import SESSIONS
from anki_audio_quick_editor.editor_session import (
    EditorSession,
    GraphVisualizationState,
)


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
        graph=GraphVisualizationState(visualized_duration_ms=2000),
    )
    SESSIONS[editor] = session

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._eval_with_callback",
        lambda _editor, _script, callback: callback(
            {"cursorMs": 1400, "restartPlayback": True, "engine": "html"},
        ),
    )

    _set_cursor_from_web(editor)

    assert session.cursor_ms == 1400
    assert session.playback.active is True
    assert session.playback.paused is False


def test_unsupported_engine_cursor_restart_intent_updates_cursor_without_restart(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.m4a"
    source.write_bytes(b"audio")
    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.m4a]"])
    editor.web = MagicMock()
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    session = EditorSession(
        state=AudioEditState("clip.m4a"),
        field_index=0,
        current_filename="clip.m4a",
        source_mtime_ns=source.stat().st_mtime_ns,
        graph=GraphVisualizationState(
            visualized_duration_ms=2000,
            filenames_by_field={0: "clip.m4a"},
            durations_by_field={0: 2000},
        ),
    )
    SESSIONS[editor] = session

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._eval_with_callback",
        lambda _editor, _script, callback: callback(
            {
                "cursorMs": 700,
                "endMs": 1250,
                "engine": "native",
                "regionMode": "selection",
                "restartPlayback": True,
            },
        ),
    )

    _set_cursor_from_web(editor)

    assert session.cursor_ms == 700
    assert session.playback.active is False
    assert session.playback.paused is False


def test_late_cursor_intent_is_ignored_after_editor_note_is_cleared(monkeypatch) -> None:
    editor = SimpleNamespace(note=None, currentField=0, web=MagicMock())

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._eval_with_callback",
        lambda _editor, _script, callback: callback(
            {"cursorMs": 700, "restartPlayback": True, "engine": "html"},
        ),
    )

    _set_cursor_from_web(editor)

    editor.web.eval.assert_not_called()
