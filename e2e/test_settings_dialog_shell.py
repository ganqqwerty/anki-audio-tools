"""E2E tests for settings dialog shell rendering and initial state."""

from __future__ import annotations

import json

from PyQt6.QtWidgets import QApplication

from e2e.conftest import import_runtime_addon_module
from e2e.helpers import wait_for_js_condition
from e2e.settings_dialog_helpers import open_settings_dialog


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
    render_settings_html = import_runtime_addon_module(".settings")._render_settings_html

    config = anki_mw.addonManager.getConfig("1000000002") or {}
    html = render_settings_html(config)
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
