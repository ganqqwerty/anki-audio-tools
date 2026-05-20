"""Architecture contracts for audio and batch core modules."""

from __future__ import annotations

from .contract_schema import Layer, ModuleContract, SideEffect, contract

AUDIO_CONTRACTS: dict[str, ModuleContract] = {
    "audio_operations": contract(
        "audio_operations",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_state", "i18n"),
    ),
    "audio_operation_params": contract(
        "audio_operation_params",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_state", "dpdfnet_settings"),
    ),
    "audio_pipeline": contract("audio_pipeline", layer=Layer.IMPORT_SAFE_CORE),
    "audio_recording": contract(
        "audio_recording",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("errors",),
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.BACKGROUND_TASK_DISPATCH,
        ),
        allow_any_anki_imports=True,
        notes="Native recorder adapter keeps Anki/Qt imports lazy for add-on import safety.",
    ),
    "audio_artifacts": contract(
        "audio_artifacts",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_pipeline", "audio_state", "audio_tools"),
    ),
    "audio_commands": contract(
        "audio_commands",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_state", "audio_types", "errors"),
    ),
    "audio_external": contract(
        "audio_external",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_state", "audio_tools", "diagnostics_runtime", "errors"),
        allowed_side_effects=(SideEffect.SUBPROCESS_RUN,),
    ),
    "audio_noise_reduction": contract(
        "audio_noise_reduction",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_commands",
            "audio_external",
            "audio_state",
            "audio_tools",
            "audio_types",
            "errors",
            "support",
        ),
        allowed_side_effects=(SideEffect.TEMP_FILESYSTEM_CLEANUP,),
    ),
    "audio_pause_pipeline": contract(
        "audio_pause_pipeline",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_artifacts",
            "audio_commands",
            "audio_external",
            "audio_noise_reduction",
            "audio_pipeline",
            "audio_state",
            "audio_tools",
            "audio_types",
            "errors",
            "support",
        ),
    ),
    "audio_processor": contract(
        "audio_processor",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_artifacts",
            "audio_commands",
            "audio_external",
            "audio_noise_reduction",
            "audio_pause_pipeline",
            "audio_rendering",
            "audio_state",
            "audio_tools",
            "audio_types",
        ),
    ),
    "audio_rendering": contract(
        "audio_rendering",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_commands",
            "audio_external",
            "audio_pause_pipeline",
            "audio_state",
            "audio_tools",
            "audio_types",
            "errors",
        ),
        allowed_side_effects=(
            SideEffect.SUBPROCESS_RUN,
            SideEffect.TEMP_FILESYSTEM_CLEANUP,
        ),
    ),
    "audio_tools": contract(
        "audio_tools",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("errors",),
    ),
    "audio_types": contract("audio_types", layer=Layer.IMPORT_SAFE_CORE),
    "audio_state": contract(
        "audio_state",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("dpdfnet_settings", "errors"),
    ),
    "batch_operations": contract(
        "batch_operations",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_operation_params",
            "audio_operations",
            "audio_processor",
            "audio_state",
            "diagnostics_runtime",
            "errors",
            "media_paths",
            "prosody_cache",
            "prosody_svg",
            "sound_refs",
        ),
        allowed_side_effects=(SideEffect.TEMP_FILESYSTEM_CLEANUP,),
    ),
    "batch_visualization": contract(
        "batch_visualization",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_operations", "batch_operations"),
        notes="Compatibility wrapper over shared batch operations; must stay thin.",
    ),
}
