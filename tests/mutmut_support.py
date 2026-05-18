"""Mutmut import alias support for the pytest add-on harness."""

from __future__ import annotations

import importlib
import inspect
import os
import sys
import types
from pathlib import Path


def addon_import_root() -> Path:
    """Return the path to place on sys.path for add-on imports."""
    root = Path(__file__).resolve().parent.parent
    if os.environ.get("MUTANT_UNDER_TEST"):
        return root
    return root / "addon"


def configure_mutmut_module_alias() -> None:
    """Reuse the active mutmut main module instead of importing it twice."""
    if not os.environ.get("MUTANT_UNDER_TEST"):
        return
    main_module = sys.modules.get("__main__")
    if main_module is None or not hasattr(main_module, "record_trampoline_hit"):
        return
    sys.modules.setdefault("mutmut.__main__", main_module)


def configure_mutmut_package_aliases() -> None:
    """Map test imports onto addon-prefixed mutmut module names."""
    if not os.environ.get("MUTANT_UNDER_TEST"):
        return
    module_names = [
        "addon.anki_audio_quick_editor",
        "addon.anki_audio_quick_editor.audio_state",
        "addon.anki_audio_quick_editor.audio_processor",
        "addon.anki_audio_quick_editor.batch_visualization",
        "addon.anki_audio_quick_editor.config_migration",
        "addon.anki_audio_quick_editor.errors",
        "addon.anki_audio_quick_editor.prosody_cache",
        "addon.anki_audio_quick_editor.prosody_svg",
        "addon.anki_audio_quick_editor.prosody_types",
        "addon.anki_audio_quick_editor.settings_state",
        "addon.anki_audio_quick_editor.sound_refs",
    ]
    for module_name in module_names:
        module = importlib.import_module(module_name)
        retarget_module_members_for_mutmut(module, module_name)
        sys.modules.setdefault(module_name.removeprefix("addon."), module)


def retarget_module_members_for_mutmut(module: types.ModuleType, module_name: str) -> None:
    """Align trampoline hit names with mutmut's addon-prefixed file identifiers."""
    original_module_name = module.__name__
    module.__name__ = module_name
    for value in vars(module).values():
        if inspect.isfunction(value):
            if value.__module__ == original_module_name:
                value.__module__ = module_name
            continue
        if inspect.isclass(value) and value.__module__ == original_module_name:
            value.__module__ = module_name
            _retarget_class_members(value, original_module_name, module_name)


def _retarget_class_members(value: type, original_module_name: str, module_name: str) -> None:
    for member in vars(value).values():
        function = None
        if inspect.isfunction(member):
            function = member
        elif isinstance(member, (staticmethod, classmethod)):
            function = member.__func__
        if function is not None and function.__module__ == original_module_name:
            function.__module__ = module_name
