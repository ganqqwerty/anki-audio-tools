"""Rule 5: every production Python module must be assigned to a layer."""

from .contracts import MODULE_CONTRACTS
from .inspection import list_production_modules


class TestAllModulesClassified:
    """Every .py file in the addon package must appear in a layer set."""

    def test_completeness(self) -> None:
        all_modules = set(list_production_modules())
        unclassified = all_modules - set(MODULE_CONTRACTS)
        assert unclassified == set(), (
            "Unclassified modules found — add them to "
            f"tests/test_architecture/contracts.py: {sorted(unclassified)}"
        )
