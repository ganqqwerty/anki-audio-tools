"""Rule 2: thin runtime modules keep Anki imports inside function boundaries."""

from __future__ import annotations

import tomllib

from .contracts import MODULE_CONTRACTS, Layer
from .inspection import ADDON_DIR, observe_all_modules

PYPROJECT = ADDON_DIR.parents[1] / "pyproject.toml"


def test_runtime_modules_avoid_module_level_anki_imports() -> None:
    observations = observe_all_modules()
    for module_name, contract in MODULE_CONTRACTS.items():
        if contract.layer not in {Layer.UI_ADAPTER, Layer.SETTINGS_BACKEND}:
            continue
        if contract.allow_module_level_anki_imports:
            continue
        hits = observations[module_name].module_level_anki_imports
        assert hits == frozenset(), f"{module_name} imports {sorted(hits)} at module level"


def test_import_linter_import_safe_contract_tracks_module_contracts() -> None:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    import_linter_contract = next(
        contract
        for contract in pyproject["tool"]["importlinter"]["contracts"]
        if contract["name"] == "import-safe-no-upper-layers"
    )
    expected = {
        f"anki_audio_quick_editor.{module_name}"
        for module_name, contract in MODULE_CONTRACTS.items()
        if contract.layer == Layer.IMPORT_SAFE_CORE
    }

    assert set(import_linter_contract["source_modules"]) == expected
