"""Canonical pytest classification used by local and CI collection."""

from __future__ import annotations

from pathlib import PurePath

PRIMARY_MARKERS = frozenset({"unit", "component", "in_anki_component", "e2e"})


def inferred_primary_marker(path: str, explicit_markers: set[str]) -> str:
    normalized = PurePath(path).as_posix()
    if normalized.startswith("e2e/"):
        if "in_anki_component" in explicit_markers:
            return "in_anki_component"
        return "e2e"
    filename = PurePath(normalized).name
    if "integration" in filename or "/test_architecture/" in f"/{normalized}":
        return "component"
    return "unit"


def classification_errors(path: str, markers: set[str]) -> list[str]:
    errors: list[str] = []
    primary = sorted(PRIMARY_MARKERS & markers)
    if len(primary) != 1:
        errors.append(f"{path}: expected one primary classification marker, got {primary}")
    if "trusted_input" in markers and "e2e" not in markers:
        errors.append(f"{path}: trusted_input requires e2e")
    if "shared_desktop" in markers and not ({"e2e", "in_anki_component"} & markers):
        errors.append(f"{path}: shared_desktop requires an Anki workflow classification")
    if "preserve_e2e_config" in markers and "e2e" not in markers:
        errors.append(f"{path}: preserve_e2e_config requires e2e")
    return errors
