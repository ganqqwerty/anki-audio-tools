"""Python module catalog: layer assignments, import classification, and module metadata."""

from __future__ import annotations

import ast
from pathlib import Path

from tests.test_architecture.contracts import MODULE_CONTRACTS

ROOT = Path(__file__).resolve().parent.parent.parent
ADDON = ROOT / "addon" / "anki_audio_quick_editor"
PKG = "anki_audio_quick_editor"

ANKI_PREFIXES = ("aqt", "anki")

STDLIB: set[str] = {
    "__future__", "ast", "collections", "copy", "dataclasses", "enum",
    "functools", "hashlib", "io", "itertools", "json", "logging",
    "math", "os", "pathlib", "re", "shutil", "subprocess",
    "sys", "tempfile", "threading", "time", "typing", "uuid",
    "warnings", "weakref", "contextlib", "urllib", "zipfile", "struct",
}


def _qualified_module_name(module_name: str) -> str:
    if module_name == "__init__":
        return PKG
    return f"{PKG}.{module_name}"


LAYERS: dict[str, str] = {
    _qualified_module_name(module_name): contract.layer.value
    for module_name, contract in MODULE_CONTRACTS.items()
}


def _resolve_relative_import(import_name: str, source_path: Path) -> str:
    level = len(import_name) - len(import_name.lstrip("."))
    module_part = import_name.lstrip(".")
    package_parts = list(source_path.relative_to(ADDON).parts[:-1])
    remaining = max(0, len(package_parts) - (level - 1))
    prefix_parts = package_parts[:remaining]
    short_parts = prefix_parts + ([*module_part.split(".")] if module_part else [])
    short_name = ".".join(part for part in short_parts if part)
    if not short_name:
        return PKG
    return f"{PKG}.{short_name}"


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


def _iter_import_nodes(nodes: list[ast.stmt]) -> list[ast.Import | ast.ImportFrom]:
    imports: list[ast.Import | ast.ImportFrom] = []
    for node in nodes:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(node)
        elif isinstance(node, ast.If):
            if not _is_type_checking_guard(node):
                imports.extend(_iter_import_nodes(node.body))
                imports.extend(_iter_import_nodes(node.orelse))
        elif isinstance(node, ast.Try):
            imports.extend(_iter_import_nodes(node.body))
            for handler in node.handlers:
                imports.extend(_iter_import_nodes(handler.body))
            imports.extend(_iter_import_nodes(node.orelse))
            imports.extend(_iter_import_nodes(node.finalbody))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            imports.extend(_iter_import_nodes(node.body))
    return imports


def _collect_imports(py_file: Path) -> dict[str, list[str]]:
    """Extract imports from a Python file grouped by category."""
    if not py_file.is_file():
        return {}
    try:
        source = py_file.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return {}

    anki_imports: list[str] = []
    addon_imports: list[str] = []
    stdlib_imports: list[str] = []
    third_party: list[str] = []

    for node in _iter_import_nodes(tree.body):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split(".")[0]
                if name in STDLIB:
                    stdlib_imports.append(alias.name)
                elif name.startswith(ANKI_PREFIXES):
                    anki_imports.append(alias.name)
                elif name == PKG.split(".", maxsplit=1)[0] or name == PKG:
                    addon_imports.append(alias.name)
                else:
                    third_party.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                module_part = node.module or ""
                if module_part:
                    addon_imports.append(_resolve_relative_import("." * node.level + module_part, py_file))
                else:
                    for alias in node.names:
                        if alias.name != "*":
                            addon_imports.append(_resolve_relative_import("." * node.level + alias.name, py_file))
                continue
            if not node.module:
                continue
            name = node.module.split(".")[0]
            if name in STDLIB:
                stdlib_imports.append(node.module)
            elif name.startswith(ANKI_PREFIXES):
                anki_imports.append(node.module)
            elif name == PKG.split(".", maxsplit=1)[0] or name == PKG:
                addon_imports.append(node.module)
            else:
                third_party.append(node.module)

    return {
        "anki": sorted(set(anki_imports)),
        "addon": sorted(set(addon_imports)),
        "stdlib": sorted(set(stdlib_imports)),
        "third_party": sorted(set(third_party)),
    }


def _module_name(py_file: Path) -> str:
    """Convert a Python file path to its dotted module name."""
    rel = py_file.relative_to(ADDON.parent)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = parts[-1].replace(".py", "")
    return ".".join(parts)


def _module_summary(py_file: Path) -> str:
    """Extract first docstring sentence or derive purpose from filename."""
    if not py_file.is_file():
        return ""
    try:
        source = py_file.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return ""

    if (isinstance(tree, ast.Module) and tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        doc = tree.body[0].value.value.strip()
        first_line = doc.split("\n")[0].rstrip(".")
        return first_line

    return f"Module: {py_file.stem}"


def _build_python_catalog() -> list[dict]:
    modules = []
    for py_file in sorted(ADDON.rglob("*.py")):
        if py_file.name.startswith("_") and py_file.name not in {"__init__.py", "_version.py"}:
            continue
        name = _module_name(py_file)
        rel_parts = py_file.relative_to(ADDON).parts
        if any(part in {"user_files", "vendor", "bin"} for part in rel_parts):
            continue
        if "templates" in name:
            continue

        imports = _collect_imports(py_file)
        modules.append({
            "module": name,
            "file": str(py_file.relative_to(ROOT)),
            "layer": LAYERS.get(name, "unclassified"),
            "summary": _module_summary(py_file),
            "imports": imports,
        })
    return modules
