"""Rule 17: addon dependencies are constrained by module contracts."""

from __future__ import annotations

from .inspection import validate_contracts


def test_contract_driven_addon_dependency_policy() -> None:
    dependency_kinds = {"addon_deps", "unused_addon_deps", "forbidden_import_prefix"}
    violations = [
        violation
        for violation in validate_contracts()
        if violation.kind in dependency_kinds
    ]
    assert violations == [], "\n".join(
        f"{violation.module}: {violation.kind}: {violation.detail}"
        for violation in violations
    )
