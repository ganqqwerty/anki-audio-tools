"""E2E tests for the Audio Quick Editor settings dialog."""

from __future__ import annotations

import json
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from e2e.helpers import click_selector, wait_for_condition


def _open_settings_dialog(anki_mw):
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

    wait_for_condition(
        lambda: isinstance(anki_audio_quick_editor._settings_dialog, SettingsDialog)
        and anki_audio_quick_editor._settings_dialog.isVisible(),
        timeout=5.0,
    )
    return anki_audio_quick_editor._settings_dialog


def test_tools_menu_action_opens_settings_dialog(anki_mw, qtbot) -> None:
    dialog = _open_settings_dialog(anki_mw)
    qtbot.waitUntil(lambda: dialog.isVisible(), timeout=5000)


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

    from anki_audio_quick_editor.config_migration import CURRENT_CONFIG_VERSION
    from anki_audio_quick_editor.settings.commands import handle_settings_command

    config = {
        "_config_version": CURRENT_CONFIG_VERSION,
        "enabled": False,
        "debug_logging": True,
        "show_ffmpeg_commands": False,
        "repeat_playback_by_default": False,
        "manual_trim_small_ms": 100,
        "manual_trim_large_ms": 500,
        "speed_step": 0.05,
        "min_speed": 0.75,
        "max_speed": 1.5,
        "volume_step_db": 3.0,
        "min_volume_db": -24.0,
        "max_volume_db": 24.0,
        "internal_pause_silence_threshold_db": -45,
        "internal_pause_threshold_ms": 300,
        "internal_pause_target_gap_ms": 100,
        "output_format": "mp3",
        "ffmpeg_path": "",
        "deep_filter_path": "",
        "deep_filter_post_filter": True,
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


def test_diagnostics_can_copy_support_report_and_open_log_file(anki_mw) -> None:
    from anki_audio_quick_editor.support import (
        clear_latest_sidon_support_incident,
        record_latest_sidon_support_incident,
    )

    clear_latest_sidon_support_incident()
    record_latest_sidon_support_incident(
        operation="sidon_restore",
        media_filename="3d8ca69aee6.mp3",
        source_path="/tmp/3d8ca69aee6.mp3",
        user_message="Sidon speech restoration failed.",
        exception_type="AudioProcessingError",
    )
    dialog = _open_settings_dialog(anki_mw)

    click_selector(dialog, '[data-testid="settings-tab-diagnostics"]', timeout=5.0)
    click_selector(dialog, '[data-testid="copy-support-report"]', timeout=5.0)

    wait_for_condition(
        lambda: "3d8ca69aee6.mp3" in QApplication.clipboard().text()
        and "Sidon speech restoration failed." in QApplication.clipboard().text(),
        timeout=5.0,
    )

    revealed: list[str] = []
    with patch(
        "anki_audio_quick_editor.file_reveal.reveal_file",
        lambda path, **_kwargs: revealed.append(str(path)),
    ):
        click_selector(dialog, '[data-testid="show-log-file"]', timeout=5.0)
        wait_for_condition(lambda: bool(revealed), timeout=5.0)

    assert revealed[0].endswith("anki_audio_quick_editor.log")
