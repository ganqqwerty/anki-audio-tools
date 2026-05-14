"""Shared fixtures, layer definitions, and AST helpers for architecture tests."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Union

ADDON_DIR = Path(__file__).parent.parent.parent / "addon" / "anki_audio_quick_editor"

IMPORT_SAFE_MODULES = {
    "_version",
    "audio_processor",
    "audio_state",
    "config_migration",
    "db_helpers",
    "editor_actions",
    "editor_ui",
    "errors",
    "settings_state",
    "sound_refs",
}
UI_MODULES = {"editor_integration"}
SETTINGS_MODULES = {"settings"}
SETTINGS_BACKEND_MODULES = {"settings.commands", "settings.initial_state"}
ENTRY_POINT = {"__init__"}

ALL_LAYERS = (
    IMPORT_SAFE_MODULES | UI_MODULES | SETTINGS_MODULES | SETTINGS_BACKEND_MODULES | ENTRY_POINT
)
ANKI_PREFIXES = ("aqt", "anki")


def _module_files(module_name: str) -> list[Path]:
    parts = module_name.split(".")
    base = ADDON_DIR / Path(*parts)
    py_file = base.with_suffix(".py")
    if py_file.exists():
        return [py_file]
    if base.is_dir() and (base / "__init__.py").exists():
        return list(base.glob("*.py"))
    return []


def _is_type_checking_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    return (
        isinstance(test, ast.Attribute)
        and test.attr == "TYPE_CHECKING"
        and isinstance(test.value, ast.Name)
        and test.value.id == "typing"
    )


def _extract_import_names(node: Union[ast.Import, ast.ImportFrom]) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    prefix = "." * node.level
    if node.module:
        return [f"{prefix}{node.module}"]
    if node.level > 0:
        return [f"{prefix}{alias.name}" for alias in node.names]
    return []


def _collect_imports(nodes: list[ast.stmt]) -> list[str]:
    imports: list[str] = []
    for node in nodes:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.extend(_extract_import_names(node))
        elif isinstance(node, ast.If):
            if not _is_type_checking_guard(node):
                imports.extend(_collect_imports(node.body))
                imports.extend(_collect_imports(node.orelse))
        elif isinstance(node, ast.Try):
            imports.extend(_collect_imports(node.body))
            for handler in node.handlers:
                imports.extend(_collect_imports(handler.body))
            imports.extend(_collect_imports(node.orelse))
            imports.extend(_collect_imports(node.finalbody))
    return imports


def _collect_all_imports(nodes: list[ast.stmt]) -> list[str]:
    imports: list[str] = []
    for node in nodes:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.extend(_extract_import_names(node))
        elif isinstance(node, ast.If):
            if not _is_type_checking_guard(node):
                imports.extend(_collect_all_imports(node.body))
                imports.extend(_collect_all_imports(node.orelse))
        elif isinstance(node, ast.Try):
            imports.extend(_collect_all_imports(node.body))
            for handler in node.handlers:
                imports.extend(_collect_all_imports(handler.body))
            imports.extend(_collect_all_imports(node.orelse))
            imports.extend(_collect_all_imports(node.finalbody))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            imports.extend(_collect_all_imports(node.body))
    return imports


def get_module_level_imports(filepath: Path) -> list[str]:
    return _collect_imports(ast.parse(filepath.read_text()).body)


def get_all_imports(filepath: Path) -> list[str]:
    return _collect_all_imports(ast.parse(filepath.read_text()).body)


def _resolve_relative_import(import_name: str, source_path: Path) -> str:
    if not import_name.startswith("."):
        return import_name
    level = len(import_name) - len(import_name.lstrip("."))
    module_part = import_name.lstrip(".")
    package_parts = list(source_path.relative_to(ADDON_DIR).parts[:-1])
    remaining = max(0, len(package_parts) - (level - 1))
    prefix_parts = package_parts[:remaining]
    if module_part:
        return ".".join(prefix_parts + module_part.split("."))
    return ".".join(prefix_parts)


def _imports_anki(imports: list[str]) -> list[str]:
    return [m for m in imports if any(m == prefix or m.startswith(prefix + ".") for prefix in ANKI_PREFIXES)]


def _classify_import(resolved: str) -> str | None:
    best: str | None = None
    for layer_name in ALL_LAYERS:
        if resolved == layer_name or resolved.startswith(layer_name + "."):
            if best is None or len(layer_name) > len(best):
                best = layer_name
    return best


def _imports_addon_modules(imports: list[str], forbidden: set[str], source_path: Path) -> list[str]:
    hits: list[str] = []
    for name in imports:
        if not name.startswith("."):
            continue
        resolved = _resolve_relative_import(name, source_path)
        classified = _classify_import(resolved)
        if classified is not None and classified in forbidden:
            hits.append(name)
    return hits


def _get_relative_deps(filepath: Path) -> set[str]:
    deps: set[str] = set()
    for name in get_all_imports(filepath):
        if name.startswith("."):
            deps.add(_resolve_relative_import(name, filepath))
    return deps


def _get_module_relative_deps(module_name: str) -> set[str]:
    deps: set[str] = set()
    for path in _module_files(module_name):
        deps |= _get_relative_deps(path)
    deps.discard(module_name)
    return {dep for dep in deps if not dep.startswith(module_name + ".")}
