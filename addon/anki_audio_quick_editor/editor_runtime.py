"""Shared editor runtime state and media helpers."""

from __future__ import annotations

import weakref
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .audio_recording import RecordingCancelReason
from .audio_state import AudioEditState
from .editor_media import (
    current_field_index,
    session_needs_media_reset,
    session_original_source_path,
    sound_reference_for_field,
)
from .editor_recording_state import (
    clear_recorder_projection,
)
from .editor_session import (
    EditorSession,
)
from .editor_session_state import BackendMediaTarget
from .editor_status import original_audio_status_summary
from .errors import AudioProcessingError, MissingMediaError
from .i18n import t
from .media_paths import existing_media_file_path, media_filenames_match
from .recorder.runtime import RECORDER_SERVICE as _RECORDER_SERVICE

RECORDER_SERVICE = _RECORDER_SERVICE

CURRENT_FIELD_AUDIO_MISSING = t("editor.status.current_field_audio_missing")
REFERENCED_AUDIO_MISSING = t("editor.status.referenced_audio_missing")
STILL_PROCESSING_MESSAGE = t("editor.status.still_processing")


@dataclass(frozen=True)
class SettingsLifecycleCallbacks:
    """Optional settings lifecycle hooks for editor-owned dialogs."""

    on_closed: Callable[[], None] | None = None
    on_saved: Callable[[], None] | None = None


SettingsOpener = Callable[[SettingsLifecycleCallbacks | None], None]
SETTINGS_OPENER: SettingsOpener | None = None

SESSIONS: "weakref.WeakKeyDictionary[Any, EditorSession]" = weakref.WeakKeyDictionary()


def session_and_source(editor: Any) -> tuple[EditorSession, Path]:
    """Return the active session and source media path for the current editor field."""
    field_index = current_field_index(editor)
    filename, _candidate_path = current_sound_reference(editor, field_index)
    session = SESSIONS.setdefault(editor, EditorSession())
    source_path = session_original_source_path(editor, session, field_index, filename)
    if source_path is not None:
        return session, source_path

    existing_path = existing_media_file_path(Path(editor.mw.col.media.dir()), filename)
    if existing_path is None:
        raise MissingMediaError(REFERENCED_AUDIO_MISSING)

    mtime = existing_path.stat().st_mtime_ns
    if session_needs_media_reset(session, field_index, filename, mtime):
        reset_session_for_media(session, field_index, filename, mtime)
    return session, existing_path


def current_sound_reference(editor: Any, field_index: int) -> tuple[str, Path]:
    """Return the active field's sound reference and resolved media path."""
    return sound_reference_for_field(editor, field_index)


def bind_backend_media_target(
    editor: Any,
    session: EditorSession,
    field_index: int,
    expected_filename: str | None = None,
) -> BackendMediaTarget | None:
    """Revalidate and bind one note field as a backend media mutation target."""
    filename, _candidate_path = current_sound_reference(editor, field_index)
    if expected_filename is not None and not media_filenames_match(filename, expected_filename):
        return None
    existing_path = existing_media_file_path(Path(editor.mw.col.media.dir()), filename)
    if existing_path is None:
        return None
    return session.bind_backend_media_target(
        field_index,
        filename,
        existing_path.stat().st_mtime_ns,
    )


def reset_session_for_media(
    session: EditorSession,
    field_index: int,
    filename: str,
    mtime: int,
) -> None:
    """Reset mutable session state when the current source media changes."""
    RECORDER_SERVICE.clear_owner(session.editor_session_id, "source_replaced")
    session.bind_backend_media_target(field_index, filename, mtime)
    session.state = AudioEditState(source_file=filename)
    session.current_filename = filename
    session.undo_history.clear()
    session.redo_history.clear()
    session.finish_processing_without_edit(clear_pending_status=True)
    session.analysis.busy = False
    session.field_index = field_index
    session.source_mtime_ns = mtime
    session.cursor_ms = 0
    session.graph.visualized_filename = None
    session.graph.visualized_duration_ms = None
    session.pending_editor_intent = None
    session.status_summary = original_audio_status_summary()
    clear_recorder_projection(session)


def dispose_editor_session(
    editor: Any,
    *,
    reason: RecordingCancelReason = "editor_closed",
) -> None:
    """Dispose external resources owned by one editor session before removal."""
    session = SESSIONS.get(editor)
    if session is None:
        return
    RECORDER_SERVICE.clear_owner(session.editor_session_id, reason)
    clear_recorder_projection(session)
    try:
        del SESSIONS[editor]
    except KeyError:
        pass


def dispose_all_editor_sessions(*, reason: RecordingCancelReason) -> None:
    """Dispose external resources for every live editor session."""
    for editor in list(SESSIONS.keys()):
        dispose_editor_session(editor, reason=reason)
    RECORDER_SERVICE.dispose(reason)


def current_media_path(editor: Any) -> tuple[EditorSession, Path]:
    """Return the active session and current generated/original media path."""
    session, _source_path = session_and_source(editor)
    filename = session.current_filename
    if not filename:
        raise AudioProcessingError(CURRENT_FIELD_AUDIO_MISSING)
    media_path = existing_media_file_path(Path(editor.mw.col.media.dir()), filename)
    if media_path is None:
        raise MissingMediaError(REFERENCED_AUDIO_MISSING)
    return session, media_path


def is_busy(session: EditorSession) -> bool:
    """Return whether the editor session has any active async operation."""
    return (
        RECORDER_SERVICE.is_busy
        or session.processing.active
        or session.analysis.busy
        or bool(session.analysis.busy_fields)
        or session.recorder.status in {"starting", "recording", "stopping", "finalizing", "analyzing"}
    )


def config(editor: Any) -> dict[str, Any]:
    """Return the persisted add-on config for an editor instance."""
    addon_id = editor.mw.addonManager.addonFromModule(__name__)
    return editor.mw.addonManager.getConfig(addon_id) or {}


def artifact_root(editor: Any) -> Path:
    """Return the directory used for retained processing artifacts."""
    addon_id = editor.mw.addonManager.addonFromModule(__name__)
    return Path(editor.mw.addonManager.addonsFolder(addon_id)) / "aqe_artifacts"
