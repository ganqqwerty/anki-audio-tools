"""Rule 14: batch adapters stay thin and persistence stays in UI adapters."""

from __future__ import annotations

import re

from .conftest import ADDON_DIR, _imports_addon_modules, get_all_imports
from .contracts import MODULE_CONTRACTS, SideEffect

BROWSER_INTEGRATION = ADDON_DIR / "browser_integration.py"
BROWSER_DIALOG = ADDON_DIR / "browser_dialog.py"
ALLOWED_PERSISTENCE_FILES = {
    "browser_integration.py",
    "editor_integration.py",
    "editor_processing.py",
    "editor_region_delete.py",
}
PERSISTENCE_PATTERNS = [
    r"\.media\.write_data\(",
    r"\.update_note\(",
    r"\.merge_undo_entries\(",
]


def test_browser_operation_selector_is_driven_by_shared_registry() -> None:
    text = BROWSER_DIALOG.read_text(encoding="utf-8")

    for symbol in ("BATCH_OPERATIONS", "OPERATION_LABELS", "OP_GRAPH", "requires_target_field"):
        assert symbol in text
    assert "for operation in BATCH_OPERATIONS:" in text
    assert "OPERATION_LABELS[operation]" in text
    for literal in (
        "remove_pauses",
        "slower",
        "faster",
        "volume_down",
        "volume_up",
    ):
        assert f'"{literal}"' not in text
        assert f"'{literal}'" not in text


def test_browser_integration_avoids_low_level_transform_mechanics_modules() -> None:
    forbidden = {
        "audio_processor",
        "prosody_cache",
        "prosody_svg",
        "sound_refs",
    }
    hits = _imports_addon_modules(get_all_imports(BROWSER_INTEGRATION), forbidden, BROWSER_INTEGRATION)
    assert hits == []

    text = BROWSER_INTEGRATION.read_text(encoding="utf-8")
    assert "AudioEditState" not in text
    assert "render_audio(" not in text
    assert "replace_sound_reference(" not in text


def test_direct_media_and_note_persistence_are_isolated_to_ui_adapters() -> None:
    violations: list[str] = []
    for path in ADDON_DIR.rglob("*.py"):
        if path.name == "__init__.py" and path.parent.name == "vendor":
            continue
        if "__pycache__" in path.parts or path.name in ALLOWED_PERSISTENCE_FILES:
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.strip().startswith("#"):
                continue
            if any(re.search(pattern, line) for pattern in PERSISTENCE_PATTERNS):
                relative = path.relative_to(ADDON_DIR)
                violations.append(f"{relative}:{line_no}: {line.strip()}")

    assert violations == [], "\n".join(violations)
    assert MODULE_CONTRACTS["browser_integration"].allowed_side_effects >= frozenset(
        {SideEffect.MEDIA_WRITE, SideEffect.NOTE_UPDATE, SideEffect.UNDO_MERGE}
    )
    assert MODULE_CONTRACTS["editor_integration"].allowed_side_effects >= frozenset({SideEffect.MEDIA_WRITE})
