"""E2E tests for the settings-hidden toolbar warning."""

from __future__ import annotations

from e2e.editor_note_helpers import DEFAULT_VISIBLE_EDITOR_BUTTONS
from e2e.helpers import click_selector, wait_for_js_condition
from e2e.settings_dialog_helpers import open_settings_dialog


def test_hidden_settings_warning_expands_thumbnail_in_qt_webview(anki_mw) -> None:
    config = anki_mw.addonManager.getConfig("1000000002") or {}
    config["visible_editor_buttons"] = [
        button for button in DEFAULT_VISIBLE_EDITOR_BUTTONS if button != "aqe:settings"
    ]
    anki_mw.addonManager.writeConfig("1000000002", config)

    dialog = open_settings_dialog(anki_mw)

    assert wait_for_js_condition(
        dialog,
        """
        (() => {
          const card = document.querySelector('[data-testid="button-settings-settings"]');
          const warning = document.querySelector('[data-testid="settings-hidden-warning"]');
          return Boolean(card && warning && card.contains(warning));
        })()
        """,
        lambda value: value is True,
        timeout=5.0,
    ) is True

    click_selector(dialog, '[data-testid="settings-hidden-warning-thumbnail"]', timeout=5.0)
    assert wait_for_js_condition(
        dialog,
        """
        (() => {
          const thumbnail = document.querySelector('[data-testid="settings-hidden-warning-thumbnail"]');
          const expanded = document.querySelector('[data-testid="settings-hidden-warning-expanded-image"]');
          return Boolean(thumbnail && expanded && thumbnail.getAttribute("aria-expanded") === "true");
        })()
        """,
        lambda value: value is True,
        timeout=5.0,
    ) is True
