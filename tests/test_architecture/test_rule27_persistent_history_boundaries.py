"""Rule 27: persistent history stays detached behind its editor adapter."""

from __future__ import annotations

import ast
from pathlib import Path

from .conftest import ADDON_DIR
from .inspection import observe_module

ALLOWED_PRODUCTION_IMPORTERS = {
    ADDON_DIR / "editor_persistent_undo.py",
    ADDON_DIR / "persistent_history.py",
    ADDON_DIR / "persistent_undo_chain.py",
}


def test_persistent_history_remains_import_safe_storage_leaf() -> None:
    observation = observe_module("persistent_history")

    assert observation.any_anki_imports == frozenset()
    assert observation.addon_deps == frozenset({"audio_state"})


def test_persistent_history_production_imports_go_through_editor_adapter() -> None:
    violations: list[str] = []
    for path in sorted(ADDON_DIR.rglob("*.py")):
        if path in ALLOWED_PRODUCTION_IMPORTERS or "__pycache__" in path.parts:
            continue
        if _imports_persistent_history(path):
            violations.append(str(path.relative_to(ADDON_DIR)))

    assert violations == [], "\n".join(violations)


def _imports_persistent_history(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and _import_from_targets_persistent_history(node):
            return True
        if isinstance(node, ast.Import) and any(
            alias.name == "anki_audio_quick_editor.persistent_history"
            for alias in node.names
        ):
            return True
    return False


def _import_from_targets_persistent_history(node: ast.ImportFrom) -> bool:
    if node.module == "anki_audio_quick_editor.persistent_history":
        return True
    return node.level == 1 and node.module == "persistent_history"
