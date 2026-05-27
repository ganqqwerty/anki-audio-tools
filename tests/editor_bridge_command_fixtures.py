from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_integration import _SESSIONS, EditorSession


class BridgeEditor:
    currentField: int
    web: Any


def make_editor(*, current_field: int = 0, web: Any | None = None) -> BridgeEditor:
    editor = BridgeEditor()
    editor.currentField = current_field
    editor.web = MagicMock() if web is None else web
    return editor


def attach_clip_session(
    editor: BridgeEditor,
    tmp_path: Path,
    *,
    session: EditorSession | None = None,
    filename: str = "clip.mp3",
) -> tuple[EditorSession, Path]:
    source = tmp_path / filename
    source.write_bytes(b"source")
    active_session = session or EditorSession(state=AudioEditState(filename), field_index=editor.currentField)
    _SESSIONS[editor] = active_session
    return active_session, source
