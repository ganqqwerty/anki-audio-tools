"""Rule 31: architecture graph archives mirror executable contracts."""

from __future__ import annotations

from scripts.graphs.python_modules import LAYERS, PKG, _build_python_catalog
from scripts.graphs.relationships import _build_relationships
from scripts.graphs.svelte_modules import _build_bridge_registry

from .contracts import MODULE_CONTRACTS
from .inspection import observe_all_modules


def _qualified(module_name: str) -> str:
    if module_name == "__init__":
        return PKG
    return f"{PKG}.{module_name}"


def test_graph_layers_match_executable_contracts() -> None:
    expected = {
        _qualified(module_name): contract.layer.value
        for module_name, contract in MODULE_CONTRACTS.items()
    }
    assert LAYERS == expected, (
        "Graph archive layer metadata must be derived from the executable "
        "architecture contracts. Keep tests/test_architecture/contracts.py "
        f"authoritative. Missing: {sorted(set(expected) - set(LAYERS))}; "
        f"extra: {sorted(set(LAYERS) - set(expected))}; "
        "mismatched: "
        f"{sorted((key, LAYERS[key], expected[key]) for key in set(LAYERS) & set(expected) if LAYERS[key] != expected[key])}"
    )


def test_python_graph_catalog_matches_contract_modules() -> None:
    expected = {_qualified(module_name) for module_name in MODULE_CONTRACTS}
    actual = {module["module"] for module in _build_python_catalog()}
    assert actual == expected, (
        "Python graph archive must catalog every production module with a "
        f"contract. Missing: {sorted(expected - actual)}; "
        f"extra: {sorted(actual - expected)}"
    )


def test_python_graph_import_categories_do_not_mix_anki_and_addon_imports() -> None:
    bad_imports = {
        module["module"]: module["imports"]["anki"]
        for module in _build_python_catalog()
        if any(not value.startswith(("anki", "aqt")) for value in module["imports"]["anki"])
    }
    assert bad_imports == {}, (
        "Graph archive import categories must not classify package-relative "
        f"add-on imports as Anki imports: {bad_imports}"
    )


def test_python_graph_relationships_match_observed_addon_dependencies() -> None:
    expected = {
        (_qualified(module_name), _qualified(dep))
        for module_name, observation in observe_all_modules().items()
        for dep in observation.addon_deps
    }
    relationships = _build_relationships(_build_python_catalog(), [])
    actual = {
        (relationship["source"], relationship["target"])
        for relationship in relationships
        if relationship["type"] == "python_import"
    }
    assert actual == expected, (
        "Graph archive Python relationships must mirror observed add-on "
        f"dependencies. Missing: {sorted(expected - actual)}; "
        f"extra: {sorted(actual - expected)}"
    )


def test_bridge_archive_omits_frontend_owned_playback_commands() -> None:
    commands = {entry["command"] for entry in _build_bridge_registry()}
    assert commands.isdisjoint({"aqe:play", "aqe:play-ended", "aqe:stop-playback"})
