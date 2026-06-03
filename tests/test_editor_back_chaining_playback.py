"""Back-chaining playback status tests."""

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


def test_back_chaining_html_playback_status_includes_practice_guidance(tmp_path: Path, monkeypatch) -> None:
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

    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_playback_segment",
        lambda *_args, **_kwargs: pytest.fail("HTML playback should not render a segment"),
    )

    _play_with_request(editor, {"engine": "html", "action": "start", "cursorMs": 700, "source": "back_chaining"})

    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any(
        "Playing from 0.70s. Practice mode. Use the toolbar buttons for back-chaining." in call
        for call in evals
    )
