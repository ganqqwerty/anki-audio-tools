"""Rule 19: shared batch-operation seams stay contract-driven and adapter-thin."""

from __future__ import annotations

from .contracts import MODULE_CONTRACTS
from .inspection import ADDON_DIR

BROWSER_INTEGRATION = ADDON_DIR / "browser_integration.py"
BROWSER_DIALOG = ADDON_DIR / "browser_dialog.py"
BATCH_OPERATIONS = ADDON_DIR / "batch_operations.py"
BATCH_VISUALIZATION = ADDON_DIR / "batch_visualization.py"


def test_browser_batch_adapter_uses_shared_registry_and_executor() -> None:
    dialog_text = BROWSER_DIALOG.read_text(encoding="utf-8")
    integration_text = BROWSER_INTEGRATION.read_text(encoding="utf-8")
    assert "build_batch_initial_state" in dialog_text
    assert "request_from_batch_start_payload" in dialog_text
    assert "batch_progress_payload" in dialog_text
    assert "batch_finish_payload" in dialog_text
    assert "BatchRunRequest" in dialog_text
    assert "process_note_batch_operation" in integration_text
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
    assert MODULE_CONTRACTS["browser_dialog"].allowed_addon_deps == frozenset(
        {
            "audio_operations",
            "batch_operations",
            "browser_dialog_state",
            "browser_report",
            "frontend_logs",
            "i18n",
            "webview_bridge",
            "webview_shell",
        }
    )
    assert MODULE_CONTRACTS["browser_dialog_state"].allowed_addon_deps == frozenset(
        {
            "audio_operation_params",
            "audio_operations",
            "audio_state",
            "batch_operations",
            "browser_report",
            "contracts_generated",
            "i18n",
        }
    )
    assert MODULE_CONTRACTS["audio_operation_params"].allowed_addon_deps == frozenset(
        {"audio_formats", "audio_state", "dpdfnet_settings"}
    )


def test_batch_core_stays_free_of_editor_bridge_strings() -> None:
    for path in (BATCH_OPERATIONS, BATCH_VISUALIZATION):
        assert "aqe:" not in path.read_text(encoding="utf-8"), path.name


def test_batch_visualization_remains_a_thin_wrapper() -> None:
    text = BATCH_VISUALIZATION.read_text(encoding="utf-8")
    assert "from .batch_operations import (" in text
    assert "process_note_batch_operation" in text
    assert "render_audio(" not in text
    assert "analyze_prosody_cached(" not in text
