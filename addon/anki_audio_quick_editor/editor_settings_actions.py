"""Settings and file-reveal actions for the editor bridge."""

from __future__ import annotations

from typing import Any, Callable

from .editor_runtime import SettingsLifecycleCallbacks
from .editor_session import PendingEditorStatus
from .file_reveal import open_external_url as open_url
from .file_reveal import reveal_file
from .i18n import t

SettingsOpener = Callable[[SettingsLifecycleCallbacks | None], None]


def open_settings_from_editor(editor: Any, settings_opener: SettingsOpener | None, deps: Any) -> None:
    """Open add-on settings from the editor toolbar command."""
    if settings_opener is None:
        deps.eval_status(editor, t("editor.status.settings_unavailable"), kind="error")
        return

    saved = False
    closed_message = t("editor.status.settings_closed")

    def _after_saved() -> None:
        nonlocal saved
        saved = True
        refresh_editor_after_settings_save(
            editor,
            deps,
            status_after_reload=closed_message,
        )

    def _after_closed() -> None:
        if saved:
            return
        deps.eval_status(editor, closed_message)

    settings_opener(SettingsLifecycleCallbacks(on_closed=_after_closed, on_saved=_after_saved))
    deps.eval_status(editor, t("editor.status.settings_opened"))


def refresh_editor_after_settings_save(editor: Any, deps: Any, status_after_reload: str = "") -> None:
    """Reload editor controls after settings are saved."""
    field_index = deps.current_field_index(editor)
    session = deps.sessions.get(editor)
    if session is not None:
        session.analysis_generation += 1
        deps.stop_session_playback(session)
        session.processing = False
        session.analysis_busy = False
        session.playback_active = False
        session.playback_paused = False
        session.playback_preparing = False
        if status_after_reload:
            session.pending_status = PendingEditorStatus(field_index, message=status_after_reload)
    deps.dispose_editor_frontend_controls(editor)
    editor.loadNote(focusTo=field_index)
    if session is not None:
        session.pending_status = None


def show_current_audio_file(editor: Any, deps: Any) -> None:
    """Reveal the current audio file in the platform file manager."""
    session, media_path = deps.current_media_path(editor)
    if deps.is_busy(session):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    reveal_file(media_path)
    deps.eval_status(editor, t("editor.status.showing_in_folder", {"filename": media_path.name}))


def open_external_url(url: str) -> None:
    """Open a trusted external URL from the editor webview."""
    open_url(url)
