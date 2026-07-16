"""Collection policies that keep the test inventory honest."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _defines_test(tree: ast.AST) -> bool:
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
        for node in ast.walk(tree)
    )


def test_every_test_named_python_module_defines_a_collected_test() -> None:
    empty_modules: list[str] = []
    for test_root in (ROOT / "tests", ROOT / "e2e"):
        for path in sorted(test_root.rglob("test_*.py")):
            if not _defines_test(ast.parse(path.read_text(encoding="utf-8"))):
                empty_modules.append(path.relative_to(ROOT).as_posix())

    assert empty_modules == [], (
        "test_* modules must define tests locally; rename fixtures/helpers and "
        f"delete compatibility wrappers: {empty_modules}"
    )
