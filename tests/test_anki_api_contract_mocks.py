"""Ensure local Anki mocks expose the generated compatibility surface."""

from __future__ import annotations

import importlib
import inspect
import types
from concurrent.futures import Future
from typing import Any
from unittest.mock import MagicMock

import pytest
from anki_api_contract.discover import (
    CallableUse,
    ImportedObject,
    discover_anki_api_surface,
)

from tests._anki_test_mocks_stubs import _TaskManager

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
    resolved = _resolve_declared(module, use.qualname)

    assert callable(resolved)
    positional = [object()] * (use.positional_args + int(use.implicit_self))
    keywords = {name: object() for name in use.keywords}
    inspect.signature(resolved).bind(*positional, **keywords)


def test_task_manager_can_hold_and_deliver_background_completion() -> None:
    taskman = _TaskManager(auto_run=False)
    callbacks: list[tuple[bool, int]] = []

    future = taskman.run_in_background(
        lambda: 42,
        lambda completed: callbacks.append((completed.done(), completed.result())),
        uses_collection=False,
    )

    assert not future.done()
    assert len(taskman.background_queue) == 1
    taskman.complete_next_background()
    assert future.result() == 42
    assert callbacks == [(True, 42)]


def test_task_manager_delivers_exceptions_through_future() -> None:
    taskman = _TaskManager(auto_run=False)
    callbacks: list[Future[Any]] = []

    def fail() -> None:
        raise RuntimeError("boom")

    future = taskman.run_in_background(fail, callbacks.append)
    taskman.complete_next_background()

    assert callbacks == [future]
    with pytest.raises(RuntimeError, match="boom"):
        future.result()


def test_browser_menu_hook_wrapper_signature_is_discovered() -> None:
    browser_hooks = {
        use.qualname: use
        for use in SURFACE.callable_uses
        if use.module == "aqt.gui_hooks" and use.qualname.startswith("browser_")
    }

    assert browser_hooks["browser_menus_did_init"].exact_parameter_names == ("browser",)
    assert "browser_will_show_context_menu" not in browser_hooks
