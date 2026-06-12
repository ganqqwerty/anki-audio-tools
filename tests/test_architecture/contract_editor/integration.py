"""Architecture contract for the editor integration entry adapter."""

from __future__ import annotations

from ..contract_schema import Layer, ModuleContract, SideEffect, contract

EDITOR_INTEGRATION_CONTRACTS: dict[str, ModuleContract] = {
    "editor_integration": contract(
        "editor_integration",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "editor_actions",
            "editor_callbacks",
            "editor_runtime",
            "editor_session",
            "editor_webview_injection",
        ),
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.GUI_HOOK_REGISTRATION,
            SideEffect.WEB_EVAL,
        ),
        allow_any_anki_imports=True,
    ),
    "editor_webview_injection": contract(
        "editor_webview_injection",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
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
