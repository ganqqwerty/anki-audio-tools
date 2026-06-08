"""Rule 27: editor reload status has one backend and frontend lifecycle owner."""

from __future__ import annotations

import ast

from .inspection import ADDON_DIR

PROJECT_ROOT = ADDON_DIR.parents[1]
EDITOR_STATUS_RELOAD_MODULES = {
    "editor_history.py",
    "editor_processing.py",
    "editor_region_delete.py",
    "editor_settings_actions.py",
    "editor_special_transforms.py",
}
PENDING_STATUS_OWNER_MODULES = {"editor_reload_status.py"}


def _calls_name(node: ast.Call, name: str) -> bool:
    return isinstance(node.func, ast.Name) and node.func.id == name


def _calls_attr(node: ast.Call, attr: str) -> bool:
    return isinstance(node.func, ast.Attribute) and node.func.attr == attr


def _assigns_pending_status_none(node: ast.AST) -> bool:
    if not isinstance(node, ast.Assign):
        return False
    if not isinstance(node.value, ast.Constant) or node.value.value is not None:
        return False
    return any(
        isinstance(target, ast.Attribute) and target.attr == "pending_status"
        for target in node.targets
    )


def test_reload_status_modules_delegate_editor_reload_to_status_helper() -> None:
    offenders: list[str] = []
    for filename in EDITOR_STATUS_RELOAD_MODULES:
        path = ADDON_DIR / filename
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _calls_attr(node, "loadNote"):
                offenders.append(f"{filename}:{node.lineno}")

    assert offenders == []


def test_pending_editor_status_is_constructed_only_by_reload_lifecycle() -> None:
    offenders: list[str] = []
    for path in ADDON_DIR.glob("*.py"):
        if path.name in PENDING_STATUS_OWNER_MODULES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _calls_name(node, "PendingEditorStatus"):
                offenders.append(f"{path.name}:{node.lineno}")

    assert offenders == []


def test_reload_status_helper_callers_do_not_clear_pending_status() -> None:
    offenders: list[str] = []
    for filename in EDITOR_STATUS_RELOAD_MODULES:
        path = ADDON_DIR / filename
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for function in [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]:
            has_reload_helper = any(
                isinstance(node, ast.Call) and _calls_name(node, "reload_editor_with_pending_status")
                for node in ast.walk(function)
            )
            if not has_reload_helper:
                continue
            for node in ast.walk(function):
                if _assigns_pending_status_none(node):
                    offenders.append(f"{filename}:{function.name}:{node.lineno}")

    assert offenders == []


def test_initial_status_by_field_is_consumed_only_by_control_actions() -> None:
    offenders: list[str] = []
    for path in (PROJECT_ROOT / "settings_ui" / "src" / "editor-inline").rglob("*"):
        if not path.is_file() or path.name in {"control-actions.ts", "types.ts", "editor-runtime-types.ts"}:
            continue
        if path.suffix not in {".ts", ".svelte"}:
            continue
        text = path.read_text(encoding="utf-8")
        if "initialStatusByField" in text:
            offenders.append(str(path.relative_to(PROJECT_ROOT)))

    assert offenders == []
