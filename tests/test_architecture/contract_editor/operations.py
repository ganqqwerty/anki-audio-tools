"""Architecture contracts for editor coordination modules."""

from __future__ import annotations

from ..contract_schema import Layer, ModuleContract, SideEffect, contract

EDITOR_OPERATION_CONTRACTS: dict[str, ModuleContract] = {
    "editor_analysis": contract(
        "editor_analysis",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "audio_state",
            "contracts_generated",
            "diagnostics_runtime",
            "editor_session",
            "error_codes",
            "errors",
            "i18n",
            "media_paths",
            "permission_guidance",
            "prosody_settings",
            "prosody_types",
            "sound_refs",
        ),
        allowed_side_effects=(
            SideEffect.THREAD_SPAWN,
            SideEffect.WEB_EVAL,
            SideEffect.BACKGROUND_TASK_DISPATCH,
        ),
    ),
    "editor_bridge": contract(
        "editor_bridge",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "diagnostics_runtime",
            "editor_actions",
            "error_codes",
            "errors",
            "frontend_logs",
            "i18n",
        ),
        allowed_side_effects=(SideEffect.WEB_EVAL,),
    ),
    "editor_conversion": contract(
        "editor_conversion",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "audio_formats",
            "audio_state",
            "editor_actions",
            "editor_session",
            "i18n",
        ),
        allowed_side_effects=(SideEffect.WEB_EVAL,),
    ),
    "editor_dependencies": contract(
        "editor_dependencies",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "audio_processor",
            "audio_recording",
            "editor_media",
            "editor_runtime",
            "file_sharing",
            "i18n",
            "prosody_cache",
            "support",
        ),
    ),
    "editor_history": contract(
        "editor_history",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=("editor_session", "editor_status", "errors", "i18n", "media_paths", "sound_refs"),
        allowed_side_effects=(SideEffect.WEB_EVAL,),
    ),
    "editor_runtime": contract(
        "editor_runtime",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "audio_state",
            "editor_media",
            "editor_playback",
            "editor_session",
            "editor_status",
            "errors",
            "i18n",
            "media_paths",
        ),
        allowed_side_effects=(SideEffect.TEMP_FILESYSTEM_CLEANUP,),
    ),
    "editor_settings_actions": contract(
        "editor_settings_actions",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "editor_runtime",
            "editor_session",
            "error_codes",
            "file_reveal",
            "i18n",
        ),
        allowed_side_effects=(SideEffect.WEB_EVAL,),
    ),
    "editor_status": contract(
        "editor_status",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "audio_formats",
            "audio_state",
            "dpdfnet_settings",
            "editor_actions",
            "editor_session",
            "i18n",
        ),
    ),
    "editor_split_defaults": contract(
        "editor_split_defaults",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "audio_operation_params",
            "error_codes",
            "i18n",
            "prosody_settings",
        ),
    ),
}
