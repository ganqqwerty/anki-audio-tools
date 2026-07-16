from __future__ import annotations

import ast
from pathlib import Path

import pytest

from .contract_schema import Layer, ModuleContract, SideEffect
from .inspection import (
    ModuleObservation,
    collect_imports_from_source,
    detect_side_effects_from_source,
    validate_contracts,
)


@pytest.mark.parametrize(
    "source",
    [
        "with resource():\n    from .target import value",
        "for item in items:\n    from .target import value",
        "while ready():\n    from .target import value",
        "match value:\n    case 1:\n        from .target import value",
        "try:\n    pass\nexcept Exception:\n    from .target import value",
    ],
)
def test_import_detector_descends_through_statement_containers(source: str) -> None:
    assert ".target" in collect_imports_from_source(source, recurse_into_defs=False)


def test_import_detector_distinguishes_definition_scope() -> None:
    source = "def load():\n    from .target import value"

    assert collect_imports_from_source(source, recurse_into_defs=False) == []
    assert collect_imports_from_source(source, recurse_into_defs=True) == [".target"]


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ('import_module(".target")', ".target"),
        ('importlib.import_module(".target")', ".target"),
        ('import_module(f"{__name__}.target")', ".target"),
        ('import_module(name)', None),
    ],
)
def test_import_detector_handles_only_literal_dynamic_imports(expression: str, expected: str | None) -> None:
    imports = collect_imports_from_source(expression, recurse_into_defs=True)
    assert (expected in imports) if expected is not None else imports == []


def test_import_detector_ignores_type_checking_imports() -> None:
    source = "if TYPE_CHECKING:\n    from .typing_only import Value"
    assert collect_imports_from_source(source, recurse_into_defs=True) == []


def test_dynamic_import_inside_type_checking_guard_is_ignored() -> None:
    source = 'if typing.TYPE_CHECKING:\n    import_module(f"{__name__}.typing_only")'
    assert collect_imports_from_source(source, recurse_into_defs=True) == []


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("subprocess.run(command)", {SideEffect.SUBPROCESS_RUN}),
        ("threading.Thread(target=work)", {SideEffect.THREAD_SPAWN}),
        ("mw.taskman.run_in_background(work)", {SideEffect.BACKGROUND_TASK_DISPATCH}),
        ("# subprocess.run(command)\nmessage = 'threading.Thread(target=work)'", set()),
    ],
)
def test_side_effect_detector_uses_executable_syntax(source: str, expected: set[SideEffect]) -> None:
    assert detect_side_effects_from_source(source) == expected


def test_contract_validator_rejects_unused_dependency_permission(tmp_path: Path) -> None:
    contract = ModuleContract(
        module="source",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=frozenset({"stale_permission"}),
        allow_module_level_anki_imports=False,
        allow_any_anki_imports=False,
        forbidden_import_prefixes=(),
        allowed_side_effects=frozenset(),
    )
    observation = ModuleObservation(
        module="source",
        path=tmp_path / "source.py",
        module_level_imports=(),
        all_imports=(),
        addon_deps=frozenset(),
        module_level_anki_imports=frozenset(),
        any_anki_imports=frozenset(),
        side_effects=frozenset(),
    )

    violations = validate_contracts({"source": contract}, {"source": observation})

    assert [(item.kind, item.detail) for item in violations] == [
        ("unused_addon_deps", "stale_permission")
    ]


def test_detector_fixture_is_valid_python() -> None:
    ast.parse("match value:\n    case 1:\n        from .target import value")
