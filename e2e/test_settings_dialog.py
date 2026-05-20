"""E2E tests for the Audio Quick Editor settings dialog."""

from __future__ import annotations

import json
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from e2e.helpers import click_selector, wait_for_condition, wait_for_js_condition


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


def test_settings_dialog_uses_anki_dark_theme_classes_and_readable_colors(anki_mw) -> None:
    from aqt.theme import Theme

    previous_theme = anki_mw.pm.theme()
    try:
        anki_mw.set_theme(Theme.DARK)
        QApplication.processEvents()
        dialog = _open_settings_dialog(anki_mw)

        theme_state = wait_for_js_condition(
            dialog,
            """
            (() => {
              const root = document.documentElement;
              const body = document.body;
              const app = document.querySelector('.settings-root');
              if (!app) return null;
              const style = getComputedStyle(app);
              const parseRgb = (value) => {
                const match = value.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
                return match ? [Number(match[1]), Number(match[2]), Number(match[3])] : null;
              };
              const luminance = (rgb) => {
                if (!rgb) return null;
                const linear = rgb.map((channel) => {
                  const scaled = channel / 255;
                  return scaled <= 0.03928 ? scaled / 12.92 : Math.pow((scaled + 0.055) / 1.055, 2.4);
                });
                return (0.2126 * linear[0]) + (0.7152 * linear[1]) + (0.0722 * linear[2]);
              };
              const fg = luminance(parseRgb(style.color));
              const bg = luminance(parseRgb(style.backgroundColor));
              const contrast = fg === null || bg === null ? 0 : (Math.max(fg, bg) + 0.05) / (Math.min(fg, bg) + 0.05);
              return {
                bodyNight: body.classList.contains('nightMode'),
                bsTheme: root.dataset.bsTheme || "",
                contrast,
                htmlNight: root.classList.contains('night-mode'),
              };
            })()
            """,
            lambda value: value is not None
            and value["htmlNight"] is True
            and value["bodyNight"] is True
            and value["bsTheme"] == "dark"
            and value["contrast"] >= 4.5,
            timeout=10.0,
        )
    finally:
        anki_mw.set_theme(previous_theme)
        QApplication.processEvents()

    assert theme_state["contrast"] >= 4.5


def test_initial_state_is_embedded(anki_mw) -> None:
    from anki_audio_quick_editor.settings import _render_settings_html

    config = anki_mw.addonManager.getConfig("1000000002") or {}
    html = _render_settings_html(config)
    assert "window.__INITIAL_STATE__" in html


def test_initial_state_shape(anki_mw) -> None:
    from anki_audio_quick_editor.settings.initial_state import build_initial_state

    config = anki_mw.addonManager.getConfig("1000000002") or {}
    state = json.loads(build_initial_state(config))
    assert set(state) == {
        "addon_dir",
        "config",
        "diagnostics",
        "direction",
        "locale",
        "log_file_path",
        "messages",
        "version",
    }
    assert state["direction"] in {"ltr", "rtl"}
    assert isinstance(state["locale"], str)
    assert isinstance(state["messages"], dict)


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
        "repeat_pause_seconds": 0.0,
        "show_graph_by_default": False,
        "graph_voice_range": "general",
        "graph_recording_condition": "auto",
        "graph_smoothness": "very_smooth",
        "graph_connect_short_dropouts_ms": 240,
        "graph_voice_lock": "balanced",
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
        "dpdfnet_attn_limit_db": 12.0,
        "denoise_algorithm": "standard",
        "pause_aggressiveness": "normal",
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


def test_show_graph_by_default_checkbox_toggles_and_saves_in_one_session(anki_mw) -> None:
    config = anki_mw.addonManager.getConfig("1000000002") or {}
    config["show_graph_by_default"] = False
    anki_mw.addonManager.writeConfig("1000000002", config)

    dialog = _open_settings_dialog(anki_mw)
    checkbox_selector = '[data-testid="show-graph-by-default"]'
    save_selector = '[data-testid="settings-save"]'

    initial = wait_for_js_condition(
        dialog,
        f"document.querySelector({json.dumps(checkbox_selector)})?.checked",
        lambda value: value is False,
        timeout=5.0,
    )
    assert initial is False

    click_selector(dialog, checkbox_selector, timeout=5.0)
    wait_for_js_condition(
        dialog,
        f"document.querySelector({json.dumps(checkbox_selector)})?.checked",
        lambda value: value is True,
        timeout=5.0,
    )
    click_selector(dialog, checkbox_selector, timeout=5.0)
    wait_for_js_condition(
        dialog,
        f"document.querySelector({json.dumps(checkbox_selector)})?.checked",
        lambda value: value is False,
        timeout=5.0,
    )
    click_selector(dialog, checkbox_selector, timeout=5.0)

    with patch.object(
        anki_mw.addonManager,
        "writeConfig",
        wraps=anki_mw.addonManager.writeConfig,
    ) as mock_write:
        click_selector(dialog, save_selector, timeout=5.0)
        wait_for_condition(lambda: mock_write.called, timeout=5.0)

    saved_config = mock_write.call_args.args[1]
    assert saved_config["show_graph_by_default"] is True


def test_diagnostics_can_copy_support_report_and_open_log_file(anki_mw) -> None:
    from anki_audio_quick_editor.support import (
        clear_latest_denoise_support_incident,
        record_latest_denoise_support_incident,
    )

    clear_latest_denoise_support_incident()
    record_latest_denoise_support_incident(
        operation="rnnoise_denoise",
        media_filename="3d8ca69aee6.mp3",
        source_path="/tmp/3d8ca69aee6.mp3",
        user_message="RNNoise denoise failed.",
        exception_type="AudioProcessingError",
    )
    dialog = _open_settings_dialog(anki_mw)

    click_selector(dialog, '[data-testid="settings-tab-diagnostics"]', timeout=5.0)
    click_selector(dialog, '[data-testid="copy-support-report"]', timeout=5.0)

    wait_for_condition(
        lambda: "3d8ca69aee6.mp3" in QApplication.clipboard().text()
        and "RNNoise denoise failed." in QApplication.clipboard().text(),
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
