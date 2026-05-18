"""Shared editor runtime state and media helpers."""

from __future__ import annotations

import weakref
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .audio_state import AudioEditState
from .editor_media import (
    current_field_index,
    session_needs_media_reset,
    session_original_source_path,
    sound_reference_for_field,
)
from .editor_playback import cleanup_temp_playback, stop_audio_playback
from .editor_session import EditorSession
from .errors import AudioProcessingError, MissingMediaError
from .sound_refs import safe_media_basename

CURRENT_FIELD_AUDIO_MISSING = "No [sound:...] reference found in the current field."
REFERENCED_AUDIO_MISSING = "The referenced audio file was not found in Anki's media folder."
STILL_PROCESSING_MESSAGE = "Still processing. Please wait."
SettingsOpener = Callable[[Callable[[], None] | None], None]
SETTINGS_OPENER: SettingsOpener | None = None

SESSIONS: "weakref.WeakKeyDictionary[Any, EditorSession]" = weakref.WeakKeyDictionary()


def session_and_source(editor: Any) -> tuple[EditorSession, Path]:
    """Return the active session and source media path for the current editor field."""
    field_index = current_field_index(editor)
    filename, media_path = current_sound_reference(editor, field_index)
    session = SESSIONS.setdefault(editor, EditorSession())
    source_path = session_original_source_path(editor, session, field_index, filename)
    if source_path is not None:
        return session, source_path

    if not media_path.is_file():
        raise MissingMediaError(REFERENCED_AUDIO_MISSING)

    mtime = media_path.stat().st_mtime_ns
    if session_needs_media_reset(session, field_index, filename, mtime):
        reset_session_for_media(session, field_index, filename, mtime)
    return session, media_path


def current_sound_reference(editor: Any, field_index: int) -> tuple[str, Path]:
    """Return the active field's sound reference and resolved media path."""
    return sound_reference_for_field(editor, field_index)


def reset_session_for_media(
    session: EditorSession,
    field_index: int,
    filename: str,
    mtime: int,
) -> None:
    """Reset mutable session state when the current source media changes."""
    stop_session_playback(session)
    session.state = AudioEditState(source_file=filename)
    session.current_filename = filename
    session.undo_history.clear()
    session.redo_history.clear()
    session.processing = False
    session.analysis_busy = False
    session.field_index = field_index
    session.source_mtime_ns = mtime
    session.cursor_ms = 0
    session.visualized_filename = None
    session.visualized_duration_ms = None
    session.playback_active = False
    session.playback_paused = False
    session.playback_preparing = False


def current_media_path(editor: Any) -> tuple[EditorSession, Path]:
    """Return the active session and current generated/original media path."""
    session, _source_path = session_and_source(editor)
    filename = session.current_filename
    if not filename:
        raise AudioProcessingError(CURRENT_FIELD_AUDIO_MISSING)
    media_path = Path(editor.mw.col.media.dir()) / safe_media_basename(filename)
    if not media_path.is_file():
        raise MissingMediaError(REFERENCED_AUDIO_MISSING)
    return session, media_path


def is_busy(session: EditorSession) -> bool:
    """Return whether the editor session has any active async operation."""
    return (
        session.processing
        or session.analysis_busy
        or bool(session.analysis_busy_fields)
        or session.playback_preparing
    )


def config(editor: Any) -> dict[str, Any]:
    """Return the persisted add-on config for an editor instance."""
    addon_id = editor.mw.addonManager.addonFromModule(__name__)
    return editor.mw.addonManager.getConfig(addon_id) or {}


def artifact_root(editor: Any) -> Path:
    """Return the directory used for retained processing artifacts."""
    addon_id = editor.mw.addonManager.addonFromModule(__name__)
    return Path(editor.mw.addonManager.addonsFolder(addon_id)) / "aqe_artifacts"


def stop_session_playback(session: EditorSession) -> None:
    """Stop playback and clear transient playback state for an editor session."""
    session.playback_generation += 1
    session.playback_preparing = False
    session.playback_active = False
    session.playback_paused = False
    stop_audio_playback()
    cleanup_temp_playback(session)
