"""Tests for Browser batch visualization integration."""

from __future__ import annotations

import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import aqt

from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_visualization import BatchNoteResult
from anki_audio_quick_editor.browser_integration import (
    ACTION_LABEL,
    _on_browser_menus_did_init,
    _open_batch_dialog,
    _run_batch,
    register_browser_hooks,
)


def test_register_browser_hooks() -> None:
    hooks = SimpleNamespace(browser_menus_did_init=MagicMock(), browser_will_show_context_menu=MagicMock())

    register_browser_hooks(hooks)

    hooks.browser_menus_did_init.append.assert_called_once()
    hooks.browser_will_show_context_menu.append.assert_called_once()


def test_browser_menu_action_is_added() -> None:
    browser = SimpleNamespace(form=SimpleNamespace(menu_Cards=MagicMock()))

    _on_browser_menus_did_init(browser)

    browser.form.menu_Cards.addAction.assert_called_once_with(ACTION_LABEL)
    assert aqt.qt.qconnect.called


def test_empty_selection_shows_warning() -> None:
    browser = SimpleNamespace(selected_notes=lambda: [], mw=MagicMock())

    _open_batch_dialog(browser)

    aqt.utils.showWarning.assert_called_once()


class _FakeNote:
    def __init__(self, note_id: int) -> None:
        self.id = note_id
        self.fields = {"Audio": "[sound:clip.mp3]", "Image": ""}

    def note_type(self) -> dict:
        return {"name": "Basic"}

    def items(self) -> list[tuple[str, str]]:
        return list(self.fields.items())

    def __setitem__(self, key: str, value: str) -> None:
        self.fields[key] = value


class _FakeCol:
    def __init__(self) -> None:
        self.notes = {1: _FakeNote(1), 2: _FakeNote(2)}
        self.updated: list[int] = []
        self.merged: list[int] = []
        self.media = SimpleNamespace(write_data=lambda name, data: name)

    def get_note(self, note_id: int) -> _FakeNote:
        return self.notes[note_id]

    def add_custom_undo_entry(self, _name: str) -> int:
        return 42

    def update_note(self, note: _FakeNote) -> object:
        self.updated.append(int(note.id))
        return object()

    def merge_undo_entries(self, entry: int) -> object:
        self.merged.append(entry)
        return object()


def test_run_batch_stops_after_current_note_when_cancel_requested(monkeypatch, tmp_path: Path) -> None:
    col = _FakeCol()
    cancel_event = threading.Event()
    progress_calls: list[int] = []

    def fake_process(*_args, **_kwargs) -> BatchNoteResult:
        return BatchNoteResult(
            note_id=int(_args[1]),
            status="written",
            message="appended viz.svg",
            target_field="Image",
            target_html='<img src="viz.svg">',
            audio_filename="clip.mp3",
            image_filename="viz.svg",
        )

    def on_progress(processed: int, *_args) -> None:
        progress_calls.append(processed)
        cancel_event.set()

    monkeypatch.setattr("anki_audio_quick_editor.browser_integration._process_note", fake_process)

    report = _run_batch(
        col,
        [1, 2],
        "Audio",
        "Image",
        tmp_path,
        AudioProcessingConfig(),
        cancel_event,
        lambda _line: None,
        on_progress,
    )

    assert report.canceled
    assert report.processed == 1
    assert report.written == 1
    assert col.updated == [1]
    assert col.merged == [42]
    assert progress_calls == [1]
