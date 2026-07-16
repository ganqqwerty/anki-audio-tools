from __future__ import annotations

import pytest
from pytest_classification_policy import classification_errors, inferred_primary_marker


@pytest.mark.parametrize(
    ("path", "explicit", "expected"),
    [
        ("tests/test_audio_state.py", set(), "unit"),
        ("tests/test_audio_pitch_hum_rendering_integration.py", set(), "component"),
        ("tests/test_architecture/test_rule1.py", set(), "component"),
        ("e2e/test_editor.py", set(), "e2e"),
        ("e2e/test_editor.py", {"in_anki_component"}, "in_anki_component"),
    ],
)
def test_primary_classification_is_inferred_from_execution_boundary(
    path: str, explicit: set[str], expected: str
) -> None:
    assert inferred_primary_marker(path, explicit) == expected


def test_classification_rejects_ambiguous_and_invalid_capabilities() -> None:
    errors = classification_errors(
        "e2e/test_bad.py::test_bad",
        {"unit", "e2e", "trusted_input"},
    )
    assert errors == [
        "e2e/test_bad.py::test_bad: expected one primary classification marker, "
        "got ['e2e', 'unit']"
    ]

    assert classification_errors("tests/test_bad.py", {"unit", "trusted_input"}) == [
        "tests/test_bad.py: trusted_input requires e2e"
    ]
    assert classification_errors(
        "tests/test_bad.py", {"unit", "preserve_e2e_config"}
    ) == ["tests/test_bad.py: preserve_e2e_config requires e2e"]
