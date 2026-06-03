"""Focused tests for toolbar visibility migration behavior."""

from __future__ import annotations

from anki_audio_quick_editor.config_migration import (
    CURRENT_CONFIG_VERSION,
    migrate_config,
)


def _defaults() -> dict[str, object]:
    return {
        "_config_version": CURRENT_CONFIG_VERSION,
        "visible_editor_buttons": ["aqe:play", "aqe:settings"],
        "editor_button_modes": {
            "aqe:play": "icon",
            "aqe:record-voice": "icon",
            "aqe:play-recording": "icon",
            "aqe:settings": "icon",
        },
    }


def test_keeps_supported_default_hidden_visible_editor_buttons() -> None:
    user = {
        "_config_version": CURRENT_CONFIG_VERSION,
        "visible_editor_buttons": ["aqe:play", "aqe:record-voice", "aqe:settings"],
    }

    migrated, changed = migrate_config(user, _defaults())

    assert changed is True
    assert migrated["visible_editor_buttons"] == [
        "aqe:play",
        "aqe:record-voice",
        "aqe:play-recording",
        "aqe:settings",
    ]


def test_normalizes_partial_recording_panel_visibility() -> None:
    user = {
        "_config_version": CURRENT_CONFIG_VERSION,
        "visible_editor_buttons": ["aqe:play", "aqe:play-recording", "aqe:settings"],
    }

    migrated, changed = migrate_config(user, _defaults())

    assert changed is True
    assert migrated["visible_editor_buttons"] == [
        "aqe:play",
        "aqe:record-voice",
        "aqe:play-recording",
        "aqe:settings",
    ]
