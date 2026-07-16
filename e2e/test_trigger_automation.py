"""Behavior-driven E2E coverage for trigger automation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from e2e.editor_note_helpers import (
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)
from e2e.settings_dialog_helpers import open_settings_dialog


@pytest.mark.allow_native_playback("stop")
def test_user_created_add_trigger_converts_audio_on_added_card(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "trigger_ui_convert_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.5)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        audio_trigger_rules=[],
        enabled=True,
        output_format="mp3",
    )

    _create_convert_on_add_trigger_through_settings_ui(anki_mw)
    added_note_id = _add_audio_note_through_add_cards_ui(anki_mw, source.name)
    generated_name = _wait_for_triggered_audio(
        anki_mw,
        added_note_id,
        media_dir,
        previous_name=source.name,
    )
    _assert_added_note_shows_triggered_audio_in_editor_ui(
        anki_mw,
        added_note_id,
        generated_name,
    )


def _create_convert_on_add_trigger_through_settings_ui(anki_mw) -> None:
    dialog = open_settings_dialog(anki_mw)
    try:
        click_selector(dialog, '[data-testid="settings-tab-triggers"]', timeout=5.0)
        click_selector(dialog, '[data-testid="trigger-add"]', timeout=5.0)
        wait_for_selector(dialog, '[data-testid="trigger-name"]', timeout=5.0)
        _set_form_value(dialog, '[data-testid="trigger-name"]', "E2E convert on add")
        _set_form_value(dialog, '[data-testid="trigger-event"]', "add")
        _select_option_by_text(dialog, '[data-testid="trigger-note-type"]', "Basic")
        _set_form_value(dialog, '[data-testid="trigger-source-field"]', "Front")
        _set_form_value(dialog, '[data-testid="trigger-action-type"]', "operation")
        _set_form_value(dialog, '[data-testid="trigger-operation"]', "convert")
        wait_for_js_condition(
            dialog,
            """
            (() => {
              const validation = document.querySelector('[data-testid="trigger-validation"]');
              const save = document.querySelector('[data-testid="settings-save"]');
              const name = document.querySelector('[data-testid="trigger-name"]');
              return {
                validation: validation?.textContent || "",
                saveDisabled: save?.disabled ?? true,
                name: name?.value || "",
              };
            })()
            """,
            lambda state: state == {
                "validation": "",
                "saveDisabled": False,
                "name": "E2E convert on add",
            },
            timeout=5.0,
        )
        click_selector(dialog, '[data-testid="settings-save"]', timeout=5.0)
        wait_for_condition(
            lambda: any(
                rule.get("name") == "E2E convert on add"
                for rule in (anki_mw.addonManager.getConfig("1000000002") or {}).get(
                    "audio_trigger_rules",
                    [],
                )
            ),
            timeout=5.0,
            message="Settings UI did not save the trigger rule",
        )
    finally:
        if dialog.isVisible():
            dialog.close()


def _add_audio_note_through_add_cards_ui(anki_mw, audio_filename: str) -> int:
    from aqt.addcards import AddCards
    from PyQt6.QtWidgets import QApplication

    add_cards = AddCards(anki_mw)
    try:
        note = _new_audio_note_for_add_cards(anki_mw, audio_filename)
        add_cards.set_note(note, anki_mw.col.decks.id("Default"))
        wait_for_js_condition(
            add_cards.editor.web,
            'typeof saveNow === "function"',
            lambda ready: ready is True,
            timeout=10.0,
        )
        add_cards.addButton.click()
        wait_for_condition(
            lambda: add_cards._last_added_note is not None,
            timeout=10.0,
            message="Add Cards UI did not add the note",
        )
        assert add_cards._last_added_note is not None
        note_id = int(add_cards._last_added_note.id)
        wait_for_condition(
            lambda: not any(
                type(widget).__name__ == "CustomLabel" and widget.isVisible()
                for widget in QApplication.topLevelWidgets()
            ),
            timeout=5.0,
            message="Add Cards success tooltip did not close",
        )
        return note_id
    finally:
        add_cards.close()


def _new_audio_note_for_add_cards(anki_mw, audio_filename: str):
    notetype = anki_mw.col.models.by_name("Basic")
    assert notetype is not None
    note = anki_mw.col.new_note(notetype)
    note["Front"] = f"Prompt [sound:{audio_filename}]"
    note["Back"] = "Back"
    return note


def _wait_for_triggered_audio(
    anki_mw,
    note_id: int,
    media_dir: Path,
    *,
    previous_name: str,
) -> str:
    generated: dict[str, str] = {}

    def _updated() -> bool:
        note = anki_mw.col.get_note(note_id)
        filename = _sound_filename(note["Front"])
        if filename == previous_name or not filename.endswith(".mp3"):
            return False
        generated["filename"] = filename
        return (media_dir / filename).is_file()

    wait_for_condition(
        _updated,
        timeout=60.0,
        message="Trigger did not convert the added note audio",
    )
    return generated["filename"]


def _assert_added_note_shows_triggered_audio_in_editor_ui(
    anki_mw,
    note_id: int,
    generated_name: str,
) -> None:
    note = anki_mw.col.get_note(note_id)
    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:play"), timeout=10.0)
        wait_for_js_condition(
            editor.web,
            """
            (() => {
              const controls = document.querySelector('[data-testid="aqe-controls-0"]');
              const play = document.querySelector('[data-testid="aqe-button-0-play"]');
              return controls ? {
                sourceFilename: controls.dataset.aqeSourceFilename || "",
                hasPlayButton: play !== null,
              } : null;
            })()
            """,
            lambda state: state is not None
            and state["sourceFilename"] == generated_name
            and state["hasPlayButton"] is True,
            timeout=10.0,
        )
    finally:
        editor.set_note(None)
        parent.close()


def _set_form_value(target: Any, selector: str, value: str) -> None:
    run_js(
        target,
        f"""
        (() => {{
          const node = document.querySelector({json.dumps(selector)});
          if (!node) return false;
          node.value = {json.dumps(value)};
          node.dispatchEvent(new Event("input", {{ bubbles: true }}));
          node.dispatchEvent(new Event("change", {{ bubbles: true }}));
          return true;
        }})()
        """,
    )
    wait_for_js_condition(
        target,
        f"document.querySelector({json.dumps(selector)})?.value",
        lambda current: current == value,
        timeout=5.0,
    )


def _select_option_by_text(target: Any, selector: str, text: str) -> None:
    run_js(
        target,
        f"""
        (() => {{
          const node = document.querySelector({json.dumps(selector)});
          if (!node) return false;
          const option = Array.from(node.options).find(
            (item) => item.textContent.trim() === {json.dumps(text)}
          );
          if (!option) return false;
          node.value = option.value;
          node.dispatchEvent(new Event("input", {{ bubbles: true }}));
          node.dispatchEvent(new Event("change", {{ bubbles: true }}));
          return true;
        }})()
        """,
    )
    wait_for_js_condition(
        target,
        f"document.querySelector({json.dumps(selector)})?.selectedOptions?.[0]?.textContent?.trim()",
        lambda current: current == text,
        timeout=5.0,
    )
