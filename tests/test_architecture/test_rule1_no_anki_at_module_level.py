"""Rule 1: import-safe modules must not import aqt/anki at module level."""

from .contracts import MODULE_CONTRACTS, Layer
from .inspection import observe_all_modules


def test_all_import_safe_modules_avoid_module_level_anki_imports() -> None:
    observations = observe_all_modules()
    for module_name, contract in MODULE_CONTRACTS.items():
        if contract.layer != Layer.IMPORT_SAFE_CORE:
            continue
        assert observations[module_name].module_level_anki_imports == frozenset(), module_name
