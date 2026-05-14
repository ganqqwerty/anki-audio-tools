"""Rule 6: settings backend modules must not import UI modules."""

from .conftest import (
    SETTINGS_BACKEND_MODULES,
    UI_MODULES,
    _imports_addon_modules,
    _module_files,
    get_all_imports,
)


def test_settings_backend_modules_avoid_ui_imports() -> None:
    for module_name in SETTINGS_BACKEND_MODULES:
        for path in _module_files(module_name):
            hits = _imports_addon_modules(get_all_imports(path), UI_MODULES, path)
            assert hits == [], f"{path.name} imports UI modules: {hits}"
