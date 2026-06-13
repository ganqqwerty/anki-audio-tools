"""Rule 32: SOLID editor workflow seams stay centralized."""

from __future__ import annotations

import ast

from .conftest import ADDON_DIR

EDITOR_RENDER_REPLACEMENT_WORKFLOWS = (
    "editor_processing.py",
    "editor_region_delete.py",
    "editor_special_transforms.py",
)
DIRECT_SOUND_REFERENCE_REPLACERS = {
    "replace_sound_reference",
    "select_first_sound_reference",
}


def test_editor_render_workflows_use_shared_media_replacement_primitives() -> None:
    violations: list[str] = []
    for relative in EDITOR_RENDER_REPLACEMENT_WORKFLOWS:
        path = ADDON_DIR / relative
        source = path.read_text(encoding="utf-8")
        if "editor_media_replacement" not in source:
            violations.append(f"{relative}: does not import editor_media_replacement")
            continue
        for line_no, name in _direct_sound_reference_calls(source):
            violations.append(f"{relative}:{line_no}: direct {name}() call")

    assert violations == [], "\n".join(violations)


def _direct_sound_reference_calls(source: str) -> list[tuple[int, str]]:
    tree = ast.parse(source)
    calls: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in DIRECT_SOUND_REFERENCE_REPLACERS:
            calls.append((node.lineno, node.func.id))
        if isinstance(node.func, ast.Attribute) and node.func.attr in DIRECT_SOUND_REFERENCE_REPLACERS:
            calls.append((node.lineno, node.func.attr))
    return calls
