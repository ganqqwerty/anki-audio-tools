"""Rule 30: batch processors use explicit dependencies, not lazy facade lookup."""

from __future__ import annotations

from .conftest import ADDON_DIR


def test_batch_processing_modules_do_not_lazy_load_batch_facade() -> None:
    violations: list[str] = []
    for relative in ("batch_operation_processing.py", "batch_operations_helpers.py"):
        text = (ADDON_DIR / relative).read_text(encoding="utf-8")
        if 'import_module(".batch_operations"' in text or "_facade_attr(" in text:
            violations.append(relative)

    assert violations == []
