"""Rule 17: addon dependencies are constrained by module contracts."""

from __future__ import annotations

from .contracts import MODULE_CONTRACTS
from .inspection import observe_all_modules


def test_contract_driven_addon_dependency_policy() -> None:
    observations = observe_all_modules()
    violations: list[str] = []
    for module_name, contract in MODULE_CONTRACTS.items():
        extras = sorted(observations[module_name].addon_deps - contract.allowed_addon_deps)
        if extras:
            violations.append(f"{module_name}: unexpected addon deps {extras}")
    assert violations == [], "\n".join(violations)

