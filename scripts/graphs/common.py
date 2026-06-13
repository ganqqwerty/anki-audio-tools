"""Shared utilities and constants for bridge diagram generators."""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
GRAPHS = ROOT / "docs" / "graphs"
ADDON = ROOT / "addon" / "anki_audio_quick_editor"
SETTINGS_UI_SRC = ROOT / "settings_ui" / "src"

MERMAID_HEADER = "```mermaid\n"
MERMAID_FOOTER = "\n```\n"


def _parse_cmd_constants(path: Path) -> dict[str, str]:
    """Parse CMD_* = 'aqe:*' constants from editor_actions.py."""
    if not path.is_file():
        return {}
    source = path.read_text()
    tree = ast.parse(source)
    constants: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith("CMD_"):
                    if isinstance(node.value, ast.Constant) and isinstance(
                        node.value.value, str
                    ):
                        constants[target.id] = node.value.value
    return constants


def _parse_bridge_handlers_dict(path: Path, dict_name: str) -> dict[str, str]:
    """Parse a handlers dict from a Python file.

    Returns a mapping of command name -> handler callable name.
    Handles patterns like:
        handlers = {
            CMD_SLOWER: deps.update_state_and_render,
            "aqe:play": deps.play,
        }
    """
    if not path.is_file():
        return {}
    source = path.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    handlers: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not (isinstance(target, ast.Name) and target.id == dict_name):
                continue
            if not isinstance(node.value, ast.Dict):
                continue
            if node.value.keys is None or node.value.values is None:
                continue
            keys: list[ast.expr] = node.value.keys  # type: ignore[assignment]
            vals: list[ast.expr] = node.value.values
            for key, val in zip(keys, vals):
                key_str = _ast_key_to_str(key)
                if key_str is None:
                    continue
                val_str = _ast_val_to_str(val)
                if val_str is None:
                    continue
                handlers[key_str] = val_str
    return handlers


def _ast_key_to_str(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return node.id
    return None


def _ast_val_to_str(node: ast.expr) -> str | None:
    if isinstance(node, ast.Attribute):
        base = _ast_val_to_str(node.value)
        return f"{base}.{node.attr}" if base else None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Lambda):
        return _ast_val_to_str(node.body)
    if isinstance(node, ast.Call):
        return _ast_val_to_str(node.func)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _parse_if_name_chain(path: Path) -> dict[str, str]:
    """Parse if/elif command_name == '...' dispatch from settings/commands.py and browser_dialog.py."""
    if not path.is_file():
        return {}
    source = path.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    handlers: dict[str, str] = {}

    class _Visitor(ast.NodeVisitor):
        def visit_If(self, node: ast.If) -> None:
            self._check_compare(node.test, node)
            self.generic_visit(node)

        def _check_compare(self, test: ast.expr, node: ast.If) -> None:
            if not isinstance(test, ast.Compare):
                return
            if not test.comparators:
                return
            condition = test.comparators[0]
            if not isinstance(condition, ast.Constant) or not isinstance(
                condition.value, str
            ):
                return
            command = condition.value
            handler = _extract_handler_from_body(node.body)
            if handler:
                handlers[command] = handler

    _Visitor().visit(tree)
    return handlers


def _extract_handler_from_body(body: list[ast.stmt]) -> str | None:
    """Extract a handler name from statement body (function call or return)."""
    for stmt in body:
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            func = stmt.value.func
            if isinstance(func, ast.Name):
                return func.id
            if isinstance(func, ast.Attribute):
                return _ast_val_to_str(func)
        if isinstance(stmt, ast.Return) and stmt.value is not None:
            if isinstance(stmt.value, ast.Call):
                return _ast_val_to_str(stmt.value.func)
            if isinstance(stmt.value, ast.Constant) and stmt.value.value is True:
                return "return True"
    return None


def _parse_ts_bridge_commands(path: Path) -> list[str]:
    """Extract command names from TypeScript bridge files using regex."""
    if not path.is_file():
        return []
    source = path.read_text()
    commands: set[str] = set()

    patterns = [
        r'sendBridgeCommand\("([^"]+)"\)',
        r'pycmd\("([^"]+)"\)',
        r"sendBridgeEnvelope\(\"([^\"]+)\"",
        r"command:\s*'([^']+)'",
        r"command:\s*\"([^\"]+)\"",
    ]
    for pat in patterns:
        for match in re.finditer(pat, source):
            commands.add(match.group(1))

    return sorted(commands)


def _parse_window_contract(path: Path) -> list[dict[str, str]]:
    """Parse EDITOR_WINDOW_CONTRACT_NAMES and installEditorWindowContract from window-contract.ts."""
    if not path.is_file():
        return []
    source = path.read_text()

    entries: list[dict[str, str]] = []
    assign_pattern = re.compile(
        r"window\.(__aqe\w+)\s*=\s*(\w+)", re.MULTILINE
    )
    for match in assign_pattern.finditer(source):
        window_name = match.group(1)
        handler = match.group(2)
        if window_name in source:
            entries.append({"window_name": window_name, "handler": handler})

    return entries
