"""Rule 1: pure modules must not import aqt/anki at module level."""

from .conftest import (
    PURE_MODULES,
    _imports_anki,
    _module_files,
    get_module_level_imports,
)


def test_all_pure_modules_avoid_module_level_anki_imports() -> None:
    for module_name in PURE_MODULES:
        for path in _module_files(module_name):
            assert _imports_anki(get_module_level_imports(path)) == [], path.name
