"""Rule 11: leaf modules remain free of addon-relative imports."""

from __future__ import annotations

import pytest

from .conftest import _module_files, get_all_imports


@pytest.mark.parametrize("module_name", ["_version", "errors"])
def test_leaf_modules_have_no_relative_imports(module_name: str) -> None:
    for path in _module_files(module_name):
        relative = [name for name in get_all_imports(path) if name.startswith(".")]
        assert relative == [], f"{path.name} must remain import-leaf safe"
