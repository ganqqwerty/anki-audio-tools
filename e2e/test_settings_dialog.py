"""E2E tests for the Audio Quick Editor settings dialog."""

from __future__ import annotations

import json

from PyQt6.QtWidgets import QApplication


def test_tools_menu_action_opens_settings_dialog(anki_mw, qtbot) -> None:
    import anki_audio_quick_editor
    from anki_audio_quick_editor.settings import SettingsDialog

    submenu = next(
        action.menu()
        for action in anki_mw.form.menuTools.actions()
        if action.menu() and action.menu().title() == "Anki Audio Quick Editor"
    )
    settings_action = next(action for action in submenu.actions() if action.text() == "Settings")
    settings_action.trigger()
    QApplication.processEvents()

    qtbot.waitUntil(
        lambda: isinstance(anki_audio_quick_editor._settings_dialog, SettingsDialog)
        and anki_audio_quick_editor._settings_dialog.isVisible(),
        timeout=5000,
    )


def test_initial_state_is_embedded(anki_mw) -> None:
    from anki_audio_quick_editor.settings import _render_settings_html

    config = anki_mw.addonManager.getConfig("1000000002") or {}
    html = _render_settings_html(config)
    assert "window.__INITIAL_STATE__" in html


def test_initial_state_shape(anki_mw) -> None:
    from anki_audio_quick_editor.settings.initial_state import build_initial_state

    config = anki_mw.addonManager.getConfig("1000000002") or {}
    state = json.loads(build_initial_state(config))
    assert set(state) == {"config", "version", "addon_dir", "log_file_path", "diagnostics"}


def test_save_command_writes_config(anki_mw) -> None:
    from unittest.mock import patch

    from anki_audio_quick_editor.settings.commands import handle_settings_command

    config = {
        "_config_version": 3,
        "enabled": False,
        "debug_logging": True,
        "show_ffmpeg_commands": False,
        "manual_trim_small_ms": 100,
        "manual_trim_large_ms": 500,
        "speed_step": 0.05,
        "min_speed": 0.75,
        "max_speed": 1.5,
        "edge_silence_threshold_db": -35,
        "edge_silence_min_ms": 100,
        "internal_pause_threshold_ms": 300,
        "internal_pause_target_gap_ms": 100,
        "output_format": "mp3",
        "ffmpeg_path": "",
    }
    eval_calls: list[str] = []
    dialog = type("Dialog", (), {"accept": lambda self: None, "reject": lambda self: None})()

    with patch.object(
        anki_mw.addonManager,
        "writeConfig",
        wraps=anki_mw.addonManager.writeConfig,
    ) as mock_write:
        handle_settings_command(
            f"settings_save:{json.dumps(config)}",
            lambda js: eval_calls.append(js),
            dialog,
        )
        QApplication.processEvents()

    assert mock_write.called
    assert eval_calls == []
