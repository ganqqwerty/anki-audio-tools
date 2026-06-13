"""Architecture layers definitions and cross-module relationships."""

from __future__ import annotations

from scripts.graphs.python_modules import LAYERS, PKG


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


def _build_relationships(python_modules: list[dict], svelte_modules: list[dict]) -> list[dict]:
    relationships = []

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

    for mod in svelte_modules:
        for dep in mod["imports"].get("internal", []):
            relationships.append({
                "source": mod["module"],
                "target": dep,
                "type": "svelte_import",
                "source_category": mod["category"],
            })

    for mod in python_modules:
        if "editor_frontend" in mod["module"]:
            relationships.append({
                "source": mod["module"],
                "target": "settings_ui/src/editor-inline/",
                "type": "bridge_python_to_js",
                "protocol": "evalWithCallback → window.__aqe*",
            })

    return relationships
