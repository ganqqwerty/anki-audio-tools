from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_ROOTS = (ROOT / "e2e", ROOT / "tests")
FORBIDDEN_PYTEST_CALLS = {"skip", "importorskip"}
FORBIDDEN_MARKS = {"skipif"}


def test_dependency_tests_do_not_silently_skip_missing_requirements() -> None:
    violations: list[str] = []
    for test_root in TEST_ROOTS:
        for path in sorted(test_root.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if _is_forbidden_pytest_call(node) or _is_forbidden_pytest_mark(node):
                    violations.append(f"{path.relative_to(ROOT)}:{node.lineno}")

    assert violations == []


def _is_forbidden_pytest_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id == "pytest"
        and func.attr in FORBIDDEN_PYTEST_CALLS
    )


def _is_forbidden_pytest_mark(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr in FORBIDDEN_MARKS
        and isinstance(func.value, ast.Attribute)
        and func.value.attr == "mark"
        and isinstance(func.value.value, ast.Name)
        and func.value.value.id == "pytest"
    )
