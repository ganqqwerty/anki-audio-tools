"""Tests for editor-button migration behavior."""

from __future__ import annotations

from anki_audio_quick_editor.config_migration import (
    CURRENT_CONFIG_VERSION,
    migrate_config,
)


class TestMigrateConfigEditorButtons:
    def test_picks_up_visible_editor_buttons_default(self) -> None:
        user = {"_config_version": 15, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "visible_editor_buttons": ["aqe:play", "aqe:settings"],
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["visible_editor_buttons"] == ["aqe:play", "aqe:settings"]
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_appends_v2_selection_buttons_to_legacy_visible_editor_buttons(self) -> None:
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "visible_editor_buttons": [
                "aqe:play",
                "aqe:settings",
                "aqe:delete-selection",
                "aqe:delete-rest",
            ],
        }
        user = {
            "_config_version": 1,
            "visible_editor_buttons": ["aqe:play", "aqe:settings"],
        }

        migrated, changed = migrate_config(user, defaults)

        assert changed is True
        assert migrated["visible_editor_buttons"] == [
            "aqe:play",
            "aqe:settings",
            "aqe:delete-selection",
            "aqe:delete-rest",
        ]

    def test_keeps_current_hidden_selection_buttons_hidden(self) -> None:
        config = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "visible_editor_buttons": ["aqe:play", "aqe:settings"],
        }
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "visible_editor_buttons": [
                "aqe:play",
                "aqe:settings",
                "aqe:delete-selection",
                "aqe:delete-rest",
            ],
        }

        migrated, changed = migrate_config(config, defaults)

        assert changed is False
        assert migrated["visible_editor_buttons"] == ["aqe:play", "aqe:settings"]

    def test_removes_stale_visible_editor_buttons(self) -> None:
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "visible_editor_buttons": ["aqe:play", "aqe:share", "aqe:settings"],
            "editor_button_modes": {
                "aqe:play": "icon",
                "aqe:share": "icon",
                "aqe:settings": "icon",
            },
        }
        user = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "visible_editor_buttons": ["aqe:play", "aqe:stale-button", "aqe:settings"],
        }

        migrated, changed = migrate_config(user, defaults)

        assert changed is True
        assert migrated["visible_editor_buttons"] == ["aqe:play", "aqe:settings"]

    def test_picks_up_editor_button_modes_default(self) -> None:
        user = {"_config_version": 18, "enabled": True}
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "enabled": True,
            "editor_button_modes": {
                "aqe:play": "text",
                "aqe:settings": "text",
            },
        }

        migrated, changed = migrate_config(user, defaults)

        assert migrated["editor_button_modes"] == {
            "aqe:play": "text",
            "aqe:settings": "text",
        }
        assert migrated["_config_version"] == CURRENT_CONFIG_VERSION
        assert changed is True

    def test_normalizes_editor_button_modes(self) -> None:
        defaults = {
            "_config_version": CURRENT_CONFIG_VERSION,
            "editor_button_modes": {
                "aqe:play": "text",
                "aqe:settings": "text",
            },
        }
        user = {
            "_config_version": 18,
            "editor_button_modes": {
                "aqe:play": "icon",
                "aqe:settings": "wide",
                "aqe:unknown": "icon",
            },
        }

        migrated, changed = migrate_config(user, defaults)

        assert changed is True
        assert migrated["editor_button_modes"] == {
            "aqe:play": "icon",
            "aqe:settings": "text",
        }

