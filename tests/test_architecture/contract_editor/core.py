"""Architecture contracts for import-safe editor modules."""

from __future__ import annotations

from ..contract_schema import Layer, ModuleContract, contract

CORE_EDITOR_CONTRACTS: dict[str, ModuleContract] = {
    "editor_actions": contract(
        "editor_actions",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_operation_params",
            "audio_operations",
            "audio_state",
            "contracts_generated",
            "editor_session_types",
            "external_links",
        ),
    ),
    "editor_edit_history": contract(
        "editor_edit_history",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_state", "editor_history_settings"),
    ),
    "editor_media": contract(
        "editor_media",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("editor_session", "errors", "i18n", "media_paths", "sound_refs"),
    ),
    "editor_processing_shared": contract(
        "editor_processing_shared",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("editor_history_snapshot", "editor_session"),
    ),
    "editor_history_snapshot": contract(
        "editor_history_snapshot",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "editor_edit_history",
            "editor_history_settings",
            "editor_session",
            "i18n",
        ),
    ),
    "editor_region_delete_request": contract(
        "editor_region_delete_request",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("editor_actions", "editor_session_types", "i18n", "sound_refs"),
    ),
    "editor_processing_guard": contract(
        "editor_processing_guard",
        layer=Layer.IMPORT_SAFE_CORE,
    ),
    "editor_recording_state": contract(
        "editor_recording_state",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("recorder.model",),
    ),
    "editor_pending_intent": contract(
        "editor_pending_intent",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("contracts_generated",),
    ),
    "recorder": contract(
        "recorder",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("recorder.service",),
    ),
    "recorder.model": contract(
        "recorder.model",
        layer=Layer.IMPORT_SAFE_CORE,
    ),
    "recorder.validation": contract(
        "recorder.validation",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("recorder.model",),
    ),
    "recorder.native_types": contract(
        "recorder.native_types",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("errors",),
    ),
    "recorder.service": contract(
        "recorder.service",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("recorder.model", "recorder.validation"),
    ),
    "recorder.runtime": contract(
        "recorder.runtime",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("recorder.service",),
    ),
    "editor_session_state": contract(
        "editor_session_state",
        layer=Layer.IMPORT_SAFE_CORE,
    ),
    "editor_session_types": contract(
        "editor_session_types",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("contracts_generated",),
    ),
    "editor_session": contract(
        "editor_session",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_state",
            "contracts_generated",
            "editor_edit_history",
            "editor_processing_guard",
            "editor_recording_state",
            "editor_region_delete_request",
            "editor_session_state",
            "editor_session_types",
            "errors",
            "recorder.model",
            "recorder.runtime",
        ),
    ),
    "editor_ui": contract("editor_ui", layer=Layer.IMPORT_SAFE_CORE, allowed_addon_deps=("i18n",)),
    "editor_deps_protocols": contract(
        "editor_deps_protocols",
        layer=Layer.IMPORT_SAFE_CORE,
    ),
    "editor_media_replacement": contract(
        "editor_media_replacement",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("errors", "media_paths", "sound_refs"),
    ),
}
