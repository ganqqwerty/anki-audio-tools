"""Rule 18: side effects are constrained by module contracts."""

from __future__ import annotations

from .contracts import MODULE_CONTRACTS
from .inspection import observe_all_modules


def test_contract_driven_side_effect_policy() -> None:
    observations = observe_all_modules()
    violations: list[str] = []
    for module_name, contract in MODULE_CONTRACTS.items():
        extras = sorted(
            side_effect.value for side_effect in (observations[module_name].side_effects - contract.allowed_side_effects)
        )
        if extras:
            violations.append(f"{module_name}: unexpected side effects {extras}")
    assert violations == [], "\n".join(violations)

