"""Rule 2: thin runtime modules keep Anki imports inside function boundaries."""

from __future__ import annotations

from .conftest import (
    ADDON_DIR,
    SETTINGS_BACKEND_MODULES,
    UI_MODULES,
    _imports_anki,
    _module_files,
    get_module_level_imports,
)

IMPORT_SAFE_RUNTIME_MODULES = UI_MODULES | SETTINGS_BACKEND_MODULES


def test_runtime_modules_avoid_module_level_anki_imports() -> None:
    for module_name in IMPORT_SAFE_RUNTIME_MODULES:
        for path in _module_files(module_name):
            hits = _imports_anki(get_module_level_imports(path))
            assert hits == [], f"{path.relative_to(ADDON_DIR)} imports {hits} at module level"
