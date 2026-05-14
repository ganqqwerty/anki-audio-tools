"""Tests for the thin Anki editor bridge layer."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.editor_integration import (
    BRIDGE_COMMANDS,
    _audio_field_indices,
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

    assert aqt.gui_hooks.main_window_did_init.append.call_count == 5


def test_editor_init_registers_all_bridge_commands(tmp_path: Path) -> None:
    from anki_audio_quick_editor.editor_integration import _on_editor_did_init

    editor = SimpleNamespace(_links={}, mw=MagicMock(), web=MagicMock(), currentField=0)
    editor.mw.col.media.dir.return_value = str(tmp_path)

    _on_editor_did_init(editor)

    assert set(BRIDGE_COMMANDS) <= set(editor._links)


def test_audio_field_indices_are_detected_from_note_fields() -> None:
    note = SimpleNamespace(fields=["plain", "<b>[sound:first.mp3]</b>", "[sound:movie.mp4]"])

    assert _audio_field_indices(note) == [1]
