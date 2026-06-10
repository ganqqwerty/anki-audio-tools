"""Rule 29: migrated editor workflows use typed dependency protocols."""

from __future__ import annotations

import ast

from .conftest import ADDON_DIR


MIGRATED_FILES = (
    "editor_region_delete.py",
    "editor_region_delete_worker.py",
)


def test_region_delete_workflow_does_not_accept_untyped_deps_any() -> None:
    violations: list[str] = []
    for relative in MIGRATED_FILES:
        path = ADDON_DIR / relative
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for arg in node.args.args + node.args.kwonlyargs:
                if arg.arg != "deps":
                    continue
                annotation = ast.unparse(arg.annotation) if arg.annotation is not None else ""
                if annotation in {"", "Any"}:
                    violations.append(f"{relative}:{node.lineno}:{node.name}")

    assert violations == []
