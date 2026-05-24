"""E2E tests for editor prosody graph rendering and graph state."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from e2e.conftest import import_runtime_addon_module
from e2e.editor_graph_helpers import _graph_state_js, _wait_for_visualizer_track
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _three_audio_field_note,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)
from e2e.test_settings_dialog import _open_settings_dialog


def _set_show_graph_by_default_from_settings(anki_mw, enabled: bool) -> None:
    dialog = _open_settings_dialog(anki_mw)
    checkbox_selector = '[data-testid="show-graph-by-default"]'
    save_selector = '[data-testid="settings-save"]'
    current = wait_for_js_condition(
        dialog,
        f"document.querySelector({json.dumps(checkbox_selector)})?.checked",
        lambda value: value in {True, False},
        timeout=5.0,
    )
    if current != enabled:
        click_selector(dialog, checkbox_selector, timeout=5.0)
        wait_for_js_condition(
            dialog,
            f"document.querySelector({json.dumps(checkbox_selector)})?.checked",
            lambda value: value is enabled,
            timeout=5.0,
        )

    with patch.object(
        anki_mw.addonManager,
        "writeConfig",
        wraps=anki_mw.addonManager.writeConfig,
    ) as mock_write:
        click_selector(dialog, save_selector, timeout=5.0)
        wait_for_condition(lambda: mock_write.called, timeout=5.0)

    saved_config = mock_write.call_args.args[1]
    assert saved_config["show_graph_by_default"] is enabled


def test_show_graph_by_default_auto_analyzes_all_audio_fields(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    sources = (
        media_dir / "editor_default_graph_one.wav",
        media_dir / "editor_default_graph_two.wav",
        media_dir / "editor_default_graph_three.wav",
    )
    for index, source in enumerate(sources):
        generate_tone(ffmpeg_config, source, duration_s=0.8 + index * 0.1)
    note = _three_audio_field_note(anki_mw, tuple(source.name for source in sources))
    _configure_ffmpeg(anki_mw, ffmpeg_config, show_graph_by_default=True)

    editor, parent = _open_editor(anki_mw, note)
    try:
        tracks = [
            _wait_for_visualizer_track(
                editor,
                lambda value, expected=source.name: value["sourceFilename"] == expected
                and value["pitchPaths"] > 0
                and value["graphButtonLabel"] == "Redraw",
                timeout=20.0,
                ord_=ord_,
            )
            for ord_, source in enumerate(sources)
        ]

        assert [track["sourceFilename"] for track in tracks] == [source.name for source in sources]
        assert all(track["active"] is True and track["hidden"] is False for track in tracks)
    finally:
        editor.set_note(None)
        parent.close()


def test_manual_graph_after_clearing_default_graph_field_shows_error_without_analyzing(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_default_graph_cleared_field.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.8)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, show_graph_by_default=True)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == source.name
            and value["graphButtonLabel"] == "Redraw",
            timeout=15.0,
        )
        run_js(
            editor.web,
            """
            (() => {
              const field = document.querySelector('.field-container[data-index="0"] [contenteditable="true"]');
              if (!field) return false;
              field.focus();
              field.innerHTML = "";
              field.dispatchEvent(new InputEvent("input", {
                bubbles: true,
                inputType: "deleteContentBackward",
              }));
              field.dispatchEvent(new Event("change", { bubbles: true }));
              field.blur();
              return true;
            })()
            """,
        )
        editor.onBridgeCmd(f"blur:0:{note.id}:")
        wait_for_condition(
            lambda: "[sound:" not in note.fields[0],
            timeout=5.0,
            message="Editor field was not cleared before graph analysis",
        )

        click_selector(editor.web, _button_selector("aqe:analyze"), timeout=5.0)
        state = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const status = document.querySelector('[data-testid="aqe-status-0"]');
              return {
                status: status?.textContent || "",
                statusKind: status?.dataset.kind || "",
              };
            })()
            """,
            lambda value: value is not None
            and value["statusKind"] == "error"
            and "No [sound:...] reference" in value["status"],
            timeout=10.0,
        )

        assert state["status"] != "Analyzing..."
    finally:
        editor.set_note(None)
        parent.close()


def test_show_graph_default_setting_change_applies_to_later_editor_loads(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    enabled_source = media_dir / "editor_default_graph_setting_enabled.wav"
    disabled_source = media_dir / "editor_default_graph_setting_disabled.wav"
    generate_tone(ffmpeg_config, enabled_source, duration_s=0.9)
    generate_tone(ffmpeg_config, disabled_source, duration_s=0.9)
    enabled_note = _basic_audio_note(anki_mw, enabled_source.name)
    disabled_note = _basic_audio_note(anki_mw, disabled_source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, show_graph_by_default=False)

    _set_show_graph_by_default_from_settings(anki_mw, True)
    editor, parent = _open_editor(anki_mw, enabled_note)
    try:
        track = _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == enabled_source.name
            and value["graphButtonLabel"] == "Redraw",
            timeout=15.0,
        )
        assert track["active"] is True
    finally:
        editor.set_note(None)
        parent.close()

    _set_show_graph_by_default_from_settings(anki_mw, False)
    editor, parent = _open_editor(anki_mw, disabled_note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
        quiet_until = time.monotonic() + 1.0
        wait_for_condition(lambda: time.monotonic() >= quiet_until, timeout=2.0)
        state = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None,
            timeout=5.0,
        )

        assert state["active"] is False
        assert state["hidden"] is True
        assert state["hasTrack"] is False
        assert state["graphButtonLabel"] == "Graph"
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_settings_save_refreshes_current_editor_repeat_default(
    anki_mw,
    ffmpeg_config,
) -> None:
    runtime_addon = import_runtime_addon_module()
    SettingsDialog = import_runtime_addon_module(".settings").SettingsDialog

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_settings_repeat_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.8)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        repeat_playback_by_default=False,
        repeat_pause_seconds=0.0,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:settings"), timeout=10.0)
        wait_for_js_condition(
            editor.web,
            "document.querySelector('[data-testid=\"aqe-split-0-play-menu\"]')?.getAttribute('data-aqe-tooltip-content')",
            lambda value: value == "Play quick settings.",
            timeout=5.0,
        )
        wait_for_js_condition(
            editor.web,
            "window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest(0)?.repeatEnabled : null",
            lambda value: value is False,
            timeout=5.0,
        )
        click_selector(editor.web, _button_selector("aqe:settings"), timeout=5.0)
        QApplication.processEvents()
        wait_for_condition(
            lambda: isinstance(runtime_addon._settings_dialog, SettingsDialog)
            and runtime_addon._settings_dialog.isVisible(),
            timeout=5.0,
        )
        dialog = runtime_addon._settings_dialog
        checkbox_selector = '[data-testid="repeat-playback-by-default"]'
        pause_selector = '[data-testid="repeat-pause-seconds"]'
        save_selector = '[data-testid="settings-save"]'
        wait_for_js_condition(
            dialog,
            f"document.querySelector({json.dumps(checkbox_selector)})?.checked",
            lambda value: value is False,
            timeout=5.0,
        )
        click_selector(dialog, checkbox_selector, timeout=5.0)
        wait_for_js_condition(
            dialog,
            f"""
            (() => {{
              const input = document.querySelector({json.dumps(pause_selector)});
              if (!input) return false;
              input.value = "1.5";
              input.dispatchEvent(new Event("input", {{ bubbles: true }}));
              input.dispatchEvent(new Event("change", {{ bubbles: true }}));
              return Number(input.value);
            }})()
            """,
            lambda value: value == 1.5,
            timeout=5.0,
        )

        with patch.object(
            anki_mw.addonManager,
            "writeConfig",
            wraps=anki_mw.addonManager.writeConfig,
        ) as mock_write:
            click_selector(dialog, save_selector, timeout=5.0)
            wait_for_condition(lambda: mock_write.called, timeout=5.0)

        saved_config = mock_write.call_args.args[1]
        assert saved_config["repeat_playback_by_default"] is True
        assert saved_config["repeat_pause_seconds"] == 1.5
        wait_for_js_condition(
            editor.web,
            "document.querySelector('[data-testid=\"aqe-split-0-play-menu\"]')?.getAttribute('data-aqe-tooltip-content')",
            lambda value: value == "Play quick settings.",
            timeout=10.0,
        )
        wait_for_js_condition(
            editor.web,
            "window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest(0)?.repeatEnabled : null",
            lambda value: value is True,
            timeout=10.0,
        )
        wait_for_js_condition(
            editor.web,
            "window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest(0)?.repeatPauseSeconds : null",
            lambda value: value == 1.5,
            timeout=10.0,
        )
    finally:
        editor.set_note(None)
        parent.close()
