#!/usr/bin/env python3
"""Generate Anki bridge message Mermaid diagrams from source code analysis.

Parses Python bridge dispatchers and TypeScript bridge modules to produce:
  docs/graphs/bridge-messages-overview.mmd
  docs/graphs/bridge-messages-editor.mmd
  docs/graphs/bridge-messages-settings-batch.mmd
  docs/graphs/bridge-messages-window-contract.mmd
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SCRIPT_ROOT))

from scripts.graphs.bridge_editor import _build_editor
from scripts.graphs.bridge_settings import _build_settings_batch, _build_window_contract
from scripts.graphs.common import GRAPHS, MERMAID_FOOTER, MERMAID_HEADER, ROOT


def _build_overview() -> str:
    """System-level: 4 Anki webview contexts -> their bridges -> Python dispatchers."""
    lines = [
        "flowchart LR",
        "",
        '    subgraph EditorWebView["Editor WebView"]',
        '        ts_editor["editor-inline/bridge.ts"]',
        "    end",
        "",
        '    subgraph SettingsWebView["Settings WebView"]',
        '        ts_settings["lib/bridge.ts"]',
        "    end",
        "",
        '    subgraph BatchWebView["Batch WebView"]',
        '        ts_batch["batch/bridge.ts"]',
        "    end",
        "",
        '    subgraph ReviewerWebView["Reviewer WebView"]',
        '        ts_reviewer["editor-inline/bridge.ts<br/>(reused)"]',
        "    end",
        "",
        '    subgraph Python["Python Add-on"]',
        '        py_editor["editor_bridge.py"]',
        '        py_settings["settings/commands.py"]',
        '        py_batch["browser_dialog.py"]',
        '        py_reviewer["reviewer_integration.py<br/>(wraps editor)"]',
        "    end",
        "",
        '    subgraph Services["Service Layer"]',
        '        audio["audio_processor.py<br/>Audio Core"]',
        '        cfg["config_migration.py<br/>Config"]',
        '        diag["diagnostics_runtime.py<br/>Diagnostics"]',
        '        support["support.py<br/>Support"]',
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


def generate_all() -> int:
    GRAPHS.mkdir(parents=True, exist_ok=True)

    (GRAPHS / "bridge-messages-overview.mmd").write_text(
        MERMAID_HEADER + _build_overview() + MERMAID_FOOTER
    )
    print(f"  wrote {GRAPHS.relative_to(ROOT)}/bridge-messages-overview.mmd")

    (GRAPHS / "bridge-messages-editor.mmd").write_text(
        MERMAID_HEADER + _build_editor() + MERMAID_FOOTER
    )
    print(f"  wrote {GRAPHS.relative_to(ROOT)}/bridge-messages-editor.mmd")

    (GRAPHS / "bridge-messages-settings-batch.mmd").write_text(
        MERMAID_HEADER + _build_settings_batch() + MERMAID_FOOTER
    )
    print(f"  wrote {GRAPHS.relative_to(ROOT)}/bridge-messages-settings-batch.mmd")

    (GRAPHS / "bridge-messages-window-contract.mmd").write_text(
        MERMAID_HEADER + _build_window_contract() + MERMAID_FOOTER
    )
    print(f"  wrote {GRAPHS.relative_to(ROOT)}/bridge-messages-window-contract.mmd")

    return 0


if __name__ == "__main__":
    raise SystemExit(generate_all())
