"""Svelte/TS module catalog, bridge command registry, and webview injection mapping."""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ADDON = ROOT / "addon" / "anki_audio_quick_editor"
UI_SRC = ROOT / "settings_ui" / "src"

IMPORT_RE = re.compile(
    r"""(?:import|export)\s+(?:type\s+)?(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)?\s*from\s*['\"]([^'\"]+)['\"]""",
    re.VERBOSE | re.MULTILINE,
)


def _resolve_ts_import(from_module: Path, import_path: str) -> str | None:
    if import_path.startswith("."):
        resolved = (from_module.parent / import_path).resolve()
        try:
            return str(resolved.relative_to(UI_SRC.parent))
        except ValueError:
            return None
    if import_path.startswith("$lib/"):
        return "src/lib/" + import_path[len("$lib/"):]
    return import_path  # external


def _collect_ts_imports(file_path: Path) -> dict[str, list[str]]:
    if not file_path.is_file():
        return {}
    try:
        source = file_path.read_text()
    except UnicodeDecodeError:
        return {}

    internal: list[str] = []
    external: list[str] = []

    for match in IMPORT_RE.finditer(source):
        resolved = _resolve_ts_import(file_path, match.group(1))
        if resolved:
            if resolved.startswith("src/") or resolved.startswith("."):
                internal.append(resolved)
            else:
                external.append(resolved)

    return {
        "internal": sorted(set(internal)),
        "external": sorted(set(external)),
    }


def _ts_relative_path(file_path: Path) -> str:
    return str(file_path.relative_to(UI_SRC.parent))


def _build_svelte_catalog() -> list[dict]:
    modules = []
    for ts_file in sorted(UI_SRC.rglob("*")):
        if ts_file.suffix not in (".ts", ".svelte"):
            continue
        if ts_file.name.startswith("_") or ts_file.name == "globals.d.ts":
            continue
        name = _ts_relative_path(ts_file)
        imports = _collect_ts_imports(ts_file)
        cat = "component" if ts_file.suffix == ".svelte" else "logic"
        if "bridge." in name:
            cat = "bridge"
        elif "types" in name:
            cat = "types"
        elif "state" in name or "store" in name:
            cat = "state"

        modules.append({
            "module": name,
            "file": name,
            "category": cat,
            "summary": f"{ts_file.stem}",
            "imports": imports,
        })
    return modules


def _parse_cmd_constants(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    source = path.read_text()
    tree = ast.parse(source)
    constants: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith("CMD_"):
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        constants[target.id] = node.value.value
    return constants


def _ast_val_to_str(node: ast.expr) -> str | None:
    if isinstance(node, ast.Attribute):
        base = _ast_val_to_str(node.value)
        return f"{base}.{node.attr}" if base else None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _parse_handlers_dict(path: Path, dict_name: str) -> dict[str, str]:
    if not path.is_file():
        return {}
    source = path.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not (isinstance(target, ast.Name) and target.id == dict_name):
                continue
            if not isinstance(node.value, ast.Dict):
                continue
            handlers: dict[str, str] = {}
            if node.value.keys is None or node.value.values is None:
                continue
            for key, val in zip(node.value.keys, node.value.values):
                key_str = None
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    key_str = key.value
                elif isinstance(key, ast.Name):
                    key_str = key.id
                if key_str is None:
                    continue
                val_str = _ast_val_to_str(val)
                if val_str:
                    handlers[key_str] = val_str
            return handlers
    return {}


def _parse_if_chain(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    source = path.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    handlers: dict[str, str] = {}

    class _V(ast.NodeVisitor):
        def visit_If(self, node: ast.If) -> None:
            if isinstance(node.test, ast.Compare) and node.test.comparators:
                c = node.test.comparators[0]
                if isinstance(c, ast.Constant) and isinstance(c.value, str):
                    command = c.value
                    for stmt in node.body:
                        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                            func = stmt.value.func
                            if isinstance(func, ast.Name):
                                handlers[command] = func.id
                            elif isinstance(func, ast.Attribute):
                                v = _ast_val_to_str(func)
                                if v:
                                    handlers[command] = v
                            break
                        if isinstance(stmt, ast.Return) and stmt.value is not None:
                            break
            self.generic_visit(node)
    _V().visit(tree)
    return handlers


def _build_bridge_registry() -> list[dict]:
    commands = []

    cmd_constants = _parse_cmd_constants(ADDON / "editor_actions.py")
    non_proc_handlers = _parse_handlers_dict(ADDON / "editor_bridge.py", "handlers")
    payload_handlers = _parse_handlers_dict(ADDON / "editor_bridge.py", "handlers")

    processing = {"CMD_SLOWER", "CMD_FASTER", "CMD_VOLUME_DOWN", "CMD_VOLUME_UP", "CMD_REMOVE_PAUSES"}
    recording = {"CMD_RECORD_VOICE", "CMD_STOP_RECORDING", "CMD_PLAY_RECORDING", "CMD_SHOW_RECORDING_FILE", "CMD_SHARE_RECORDING"}
    denoise = {"CMD_DENOISE_STANDARD", "CMD_RNNOISE", "CMD_DPDFNET", "CMD_VOICE_ONLY"}
    chorus = {"CMD_BACK_CHAIN_PRACTICE", "CMD_BACK_CHAIN_PREVIOUS", "CMD_BACK_CHAIN_NEXT"}

    for const_name, command in sorted(cmd_constants.items()):
        if const_name in processing:
            handler = "update_state_and_render()"
        elif const_name in denoise or const_name in recording or const_name in chorus:
            handler = non_proc_handlers.get(command, "")
        else:
            handler = non_proc_handlers.get(command, "") or payload_handlers.get(command, "")

        cat = (
            "processing" if const_name in processing else
            "denoise" if const_name in denoise else
            "recording" if const_name in recording else
            "chorusing" if const_name in chorus else
            "payload" if command in payload_handlers else
            "non_processing"
        )

        commands.append({
            "context": "editor",
            "command": command,
            "constant": const_name,
            "category": cat,
            "handler": handler,
            "protocol": "raw pycmd (aqe:* namespace)",
            "ts_sender": "src/editor-inline/bridge.ts",
            "python_handler": "anki_audio_quick_editor.editor_bridge.py",
        })

    extra_commands = {
        "aqe:scan": "eval_status + window.__aqeScan()",
        "aqe:analyze": "analyze_current_async()",
        "aqe:set-cursor": "set_cursor_from_web()",
        "aqe:play": "play()",
        "aqe:play-ended": "play_ended()",
        "aqe:frontend-log": "handle_editor_frontend_log()",
        "aqe:show-file": "show_current_audio_file()",
        "aqe:undo": "undo()",
        "aqe:command-payload": "handle_pending_command_payload()",
        "focus:*": "editor.currentField = ord",
    }
    for cmd, handler in extra_commands.items():
        commands.append({
            "context": "editor",
            "command": cmd,
            "constant": "",
            "category": "non_processing",
            "handler": handler,
            "protocol": "raw pycmd",
            "ts_sender": "src/editor-inline/bridge.ts",
            "python_handler": "anki_audio_quick_editor.editor_bridge.py",
        })

    settings_handlers = _parse_if_chain(ADDON / "settings" / "commands.py")
    for cmd, handler in sorted(settings_handlers.items()):
        commands.append({
            "context": "settings",
            "command": cmd,
            "constant": "",
            "category": "settings",
            "handler": handler,
            "protocol": "bridge:{json} envelope",
            "ts_sender": "src/lib/bridge.ts",
            "python_handler": "anki_audio_quick_editor.settings.commands.py",
        })

    batch_handlers = _parse_if_chain(ADDON / "browser_dialog.py")
    for cmd, handler in sorted(batch_handlers.items()):
        commands.append({
            "context": "batch",
            "command": cmd,
            "constant": "",
            "category": "batch",
            "handler": handler,
            "protocol": "bridge:{json} envelope",
            "ts_sender": "src/batch/bridge.ts",
            "python_handler": "anki_audio_quick_editor.browser_dialog.py",
        })

    wc_file = UI_SRC / "editor-inline" / "window-contract.ts"
    if wc_file.is_file():
        source = wc_file.read_text()
        assign_re = re.compile(r"window\.(__aqe\w+)\s*=\s*(\w+)", re.MULTILINE)
        for match in assign_re.finditer(source):
            commands.append({
                "context": "window_contract",
                "command": match.group(1),
                "constant": "",
                "category": "python_to_js",
                "handler": match.group(2),
                "protocol": "evalWithCallback / web.eval",
                "ts_sender": "N/A (Python calls JS)",
                "python_handler": "anki_audio_quick_editor.editor_frontend/",
            })

    return commands


def _build_webview_injection() -> list[dict]:
    yaml_path = ROOT / "docs" / "architecture" / "webviews.yaml"
    if not yaml_path.is_file():
        return []

    text = yaml_path.read_text()
    screens: list[dict] = []
    current: dict | None = None
    in_hooks = False
    in_assets = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if stripped.endswith(":"):
            key = stripped[:-1]
            if indent == 0 and key == "screens":
                continue
            if indent == 2:
                current = {"name": key}
                screens.append(current)
            elif indent == 4 and current is not None:
                in_hooks = key == "hooks"
                in_assets = key == "assets"
            continue
        if current is None:
            continue
        if stripped.startswith("- ") and (in_hooks or in_assets):
            value = stripped[2:].strip()
            list_key = "hooks" if in_hooks else "assets"
            current.setdefault(list_key, []).append(value)
            continue
        if ":" in stripped and not stripped.startswith("-"):
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            current[key] = value
            in_hooks = False
            in_assets = False

    return screens
