"""Rule 15: every production module must have an executable architecture contract."""

from __future__ import annotations

from .contracts import MODULE_CONTRACTS
from .inspection import list_production_modules


def test_all_production_modules_have_contracts() -> None:
    actual = set(list_production_modules())
    declared = set(MODULE_CONTRACTS)
    assert actual == declared, (
        "Module contract manifest drift detected. "
        f"Missing: {sorted(actual - declared)}; Extra: {sorted(declared - actual)}"
    )

