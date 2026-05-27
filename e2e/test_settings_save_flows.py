"""E2E tests for settings controls that save within one dialog session."""

from __future__ import annotations

import json
from unittest.mock import patch

from e2e.helpers import click_selector, wait_for_condition, wait_for_js_condition
from e2e.settings_dialog_helpers import open_settings_dialog


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
