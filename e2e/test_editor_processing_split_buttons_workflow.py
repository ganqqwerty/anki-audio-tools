"""E2E tests for editor processing split-button controls."""

from __future__ import annotations

import json
from pathlib import Path

from e2e.editor_note_helpers import (
    ADDON_NUMERIC_ID,
    _basic_audio_note,
    _button_selector,
    _click_and_wait_for_new_file,
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


def _split_menu_selector(command: str, ord_: int = 0) -> str:
    slug = command.removeprefix("aqe:")
    return f'[data-testid="aqe-split-{ord_}-{slug}-menu"]'


def _split_value_state_js(command: str, ord_: int = 0) -> str:
    slug = command.removeprefix("aqe:")
    return f"""
    (() => {{
      const input = document.querySelector('[data-testid="aqe-split-{ord_}-{slug}-value"]');
      const slider = document.querySelector('[data-testid="aqe-split-{ord_}-{slug}-slider"]');
      return input && slider ? {{
        inputMax: input.max,
        inputMin: input.min,
        inputStep: input.step,
        inputValue: input.value,
        sliderValue: slider.value,
      }} : null;
    }})()
    """


def _set_split_value_input_js(command: str, value: str, ord_: int = 0) -> str:
    slug = command.removeprefix("aqe:")
    return f"""
    (() => {{
      const input = document.querySelector('[data-testid="aqe-split-{ord_}-{slug}-value"]');
      if (!input) return false;
      input.value = {json.dumps(value)};
      input.dispatchEvent(new Event("input", {{ bubbles: true }}));
      return true;
    }})()
    """


def _set_split_slider_js(command: str, value: str, ord_: int = 0) -> str:
    slug = command.removeprefix("aqe:")
    return f"""
    (() => {{
      const slider = document.querySelector('[data-testid="aqe-split-{ord_}-{slug}-slider"]');
      if (!slider) return false;
      slider.value = {json.dumps(value)};
      slider.dispatchEvent(new Event("input", {{ bubbles: true }}));
      return true;
    }})()
    """


def test_volume_split_button_uses_settings_default_and_local_value(
    anki_mw,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.editor_integration import _SESSIONS

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_split_volume_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, volume_step_db=6)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:volume-up"), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:volume-up"), timeout=5.0)
        state = wait_for_js_condition(
            editor.web,
            _split_value_state_js("aqe:volume-up"),
            lambda value: value is not None and value["inputValue"] == "6",
            timeout=5.0,
        )
        assert state["inputMin"] == "0.5"
        assert state["inputMax"] == "12"
        assert state["inputStep"] == "0.5"

        wait_for_js_condition(
            editor.web,
            _set_split_value_input_js("aqe:volume-up", "6.5"),
            lambda value: value is True,
            timeout=5.0,
        )
        generated_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:volume-up",
            source.name,
        )
        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.state is not None
                and session.state.volume_db == 6.5
            ),
            timeout=5.0,
            message="Volume split input did not apply the local value",
        )
        assert (media_dir / generated_name).is_file()
    finally:
        editor.set_note(None)
        parent.close()


def test_split_tooltip_save_icon_promotes_local_volume_value_to_settings(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_split_save_default_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, volume_step_db=3)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:volume-up"), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:volume-up"), timeout=5.0)
        wait_for_js_condition(
            editor.web,
            _set_split_slider_js("aqe:volume-up", "6"),
            lambda value: value is True,
            timeout=5.0,
        )
        click_selector(
            editor.web,
            '[data-testid="aqe-split-0-volume-up-save-default"]',
            timeout=5.0,
        )

        wait_for_condition(
            lambda: anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID)["volume_step_db"] == 6,
            timeout=5.0,
            message="Split default save did not update volume_step_db",
        )
    finally:
        editor.set_note(None)
        parent.close()
