"""Rule 16: Anki import policy is enforced by module contracts."""

from __future__ import annotations

from .contracts import MODULE_CONTRACTS
from .inspection import observe_all_modules


def test_contract_driven_anki_import_policy() -> None:
    observations = observe_all_modules()
    for module_name, contract in MODULE_CONTRACTS.items():
        observation = observations[module_name]
        if not contract.allow_module_level_anki_imports:
            assert observation.module_level_anki_imports == frozenset(), (
                f"{module_name} imports {sorted(observation.module_level_anki_imports)} at module level"
            )
        if not contract.allow_any_anki_imports:
            assert observation.any_anki_imports == frozenset(), (
                f"{module_name} imports {sorted(observation.any_anki_imports)} outside its contract"
            )

