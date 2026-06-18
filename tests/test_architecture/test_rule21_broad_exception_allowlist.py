"""Rule 21: broad exception handlers require a documented allowlist entry."""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

from .broad_exception_allowlist_data import BROAD_EXCEPTION_ALLOWLIST
from .inspection import ADDON_DIR


class BroadExceptionVisitor(ast.NodeVisitor):
    """Collect broad exception handlers by module-qualified function name."""

    def __init__(self, module: str) -> None:
        self.module = module
        self._stack: list[str] = []
        self.handlers: Counter[tuple[str, str]] = Counter()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if _is_broad_exception_type(node.type):
            qualname = ".".join(self._stack) or "<module>"
            self.handlers[(self.module, qualname)] += 1
        self.generic_visit(node)


def test_broad_exception_handlers_are_allowlisted_with_reasons() -> None:
    observed = _collect_broad_exception_handlers()
    allowed = {(item.module, item.qualname): item for item in BROAD_EXCEPTION_ALLOWLIST}
    violations: list[str] = []

    for key, count in sorted(observed.items()):
        allowance = allowed.get(key)
        if allowance is None:
            violations.append(f"{key[0]}.{key[1]} has {count} unallowlisted broad exception handler(s)")
            continue
        if count != allowance.count:
            violations.append(
                f"{key[0]}.{key[1]} has {count} broad exception handler(s), expected {allowance.count}"
            )
        if not allowance.reason.strip():
            violations.append(f"{key[0]}.{key[1]} allowlist entry must include a reason")

    for key, allowance in sorted(allowed.items()):
        if key not in observed:
            violations.append(f"{allowance.module}.{allowance.qualname} is allowlisted but no handler was found")

    assert violations == [], "\n".join(violations)


def _collect_broad_exception_handlers() -> Counter[tuple[str, str]]:
    observed: Counter[tuple[str, str]] = Counter()
    for path in sorted(ADDON_DIR.rglob("*.py")):
        if "vendor" in path.parts or "user_files" in path.parts:
            continue
        module = _module_name(path)
        visitor = BroadExceptionVisitor(module)
        visitor.visit(ast.parse(path.read_text(encoding="utf-8")))
        observed.update(visitor.handlers)
    return observed


def _is_broad_exception_type(node: ast.expr | None) -> bool:
    if node is None:
        return True
    if isinstance(node, ast.Name):
        return node.id in {"Exception", "BaseException"}
    if isinstance(node, ast.Attribute):
        return node.attr in {"Exception", "BaseException"}
    if isinstance(node, ast.Tuple):
        return any(_is_broad_exception_type(item) for item in node.elts)
    return False


def _module_name(path: Path) -> str:
    relative = path.relative_to(ADDON_DIR).with_suffix("")
    parts = relative.parts
    if parts == ("__init__",):
        return "__init__"
    if parts[-1] == "__init__":
        return ".".join(parts[:-1])
    return ".".join(parts)
