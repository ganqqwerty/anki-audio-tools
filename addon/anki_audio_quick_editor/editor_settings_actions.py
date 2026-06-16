"""Settings and file-reveal actions for the editor bridge."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from .editor_reload_status import reload_editor_with_pending_status
from .editor_runtime import SettingsLifecycleCallbacks
from .editor_session import ready_learner_recording_media_path
from .error_codes import (
    AQE_FILE_REVEAL_FAILED,
    AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING,
    AQE_MEDIA_REFERENCED_AUDIO_MISSING,
    AQE_SETTINGS_INVALID_PAYLOAD,
    coded_error,
)
from .errors import AudioProcessingError, MissingMediaError
from .file_reveal import open_external_url as open_url
from .file_reveal import reveal_file
from .i18n import t

if TYPE_CHECKING:
    from .editor_deps_protocols import SettingsActionDeps

SettingsOpener = Callable[[SettingsLifecycleCallbacks | None], None]


def open_settings_from_editor(editor: Any, settings_opener: SettingsOpener | None, deps: SettingsActionDeps) -> None:
    """Open add-on settings from the editor toolbar command."""
    if settings_opener is None:
        message = t("editor.status.settings_unavailable")
        deps.eval_status(
            editor,
            coded_error(AQE_SETTINGS_INVALID_PAYLOAD, message),
            kind="error",
        )
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


def refresh_editor_after_settings_save(
    editor: Any,
    deps: SettingsActionDeps,
    status_after_reload: str = "",
) -> None:
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
    reload_editor_with_pending_status(
        editor,
        session,
        field_index,
        message=status_after_reload,
        deps=deps,
    )


def show_current_audio_file(editor: Any, deps: SettingsActionDeps) -> None:
    """Reveal the current audio file in the platform file manager."""
    try:
        session, media_path = deps.current_media_path(editor)
    except MissingMediaError as exc:
        deps.eval_status(
            editor,
            coded_error(AQE_MEDIA_REFERENCED_AUDIO_MISSING, str(exc)),
            kind="error",
        )
        return
    except AudioProcessingError as exc:
        deps.eval_status(
            editor,
            coded_error(AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING, str(exc)),
            kind="error",
        )
        return
    show_media_file(editor, session, media_path, deps)


def show_learner_recording_file(editor: Any, deps: SettingsActionDeps) -> None:
    """Reveal the latest learner recording sidecar in the platform file manager."""
    session = deps.sessions.get(editor)
    media_path = ready_learner_recording_media_path(session)
    if session is None or media_path is None:
        message = t("editor.status.referenced_audio_missing")
        deps.eval_status(editor, coded_error(AQE_MEDIA_REFERENCED_AUDIO_MISSING, message), kind="error")
        return
    show_media_file(editor, session, media_path, deps)


def show_media_file(editor: Any, session: Any, media_path: Any, deps: SettingsActionDeps) -> None:
    """Reveal an already-resolved editor media file."""
    if deps.is_busy(session):
        deps.eval_status(editor, deps.still_processing_message, kind="processing")
        return
    try:
        reveal_file(media_path)
    except MissingMediaError as exc:
        deps.eval_status(
            editor,
            coded_error(AQE_MEDIA_REFERENCED_AUDIO_MISSING, str(exc)),
            kind="error",
        )
        return
    except AudioProcessingError as exc:
        deps.eval_status(
            editor,
            coded_error(AQE_FILE_REVEAL_FAILED, str(exc)),
            kind="error",
        )
        return
    deps.eval_status(editor, t("editor.status.showing_in_folder", {"filename": media_path.name}))


def open_external_url(url: str) -> None:
    """Open a trusted external URL from the editor webview."""
    open_url(url)
