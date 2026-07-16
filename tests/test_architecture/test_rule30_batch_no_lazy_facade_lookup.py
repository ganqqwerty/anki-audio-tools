"""Rule 30: batch processors use explicit dependencies, not lazy facade lookup."""

from __future__ import annotations

import ast

from .conftest import ADDON_DIR


def _lazy_facade_lookups(source: str) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "_facade_attr":
            violations.append("_facade_attr")
            continue
        if not (
            (isinstance(node.func, ast.Name) and node.func.id == "import_module")
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "importlib"
            )
        ):
            continue
        if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == ".batch_operations":
            violations.append("import_module")
    return violations


def test_batch_processing_modules_do_not_lazy_load_batch_facade() -> None:
    violations: list[str] = []
    for relative in ("batch_operation_processing.py", "batch_operations_helpers.py"):
        text = (ADDON_DIR / relative).read_text(encoding="utf-8")
        if _lazy_facade_lookups(text):
            violations.append(relative)

    assert violations == []


def test_lazy_facade_detector_catches_equivalent_call_syntax() -> None:
    assert _lazy_facade_lookups("importlib.import_module( '.batch_operations' )") == ["import_module"]
    assert _lazy_facade_lookups("value = _facade_attr ('render')") == ["_facade_attr"]


def test_lazy_facade_detector_ignores_comments_and_strings() -> None:
    source = '# import_module(".batch_operations")\nvalue = "_facade_attr(render)"'
    assert _lazy_facade_lookups(source) == []
