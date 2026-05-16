"""Rule 2: thin runtime modules keep Anki imports inside function boundaries."""

from __future__ import annotations

from .contracts import MODULE_CONTRACTS, Layer
from .inspection import observe_all_modules


def test_runtime_modules_avoid_module_level_anki_imports() -> None:
    observations = observe_all_modules()
    for module_name, contract in MODULE_CONTRACTS.items():
        if contract.layer not in {Layer.UI_ADAPTER, Layer.SETTINGS_BACKEND}:
            continue
        if contract.allow_module_level_anki_imports:
            continue
        hits = observations[module_name].module_level_anki_imports
        assert hits == frozenset(), f"{module_name} imports {sorted(hits)} at module level"
