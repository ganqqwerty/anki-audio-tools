"""E2E tests for promoting split-button tooltip values to defaults."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_note_helpers import (
    ADDON_NUMERIC_ID,
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)
from e2e.test_editor_processing_split_buttons_workflow import (
    _set_split_slider_js,
    _split_menu_selector,
    _split_value_state_js,
)


def _split_save_default_selector(command: str, ord_: int = 0) -> str:
    slug = command.removeprefix("aqe:")
    return f'[data-testid="aqe-split-{ord_}-{slug}-save-default"]'


def test_split_tooltip_save_icon_promotes_local_trim_value_to_settings(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_split_save_default_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, manual_trim_small_ms=100)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:trim-left"), timeout=5.0)
        wait_for_selector(editor.web, _split_save_default_selector("aqe:trim-left"), timeout=5.0)
        wait_for_js_condition(
            editor.web,
            _set_split_slider_js("aqe:trim-left", "250"),
            lambda value: value is True,
            timeout=5.0,
        )
        wait_for_js_condition(
            editor.web,
            _split_value_state_js("aqe:trim-left"),
            lambda value: value is not None and value["sliderValue"] == "250",
            timeout=5.0,
        )

        click_selector(editor.web, _split_save_default_selector("aqe:trim-left"), timeout=5.0)

        wait_for_condition(
            lambda: anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID)["manual_trim_small_ms"] == 250,
            timeout=5.0,
            message="Split default save did not update manual_trim_small_ms",
        )
        wait_for_js_condition(
            editor.web,
            """
            document
              .querySelector('[data-testid="aqe-split-0-trim-left-save-default"]')
              ?.getAttribute('title')
            """,
            lambda value: value == "Promote these settings to default",
            timeout=5.0,
        )
    finally:
        editor.set_note(None)
        parent.close()
