"""Rule 24: runtime sibling imports must not hard-code the source package name."""

from __future__ import annotations

import ast

from .inspection import ADDON_DIR


def test_runtime_import_module_calls_do_not_hard_code_source_package() -> None:
    violations: list[str] = []
    for path in sorted(ADDON_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Name) or func.id != "import_module":
                continue
            if not node.args:
                continue
            module_arg = node.args[0]
            if (
                isinstance(module_arg, ast.Constant)
                and isinstance(module_arg.value, str)
                and module_arg.value.startswith("anki_audio_quick_editor.")
            ):
                rel = path.relative_to(ADDON_DIR)
                violations.append(f"{rel}:{node.lineno}: import_module({module_arg.value!r})")

    assert violations == [], "\n".join(violations)
