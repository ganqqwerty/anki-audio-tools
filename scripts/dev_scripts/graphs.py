"""Graph generation commands for the dev.py CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
GRAPH_SCRIPTS = ROOT / "scripts"
GRAPHS_DIR = ROOT / "docs" / "graphs"


def cmd_graphs_python(_command_args: list[str]) -> int:
    """Generate pydeps SVG dependency graphs for Python."""
    return _run_graph_script("graphs_python.py")


def cmd_graphs_svelte(_command_args: list[str]) -> int:
    """Generate dependency-cruiser SVG graphs for Svelte/TS."""
    return _run_graph_script("graphs_svelte.py")


def cmd_graphs_bridge(_command_args: list[str]) -> int:
    """Generate Anki bridge message Mermaid diagrams."""
    return _run_graph_script("graphs_bridge.py")


def cmd_graphs_webview(_command_args: list[str]) -> int:
    """Generate webview injection Mermaid diagram."""
    return _run_graph_script("graphs_webview.py")


def cmd_graphs_all(_command_args: list[str]) -> int:
    """Run all graph generators (python, svelte, bridge, webview)."""
    results = [
        _run_graph_script("graphs_python.py"),
        _run_graph_script("graphs_svelte.py"),
        _run_graph_script("graphs_bridge.py"),
        _run_graph_script("graphs_webview.py"),
    ]
    return max(results) if results else 0


def cmd_graphs_check(_command_args: list[str]) -> int:
    """Regenerate all graphs and fail if any differ from committed."""
    rc = cmd_graphs_all([])
    if rc != 0:
        print("[graphs-check] generation failed")
        return rc

    result = subprocess.run(
        ["git", "diff", "--exit-code", "--", str(GRAPHS_DIR)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("[graphs-check] all graphs are current")
        return 0

    print("[graphs-check] graphs are stale. Run: python3 scripts/dev.py graphs-all")
    print(result.stdout)
    return 1


def _run_graph_script(script_name: str) -> int:
    script_path = GRAPH_SCRIPTS / script_name
    if not script_path.is_file():
        print(f"[graphs] missing script: {script_path}", file=sys.stderr)
        return 1
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT,
    )
    return result.returncode
