"""Executable architecture contracts for production addon modules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Layer(str, Enum):
    ENTRY_POINT = "entry_point"
    UI_ADAPTER = "ui_adapter"
    SETTINGS_SHELL = "settings_shell"
    SETTINGS_BACKEND = "settings_backend"
    IMPORT_SAFE_CORE = "import_safe_core"


class SideEffect(str, Enum):
    ANKI_IMPORTS_ANYWHERE = "anki_imports_anywhere"
    ANKI_IMPORTS_MODULE_LEVEL = "anki_imports_module_level"
    MEDIA_WRITE = "media_write"
    NOTE_UPDATE = "note_update"
    UNDO_MERGE = "undo_merge"
    SUBPROCESS_RUN = "subprocess_run"
    SUBPROCESS_POPEN = "subprocess_popen"
    THREAD_SPAWN = "thread_spawn"
    DB_ACCESS = "db_access"
    GUI_HOOK_REGISTRATION = "gui_hook_registration"
    WEB_EVAL = "web_eval"
    BACKGROUND_TASK_DISPATCH = "background_task_dispatch"
    TEMP_FILESYSTEM_CLEANUP = "temp_filesystem_cleanup"


@dataclass(frozen=True)
class ModuleContract:
    """Allowed architecture surface for one production module."""

    module: str
    layer: Layer
    allowed_addon_deps: frozenset[str]
    allowed_side_effects: frozenset[SideEffect]
    forbidden_import_prefixes: tuple[str, ...] = ()
    allow_module_level_anki_imports: bool = False
    allow_any_anki_imports: bool = False
    notes: str = ""


def _contract(
    module: str,
    *,
    layer: Layer,
    allowed_addon_deps: tuple[str, ...] = (),
    allowed_side_effects: tuple[SideEffect, ...] = (),
    forbidden_import_prefixes: tuple[str, ...] = (),
    allow_module_level_anki_imports: bool = False,
    allow_any_anki_imports: bool = False,
    notes: str = "",
) -> ModuleContract:
    return ModuleContract(
        module=module,
        layer=layer,
        allowed_addon_deps=frozenset(allowed_addon_deps),
        allowed_side_effects=frozenset(allowed_side_effects),
        forbidden_import_prefixes=forbidden_import_prefixes,
        allow_module_level_anki_imports=allow_module_level_anki_imports,
        allow_any_anki_imports=allow_any_anki_imports,
        notes=notes,
    )


MODULE_CONTRACTS: dict[str, ModuleContract] = {
    "__init__": _contract(
        "__init__",
        layer=Layer.ENTRY_POINT,
        allowed_addon_deps=("_version", "browser_integration", "config_migration", "editor_integration", "settings"),
        allowed_side_effects=(SideEffect.ANKI_IMPORTS_ANYWHERE, SideEffect.ANKI_IMPORTS_MODULE_LEVEL, SideEffect.GUI_HOOK_REGISTRATION),
        allow_module_level_anki_imports=True,
        allow_any_anki_imports=True,
        notes="Bootstrap only: hook registration, menu wiring, and settings entrypoint.",
    ),
    "_version": _contract("_version", layer=Layer.IMPORT_SAFE_CORE),
    "audio_operations": _contract(
        "audio_operations",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_state",),
    ),
    "audio_processor": _contract(
        "audio_processor",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_state", "errors"),
        allowed_side_effects=(SideEffect.SUBPROCESS_RUN, SideEffect.TEMP_FILESYSTEM_CLEANUP),
    ),
    "audio_state": _contract(
        "audio_state",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("errors",),
    ),
    "batch_operations": _contract(
        "batch_operations",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_operations",
            "audio_processor",
            "audio_state",
            "errors",
            "prosody_cache",
            "prosody_svg",
            "sound_refs",
        ),
        allowed_side_effects=(SideEffect.TEMP_FILESYSTEM_CLEANUP,),
    ),
    "batch_visualization": _contract(
        "batch_visualization",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_operations", "batch_operations"),
        notes="Compatibility wrapper over shared batch operations; must stay thin.",
    ),
    "browser_integration": _contract(
        "browser_integration",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=("audio_operations", "audio_state", "batch_operations"),
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
    "config_migration": _contract("config_migration", layer=Layer.IMPORT_SAFE_CORE),
    "db_helpers": _contract(
        "db_helpers",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_side_effects=(SideEffect.DB_ACCESS,),
    ),
    "diagnostics": _contract(
        "diagnostics",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_processor",),
        allowed_side_effects=(SideEffect.SUBPROCESS_RUN,),
    ),
    "editor_actions": _contract(
        "editor_actions",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_operations", "audio_state"),
    ),
    "editor_integration": _contract(
        "editor_integration",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "audio_processor",
            "audio_state",
            "editor_actions",
            "editor_ui",
            "errors",
            "prosody_cache",
            "prosody_types",
            "sound_refs",
        ),
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.MEDIA_WRITE,
            SideEffect.SUBPROCESS_POPEN,
            SideEffect.THREAD_SPAWN,
            SideEffect.GUI_HOOK_REGISTRATION,
            SideEffect.WEB_EVAL,
            SideEffect.BACKGROUND_TASK_DISPATCH,
            SideEffect.TEMP_FILESYSTEM_CLEANUP,
        ),
        allow_any_anki_imports=True,
    ),
    "editor_ui": _contract("editor_ui", layer=Layer.IMPORT_SAFE_CORE),
    "errors": _contract("errors", layer=Layer.IMPORT_SAFE_CORE),
    "prosody_analyzer": _contract(
        "prosody_analyzer",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_state", "prosody_fallback", "prosody_praat", "prosody_types"),
    ),
    "prosody_cache": _contract(
        "prosody_cache",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_state", "prosody_analyzer", "prosody_types"),
    ),
    "prosody_fallback": _contract(
        "prosody_fallback",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_processor", "audio_state", "errors", "prosody_types"),
        allowed_side_effects=(SideEffect.SUBPROCESS_RUN,),
    ),
    "prosody_praat": _contract(
        "prosody_praat",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_processor", "audio_state", "prosody_types"),
    ),
    "prosody_svg": _contract(
        "prosody_svg",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("prosody_types",),
    ),
    "prosody_types": _contract("prosody_types", layer=Layer.IMPORT_SAFE_CORE),
    "settings": _contract(
        "settings",
        layer=Layer.SETTINGS_SHELL,
        allowed_addon_deps=("settings.commands", "settings.initial_state"),
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.ANKI_IMPORTS_MODULE_LEVEL,
            SideEffect.WEB_EVAL,
        ),
        allow_module_level_anki_imports=True,
        allow_any_anki_imports=True,
    ),
    "settings.commands": _contract(
        "settings.commands",
        layer=Layer.SETTINGS_BACKEND,
        allowed_addon_deps=("db_helpers", "diagnostics"),
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.THREAD_SPAWN,
            SideEffect.WEB_EVAL,
            SideEffect.BACKGROUND_TASK_DISPATCH,
        ),
        allow_any_anki_imports=True,
    ),
    "settings.initial_state": _contract(
        "settings.initial_state",
        layer=Layer.SETTINGS_BACKEND,
        allowed_addon_deps=("_version", "settings_state"),
        allowed_side_effects=(SideEffect.ANKI_IMPORTS_ANYWHERE,),
        allow_any_anki_imports=True,
    ),
    "settings_state": _contract("settings_state", layer=Layer.IMPORT_SAFE_CORE),
    "sound_refs": _contract(
        "sound_refs",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("errors",),
    ),
}
