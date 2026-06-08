"""Playback request and segment rendering tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    EditorSession,
    _play_with_request,
)


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
        visualized_duration_ms=2000,
        analysis_busy=True,
        analysis_busy_fields={1},
    )
    _SESSIONS[editor] = session

    _play_with_request(editor, {"engine": "native", "action": "start", "cursorMs": 0, "source": "post_edit"})

    editor.web.eval.assert_not_called()
    assert session.playback_active is False
    assert session.playback_preparing is False


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
    _SESSIONS[editor] = session

    _play_with_request(editor, {"engine": "native", "action": "start", "cursorMs": 0})

    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any('"code": "AQE-MEDIA-002"' in call for call in evals)
    assert any(
        '"message": "The referenced audio file was not found in Anki\'s media folder."' in call
        for call in evals
    )
    assert session.playback_active is False
    assert session.playback_preparing is False


def test_native_selected_playback_renders_segment_from_cursor_to_selection_end(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class ImmediateThread:
        def __init__(self, target, daemon=True):
            del daemon
            self._target = target

        def start(self) -> None:
            self._target()

    class Editor:
        pass

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    source = media_dir / "clip.m4a"
    source.write_bytes(b"audio")
    segment = tmp_path / "segment.mp3"
    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.m4a]"])
    editor.web = MagicMock()
    editor.mw = SimpleNamespace(
        addonManager=SimpleNamespace(addonFromModule=lambda _module: "aqe", getConfig=lambda _addon_id: {}),
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
    )
    session = EditorSession(
        state=AudioEditState("clip.m4a"),
        field_index=0,
        current_filename="clip.m4a",
        source_mtime_ns=source.stat().st_mtime_ns,
        visualized_duration_ms=2000,
        visualized_filenames_by_field={0: "clip.m4a"},
        visualized_durations_by_field={0: 2000},
    )
    _SESSIONS[editor] = session
    render_calls: list[dict[str, object]] = []

    monkeypatch.setattr("anki_audio_quick_editor.editor_dependencies.threading.Thread", ImmediateThread)

    def fake_render_playback_segment(
        source_path: Path,
        start_ms: int,
        _config: object,
        output_path: Path | None = None,
        on_command=None,
        end_ms: int | None = None,
    ) -> SimpleNamespace:
        del output_path
        render_calls.append({"source_path": source_path, "start_ms": start_ms, "end_ms": end_ms})
        if on_command:
            on_command(("ffmpeg", "-i", str(source_path)))
        return SimpleNamespace(output_path=segment, command=(), duration_ms=500)

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_playback_segment",
        fake_render_playback_segment,
    )

    _play_with_request(
        editor,
        {"engine": "native", "action": "start", "cursorMs": 0, "endMs": 500, "regionMode": "selection"},
    )

    from aqt.sound import av_player

    assert render_calls == [{"source_path": source, "start_ms": 0, "end_ms": 500}]
    av_player.play_tags.assert_called_once()
    played_tag = av_player.play_tags.call_args.args[0][0]
    assert played_tag.filename == str(segment)
    assert session.cursor_ms == 0
    assert session.playback_active is True
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any("window.__aqeSetPlaybackState && window.__aqeSetPlaybackState(0, \"playing\", 0)" in call for call in evals)
    assert any("Playing\"" in call for call in evals)
    assert not any("Playing from 0.00s" in call for call in evals)


def test_late_html_playback_request_is_ignored_after_editor_note_is_cleared() -> None:
    editor = SimpleNamespace(note=None, currentField=0, web=MagicMock())

    _play_with_request(editor, {"engine": "html", "action": "start", "cursorMs": 700})

    editor.web.eval.assert_not_called()
