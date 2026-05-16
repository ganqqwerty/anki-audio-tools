"""Shared fixtures and compatibility helpers for architecture tests."""

from __future__ import annotations

from pathlib import Path

from .contracts import MODULE_CONTRACTS, Layer
from .inspection import (
    ANKI_PREFIXES,
    get_all_imports,  # noqa: F401 - re-exported for architecture rule modules
    get_module_level_imports,  # noqa: F401 - re-exported for architecture rule modules
    module_to_path,
    observe_module,
    resolve_relative_import,
)

ADDON_DIR = Path(__file__).parent.parent.parent / "addon" / "anki_audio_quick_editor"

IMPORT_SAFE_MODULES = {
    name for name, contract in MODULE_CONTRACTS.items() if contract.layer == Layer.IMPORT_SAFE_CORE
}
UI_MODULES = {
    name for name, contract in MODULE_CONTRACTS.items() if contract.layer == Layer.UI_ADAPTER
}
SETTINGS_MODULES = {
    name for name, contract in MODULE_CONTRACTS.items() if contract.layer == Layer.SETTINGS_SHELL
}
SETTINGS_BACKEND_MODULES = {
    name for name, contract in MODULE_CONTRACTS.items() if contract.layer == Layer.SETTINGS_BACKEND
}
ENTRY_POINT = {
    name for name, contract in MODULE_CONTRACTS.items() if contract.layer == Layer.ENTRY_POINT
}

ALL_LAYERS = (
    IMPORT_SAFE_MODULES | UI_MODULES | SETTINGS_MODULES | SETTINGS_BACKEND_MODULES | ENTRY_POINT
)


def _module_files(module_name: str) -> list[Path]:
    return [module_to_path(module_name)]


def _imports_anki(imports: list[str]) -> list[str]:
    return [m for m in imports if any(m == prefix or m.startswith(prefix + ".") for prefix in ANKI_PREFIXES)]


def _classify_import(resolved: str) -> str | None:
    return resolved if resolved in MODULE_CONTRACTS else None


def _imports_addon_modules(imports: list[str], forbidden: set[str], source_path: Path) -> list[str]:
    hits: list[str] = []
    for name in imports:
        if not name.startswith("."):
            continue
        resolved = resolve_relative_import(name, source_path)
        classified = _classify_import(resolved)
        if classified is not None and classified in forbidden:
            hits.append(name)
    return hits


def _get_relative_deps(filepath: Path) -> set[str]:
    return set(observe_module(filepath.relative_to(ADDON_DIR).with_suffix("").as_posix().replace("/", ".")).addon_deps)


def _get_module_relative_deps(module_name: str) -> set[str]:
    deps = set(observe_module(module_name).addon_deps)
    deps.discard(module_name)
    return {dep for dep in deps if not dep.startswith(module_name + ".")}
