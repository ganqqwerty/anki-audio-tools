"""E2E smoke checks for editor hook registration."""

from __future__ import annotations

import json
from pathlib import Path

from e2e.editor_note_helpers import (
    ADDON_NUMERIC_ID,
    DEFAULT_VISIBLE_EDITOR_BUTTONS,
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.helpers import generate_tone, wait_for_js_condition, wait_for_selector


# noinspection PyUnusedLocal
def test_editor_hooks_are_registered(anki_mw) -> None:
    from aqt import gui_hooks

    del anki_mw
    assert gui_hooks.editor_did_init.count() > 0
    assert gui_hooks.editor_will_load_note.count() > 0


def test_visible_editor_buttons_can_hide_settings(anki_mw, ffmpeg_config) -> None:
    original_config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_hidden_settings_button.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.5)
    visible_buttons = [
        command for command in DEFAULT_VISIBLE_EDITOR_BUTTONS if command != "aqe:settings"
    ]
    _configure_ffmpeg(anki_mw, ffmpeg_config, visible_editor_buttons=visible_buttons)
    note = _basic_audio_note(anki_mw, source.name)
    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:play"), timeout=10.0)
        assert wait_for_js_condition(
            editor.web,
            f"document.querySelector({json.dumps(_button_selector('aqe:settings'))}) === null",
            lambda value: value is True,
            timeout=5.0,
        ) is True
    finally:
        editor.set_note(None)
        parent.close()
        anki_mw.addonManager.writeConfig(ADDON_NUMERIC_ID, original_config)
