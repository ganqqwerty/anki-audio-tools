"""E2E tests for SQLite-backed editor history across editor sessions."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _click_and_wait_for_new_file,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
    _wait_for_status_flow,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)


def _history_menu_selector(direction: str, steps: int, ord_: int = 0) -> str:
    return f'[data-testid="aqe-history-{ord_}-{direction}-{steps}"]'


def _history_labels_js(direction: str, ord_: int = 0) -> str:
    return f"""
    Array.from(document.querySelectorAll('[data-testid^="aqe-history-{ord_}-{direction}-"]'))
      .map((node) => node.textContent)
    """


def test_processing_persistent_history_survives_editor_reopen(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_persistent_history_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, editor_history_size=100)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        first_generated = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:faster",
            source.name,
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Increased speed to x1.5.",
            timeout=10.0,
        )
        second_generated = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:volume-up",
            first_generated,
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Increased volume by 15 dB.",
            timeout=10.0,
        )
        third_generated = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:slower",
            second_generated,
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Decreased speed to x1.5.",
            timeout=10.0,
        )
    finally:
        editor.set_note(None)
        parent.close()

    reopened, reopened_parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(reopened.web, _button_selector("aqe:faster"), timeout=10.0)
        click_selector(reopened.web, '[data-testid="aqe-split-0-undo-menu"]', timeout=5.0)
        wait_for_selector(reopened.web, _history_menu_selector("undo", 3), timeout=5.0)
        undo_labels = wait_for_js_condition(
            reopened.web,
            _history_labels_js("undo"),
            lambda labels: len(labels) >= 3,
            timeout=5.0,
        )
        assert undo_labels[:3] == [
            "Decreased speed to x1.5.",
            "Increased volume by 15 dB.",
            "Increased speed to x1.5.",
        ]
        click_selector(reopened.web, _history_menu_selector("undo", 2), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == first_generated,
            timeout=5.0,
            message="Persistent undo history jump did not restore the selected generated reference",
        )
    finally:
        reopened.set_note(None)
        reopened_parent.close()

    reopened_again, reopened_again_parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(reopened_again.web, _button_selector("aqe:faster"), timeout=10.0)
        click_selector(reopened_again.web, '[data-testid="aqe-split-0-undo-menu"]', timeout=5.0)
        wait_for_selector(reopened_again.web, _history_menu_selector("undo", 1), timeout=5.0)
        remaining_labels = wait_for_js_condition(
            reopened_again.web,
            _history_labels_js("undo"),
            lambda labels: len(labels) >= 1,
            timeout=5.0,
        )
        assert remaining_labels[:1] == ["Increased speed to x1.5."]
        assert third_generated not in note.fields[0]
    finally:
        reopened_again.set_note(None)
        reopened_again_parent.close()
