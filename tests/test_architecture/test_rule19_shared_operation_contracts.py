"""Rule 19: shared batch-operation seams stay contract-driven and adapter-thin."""

from __future__ import annotations

from .conftest import _imports_addon_modules, get_all_imports
from .contracts import MODULE_CONTRACTS, Layer, SideEffect
from .inspection import ADDON_DIR

BROWSER_INTEGRATION = ADDON_DIR / "browser_integration.py"
BROWSER_BATCH_RUNNER = ADDON_DIR / "browser_batch_runner.py"
BROWSER_DIALOG = ADDON_DIR / "browser_dialog.py"
BROWSER_AUDIO_EXPORT_DIALOG = ADDON_DIR / "browser_audio_export_dialog.py"
BATCH_OPERATIONS = ADDON_DIR / "batch_operations.py"
PROCESSING_PRESET_RUNNER = ADDON_DIR / "audio_processing_preset_runner.py"


def test_browser_batch_adapter_uses_shared_registry_and_executor() -> None:
    dialog_text = BROWSER_DIALOG.read_text(encoding="utf-8")
    export_dialog_text = BROWSER_AUDIO_EXPORT_DIALOG.read_text(encoding="utf-8")
    integration_text = BROWSER_INTEGRATION.read_text(encoding="utf-8")
    runner_text = BROWSER_BATCH_RUNNER.read_text(encoding="utf-8")
    assert "build_batch_initial_state" in dialog_text
    assert "request_from_batch_start_payload" in dialog_text
    assert "batch_progress_payload" in dialog_text
    assert "batch_finish_payload" in dialog_text
    assert "BatchRunRequest" in dialog_text
    assert "process_note_batch_operation" not in integration_text
    assert "process_note_batch_operation" not in export_dialog_text
    assert "process_note_batch_operation" in runner_text
    assert MODULE_CONTRACTS["browser_integration"].allowed_addon_deps == frozenset(
        {
            "audio_processing_presets",
            "audio_state",
            "batch_operations",
            "browser_audio_export_dialog",
            "browser_batch_runner",
            "browser_dialog",
            "diagnostics_runtime",
            "i18n",
        }
    )
    assert MODULE_CONTRACTS["browser_batch_runner"].allowed_addon_deps == frozenset(
        {
            "audio_state",
            "batch_operations",
            "browser_result_application",
            "browser_report",
            "diagnostics_runtime",
            "error_codes",
            "i18n",
        }
    )
    assert MODULE_CONTRACTS["browser_dialog"].allowed_addon_deps == frozenset(
        {
            "audio_operations",
            "batch_operations",
            "browser_dialog_state",
            "browser_report",
            "error_codes",
            "external_links",
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
            "audio_processing_presets",
            "audio_state",
            "batch_operations",
            "browser_report",
            "contracts_generated",
            "i18n",
        }
    )
    assert MODULE_CONTRACTS["audio_operation_params"].allowed_addon_deps == frozenset(
        {
            "audio_operation_params_config",
            "audio_operation_params_normalize",
            "audio_operation_params_types",
        }
    )
    assert MODULE_CONTRACTS["batch_processing_presets"].allowed_addon_deps == frozenset(
        {
            "audio_processing_preset_runner",
            "audio_state",
            "batch_operation_processing",
            "batch_operation_types",
            "batch_operations_helpers",
            "diagnostics_runtime",
            "error_codes",
            "permission_guidance",
            "sound_refs",
        }
    )
    assert MODULE_CONTRACTS["browser_result_application"].allowed_side_effects == frozenset(
        {SideEffect.NOTE_UPDATE}
    )


def test_batch_core_stays_free_of_editor_bridge_strings() -> None:
    for path in (BATCH_OPERATIONS,):
        assert "aqe:" not in path.read_text(encoding="utf-8"), path.name


def test_processing_preset_runner_stays_adapter_driven_import_safe_core() -> None:
    forbidden = {
        "audio_processor",
        "audio_processor_rendering_portal",
        "audio_rendering",
        "batch_operation_processing",
        "batch_operations",
        "browser_batch_runner",
        "browser_integration",
        "editor_presets",
        "editor_processing",
        "prosody_svg",
        "sound_refs",
    }
    hits = _imports_addon_modules(
        get_all_imports(PROCESSING_PRESET_RUNNER),
        forbidden,
        PROCESSING_PRESET_RUNNER,
    )

    assert hits == []
    assert MODULE_CONTRACTS["audio_processing_preset_runner"].layer == Layer.IMPORT_SAFE_CORE
    assert MODULE_CONTRACTS["audio_processing_preset_runner"].allowed_side_effects == frozenset(
        {SideEffect.TEMP_FILESYSTEM_CLEANUP}
    )
    text = PROCESSING_PRESET_RUNNER.read_text(encoding="utf-8")
    assert "AudioOutputNameFactory" in text
    assert "Callable[..., str]" not in text
