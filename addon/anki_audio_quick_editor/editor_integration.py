"""Anki editor hook registration adapter."""

from __future__ import annotations

from typing import Any, Callable

from . import editor_runtime
from .editor_actions import BRIDGE_COMMANDS
from .editor_bridge_hooks import on_editor_did_init
from .editor_note_load_hooks import on_editor_will_load_note
from .editor_runtime import SettingsLifecycleCallbacks
from .editor_session import EditorSession
from .editor_webview_injection import editor_injection_script

SettingsOpener = Callable[[SettingsLifecycleCallbacks | None], None]
__all__ = [
    "BRIDGE_COMMANDS",
    "EditorSession",
    "editor_injection_script",
    "register_editor_hooks",
]


def register_editor_hooks(
    gui_hooks: Any,
    *,
    settings_opener: SettingsOpener | None = None,
) -> None:
    """Register all editor hooks used by the add-on."""
    editor_runtime.SETTINGS_OPENER = settings_opener
    gui_hooks.editor_did_init.append(on_editor_did_init)
    gui_hooks.editor_will_load_note.append(on_editor_will_load_note)
