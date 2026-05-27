"""E2E tests for the Audio Quick Editor settings dialog."""

from __future__ import annotations

import json
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from e2e.conftest import import_runtime_addon_module
from e2e.editor_note_helpers import DEFAULT_VISIBLE_EDITOR_BUTTONS
from e2e.helpers import (
    click_selector,
    wait_for_condition,
    wait_for_js_condition,
)
from e2e.settings_dialog_helpers import open_settings_dialog


def _bridge_command(command: str, payload: object) -> str:
    return "bridge:" + json.dumps({"command": command, "payload": payload})


def test_tools_menu_action_opens_settings_dialog(anki_mw, qtbot) -> None:
    dialog = open_settings_dialog(anki_mw)
    qtbot.waitUntil(lambda: dialog.isVisible(), timeout=5000)


def test_settings_dialog_uses_anki_dark_theme_classes_and_readable_colors(anki_mw) -> None:
    from aqt.theme import Theme

    previous_theme = anki_mw.pm.theme()
    try:
        anki_mw.set_theme(Theme.DARK)
        QApplication.processEvents()
        dialog = open_settings_dialog(anki_mw)

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
    _render_settings_html = import_runtime_addon_module(".settings")._render_settings_html

    config = anki_mw.addonManager.getConfig("1000000002") or {}
    html = _render_settings_html(config)
    assert "window.__INITIAL_STATE__" in html


def test_initial_state_shape(anki_mw) -> None:
    build_initial_state = import_runtime_addon_module(".settings.initial_state").build_initial_state

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

    current_config_version = import_runtime_addon_module(".config_migration").CURRENT_CONFIG_VERSION
    handle_settings_command = import_runtime_addon_module(".settings.commands").handle_settings_command

    config = {
        "_config_version": current_config_version,
        "enabled": False,
        "debug_logging": True,
        "show_ffmpeg_commands": False,
        "repeat_playback_by_default": False,
        "repeat_pause_seconds": 0.0,
        "voice_recording_countdown_seconds": 3,
        "share_target": "litterbox",
        "show_graph_by_default": False,
        "visible_editor_buttons": list(DEFAULT_VISIBLE_EDITOR_BUTTONS),
        "editor_button_modes": {
            "aqe:play": "text",
            "aqe:analyze": "text",
            "aqe:record-voice": "icon",
            "aqe:play-recording": "icon",
            "aqe:show-file": "text",
            "aqe:share": "text",
            "aqe:convert": "text",
            "aqe:remove-pauses": "text",
            "aqe:denoise-standard": "text",
            "aqe:pitch-hum": "text",
            "aqe:slower": "text",
            "aqe:faster": "text",
            "aqe:volume-down": "text",
            "aqe:volume-up": "text",
            "aqe:undo": "text",
            "aqe:redo": "text",
            "aqe:settings": "text",
        },
        "graph_voice_range": "general",
        "graph_recording_condition": "auto",
        "graph_smoothness": "very_smooth",
        "graph_connect_short_dropouts_ms": 240,
        "graph_voice_lock": "balanced",
        "speed_step": 1.5,
        "min_speed": 0.2,
        "max_speed": 5.0,
        "volume_step_db": 15.0,
        "min_volume_db": -40.0,
        "max_volume_db": 40.0,
        "pause_detection_algorithm": "silencedetect",
        "pause_aggressiveness": "normal",
        "pause_silencedetect_threshold_db": -45.0,
        "pause_silencedetect_min_silence_seconds": 0.3,
        "pause_silencedetect_min_speech_seconds": 0.1,
        "pause_silencedetect_preprocess_denoise": True,
        "pause_silero_threshold": 0.5,
        "pause_silero_min_silence_seconds": 0.45,
        "pause_silero_min_speech_seconds": 0.1,
        "pause_silero_preprocess_denoise": False,
        "output_format": "mp3",
        "ffmpeg_path": "",
        "deep_filter_post_filter": True,
        "dpdfnet_attn_limit_db": 12.0,
        "denoise_algorithm": "standard",
        "pitch_hum_mode": "direct",
    }
    eval_calls: list[str] = []
    dialog = type("Dialog", (), {"accept": lambda self: None, "reject": lambda self: None})()

    with patch.object(
        anki_mw.addonManager,
        "writeConfig",
        wraps=anki_mw.addonManager.writeConfig,
    ) as mock_write:
        handle_settings_command(
            _bridge_command("settings.save", config),
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

    dialog = open_settings_dialog(anki_mw)
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


def test_pitch_hum_default_mode_select_saves_in_one_session(anki_mw) -> None:
    config = anki_mw.addonManager.getConfig("1000000002") or {}
    config["pitch_hum_mode"] = "direct"
    anki_mw.addonManager.writeConfig("1000000002", config)

    dialog = open_settings_dialog(anki_mw)
    direct_selector = '[data-testid="pitch-hum-mode-direct"]'
    pitch_tier_selector = '[data-testid="pitch-hum-mode-pitch_tier"]'
    save_selector = '[data-testid="settings-save"]'

    initial = wait_for_js_condition(
        dialog,
        f"document.querySelector({json.dumps(direct_selector)})?.getAttribute('aria-checked')",
        lambda value: value == "true",
        timeout=5.0,
    )
    assert initial == "true"

    click_selector(dialog, pitch_tier_selector, timeout=5.0)
    wait_for_js_condition(
        dialog,
        f"document.querySelector({json.dumps(pitch_tier_selector)})?.getAttribute('aria-checked')",
        lambda value: value == "true",
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
    assert saved_config["pitch_hum_mode"] == "pitch_tier"


def test_share_target_select_saves_in_one_session(anki_mw) -> None:
    config = anki_mw.addonManager.getConfig("1000000002") or {}
    config["share_target"] = "litterbox"
    anki_mw.addonManager.writeConfig("1000000002", config)

    dialog = open_settings_dialog(anki_mw)
    litterbox_selector = '[data-testid="share-target-litterbox"]'
    catbox_selector = '[data-testid="share-target-catbox"]'
    save_selector = '[data-testid="settings-save"]'

    initial = wait_for_js_condition(
        dialog,
        f"document.querySelector({json.dumps(litterbox_selector)})?.getAttribute('aria-checked')",
        lambda value: value == "true",
        timeout=5.0,
    )
    assert initial == "true"

    click_selector(dialog, catbox_selector, timeout=5.0)
    wait_for_js_condition(
        dialog,
        f"document.querySelector({json.dumps(catbox_selector)})?.getAttribute('aria-checked')",
        lambda value: value == "true",
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
    assert saved_config["share_target"] == "catbox"


def test_toolbar_button_mode_toggle_saves_in_one_session(anki_mw) -> None:
    config = anki_mw.addonManager.getConfig("1000000002") or {}
    config["editor_button_modes"] = {
        **config.get("editor_button_modes", {}),
        "aqe:play": "text",
        "aqe:settings": "text",
    }
    anki_mw.addonManager.writeConfig("1000000002", config)

    dialog = open_settings_dialog(anki_mw)
    play_icon_selector = '[data-testid="button-settings-play-mode-icon"]'
    settings_icon_selector = '[data-testid="button-settings-settings-mode-icon"]'
    save_selector = '[data-testid="settings-save"]'

    wait_for_js_condition(
        dialog,
        f"document.querySelector({json.dumps(play_icon_selector)})?.checked",
        lambda value: value is False,
        timeout=5.0,
    )
    click_selector(dialog, play_icon_selector, timeout=5.0)
    click_selector(dialog, settings_icon_selector, timeout=5.0)
    wait_for_js_condition(
        dialog,
        f"""
        (() => {{
          const play = document.querySelector({json.dumps(play_icon_selector)});
          const settings = document.querySelector({json.dumps(settings_icon_selector)});
          return play && settings ? {{
            play: play.checked,
            settings: settings.checked,
          }} : null;
        }})()
        """,
        lambda value: value == {"play": True, "settings": True},
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
    assert saved_config["editor_button_modes"]["aqe:play"] == "icon"
    assert saved_config["editor_button_modes"]["aqe:settings"] == "icon"
