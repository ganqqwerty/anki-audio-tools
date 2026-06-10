#!/usr/bin/env python3
"""Generate machine-readable architecture data for LLM consumption.

Output (docs/archive/architecture_diagrams/YYYY-MM-DD/):
  python-modules.json     — Catalog of all Python modules: layer, deps, imports
  svelte-modules.json     — Catalog of all Svelte/TS modules: deps, imports
  bridge-commands.json    — Complete pycmd protocol registry
  webview-injection.json  — WebView screen → hook → bundle mapping
  architecture-layers.json — Layer definitions, rules, and boundary contracts
  relationships.json      — All cross-module relationships (Python↔Python, TS↔TS, Python↔TS)
"""

from __future__ import annotations

import ast
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADDON = ROOT / "addon" / "anki_audio_quick_editor"
UI_SRC = ROOT / "settings_ui" / "src"
PKG = "anki_audio_quick_editor"

OUT = ROOT / "docs" / "archive" / "architecture_diagrams" / date.today().isoformat()
OUT.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────
# layer assignments from tests/test_architecture/contracts.py
# ──────────────────────────────────────────────────────────────────────

LAYERS = {
    f"{PKG}": "entry_point",
}

# Import-safe core modules
IMPORT_SAFE = [
    "_version", "audio_artifacts", "audio_commands", "audio_commands_runtime",
    "audio_deps", "audio_external", "audio_formats", "audio_operation_params",
    "audio_operations", "audio_output_policy", "audio_pause_pipeline",
    "audio_pause_pipeline_detection", "audio_pause_pipeline_stage",
    "audio_pause_pipeline_steps", "audio_pitch_hum", "audio_pitch_hum_frames",
    "audio_pitch_hum_synthesis", "audio_processor", "audio_rendering",
    "audio_size_reduction", "audio_state", "audio_tools", "audio_types",
    "audio_noise_reduction", "audio_noise_reduction_bundled",
    "batch_operation_processing", "batch_operation_types",
    "batch_operations", "batch_operations_helpers",
    "config_migration", "config", "config.schema",
    "contracts_generated", "diagnostics", "diagnostics_runtime",
    "diagnostics_runtime_json", "diagnostics_runtime_storage",
    "editor_actions", "editor_button_visibility", "editor_media",
    "editor_session", "editor_ui", "editor_settings_actions",
    "error_codes", "errors", "external_links", "file_reveal",
    "file_sharing", "frontend_logs", "i18n", "media_paths",
    "persistent_history", "prosody_analyzer", "prosody_cache",
    "prosody_fallback", "prosody_praat", "prosody_settings",
    "prosody_svg", "prosody_types", "runtime_install", "runtime_manager",
    "runtime_manifest", "runtime_status", "settings_state",
    "sound_refs", "support", "support_reporting",
    "webview_bridge", "webview_shell",
]

# UI adapter modules
UI_ADAPTERS = [
    "audio_recording", "browser_batch_runner", "browser_dialog",
    "browser_dialog_state", "browser_integration", "browser_report",
    "editor_analysis", "editor_bridge", "editor_callbacks",
    "editor_conversion", "editor_dependencies", "editor_frontend",
    "editor_frontend_callbacks", "editor_history", "editor_integration",
    "editor_persistent_undo", "editor_playback", "editor_playback_bounds",
    "editor_playback_request", "editor_processing", "editor_recording",
    "editor_recording_analysis", "editor_recording_frontend",
    "editor_recording_requests", "editor_region_delete",
    "editor_region_delete_request", "editor_region_delete_worker",
    "editor_reload_status", "editor_runtime", "editor_sharing",
    "editor_source_metadata", "editor_special_transforms",
    "editor_split_defaults", "editor_status", "editor_webview_injection",
    "reviewer_audio_targets", "reviewer_integration",
    "reviewer_template_filter", "reviewer_template_filter_integration",
    "runtime_installer_dialog",
]

# Settings
SETTINGS_SHELL = ["settings"]
SETTINGS_BACKEND = [
    "settings.async_commands", "settings.async_operations",
    "settings.commands", "settings.initial_state",
]

for m in IMPORT_SAFE:
    LAYERS.setdefault(f"{PKG}.{m}", "import_safe_core")
for m in UI_ADAPTERS:
    LAYERS.setdefault(f"{PKG}.{m}", "ui_adapter")
for m in SETTINGS_SHELL:
    LAYERS.setdefault(f"{PKG}.{m}", "settings_shell")
for m in SETTINGS_BACKEND:
    LAYERS.setdefault(f"{PKG}.{m}", "settings_backend")


# ──────────────────────────────────────────────────────────────────────
# AST helpers
# ──────────────────────────────────────────────────────────────────────

def _collect_imports(py_file: Path) -> dict[str, list[str]]:
    """Extract imports from a Python file grouped by category."""
    if not py_file.is_file():
        return {}
    try:
        source = py_file.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return {}

    anki_imports: list[str] = []
    addon_imports: list[str] = []
    stdlib_imports: list[str] = []
    third_party: list[str] = []

    ANKI_PREFIXES = ("aqt", "anki")
    STDLIB = {"__future__", "ast", "collections", "copy", "dataclasses", "enum",
              "functools", "hashlib", "io", "itertools", "json", "logging",
              "math", "os", "pathlib", "re", "shutil", "subprocess",
              "sys", "tempfile", "threading", "time", "typing", "uuid",
              "warnings", "weakref", "contextlib", "urllib", "zipfile", "struct"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split(".")[0]
                if name in STDLIB:
                    stdlib_imports.append(alias.name)
                elif name.startswith(ANKI_PREFIXES):
                    anki_imports.append(alias.name)
                elif name == PKG.split(".")[0] or name == PKG:
                    addon_imports.append(alias.name)
                else:
                    third_party.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                name = node.module.split(".")[0]
                full = node.module + (f".{node.names[0].name}" if node.names and node.names[0].name != "*" else "")
                if name in STDLIB:
                    stdlib_imports.append(node.module)
                elif name.startswith(ANKI_PREFIXES) or (node.level > 0):
                    anki_imports.append(full)
                elif name == PKG.split(".")[0] or name == PKG:
                    addon_imports.append(full)
                elif node.level > 0:
                    stdlib_imports.append(node.module)  # relative internal
                else:
                    third_party.append(node.module)

    return {
        "anki": sorted(set(anki_imports)),
        "addon": sorted(set(addon_imports)),
        "stdlib": sorted(set(stdlib_imports)),
        "third_party": sorted(set(third_party)),
    }


def _module_name(py_file: Path) -> str:
    """Convert a Python file path to its dotted module name."""
    rel = py_file.relative_to(ADDON.parent)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = parts[-1].replace(".py", "")
    return ".".join(parts)


def _module_summary(py_file: Path) -> str:
    """Extract first docstring sentence or derive purpose from filename."""
    if not py_file.is_file():
        return ""
    try:
        source = py_file.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return ""

    if (isinstance(tree, ast.Module) and tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        doc = tree.body[0].value.value.strip()
        first_line = doc.split("\n")[0].rstrip(".")
        return first_line

    return f"Module: {py_file.stem}"


# ──────────────────────────────────────────────────────────────────────
# Python module catalog
# ──────────────────────────────────────────────────────────────────────

def _build_python_catalog() -> list[dict]:
    modules = []
    for py_file in sorted(ADDON.rglob("*.py")):
        if py_file.name.startswith("_") and py_file.name != "__init__.py":
            continue
        name = _module_name(py_file)
        if "user_files" in name or "vendor" in name or "bin" in name:
            continue
        if "templates" in name:
            continue

        imports = _collect_imports(py_file)
        modules.append({
            "module": name,
            "file": str(py_file.relative_to(ROOT)),
            "layer": LAYERS.get(name, "unclassified"),
            "summary": _module_summary(py_file),
            "imports": imports,
        })
    return modules


# ──────────────────────────────────────────────────────────────────────
# Svelte/TS module catalog
# ──────────────────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────────────────
# Bridge command registry
# ──────────────────────────────────────────────────────────────────────

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
                        elif isinstance(stmt, ast.Return) and stmt.value is not None:
                            break
            self.generic_visit(node)
    _V().visit(tree)
    return handlers


def _build_bridge_registry() -> list[dict]:
    commands = []

    # Editor commands
    cmd_constants = _parse_cmd_constants(ADDON / "editor_actions.py")
    non_proc_handlers = _parse_handlers_dict(ADDON / "editor_bridge.py", "handlers")
    payload_handlers = _parse_handlers_dict(ADDON / "editor_bridge.py", "handlers")

    # Known command categories
    processing = {"CMD_SLOWER", "CMD_FASTER", "CMD_VOLUME_DOWN", "CMD_VOLUME_UP", "CMD_REMOVE_PAUSES"}
    recording = {"CMD_RECORD_VOICE", "CMD_STOP_RECORDING", "CMD_PLAY_RECORDING", "CMD_SHOW_RECORDING_FILE", "CMD_SHARE_RECORDING"}
    denoise = {"CMD_DENOISE_STANDARD", "CMD_RNNOISE", "CMD_DPDFNET", "CMD_VOICE_ONLY"}
    chorus = {"CMD_BACK_CHAIN_PRACTICE", "CMD_BACK_CHAIN_PREVIOUS", "CMD_BACK_CHAIN_NEXT"}

    for const_name, command in sorted(cmd_constants.items()):
        if const_name in processing:
            handler = "update_state_and_render()"
        elif const_name in denoise:
            handler = non_proc_handlers.get(command, "")
        elif const_name in recording:
            handler = non_proc_handlers.get(command, "")
        elif const_name in chorus:
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

    # Non-CMD commands in editor
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

    # Settings commands
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

    # Batch commands
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

    # Window contract (Python -> JS)
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


# ──────────────────────────────────────────────────────────────────────
# WebView injection map (from YAML)
# ──────────────────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────────────────
# Architecture layers
# ──────────────────────────────────────────────────────────────────────

def _build_layers() -> dict:
    return {
        "layers": [
            {
                "name": "entry_point",
                "description": "Startup hook registration, menu setup, config action",
                "modules": [k for k, v in LAYERS.items() if v == "entry_point"],
            },
            {
                "name": "import_safe_core",
                "description": "Logic that stays safe to inspect and test without loading Anki runtime objects",
                "modules": sorted([k for k, v in LAYERS.items() if v == "import_safe_core"]),
            },
            {
                "name": "ui_adapter",
                "description": "User-facing Browser/editor behavior that touches Anki, Qt, playback, taskman, and media APIs",
                "modules": sorted([k for k, v in LAYERS.items() if v == "ui_adapter"]),
            },
            {
                "name": "settings_shell",
                "description": "Thin QDialog + AnkiWebView host only",
                "modules": sorted([k for k, v in LAYERS.items() if v == "settings_shell"]),
            },
            {
                "name": "settings_backend",
                "description": "Bridge dispatch and startup state for settings dialog",
                "modules": sorted([k for k, v in LAYERS.items() if v == "settings_backend"]),
            },
        ],
        "rules": [
            "Import-safe core must not import UI adapters, settings shell, or settings backend",
            "Settings backend must not import editor_integration",
            "Editor bridge commands must stay in sync between Python and TypeScript",
            "Shared batch operations must stay free of editor bridge strings and editor-adapter imports",
            "Optional analysis dependencies must stay isolated to their backend module",
            "Every production module must have an executable contract entry",
            "Broad exception handlers must stay in the function-qualified allowlist",
        ],
    }


# ──────────────────────────────────────────────────────────────────────
# Relationships (cross-module)
# ──────────────────────────────────────────────────────────────────────

def _build_relationships(python_modules: list[dict], svelte_modules: list[dict]) -> list[dict]:
    relationships = []

    # Python internal dependencies
    for mod in python_modules:
        for dep in mod["imports"].get("addon", []):
            if dep.startswith(PKG):
                relationships.append({
                    "source": mod["module"],
                    "target": dep,
                    "type": "python_import",
                    "source_layer": mod["layer"],
                    "target_layer": LAYERS.get(dep, "unknown"),
                })

    # Svelte internal dependencies
    for mod in svelte_modules:
        for dep in mod["imports"].get("internal", []):
            relationships.append({
                "source": mod["module"],
                "target": dep,
                "type": "svelte_import",
                "source_category": mod["category"],
            })

    # Bridge relationships (Python ↔ Svelte)
    for mod in python_modules:
        if "editor_frontend" in mod["module"]:
            relationships.append({
                "source": mod["module"],
                "target": "settings_ui/src/editor-inline/",
                "type": "bridge_python_to_js",
                "protocol": "evalWithCallback → window.__aqe*",
            })

    return relationships


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def generate_all() -> int:
    python_modules = _build_python_catalog()
    svelte_modules = _build_svelte_catalog()
    bridge_commands = _build_bridge_registry()
    webview_injection = _build_webview_injection()
    layers = _build_layers()
    relationships = _build_relationships(python_modules, svelte_modules)

    files = {
        "python-modules.json": python_modules,
        "svelte-modules.json": svelte_modules,
        "bridge-commands.json": bridge_commands,
        "webview-injection.json": webview_injection,
        "architecture-layers.json": layers,
        "relationships.json": relationships,
    }

    for filename, data in files.items():
        path = OUT / filename
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"  wrote {path.relative_to(ROOT)} ({len(data)} entries)")

    # Write an index with summaries
    index = {
        "generated": date.today().isoformat(),
        "project": "anki-audio-quick-editor",
        "description": "Machine-readable architecture data for LLM consumption",
        "files": {
            "python-modules.json": f"{len(python_modules)} Python modules cataloged by layer, imports, and purpose",
            "svelte-modules.json": f"{len(svelte_modules)} Svelte/TypeScript modules cataloged by category and imports",
            "bridge-commands.json": f"{len(bridge_commands)} bridge commands (pycmd protocol) across editor, settings, batch, and window contract",
            "webview-injection.json": f"{len(webview_injection)} webview screens mapped to Anki hooks, Python handlers, and Svelte bundles",
            "architecture-layers.json": "5-layer architecture model with rules and module assignments",
            "relationships.json": f"{len(relationships)} cross-module relationships (Python, Svelte, and bridge)",
        },
        "totals": {
            "python_modules": len(python_modules),
            "svelte_modules": len(svelte_modules),
            "bridge_commands": len(bridge_commands),
            "webview_screens": len(webview_injection),
            "relationships": len(relationships),
        },
    }
    (OUT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False))
    print(f"  wrote {OUT.relative_to(ROOT)}/index.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(generate_all())
