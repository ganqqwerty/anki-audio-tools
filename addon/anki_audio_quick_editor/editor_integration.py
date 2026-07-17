"""Anki editor hook registration adapter."""

from __future__ import annotations

import logging
from typing import Any, Callable

from . import editor_runtime
from .editor_bridge_hooks import on_editor_did_init
from .editor_lifecycle_bridge import on_editor_lifecycle_message
from .editor_note_load_hooks import on_editor_will_load_note
from .editor_runtime import SettingsLifecycleCallbacks, dispose_all_editor_sessions

SettingsOpener = Callable[[SettingsLifecycleCallbacks | None], None]
logger = logging.getLogger(__name__)
__all__ = [
    "register_editor_hooks",
]


def on_collection_will_temporarily_close(col: Any) -> None:
    """Cancel all editor resources before Anki temporarily closes the collection."""
    logger.debug("disposing editor resources before collection close | collection_id=%s", id(col))
    dispose_all_editor_sessions(reason="collection_closed")


def on_profile_will_close() -> None:
    """Cancel all editor resources before application/profile teardown."""
    dispose_all_editor_sessions(reason="application_shutdown")


def register_editor_hooks(
    gui_hooks: Any,
    *,
    settings_opener: SettingsOpener | None = None,
) -> None:
    """Register all editor hooks used by the add-on."""
    editor_runtime.SETTINGS_OPENER = settings_opener
    gui_hooks.editor_did_init.append(on_editor_did_init)
    gui_hooks.editor_will_load_note.append(on_editor_will_load_note)
    gui_hooks.webview_did_receive_js_message.append(on_editor_lifecycle_message)
    gui_hooks.collection_will_temporarily_close.append(on_collection_will_temporarily_close)
    gui_hooks.profile_will_close.append(on_profile_will_close)
