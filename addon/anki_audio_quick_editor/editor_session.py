"""Editor session state for inline audio editing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .audio_state import AudioEditState

RegionDeleteOperation = Literal["delete-selection", "delete-rest"]
LearnerRecordingStatus = Literal["idle", "recording", "stopping", "analyzing", "ready", "failed"]


@dataclass(frozen=True)
class UndoEntry:
    """A field reference and edit state that can be restored by Undo."""

    state: AudioEditState
    filename: str
    status_summary: str = ""


@dataclass(frozen=True)
class PendingEditorStatus:
    """One status message to reapply after the editor controls remount."""

    field_index: int
    kind: str = "info"
    message: str = ""


@dataclass(frozen=True)
class LearnerRecordingState:
    """Learner recording attempt state owned by Python."""

    status: LearnerRecordingStatus = "idle"
    field_index: int | None = None
    generation: int = 0
    source_filename: str | None = None
    media_filename: str | None = None
    media_path: Path | None = None
    target_duration_ms: int | None = None
    recording_started_at_monotonic: float | None = None
    recording_duration_ms: int | None = None
    prosody_payload: dict[str, object] | None = None
    failure_message: str | None = None
    graph_settings: dict[str, object] | None = None


@dataclass(frozen=True)
class EditorProcessingGuard:
    """Identity for one async editor operation that may later mutate the note."""

    generation: int
    note_id: int | None
    field_index: int
    source_filename: str


@dataclass
class UndoHistory:
    """Undo stack for generated audio references."""

    entries: list[UndoEntry] = field(default_factory=list)

    def push(
        self,
        state: AudioEditState | None,
        filename: str | None,
        status_summary: str = "",
    ) -> None:
        """Remember the current generated/reference state before rendering."""
        if state is not None and filename:
            self.entries.append(UndoEntry(state, filename, status_summary=status_summary))

    def pop(self) -> UndoEntry | None:
        """Return the previous state to restore, if one exists."""
        return self.entries.pop() if self.entries else None

    def clear(self) -> None:
        """Drop history when switching fields or source media."""
        self.entries.clear()


@dataclass(frozen=True)
class RegionDeleteRequest:
    """Frontend request to delete or keep a selected graph region."""

    field_index: int
    source_filename: str
    selection_start_ms: int
    selection_end_ms: int
    cursor_ms: int
    duration_ms: int
    trigger: str
    playback_active: bool
    operation: RegionDeleteOperation = "delete-selection"

    @property
    def selected_duration_ms(self) -> int:
        """Return the normalized selected duration."""
        return self.selection_end_ms - self.selection_start_ms

    @property
    def removed_duration_ms(self) -> int:
        """Return the approximate duration removed by this operation."""
        if self.operation == "delete-rest":
            return self.duration_ms - self.selected_duration_ms
        return self.selected_duration_ms


@dataclass
class EditorSession:
    """Mutable edit session for a single editor instance."""

    note_id: int | None = None
    state: AudioEditState | None = None
    field_index: int | None = None
    current_filename: str | None = None
    undo_history: UndoHistory = field(default_factory=UndoHistory)
    redo_history: UndoHistory = field(default_factory=UndoHistory)
    processing: bool = False
    analysis_busy: bool = False
    analysis_busy_fields: set[int] = field(default_factory=set)
    source_mtime_ns: int | None = None
    cursor_ms: int = 0
    processing_generation: int = 0
    analysis_generation: int = 0
    analysis_generations_by_field: dict[int, int] = field(default_factory=dict)
    graph_active_fields: set[int] = field(default_factory=set)
    visualized_filename: str | None = None
    visualized_duration_ms: int | None = None
    visualized_filenames_by_field: dict[int, str] = field(default_factory=dict)
    visualized_durations_by_field: dict[int, int] = field(default_factory=dict)
    playback_active: bool = False
    playback_paused: bool = False
    playback_preparing: bool = False
    preserve_status_during_playback: bool = False
    playback_generation: int = 0
    post_edit_playback_generation: int = 0
    temp_playback_path: Path | None = None
    next_status_summary: str = ""
    status_summary: str = ""
    pending_status: PendingEditorStatus | None = None
    learner_recording: LearnerRecordingState = field(default_factory=LearnerRecordingState)
    learner_recording_controller: Any | None = None


def reset_for_note_load(session: EditorSession, note_id: int | None) -> bool:
    """Reset note-specific session state when the editor changes notes."""
    if session.note_id == note_id:
        return False
    session.analysis_generation += 1
    session.processing_generation += 1
    session.note_id = note_id
    session.state = None
    session.field_index = None
    session.current_filename = None
    session.undo_history.clear()
    session.redo_history.clear()
    session.processing = False
    session.analysis_busy = False
    session.analysis_busy_fields.clear()
    session.source_mtime_ns = None
    session.cursor_ms = 0
    session.analysis_generations_by_field.clear()
    session.graph_active_fields.clear()
    session.visualized_filename = None
    session.visualized_duration_ms = None
    session.visualized_filenames_by_field.clear()
    session.visualized_durations_by_field.clear()
    session.playback_active = False
    session.playback_paused = False
    session.playback_preparing = False
    session.preserve_status_during_playback = False
    session.post_edit_playback_generation += 1
    session.next_status_summary = ""
    session.status_summary = ""
    session.pending_status = None
    clear_learner_recording_state(session)
    return True


def begin_processing_guard(
    session: EditorSession,
    *,
    field_index: int,
    source_filename: str,
) -> EditorProcessingGuard:
    """Start a guarded editor mutation generation."""
    session.processing_generation += 1
    session.field_index = int(field_index)
    return EditorProcessingGuard(
        generation=session.processing_generation,
        note_id=session.note_id,
        field_index=int(field_index),
        source_filename=source_filename,
    )


def invalidate_processing_guard(session: EditorSession) -> None:
    """Invalidate pending editor processing completions."""
    session.processing_generation += 1


def is_current_processing_guard(session: EditorSession, guard: EditorProcessingGuard) -> bool:
    """Return whether an async processing completion still targets the same editor state."""
    return (
        session.processing_generation == guard.generation
        and session.note_id == guard.note_id
        and session.field_index == guard.field_index
        and session.current_filename == guard.source_filename
    )


def processing_guard_matches_editor(
    editor: Any,
    session: EditorSession | None,
    guard: EditorProcessingGuard,
    deps: Any,
) -> bool:
    """Return whether a guarded completion still matches session and focused field."""
    if session is None or not is_current_processing_guard(session, guard):
        return False
    current_field_index = getattr(deps, "current_field_index", None)
    if not callable(current_field_index):
        return True
    return int(current_field_index(editor)) == guard.field_index


def clear_processing_for_stale_guard(session: EditorSession | None, guard: EditorProcessingGuard) -> bool:
    """Clear stale processing state only when no newer processing generation exists."""
    if session is None or session.processing_generation != guard.generation:
        return False
    session.processing = False
    session.playback_active = False
    session.playback_paused = False
    session.next_status_summary = ""
    session.pending_status = None
    return True


def begin_learner_recording_state(
    session: EditorSession,
    *,
    field_index: int,
    source_filename: str,
    target_duration_ms: int,
    media_filename: str,
    media_path: Path,
    graph_settings: dict[str, object] | None = None,
    started_at: float | None = None,
) -> LearnerRecordingState:
    """Start a new learner recording generation."""
    generation = session.learner_recording.generation + 1
    state = LearnerRecordingState(
        status="recording",
        field_index=field_index,
        generation=generation,
        source_filename=source_filename,
        media_filename=media_filename,
        media_path=media_path,
        target_duration_ms=target_duration_ms,
        recording_started_at_monotonic=started_at,
        graph_settings=graph_settings,
    )
    session.learner_recording = state
    return state


def clear_learner_recording_state(session: EditorSession) -> LearnerRecordingState:
    """Clear learner recording state and invalidate pending callbacks."""
    state = LearnerRecordingState(generation=session.learner_recording.generation + 1)
    session.learner_recording = state
    session.learner_recording_controller = None
    return state


def learner_recording_is_current(
    session: EditorSession,
    *,
    generation: int,
    field_index: int,
    source_filename: str,
) -> bool:
    """Return whether a learner recording callback still matches the active attempt."""
    state = session.learner_recording
    return (
        state.generation == generation
        and state.field_index == field_index
        and state.source_filename == source_filename
    )
