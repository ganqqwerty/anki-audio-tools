"""Rule 29: migrated editor workflows use typed dependency protocols."""

from __future__ import annotations

import ast

from .conftest import ADDON_DIR

MIGRATED_FILES = (
    "editor_region_delete.py",
    "editor_region_delete_worker.py",
)
REGION_DELETE_PROTOCOL = ADDON_DIR / "editor_deps_protocols.py"
EDITOR_DEPENDENCIES = ADDON_DIR / "editor_dependencies.py"


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


def test_region_delete_protocol_and_factory_stay_in_sync() -> None:
    protocol_members = _protocol_members(REGION_DELETE_PROTOCOL, "RegionDeleteDeps")
    factory_members = _simple_namespace_keywords(EDITOR_DEPENDENCIES, "region_delete_deps")

    assert factory_members == protocol_members


def _protocol_members(path, class_name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                statement.target.id
                for statement in node.body
                if isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
            }
    raise AssertionError(f"Protocol {class_name} not found")


def _simple_namespace_keywords(path, function_name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != function_name:
            continue
        for child in ast.walk(node):
            if not (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "SimpleNamespace"
            ):
                continue
            return {keyword.arg for keyword in child.keywords if keyword.arg is not None}
    raise AssertionError(f"SimpleNamespace factory {function_name} not found")
