"""Architecture contract for the editor integration entry adapter."""

from __future__ import annotations

from ..contract_schema import Layer, ModuleContract, SideEffect, contract

EDITOR_INTEGRATION_CONTRACTS: dict[str, ModuleContract] = {
    "editor_integration": contract(
        "editor_integration",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "audio_processor",
            "audio_state",
            "contracts_generated",
            "editor_actions",
            "editor_analysis",
            "editor_bridge",
            "editor_callbacks",
            "editor_dependencies",
            "editor_frontend",
            "editor_history",
            "editor_media",
            "editor_playback",
            "editor_processing",
            "editor_region_delete",
            "editor_runtime",
            "editor_session",
            "editor_settings_actions",
            "editor_status",
            "editor_split_defaults",
            "editor_ui",
            "errors",
            "file_reveal",
            "media_paths",
            "prosody_cache",
            "prosody_types",
            "sound_refs",
            "support",
        ),
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.MEDIA_WRITE,
            SideEffect.THREAD_SPAWN,
            SideEffect.GUI_HOOK_REGISTRATION,
            SideEffect.WEB_EVAL,
            SideEffect.BACKGROUND_TASK_DISPATCH,
            SideEffect.TEMP_FILESYSTEM_CLEANUP,
        ),
        allow_any_anki_imports=True,
    ),
}
