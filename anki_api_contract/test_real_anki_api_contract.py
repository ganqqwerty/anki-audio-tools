"""Compatibility checks against the installed real Anki Python runtime."""

from __future__ import annotations

import importlib
import inspect
from collections.abc import Callable
from types import ModuleType
from typing import Any

import pytest

from anki_api_contract.discover import (
    CallableUse,
    ImportedObject,
    discover_anki_api_surface,
)

importlib.import_module("aqt")

SURFACE = discover_anki_api_surface()


def _resolve(module: ModuleType, qualname: str) -> Any:
    current: Any = module
    for part in qualname.split("."):
        current = getattr(current, part)
    return current


def _signature_parameters(obj: Callable[..., Any]) -> tuple[inspect.Parameter, ...]:
    signature = _signature(obj)
    if signature is None:
        return ()
    return tuple(
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind
        in {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }
    )


def _signature(obj: Callable[..., Any]) -> inspect.Signature | None:
    try:
        return inspect.signature(obj)
    except (TypeError, ValueError):
        return None


def _assert_call_compatible(use: CallableUse, obj: Callable[..., Any]) -> None:
    signature = _signature(obj)
    if signature is None:
        assert not use.exact
        return

    parameters = _signature_parameters(obj)
    actual_names = tuple(parameter.name for parameter in parameters)
    expected_args = use.positional_args + (1 if use.implicit_self else 0)
    if use.exact and use.exact_parameter_names:
        assert actual_names == use.exact_parameter_names
    elif use.exact:
        assert len(actual_names) == expected_args

    placeholders = [object()] * expected_args
    keywords = {name: object() for name in use.keywords}
    signature.bind(*placeholders, **keywords)


@pytest.mark.parametrize("module_name", SURFACE.imported_modules)
def test_real_anki_module_imports(module_name: str) -> None:
    importlib.import_module(module_name)


@pytest.mark.parametrize("imported", SURFACE.imported_objects, ids=lambda item: item.display_name)
def test_real_anki_imported_objects_exist(imported: ImportedObject) -> None:
    module = importlib.import_module(imported.module)

    assert hasattr(module, imported.name)


@pytest.mark.parametrize("use", SURFACE.callable_uses, ids=lambda item: item.display_name)
def test_real_anki_callable_uses_are_compatible(use: CallableUse) -> None:
    module = importlib.import_module(use.module)
    obj = _resolve(module, use.qualname)

    _assert_call_compatible(use, obj)
