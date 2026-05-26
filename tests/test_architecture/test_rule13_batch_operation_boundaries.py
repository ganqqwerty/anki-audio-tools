"""Rule 13: batch operations use the shared core, not editor bridge details."""

from __future__ import annotations

from anki_audio_quick_editor.audio_operations import (
    BATCH_OPERATIONS,
    OP_DENOISE,
    OP_GRAPH,
    TRANSFORM_OPERATIONS,
)
from anki_audio_quick_editor.editor_actions import BRIDGE_COMMAND_TO_OPERATION

from .conftest import ADDON_DIR, _imports_addon_modules, get_all_imports
from .contracts import MODULE_CONTRACTS


def test_batch_transform_operations_are_covered_by_editor_mapping() -> None:
    assert set(BRIDGE_COMMAND_TO_OPERATION.values()) == set(TRANSFORM_OPERATIONS) - {OP_DENOISE}
    assert OP_GRAPH in BATCH_OPERATIONS
    assert OP_DENOISE in BATCH_OPERATIONS


def test_batch_core_modules_avoid_editor_bridge_strings() -> None:
    for relative in ("audio_operations.py", "batch_operations.py"):
        text = (ADDON_DIR / relative).read_text(encoding="utf-8")
        assert "aqe:" not in text, relative


def test_batch_and_editor_share_operation_parameter_helper() -> None:
    editor_text = (ADDON_DIR / "editor_actions.py").read_text(encoding="utf-8")
    batch_text = (ADDON_DIR / "batch_operation_processing.py").read_text(encoding="utf-8")

    assert "audio_operation_params" in editor_text
    assert "audio_operation_params" in batch_text


def test_browser_integration_avoids_editor_actions_module() -> None:
    path = ADDON_DIR / "browser_integration.py"
    hits = _imports_addon_modules(get_all_imports(path), {"editor_actions"}, path)
    assert hits == []
    assert MODULE_CONTRACTS["browser_integration"].allowed_addon_deps == frozenset(
        {
            "audio_state",
            "batch_operations",
            "browser_dialog",
            "browser_report",
            "diagnostics_runtime",
            "i18n",
        }
    )
