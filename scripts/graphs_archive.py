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

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.graphs.python_modules import _build_python_catalog
from scripts.graphs.relationships import _build_layers, _build_relationships
from scripts.graphs.svelte_modules import (
    _build_bridge_registry,
    _build_svelte_catalog,
    _build_webview_injection,
)

OUT = ROOT / "docs" / "archive" / "architecture_diagrams" / date.today().isoformat()


def _write_json(filename: str, data: object) -> None:
    path = OUT / filename
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    if isinstance(data, list):
        print(f"  wrote {path.relative_to(ROOT)} ({len(data)} entries)")
    else:
        print(f"  wrote {path.relative_to(ROOT)}")


def generate_all() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    python_modules = _build_python_catalog()
    svelte_modules = _build_svelte_catalog()
    bridge_commands = _build_bridge_registry()
    webview_injection = _build_webview_injection()
    layers = _build_layers()
    relationships = _build_relationships(python_modules, svelte_modules)

    _write_json("python-modules.json", python_modules)
    _write_json("svelte-modules.json", svelte_modules)
    _write_json("bridge-commands.json", bridge_commands)
    _write_json("webview-injection.json", webview_injection)
    _write_json("architecture-layers.json", layers)
    _write_json("relationships.json", relationships)

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
    _write_json("index.json", index)

    return 0


if __name__ == "__main__":
    raise SystemExit(generate_all())
