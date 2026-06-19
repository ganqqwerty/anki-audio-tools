"""Architecture contracts for batch operation modules."""

from __future__ import annotations

from .contract_schema import Layer, ModuleContract, SideEffect, contract

AUDIO_BATCH_CONTRACTS: dict[str, ModuleContract] = {
    "batch_operations": contract(
        "batch_operations",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_operations",
            "audio_processor",
            "audio_state",
            "batch_operation_processing",
            "batch_operation_types",
            "batch_operations_helpers",
            "batch_processing_presets",
            "diagnostics_runtime",
            "error_codes",
            "errors",
            "media_paths",
            "prosody_cache",
            "sound_refs",
        ),
    ),
    "batch_processing_presets": contract(
        "batch_processing_presets",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_processing_preset_runner",
            "audio_state",
            "batch_operation_processing",
            "batch_operation_types",
            "batch_operations_helpers",
            "diagnostics_runtime",
            "error_codes",
            "permission_guidance",
            "sound_refs",
        ),
        allowed_side_effects=(SideEffect.TEMP_FILESYSTEM_CLEANUP,),
    ),
    "batch_operation_processing": contract(
        "batch_operation_processing",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_formats",
            "audio_operation_params",
            "audio_operations",
            "audio_processing_preset_runner",
            "audio_processor",
            "audio_state",
            "batch_operation_types",
            "batch_operations",
            "batch_operations_helpers",
            "diagnostics_runtime",
            "error_codes",
            "errors",
            "permission_guidance",
            "prosody_svg",
            "sound_refs",
        ),
        allowed_side_effects=(SideEffect.TEMP_FILESYSTEM_CLEANUP,),
    ),
    "batch_operation_types": contract(
        "batch_operation_types",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_operation_params", "audio_operations", "audio_processing_presets"),
    ),
    "batch_operations_helpers": contract(
        "batch_operations_helpers",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_processor", "audio_state", "audio_types", "batch_operation_types", "batch_operations"),
    ),
}
