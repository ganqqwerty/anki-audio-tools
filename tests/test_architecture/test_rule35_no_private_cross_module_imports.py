"""Rule 35: underscore-prefixed symbols must not cross module boundaries."""

from __future__ import annotations

from .inspection import collect_private_cross_module_imports

ALLOWED_CROSS_MODULE_PRIVATE = {
    "__version__",
}


def test_no_private_cross_module_imports() -> None:
    violations = [
        (source, target, symbol)
        for source, target, symbol in collect_private_cross_module_imports()
        if symbol not in ALLOWED_CROSS_MODULE_PRIVATE
    ]
    if not violations:
        return
    lines = [
        f"  {source} -> {target}: {symbol}"
        for source, target, symbol in violations
    ]
    raise AssertionError(
        "Cross-module imports of private symbols:\n" + "\n".join(sorted(lines))
    )
