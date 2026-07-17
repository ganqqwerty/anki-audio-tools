"""Architecture contract for the editor integration entry adapter."""

from __future__ import annotations

from ..contract_schema import Layer, ModuleContract, SideEffect, contract

EDITOR_INTEGRATION_CONTRACTS: dict[str, ModuleContract] = {
    "editor_bridge_hooks": contract(
        "editor_bridge_hooks",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "editor_actions",
            "editor_callbacks",
            "editor_runtime",
        ),
        notes="Anki editor bridge command callback wiring.",
    ),
    "editor_integration": contract(
        "editor_integration",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "editor_bridge_hooks",
            "editor_lifecycle_bridge",
            "editor_note_load_hooks",
            "editor_runtime",
        ),
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.GUI_HOOK_REGISTRATION,
        ),
        allow_any_anki_imports=True,
    ),
    "editor_lifecycle_bridge": contract(
        "editor_lifecycle_bridge",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "contracts_generated",
            "editor_actions",
            "editor_callbacks",
            "editor_pending_intent",
            "editor_runtime",
            "errors",
            "webview_bridge",
        ),
    ),
    "editor_note_load_hooks": contract(
        "editor_note_load_hooks",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "editor_runtime",
            "editor_session",
            "editor_webview_injection",
        ),
        allowed_side_effects=(SideEffect.WEB_EVAL,),
        notes="Anki editor note-load session reset and inline control injection.",
    ),
    "editor_webview_injection": contract(
        "editor_webview_injection",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "audio_processing_presets",
            "editor_callbacks",
            "editor_history_settings",
            "editor_history_snapshot",
            "editor_media",
            "editor_persistent_undo",
            "editor_runtime",
            "editor_session",
            "editor_ui",
        ),
        notes="Shared webview script builder used by edit and reviewer surfaces.",
    ),
}
