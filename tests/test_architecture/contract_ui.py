"""Architecture contracts for entrypoint, browser, and settings UI modules."""

from __future__ import annotations

from .contract_schema import Layer, ModuleContract, SideEffect, contract

UI_CONTRACTS: dict[str, ModuleContract] = {
    "__init__": contract(
        "__init__",
        layer=Layer.ENTRY_POINT,
        allowed_addon_deps=(
            "_version",
            "browser_integration",
            "config_migration",
            "diagnostics_runtime",
            "editor_integration",
            "ffmpeg_defaults",
            "i18n",
            "settings",
        ),
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.ANKI_IMPORTS_MODULE_LEVEL,
            SideEffect.GUI_HOOK_REGISTRATION,
        ),
        allow_module_level_anki_imports=True,
        allow_any_anki_imports=True,
        notes="Bootstrap only: hook registration, menu wiring, and settings entrypoint.",
    ),
    "browser_integration": contract(
        "browser_integration",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "audio_state",
            "batch_operations",
            "browser_dialog",
            "browser_report",
            "diagnostics_runtime",
            "i18n",
        ),
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.MEDIA_WRITE,
            SideEffect.NOTE_UPDATE,
            SideEffect.UNDO_MERGE,
            SideEffect.GUI_HOOK_REGISTRATION,
            SideEffect.BACKGROUND_TASK_DISPATCH,
        ),
        allow_any_anki_imports=True,
    ),
    "browser_dialog": contract(
        "browser_dialog",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "audio_operations",
            "batch_operations",
            "browser_dialog_state",
            "browser_report",
            "frontend_logs",
            "i18n",
            "webview_bridge",
            "webview_shell",
        ),
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.WEB_EVAL,
        ),
        allow_any_anki_imports=True,
    ),
    "browser_dialog_state": contract(
        "browser_dialog_state",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_operation_params",
            "audio_operations",
            "audio_state",
            "batch_operations",
            "browser_report",
            "contracts_generated",
            "i18n",
        ),
    ),
    "browser_report": contract(
        "browser_report",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("batch_operations", "i18n"),
    ),
    "settings": contract(
        "settings",
        layer=Layer.SETTINGS_SHELL,
        allowed_addon_deps=("i18n", "settings.commands", "settings.initial_state", "webview_shell"),
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.ANKI_IMPORTS_MODULE_LEVEL,
            SideEffect.WEB_EVAL,
        ),
        allow_module_level_anki_imports=True,
        allow_any_anki_imports=True,
    ),
    "settings.commands": contract(
        "settings.commands",
        layer=Layer.SETTINGS_BACKEND,
        allowed_addon_deps=(
            "_version",
            "contracts_generated",
            "db_helpers",
            "diagnostics",
            "diagnostics_runtime",
            "errors",
            "ffmpeg_defaults",
            "file_reveal",
            "frontend_logs",
            "i18n",
            "support",
            "webview_bridge",
        ),
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.THREAD_SPAWN,
            SideEffect.WEB_EVAL,
            SideEffect.BACKGROUND_TASK_DISPATCH,
        ),
        allow_any_anki_imports=True,
    ),
    "settings.initial_state": contract(
        "settings.initial_state",
        layer=Layer.SETTINGS_BACKEND,
        allowed_addon_deps=("_version", "i18n", "settings_state"),
        allowed_side_effects=(SideEffect.ANKI_IMPORTS_ANYWHERE,),
        allow_any_anki_imports=True,
    ),
}
