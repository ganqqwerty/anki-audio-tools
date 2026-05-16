"""Ensure local Anki mocks expose the generated compatibility surface."""

from __future__ import annotations

import importlib
import types
from typing import Any
from unittest.mock import MagicMock

import pytest
from anki_api_contract.discover import (
    CallableUse,
    ImportedObject,
    discover_anki_api_surface,
)

SURFACE = discover_anki_api_surface()


def _declared_child(obj: Any, name: str) -> Any:
    if isinstance(obj, types.ModuleType):
        assert name in vars(obj)
        return vars(obj)[name]
    if isinstance(obj, MagicMock):
        explicit_attrs = vars(obj)
        mock_children = getattr(obj, "_mock_children", {})
        assert name in explicit_attrs or name in mock_children
        return getattr(obj, name)
    assert hasattr(obj, name)
    return getattr(obj, name)


def _resolve_declared(module: types.ModuleType, qualname: str) -> Any:
    current: Any = module
    for part in qualname.split("."):
        current = _declared_child(current, part)
    return current


@pytest.mark.parametrize("module_name", SURFACE.imported_modules)
def test_mocked_anki_module_imports(module_name: str) -> None:
    importlib.import_module(module_name)


@pytest.mark.parametrize("imported", SURFACE.imported_objects, ids=lambda item: item.display_name)
def test_mocked_anki_imported_objects_exist(imported: ImportedObject) -> None:
    module = importlib.import_module(imported.module)

    assert imported.name in vars(module)


@pytest.mark.parametrize("use", SURFACE.callable_uses, ids=lambda item: item.display_name)
def test_mocked_anki_callable_uses_are_declared(use: CallableUse) -> None:
    module = importlib.import_module(use.module)

    assert _resolve_declared(module, use.qualname) is not None
