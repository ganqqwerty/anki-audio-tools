"""Architecture contracts for import-safe editor modules."""

from __future__ import annotations

from ..contract_schema import Layer, ModuleContract, contract

CORE_EDITOR_CONTRACTS: dict[str, ModuleContract] = {
    "editor_actions": contract(
        "editor_actions",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_operation_params", "audio_operations", "audio_state"),
    ),
    "editor_media": contract(
        "editor_media",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("editor_session", "errors", "i18n", "media_paths", "sound_refs"),
    ),
    "editor_playback_bounds": contract(
        "editor_playback_bounds",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("prosody_types",),
    ),
    "editor_processing_shared": contract(
        "editor_processing_shared",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("editor_session",),
    ),
    "editor_region_delete_request": contract(
        "editor_region_delete_request",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("editor_session", "i18n", "sound_refs"),
    ),
    "editor_session": contract(
        "editor_session",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_state",),
    ),
    "editor_ui": contract("editor_ui", layer=Layer.IMPORT_SAFE_CORE, allowed_addon_deps=("i18n",)),
}
