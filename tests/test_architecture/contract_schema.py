"""Schema primitives for executable architecture contracts."""

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


def contract(
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
