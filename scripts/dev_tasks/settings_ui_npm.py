"""Fallback npm-compatible runner for checked-out settings_ui scripts."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.dev_tasks.node_tools import SETTINGS_UI_DIR, find_node_command

TOOL_PATHS = {
    "vite": SETTINGS_UI_DIR / "node_modules" / "vite" / "bin" / "vite.js",
    "vitest": SETTINGS_UI_DIR / "node_modules" / "vitest" / "vitest.mjs",
    "eslint": SETTINGS_UI_DIR / "node_modules" / "eslint" / "bin" / "eslint.js",
    "svelte-check": SETTINGS_UI_DIR / "node_modules" / "svelte-check" / "bin" / "svelte-check",
    "tsc": SETTINGS_UI_DIR / "node_modules" / "typescript" / "bin" / "tsc",
}

SCRIPT_STEPS = {
    "build": ("build:settings", "build:editor", "build:batch"),
    "lint": ("lint:run", "lint:max-lines"),
    "validate": ("check", "lint", "typecheck", "test:coverage"),
}

SCRIPT_COMMANDS = {
    "build:settings": ("vite", "build"),
    "build:editor": ("vite", "build", "--config", "vite.editor.config.ts"),
    "build:batch": ("vite", "build", "--config", "vite.batch.config.ts"),
    "check": ("svelte-check", "--tsconfig", "./tsconfig.json"),
    "lint:run": ("eslint", "."),
    "lint:max-lines": ("eslint", ".", "--config", "eslint.max-lines.config.js"),
    "typecheck": ("tsc", "--noEmit"),
    "test": ("vitest", "run"),
    "test:coverage": ("vitest", "run", "--coverage"),
}

SCRIPTS_WITH_EXTRA_ARGS = {
    "build:settings",
    "build:editor",
    "build:batch",
    "check",
    "lint:run",
    "typecheck",
    "test",
    "test:coverage",
}


def _run_node_tool(tool_path: Path, args: Sequence[str]) -> int:
    node = find_node_command()
    if not node:
        print("ERROR: Node.js not found. Install Node.js 18+.", file=sys.stderr)
        return 1
    if not tool_path.is_file():
        print(f"ERROR: frontend tool not found: {tool_path}", file=sys.stderr)
        return 1
    result = subprocess.run(
        [node, str(tool_path), *args],
        cwd=SETTINGS_UI_DIR,
        env=os.environ.copy(),
        check=False,
    )
    return result.returncode


def _run_script_steps(steps: Sequence[str], extra_args: Sequence[str] = ()) -> int:
    for step in steps:
        step_args = extra_args if step == "lint:run" else ()
        rc = _run_script(step, step_args)
        if rc != 0:
            return rc
    return 0


def _script_command(script: str, extra_args: Sequence[str]) -> tuple[Path, tuple[str, ...]] | None:
    spec = SCRIPT_COMMANDS.get(script)
    if spec is None:
        return None
    tool_name, *args = spec
    command_args = tuple(args)
    if script in SCRIPTS_WITH_EXTRA_ARGS:
        command_args = (*command_args, *extra_args)
    return TOOL_PATHS[tool_name], command_args


def _run_script(script: str, extra_args: Sequence[str]) -> int:
    if script in SCRIPT_STEPS:
        return _run_script_steps(SCRIPT_STEPS[script], extra_args)
    command = _script_command(script, extra_args)
    if command is not None:
        tool_path, args = command
        return _run_node_tool(tool_path, args)
    print(f"ERROR: unsupported fallback npm script: {script}", file=sys.stderr)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    if not args:
        print("ERROR: expected npm-style arguments.", file=sys.stderr)
        return 1
    if args[0] in {"--version", "-v"}:
        print("0.0.0-dev-runner-fallback")
        return 0
    if args[0] not in {"run", "run-script"}:
        print(f"ERROR: unsupported fallback npm command: {' '.join(args)}", file=sys.stderr)
        return 1
    if len(args) < 2:
        print("ERROR: missing npm script name.", file=sys.stderr)
        return 1

    script = args[1]
    extra_args = args[2:]
    if extra_args and extra_args[0] == "--":
        extra_args = extra_args[1:]
    return _run_script(script, extra_args)


if __name__ == "__main__":
    raise SystemExit(main())
