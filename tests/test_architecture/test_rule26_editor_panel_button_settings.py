"""Rule 26: editor panel command buttons stay configurable from settings."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.dev_tasks.node_tools import find_node_command

ROOT = Path(__file__).parent.parent.parent
NODE = find_node_command()
EDITOR_BUTTONS = ROOT / "settings_ui" / "src" / "lib" / "editor-toolbar-buttons.ts"
SETTINGS_BUTTONS = ROOT / "settings_ui" / "src" / "lib" / "settings-toolbar-buttons.ts"
SELECTION_TOOLBAR = ROOT / "settings_ui" / "src" / "editor-inline" / "SelectionToolbar.svelte"
TOOLBAR_SETTINGS = ROOT / "settings_ui" / "src" / "settings" / "ToolbarVisibilitySettings.svelte"
CONFIG_SCHEMA = ROOT / "addon" / "anki_audio_quick_editor" / "config.schema.json"
CONFIG_DEFAULTS = ROOT / "addon" / "anki_audio_quick_editor" / "config.json"


_FUNCTION_QUERY = r"""
const ts = require("typescript");
const functionName = process.argv[1];
let source = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", chunk => source += chunk);
process.stdin.on("end", () => {
  const file = ts.createSourceFile("query.ts", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  let target;
  const visit = node => {
    if (ts.isFunctionDeclaration(node) && node.name?.text === functionName) target = node;
    ts.forEachChild(node, visit);
  };
  visit(file);
  if (!target?.body) process.exit(2);
  const commands = [];
  const collect = node => {
    if (ts.isPropertyAssignment(node)
        && ((ts.isIdentifier(node.name) && node.name.text === "command")
            || (ts.isStringLiteral(node.name) && node.name.text === "command"))
        && ts.isStringLiteralLike(node.initializer)) commands.push(node.initializer.text);
    ts.forEachChild(node, collect);
  };
  collect(target.body);
  process.stdout.write(JSON.stringify({body: target.body.getText(file), commands}));
});
"""


def _function_query(source: str, function_name: str) -> dict[str, object]:
    assert NODE is not None, "Node.js is required for TypeScript architecture queries"
    result = subprocess.run(
        [NODE, "-e", _FUNCTION_QUERY, function_name],
        cwd=ROOT / "settings_ui",
        input=source,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"{function_name} function not found: {result.stderr}"
    value = json.loads(result.stdout)
    assert isinstance(value, dict)
    return value


def _commands_in_function(source: str, function_name: str) -> set[str]:
    commands = _function_query(source, function_name)["commands"]
    assert isinstance(commands, list)
    return {str(command) for command in commands}


def _selection_toolbar_literal_commands() -> set[str]:
    source = SELECTION_TOOLBAR.read_text(encoding="utf-8")
    marker = 'data-aqe-command="'
    return {part.split('"', 1)[0] for part in source.split(marker)[1:]}


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
    body = _function_query(settings_buttons_source, "settingsToolbarButtons")["body"]
    assert isinstance(body, str)
    assert "selectionActionButtons()" in body
    assert "settingsToolbarButtons" in settings_source
    assert "const buttons = settingsToolbarButtons();" in settings_source


def test_function_query_ignores_braces_and_commands_in_comments_or_strings() -> None:
    source = '''
    function commandButtons() {
      const example = "} command: \\\"aqe:false\\\"";
      // { command: "aqe:comment" }
      return [{ command: "aqe:real" }];
    }
    '''
    assert _commands_in_function(source, "commandButtons") == {"aqe:real"}
