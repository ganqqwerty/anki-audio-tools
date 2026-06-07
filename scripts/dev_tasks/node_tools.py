"""Node.js and frontend tool discovery helpers for development tasks."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_UI_DIR = ROOT / "settings_ui"
FALLBACK_NPM_RUNNER = ROOT / "scripts" / "dev_tasks" / "settings_ui_npm.py"


def _which_first(*names: str) -> str | None:
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    return None


def _command_is_usable(command: Sequence[str]) -> bool:
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def find_node_command() -> str | None:
    """Return a usable Node.js executable path if one is available."""
    candidates: list[Path] = []
    if os.name == "nt":
        path_node = _which_first("node.exe", "node")
        if path_node:
            candidates.append(Path(path_node))
        candidates.extend(
            [
            Path(r"C:\Program Files\nodejs\node.exe"),
            Path(r"C:\Program Files (x86)\nodejs\node.exe"),
            ]
        )
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidates.append(Path(local_app_data) / "Programs" / "nodejs" / "node.exe")
        candidates.append(
            Path.home()
            / ".cache"
            / "codex-runtimes"
            / "codex-primary-runtime"
            / "dependencies"
            / "node"
            / "bin"
            / "node.exe"
        )
    else:
        path_node = _which_first("node")
        if path_node:
            candidates.append(Path(path_node))

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve() if candidate.exists() else candidate
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        if _command_is_usable([str(resolved), "--version"]):
            return str(resolved)
    return None


def find_npm_install_command(node_command: str | None = None) -> list[str] | None:
    """Return a command prefix for a real npm CLI when one is discoverable."""
    if os.name == "nt":
        npm_on_path = _which_first("npm.cmd", "npm")
        if npm_on_path and _command_is_usable([npm_on_path, "--version"]):
            return [npm_on_path]
    else:
        npm_on_path = _which_first("npm")
        if npm_on_path and _command_is_usable([npm_on_path, "--version"]):
            return [npm_on_path]

    node = node_command or find_node_command()
    if not node:
        return None

    node_path = Path(node)
    if os.name == "nt":
        npm_cmd = node_path.parent / "npm.cmd"
        if npm_cmd.is_file():
            return [str(npm_cmd)]
        npm_cli = node_path.parent / "node_modules" / "npm" / "bin" / "npm-cli.js"
        if npm_cli.is_file():
            return [node, str(npm_cli)]
        return None

    npm_cli_candidates = [
        node_path.parent.parent / "lib" / "node_modules" / "npm" / "bin" / "npm-cli.js",
        node_path.parent / "../lib/node_modules/npm/bin/npm-cli.js",
    ]
    for candidate in npm_cli_candidates:
        resolved = candidate.resolve()
        if resolved.is_file():
            return [node, str(resolved)]
    return None


def frontend_npm_command(
    script: str,
    *,
    extra_args: Sequence[str] = (),
    settings_ui_dir: Path = SETTINGS_UI_DIR,
) -> list[str] | None:
    """Return a command that can execute a settings_ui package script."""
    node = find_node_command()
    npm = find_npm_install_command(node)
    if npm:
        command = [*npm, "run", script]
        if extra_args:
            command.extend(["--", *extra_args])
        return command
    if node and (settings_ui_dir / "node_modules").is_dir():
        command = [sys.executable, str(FALLBACK_NPM_RUNNER), "run", script]
        if extra_args:
            command.extend(["--", *extra_args])
        return command
    return None


def quicktype_command(settings_ui_dir: Path = SETTINGS_UI_DIR) -> list[str] | None:
    """Return a command prefix that can run the local quicktype install."""
    node = find_node_command()
    quicktype_js = settings_ui_dir / "node_modules" / "quicktype" / "dist" / "index.js"
    if node and quicktype_js.is_file():
        return [node, str(quicktype_js)]

    binary_name = "quicktype.cmd" if os.name == "nt" else "quicktype"
    quicktype_bin = settings_ui_dir / "node_modules" / ".bin" / binary_name
    if quicktype_bin.is_file():
        return [str(quicktype_bin)]
    return None


def frontend_runner_status(settings_ui_dir: Path = SETTINGS_UI_DIR) -> tuple[str, str]:
    """Describe how frontend scripts will be executed."""
    node = find_node_command()
    npm = find_npm_install_command(node)
    if node:
        try:
            version = subprocess.run(
                [node, "--version"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
        except OSError:
            version = ""
        if version:
            if npm:
                return version, " ".join(npm)
            if (settings_ui_dir / "node_modules").is_dir():
                return version, "repo fallback via settings_ui script runner"
        elif npm:
            return "", " ".join(npm)
    if npm:
        return "", " ".join(npm)
    return "", "not found"
