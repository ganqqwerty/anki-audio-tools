#!/usr/bin/env python3
"""Generate Anki bridge message Mermaid diagrams from source code analysis.

Parses Python bridge dispatchers and TypeScript bridge modules to produce:
  docs/graphs/bridge-messages-overview.mmd
  docs/graphs/bridge-messages-editor.mmd
  docs/graphs/bridge-messages-settings-batch.mmd
  docs/graphs/bridge-messages-window-contract.mmd
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRAPHS = ROOT / "docs" / "graphs"
ADDON = ROOT / "addon" / "anki_audio_quick_editor"
SETTINGS_UI_SRC = ROOT / "settings_ui" / "src"

GRAPHS.mkdir(parents=True, exist_ok=True)

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
        # Only include if it's in the EDITOR_WINDOW_CONTRACT_NAMES list
        if window_name in source:
            entries.append({"window_name": window_name, "handler": handler})

    return entries


def _render_overview() -> str:
    """System-level: 4 Anki webview contexts -> their bridges -> Python dispatchers."""
    lines = [
        "flowchart LR",
        "",
        "    subgraph EditorWebView[\"Editor WebView\"]",
        "        ts_editor[\"editor-inline/bridge.ts\"]",
        "    end",
        "",
        "    subgraph SettingsWebView[\"Settings WebView\"]",
        "        ts_settings[\"lib/bridge.ts\"]",
        "    end",
        "",
        "    subgraph BatchWebView[\"Batch WebView\"]",
        "        ts_batch[\"batch/bridge.ts\"]",
        "    end",
        "",
        "    subgraph ReviewerWebView[\"Reviewer WebView\"]",
        "        ts_reviewer[\"editor-inline/bridge.ts<br/>(reused)\"]",
        "    end",
        "",
        "    subgraph Python[\"Python Add-on\"]",
        "        py_editor[\"editor_bridge.py\"]",
        "        py_settings[\"settings/commands.py\"]",
        "        py_batch[\"browser_dialog.py\"]",
        "        py_reviewer[\"reviewer_integration.py<br/>(wraps editor)\"]",
        "    end",
        "",
        "    subgraph Services[\"Service Layer\"]",
        "        audio[\"audio_processor.py<br/>Audio Core\"]",
        "        cfg[\"config_migration.py<br/>Config\"]",
        "        diag[\"diagnostics_runtime.py<br/>Diagnostics\"]",
        "        support[\"support.py<br/>Support\"]",
        "    end",
        "",
        "    ts_editor -->|\"pycmd('aqe:*')\"| py_editor",
        "    ts_settings -->|\"pycmd('bridge:{json}')\"| py_settings",
        "    ts_batch -->|\"pycmd('bridge:{json}')\"| py_batch",
        "    py_reviewer -->|\"aqe:* | focus:*\"| ts_reviewer",
        "    ts_reviewer -->|\"pycmd('aqe:*')\"| py_editor",
        "",
        "    py_editor --> audio",
        "    py_editor --> cfg",
        "    py_editor --> diag",
        "    py_settings --> cfg",
        "    py_settings --> diag",
        "    py_settings --> support",
        "    py_batch --> audio",
        "    py_batch --> diag",
    ]
    return "\n".join(lines)


def _render_editor_commands() -> str:
    """Per-command editor dispatch table."""
    cmd_constants = _parse_cmd_constants(ADDON / "editor_actions.py")
    handlers = _parse_bridge_handlers_dict(ADDON / "editor_bridge.py", "handlers")
    payload_handlers = _parse_bridge_handlers_dict(
        ADDON / "editor_bridge.py", "handlers"
    )
    # Actually handlers dict is the second one in handle_payload_command
    payload_handlers = _parse_bridge_handlers_dict(
        ADDON / "editor_bridge.py", "handlers"
    )

    lines = [
        "flowchart TD",
        "",
        "    subgraph ProcessingCommands[\"Processing Commands<br/>(update_state_and_render)\"]",
    ]
    processing = ["aqe:slower", "aqe:faster", "aqe:volume-down", "aqe:volume-up", "aqe:remove-pauses"]
    for cmd in processing:
        slug = cmd.replace(":", "_").replace("-", "_")
        lines.append(f"        {slug}[\"{cmd}\"]")
    lines.append("    end")

    lines.append("")
    lines.append("    subgraph NonProcessingCommands[\"Non-Processing Commands\"]")
    non_processing = [
        "aqe:play", "aqe:stop-playback", "aqe:play-ended", "aqe:undo", "aqe:redo",
        "aqe:scan", "aqe:analyze", "aqe:analyze-field", "aqe:set-cursor",
        "aqe:settings", "aqe:show-file", "aqe:open-url",
        "aqe:frontend-log", "aqe:command-payload",
    ]
    for cmd in non_processing:
        slug = cmd.replace(":", "_").replace("-", "_")
        lines.append(f"        {slug}[\"{cmd}\"]")
    lines.append("    end")

    lines.append("")
    lines.append("    subgraph RecordingCommands[\"Recording Commands\"]")
    recording = [
        "aqe:record-voice", "aqe:stop-recording", "aqe:play-recording",
        "aqe:show-recording-file", "aqe:share-recording",
    ]
    for cmd in recording:
        slug = cmd.replace(":", "_").replace("-", "_")
        lines.append(f"        {slug}[\"{cmd}\"]")
    lines.append("    end")

    lines.append("")
    lines.append("    subgraph DenoiseCommands[\"Denoise Commands\"]")
    denoise = ["aqe:denoise-standard", "aqe:rnnoise", "aqe:dpdfnet", "aqe:voice-only"]
    for cmd in denoise:
        slug = cmd.replace(":", "_").replace("-", "_")
        lines.append(f"        {slug}[\"{cmd}\"]")
    lines.append("    end")

    lines.append("")
    lines.append("    subgraph PayloadCommands[\"Payload Commands\"]")
    payload = [
        "aqe:convert", "aqe:reduce-size", "aqe:pitch-hum",
        "aqe:share", "aqe:post-edit-playback-ready",
        "aqe:delete-selection", "aqe:delete-rest",
        "aqe:save-split-defaults", "aqe:source-metadata",
    ]
    for cmd in payload:
        slug = cmd.replace(":", "_").replace("-", "_")
        lines.append(f"        {slug}[\"{cmd}\"]")
    lines.append("    end")

    lines.append("")
    lines.append("    subgraph ChorusCommands[\"Chorusing Commands\"]")
    chorus = ["aqe:chorusing-practice", "aqe:chorusing-previous", "aqe:chorusing-next"]
    for cmd in chorus:
        slug = cmd.replace(":", "_").replace("-", "_")
        lines.append(f"        {slug}[\"{cmd}\"]")
    lines.append("    end")

    lines.append("")
    lines.append("    subgraph Handlers[\"Python Handlers\"]")
    lines.append("        editor_bridge[\"handle_bridge_command()\"]")
    lines.append("        non_proc[\"handle_non_processing_command()\"]")
    lines.append("        payload_handler[\"handle_payload_command()\"]")
    lines.append("        update[\"update_state_and_render()\"]")
    lines.append("    end")
    lines.append("")
    lines.append("    aqe_slower --> update")
    lines.append("    aqe_faster --> update")
    lines.append("    aqe_volume_down --> update")
    lines.append("    aqe_volume_up --> update")
    lines.append("    aqe_remove_pauses --> update")
    lines.append("")
    lines.append("    aqe_play --> non_proc")
    lines.append("    aqe_stop_playback --> non_proc")
    lines.append("    aqe_denoise_standard --> non_proc")
    lines.append("    aqe_convert --> payload_handler")

    return "\n".join(lines)


def _render_settings_batch() -> str:
    """Settings + Batch bridge commands."""
    settings_handlers = _parse_if_name_chain(ADDON / "settings" / "commands.py")
    batch_handlers = _parse_if_name_chain(ADDON / "browser_dialog.py")

    lines = [
        "flowchart TD",
        "",
        "    subgraph SettingsCommands[\"Settings Commands<br/>(bridge:{json} envelope)\"]",
    ]
    for cmd, handler in sorted(settings_handlers.items()):
        slug = cmd.replace(".", "_").replace("-", "_")
        lines.append(f"        s_{slug}[\"{cmd}\"]")
    lines.append("    end")

    lines.append("")
    lines.append("    subgraph BatchCommands[\"Batch Commands<br/>(bridge:{json} envelope)\"]")
    for cmd, handler in sorted(batch_handlers.items()):
        slug = cmd.replace(".", "_").replace("-", "_")
        lines.append(f"        b_{slug}[\"{cmd}\"]")
    lines.append("    end")

    lines.append("")
    lines.append("    subgraph SettingsHandlers[\"Python: settings/commands.py\"]")
    for cmd, handler in sorted(settings_handlers.items()):
        slug = cmd.replace(".", "_").replace("-", "_")
        lines.append(f"        sh_{slug}[\"{handler}\"]")
    lines.append("    end")

    lines.append("")
    lines.append("    subgraph BatchHandlers[\"Python: browser_dialog.py\"]")
    for cmd, handler in sorted(batch_handlers.items()):
        slug = cmd.replace(".", "_").replace("-", "_")
        lines.append(f"        bh_{slug}[\"{handler}\"]")
    lines.append("    end")

    lines.append("")
    lines.append("    subgraph Services[\"Backend Services\"]")
    lines.append("        ts_settings_bridge[\"lib/bridge.ts\"]")
    lines.append("        ts_batch_bridge[\"batch/bridge.ts\"]")
    lines.append("    end")

    for cmd in sorted(settings_handlers):
        slug = cmd.replace(".", "_").replace("-", "_")
        lines.append(f"    ts_settings_bridge --> s_{slug}")

    for cmd in sorted(batch_handlers):
        slug = cmd.replace(".", "_").replace("-", "_")
        lines.append(f"    ts_batch_bridge --> b_{slug}")

    return "\n".join(lines)


def _render_window_contract() -> str:
    """Python -> JavaScript window.__aqe* entry points."""
    entries = _parse_window_contract(
        SETTINGS_UI_SRC / "editor-inline" / "window-contract.ts"
    )

    lines = [
        "flowchart TD",
        "    subgraph Python[\"Python (evalWithCallback / web.eval)\"]",
        "        py[\"editor_bridge.py<br/>editor_processing.py<br/>editor_playback.py\"]",
        "    end",
        "",
        "    subgraph Window[\"window.__aqe* JavaScript Contract\"]",
    ]
    for entry in entries:
        name = entry["window_name"]
        handler = entry.get("handler", "")
        lines.append(f"        {name.lstrip('_').replace('__', '')}[\"{name}()\"]")
    lines.append("    end")

    lines.append("")
    lines.append("    py --> |\"eval()\"| Window")
    lines.append("")
    lines.append("    subgraph Legend[\"Legend\"]")
    lines.append("        note[\"22 entry points<br/>Install: installEditorWindowContract()<br/>File: window-contract.ts\"]")
    lines.append("    end")

    return "\n".join(lines)


def generate_all() -> int:
    graphs = GRAPHS

    (graphs / "bridge-messages-overview.mmd").write_text(
        MERMAID_HEADER + _render_overview() + MERMAID_FOOTER
    )
    print(f"  wrote {graphs.relative_to(ROOT)}/bridge-messages-overview.mmd")

    (graphs / "bridge-messages-editor.mmd").write_text(
        MERMAID_HEADER + _render_editor_commands() + MERMAID_FOOTER
    )
    print(f"  wrote {graphs.relative_to(ROOT)}/bridge-messages-editor.mmd")

    (graphs / "bridge-messages-settings-batch.mmd").write_text(
        MERMAID_HEADER + _render_settings_batch() + MERMAID_FOOTER
    )
    print(f"  wrote {graphs.relative_to(ROOT)}/bridge-messages-settings-batch.mmd")

    (graphs / "bridge-messages-window-contract.mmd").write_text(
        MERMAID_HEADER + _render_window_contract() + MERMAID_FOOTER
    )
    print(f"  wrote {graphs.relative_to(ROOT)}/bridge-messages-window-contract.mmd")

    return 0


if __name__ == "__main__":
    raise SystemExit(generate_all())
