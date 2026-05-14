"""Rule 1: import-safe modules must not import aqt/anki at module level."""

from .conftest import (
    IMPORT_SAFE_MODULES,
    _imports_anki,
    _module_files,
    get_module_level_imports,
)


def test_all_import_safe_modules_avoid_module_level_anki_imports() -> None:
    for module_name in IMPORT_SAFE_MODULES:
        for path in _module_files(module_name):
            assert _imports_anki(get_module_level_imports(path)) == [], path.name
