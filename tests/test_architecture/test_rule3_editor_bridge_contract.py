"""Rule 3: Python bridge commands and injected editor UI stay in sync."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from .conftest import ADDON_DIR

EDITOR_ACTIONS = ADDON_DIR / "editor_actions.py"
EDITOR_UI = ADDON_DIR / "editor_ui.py"
EDITOR_UI_TS = ADDON_DIR.parent.parent / "settings_ui" / "src" / "editor-inline"
LEGACY_COMMANDS = {"aqe:preview", "aqe:save", "aqe:cancel"}


def _constant_tuple_assignment(path: Path, name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    constants = {
        node.targets[0].id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        if not isinstance(node.value, ast.Tuple):
            raise AssertionError(f"{name} must stay a tuple literal")
        values: set[str] = set()
        for element in node.value.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                values.add(element.value)
            elif isinstance(element, ast.Name) and element.id in constants:
                values.add(constants[element.id])
        if len(values) != len(node.value.elts):
            raise AssertionError(f"{name} must contain only string literals or string constants")
        return values
    raise AssertionError(f"{name} assignment not found in {path}")


def _editor_ui_commands() -> set[str]:
    tree = ast.parse(EDITOR_UI.read_text(encoding="utf-8"))
    commands: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            commands.update(re.findall(r"aqe:[a-z-]+", node.value))
    for path in sorted(EDITOR_UI_TS.rglob("*")):
        if path.suffix not in {".svelte", ".ts"}:
            continue
        commands.update(re.findall(r"aqe:[a-z-]+", path.read_text(encoding="utf-8")))
    return commands


def test_editor_ui_commands_are_registered_by_python_bridge() -> None:
    registered = _constant_tuple_assignment(EDITOR_ACTIONS, "BRIDGE_COMMANDS")
    ui_commands = _editor_ui_commands()

    assert ui_commands <= registered
    assert registered - {"aqe:scan"} <= ui_commands


def test_legacy_manual_preview_save_cancel_commands_are_not_registered() -> None:
    registered = _constant_tuple_assignment(EDITOR_ACTIONS, "BRIDGE_COMMANDS")
    ui_commands = _editor_ui_commands()

    assert registered.isdisjoint(LEGACY_COMMANDS)
    assert ui_commands.isdisjoint(LEGACY_COMMANDS)
