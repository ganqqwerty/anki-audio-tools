"""Playback request and segment rendering tests."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_callbacks import (
    _play_with_request,
)
from anki_audio_quick_editor.editor_runtime import SESSIONS
from anki_audio_quick_editor.editor_session import (
    AnalysisState,
    EditorSession,
    GraphVisualizationState,
)


def test_html_playback_request_updates_session_without_temporary_segment(tmp_path: Path, monkeypatch) -> None:
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
    stop_calls: list[str] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.stop_audio_playback",
        lambda: stop_calls.append("stop"),
    )

    _play_with_request(editor, {"engine": "html", "action": "start", "cursorMs": 700})

    assert session.cursor_ms == 700
    assert session.playback.active is True
    assert session.playback.paused is False
    assert session.playback.preparing is False
    assert stop_calls == ["stop"]
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any("Playing from 0.70s" in call for call in evals)
    assert not any("Practice mode. Use the toolbar buttons for chorusing." in call for call in evals)


def test_post_edit_playback_request_does_not_replace_status_while_analysis_is_busy(tmp_path: Path) -> None:
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
        analysis=AnalysisState(busy=True, busy_fields={1}),
    )
    SESSIONS[editor] = session

    _play_with_request(editor, {"engine": "html", "action": "start", "cursorMs": 0, "source": "post_edit"})

    editor.web.eval.assert_not_called()
    assert session.playback.active is False
    assert session.playback.preparing is False


def test_playback_request_reports_missing_referenced_media_with_media_code(tmp_path: Path) -> None:
    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.mp3"
    source.write_bytes(b"audio")
    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:missing.mp3]"])
    editor.web = MagicMock()
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        source_mtime_ns=source.stat().st_mtime_ns,
    )
    SESSIONS[editor] = session

    _play_with_request(editor, {"engine": "html", "action": "start", "cursorMs": 0})

    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any('"code": "AQE-MEDIA-002"' in call for call in evals)
    assert any(
        '"message": "The referenced audio file was not found in Anki\'s media folder."' in call
        for call in evals
    )
    assert session.playback.active is False
    assert session.playback.preparing is False


def test_unsupported_playback_engine_request_is_ignored_without_state_change(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
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
    )
    SESSIONS[editor] = session
    caplog.set_level(logging.DEBUG, logger="anki_audio_quick_editor.editor_playback")

    _play_with_request(editor, {"engine": "native", "action": "start", "cursorMs": 0})

    assert session.cursor_ms == 0
    assert session.playback.active is False
    assert session.playback.preparing is False
    assert "ignoring unsupported playback engine request for field 0" in caplog.text


def test_missing_engine_playback_request_defaults_to_html_state_sync(
    tmp_path: Path,
    monkeypatch,
) -> None:
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
    stop_calls: list[str] = []
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.stop_audio_playback",
        lambda: stop_calls.append("stop"),
    )

    _play_with_request(editor, {"action": "start", "cursorMs": 700})

    assert stop_calls == ["stop"]
    assert session.cursor_ms == 700
    assert session.playback.active is True
    assert session.playback.paused is False
    assert session.playback.preparing is False
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any("Playing from 0.70s" in call for call in evals)


def test_late_html_playback_request_is_ignored_after_editor_note_is_cleared() -> None:
    editor = SimpleNamespace(note=None, currentField=0, web=MagicMock())

    _play_with_request(editor, {"engine": "html", "action": "start", "cursorMs": 700})

    editor.web.eval.assert_not_called()
