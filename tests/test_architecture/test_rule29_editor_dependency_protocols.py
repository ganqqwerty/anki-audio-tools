"""Rule 29: editor workflows use typed dependency protocols."""

from __future__ import annotations

import ast

from .conftest import ADDON_DIR

MIGRATED_FILES = (
    "editor_analysis.py",
    "editor_bridge.py",
    "editor_conversion.py",
    "editor_dependencies.py",
    "editor_cursor_bridge.py",
    "editor_frontend/busy.py",
    "editor_frontend/playback.py",
    "editor_frontend/refresh.py",
    "editor_frontend_callbacks.py",
    "editor_history.py",
    "editor_media_replacement.py",
    "editor_persistent_undo.py",
    "editor_presets.py",
    "editor_processing.py",
    "editor_processing_shared.py",
    "editor_recording.py",
    "editor_recording_analysis.py",
    "editor_recording_requests.py",
    "editor_region_delete.py",
    "editor_region_delete_worker.py",
    "editor_reload_status.py",
    "editor_session.py",
    "editor_settings_actions.py",
    "editor_sharing.py",
    "editor_source_metadata.py",
    "editor_special_transform_worker.py",
    "editor_special_transforms.py",
    "editor_split_defaults.py",
)
DEPENDENCY_PROTOCOLS = ADDON_DIR / "editor_deps_protocols.py"
EDITOR_DEPENDENCIES = ADDON_DIR / "editor_dependencies.py"
FACTORY_PROTOCOLS = {
    "frontend_deps": "FrontendDeps",
    "bridge_deps": "BridgeDeps",
    "recording_deps": "RecordingDeps",
    "share_deps": "ShareDeps",
    "history_deps": "HistoryDeps",
    "processing_deps": "ProcessingDeps",
    "settings_action_deps": "SettingsActionDeps",
    "cursor_deps": "CursorDeps",
    "analysis_deps": "AnalysisDeps",
    "region_delete_deps": "RegionDeleteDeps",
}


def test_editor_workflows_do_not_accept_untyped_deps_any() -> None:
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


def test_dependency_protocols_and_factories_stay_in_sync() -> None:
    violations: dict[str, dict[str, set[str]]] = {}
    for factory_name, protocol_name in FACTORY_PROTOCOLS.items():
        protocol_members = _protocol_members(DEPENDENCY_PROTOCOLS, protocol_name)
        factory_members = _simple_namespace_keywords(EDITOR_DEPENDENCIES, factory_name)
        if factory_members != protocol_members:
            violations[factory_name] = {
                "missing_from_protocol": factory_members - protocol_members,
                "missing_from_factory": protocol_members - factory_members,
            }

    assert violations == {}


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
