from __future__ import annotations

import sys
from pathlib import Path

from scripts.dev_tasks import node_tools


def test_find_npm_install_command_uses_node_adjacent_npm_cli(monkeypatch, tmp_path: Path) -> None:
    node_dir = tmp_path / "node"
    npm_cli = node_dir / "node_modules" / "npm" / "bin" / "npm-cli.js"
    npm_cli.parent.mkdir(parents=True)
    npm_cli.write_text("", encoding="utf-8")
    node = node_dir / "node.exe"
    node.write_text("", encoding="utf-8")

    monkeypatch.setattr(node_tools.os, "name", "nt", raising=False)
    monkeypatch.setattr(node_tools, "_which_first", lambda *names: None)
    monkeypatch.setattr(node_tools, "_command_is_usable", lambda command: True)

    assert node_tools.find_npm_install_command(str(node)) == [str(node), str(npm_cli)]


def test_frontend_npm_command_uses_repo_fallback_when_node_modules_exist(monkeypatch, tmp_path: Path) -> None:
    settings_ui = tmp_path / "settings_ui"
    (settings_ui / "node_modules").mkdir(parents=True)

    monkeypatch.setattr(node_tools, "find_node_command", lambda: "/usr/bin/node")
    monkeypatch.setattr(node_tools, "find_npm_install_command", lambda node_command=None: None)

    assert node_tools.frontend_npm_command("validate", settings_ui_dir=settings_ui) == [
        sys.executable,
        str(node_tools.FALLBACK_NPM_RUNNER),
        "run",
        "validate",
    ]


def test_quicktype_command_prefers_js_entrypoint(monkeypatch, tmp_path: Path) -> None:
    settings_ui = tmp_path / "settings_ui"
    quicktype_js = settings_ui / "node_modules" / "quicktype" / "dist" / "index.js"
    quicktype_js.parent.mkdir(parents=True)
    quicktype_js.write_text("", encoding="utf-8")

    monkeypatch.setattr(node_tools, "find_node_command", lambda: "/usr/bin/node")

    assert node_tools.quicktype_command(settings_ui) == ["/usr/bin/node", str(quicktype_js)]
