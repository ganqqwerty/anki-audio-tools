"""E2E smoke checks for editor hook registration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from e2e.conftest import import_runtime_addon_module
from e2e.editor_note_helpers import (
    ADDON_NUMERIC_ID,
    DEFAULT_VISIBLE_EDITOR_BUTTONS,
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _wait_for_status,
    _wait_for_status_flow,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)


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


def test_editor_settings_save_refreshes_current_editor_button_modes(
    anki_mw,
    ffmpeg_config,
) -> None:
    runtime_addon = import_runtime_addon_module()
    SettingsDialog = import_runtime_addon_module(".settings").SettingsDialog

    original_config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_button_mode_refresh_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.5)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        editor_button_modes={
            **original_config.get("editor_button_modes", {}),
            "aqe:settings": "text",
            "aqe:show-file": "text",
        },
    )
    note = _basic_audio_note(anki_mw, source.name)
    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:settings"), timeout=10.0)
        wait_for_js_condition(
            editor.web,
            f"""
            (() => {{
              const settings = document.querySelector({json.dumps(_button_selector("aqe:settings"))});
              const showFile = document.querySelector({json.dumps(_button_selector("aqe:show-file"))});
              return settings && showFile ? {{
                settingsIconOnly: settings.classList.contains("aqe-icon-only"),
                settingsIcons: settings.querySelectorAll("svg").length,
                showFileIconOnly: showFile.classList.contains("aqe-icon-only"),
                showFileIcons: showFile.querySelectorAll("svg").length,
              }} : null;
            }})()
            """,
            lambda value: value
            == {
                "settingsIconOnly": False,
                "settingsIcons": 0,
                "showFileIconOnly": False,
                "showFileIcons": 0,
            },
            timeout=5.0,
        )

        click_selector(editor.web, _button_selector("aqe:settings"), timeout=5.0)
        QApplication.processEvents()
        wait_for_condition(
            lambda: isinstance(runtime_addon._settings_dialog, SettingsDialog)
            and runtime_addon._settings_dialog.isVisible(),
            timeout=5.0,
        )
        _wait_for_status(
            editor,
            lambda status: status["text"] == "Opened settings.",
            timeout=10.0,
        )
        wait_for_condition(
            lambda: isinstance(runtime_addon._settings_dialog, SettingsDialog)
            and runtime_addon._settings_dialog.isVisible(),
            timeout=1.0,
        )
        assert _wait_for_status(
            editor,
            lambda status: status["text"] == "Opened settings.",
            timeout=2.0,
        )["text"] == "Opened settings."
        dialog = runtime_addon._settings_dialog

        settings_icon_selector = '[data-testid="button-settings-settings-mode-icon"]'
        click_selector(dialog, settings_icon_selector, timeout=5.0)
        wait_for_js_condition(
            dialog,
            f"document.querySelector({json.dumps(settings_icon_selector)})?.checked",
            lambda value: value is True,
            timeout=5.0,
        )

        with patch.object(
            anki_mw.addonManager,
            "writeConfig",
            wraps=anki_mw.addonManager.writeConfig,
        ) as mock_write:
            click_selector(dialog, '[data-testid="settings-save"]', timeout=5.0)
            wait_for_condition(lambda: mock_write.called, timeout=5.0)
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Closed settings.",
            timeout=10.0,
        )

        wait_for_js_condition(
            editor.web,
            f"""
            (() => {{
              const settings = document.querySelector({json.dumps(_button_selector("aqe:settings"))});
              const showFile = document.querySelector({json.dumps(_button_selector("aqe:show-file"))});
              return settings && showFile ? {{
                settingsIconOnly: settings.classList.contains("aqe-icon-only"),
                settingsIcons: settings.querySelectorAll("svg").length,
                showFileIconOnly: showFile.classList.contains("aqe-icon-only"),
                showFileIcons: showFile.querySelectorAll("svg").length,
              }} : null;
            }})()
            """,
            lambda value: value
            == {
                "settingsIconOnly": True,
                "settingsIcons": 1,
                "showFileIconOnly": False,
                "showFileIcons": 0,
            },
            timeout=10.0,
        )
    finally:
        editor.set_note(None)
        parent.close()
        anki_mw.addonManager.writeConfig(ADDON_NUMERIC_ID, original_config)


def test_editor_settings_close_without_save_reports_closed_status(
    anki_mw,
    ffmpeg_config,
) -> None:
    runtime_addon = import_runtime_addon_module()
    SettingsDialog = import_runtime_addon_module(".settings").SettingsDialog

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_settings_close_status_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.5)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    note = _basic_audio_note(anki_mw, source.name)
    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:settings"), timeout=10.0)
        click_selector(editor.web, _button_selector("aqe:settings"), timeout=5.0)
        QApplication.processEvents()
        wait_for_condition(
            lambda: isinstance(runtime_addon._settings_dialog, SettingsDialog)
            and runtime_addon._settings_dialog.isVisible(),
            timeout=5.0,
        )
        _wait_for_status(
            editor,
            lambda status: status["text"] == "Opened settings.",
            timeout=10.0,
        )
        dialog = runtime_addon._settings_dialog

        click_selector(dialog, '[data-testid="settings-cancel"]', timeout=5.0)
        wait_for_condition(
            lambda: not dialog.isVisible(),
            timeout=5.0,
            message="Timed out waiting for settings dialog to close after cancel",
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Closed settings.",
            timeout=10.0,
        )
    finally:
        editor.set_note(None)
        parent.close()
