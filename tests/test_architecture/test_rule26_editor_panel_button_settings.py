"""Rule 26: editor panel command buttons stay configurable from settings."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
EDITOR_BUTTONS = ROOT / "settings_ui" / "src" / "lib" / "editor-toolbar-buttons.ts"
SETTINGS_BUTTONS = ROOT / "settings_ui" / "src" / "lib" / "settings-toolbar-buttons.ts"
SELECTION_TOOLBAR = ROOT / "settings_ui" / "src" / "editor-inline" / "SelectionToolbar.svelte"
TOOLBAR_SETTINGS = ROOT / "settings_ui" / "src" / "settings" / "ToolbarVisibilitySettings.svelte"
CONFIG_SCHEMA = ROOT / "addon" / "anki_audio_quick_editor" / "config.schema.json"
CONFIG_DEFAULTS = ROOT / "addon" / "anki_audio_quick_editor" / "config.json"


def _function_body(source: str, function_name: str) -> str:
    match = re.search(rf"\bfunction\s+{re.escape(function_name)}\b[^\{{]*\{{", source)
    assert match is not None, f"{function_name} function not found"
    body_start = match.end()
    depth = 1
    for index, char in enumerate(source[body_start:], start=body_start):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[body_start:index]
    raise AssertionError(f"{function_name} function body is incomplete")


def _commands_in_function(source: str, function_name: str) -> set[str]:
    return set(re.findall(r'command:\s*"([^"]+)"', _function_body(source, function_name)))


def _selection_toolbar_literal_commands() -> set[str]:
    source = SELECTION_TOOLBAR.read_text(encoding="utf-8")
    return set(re.findall(r'data-aqe-command="([^"]+)"', source))


def _config_schema_enum(property_name: str) -> set[str]:
    schema = json.loads(CONFIG_SCHEMA.read_text(encoding="utf-8"))
    property_schema = schema["properties"][property_name]
    if property_name == "visible_editor_buttons":
        return set(property_schema["items"]["enum"])
    if property_name == "editor_button_modes":
        return set(property_schema["propertyNames"]["enum"])
    raise AssertionError(f"unsupported config property: {property_name}")


def test_editor_panel_commands_are_settings_configurable() -> None:
    source = EDITOR_BUTTONS.read_text(encoding="utf-8")
    settings_source = SETTINGS_BUTTONS.read_text(encoding="utf-8")
    main_toolbar_commands = (
        _commands_in_function(source, "commandButtons")
        | _commands_in_function(source, "denoiseTopLevelButton")
    )
    selection_action_commands = _commands_in_function(settings_source, "selectionActionButtons")
    panel_commands = main_toolbar_commands | selection_action_commands

    assert _selection_toolbar_literal_commands() <= panel_commands
    assert panel_commands <= _config_schema_enum("visible_editor_buttons")
    assert panel_commands <= _config_schema_enum("editor_button_modes")
    assert panel_commands <= set(json.loads(CONFIG_DEFAULTS.read_text(encoding="utf-8"))["editor_button_modes"])
    assert {"aqe:rnnoise", "aqe:dpdfnet", "aqe:voice-only"}.isdisjoint(panel_commands)


def test_settings_uses_settings_facing_editor_button_registry() -> None:
    settings_buttons_source = SETTINGS_BUTTONS.read_text(encoding="utf-8")
    settings_source = TOOLBAR_SETTINGS.read_text(encoding="utf-8")

    assert "export function settingsToolbarButtons" in settings_buttons_source
    assert "selectionActionButtons()" in _function_body(settings_buttons_source, "settingsToolbarButtons")
    assert "settingsToolbarButtons" in settings_source
    assert "const buttons = settingsToolbarButtons();" in settings_source
