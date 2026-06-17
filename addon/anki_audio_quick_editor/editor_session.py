"""Editor session state for inline audio editing."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from .audio_state import (
    AudioEditState,
)
from .editor_history_settings import (
    DEFAULT_EDITOR_HISTORY_SIZE,
    normalize_editor_history_size,
)

if TYPE_CHECKING:
    from .editor_deps_protocols import ProcessingGuardDeps

RegionDeleteOperation = Literal["delete-selection", "delete-rest"]
LearnerRecordingStatus = Literal["idle", "recording", "stopping", "analyzing", "ready", "failed"]
LearnerPlaybackStatus = Literal["stopped", "playing", "paused"]


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
    start_cursor_ms: int = 0
    recording_started_at_monotonic: float | None = None
    recording_duration_ms: int | None = None
    playback_status: LearnerPlaybackStatus = "stopped"
    playback_position_ms: int = 0
    playback_started_at_monotonic: float | None = None
    playback_generation: int = 0
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
    max_entries: int = DEFAULT_EDITOR_HISTORY_SIZE

    def set_max_entries(self, value: object) -> None:
        """Apply a new stack limit and prune oldest entries."""
        self.max_entries = normalize_editor_history_size(value)
        self._prune()

    def push(
        self,
        state: AudioEditState | None,
        filename: str | None,
        status_summary: str = "",
    ) -> None:
        """Remember the current generated/reference state before rendering."""
        if state is not None and filename:
            self.entries.append(UndoEntry(state, filename, status_summary=status_summary))
            self._prune()

    def pop(self) -> UndoEntry | None:
        """Return the previous state to restore, if one exists."""
        return self.entries.pop() if self.entries else None

    def clear(self) -> None:
        """Drop history when switching fields or source media."""
        self.entries.clear()

    def _prune(self) -> None:
        overflow = len(self.entries) - self.max_entries
        if overflow > 0:
            del self.entries[:overflow]


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
class ProcessingState:
    active: bool = False
    generation: int = 0
    next_status_summary: str = ""

    def begin_guard(self) -> int:
        self.generation += 1
        return self.generation

    def invalidate(self) -> None:
        self.generation += 1

    def reset_generation(self) -> None:
        self.generation += 1


@dataclass
class PlaybackState:
    active: bool = False
    paused: bool = False
    preparing: bool = False
    generation: int = 0
    temp_path: Path | None = None
    preserve_status: bool = False

    def stop(self) -> None:
        """Stop playback and bump generation."""
        self.generation += 1
        self.preparing = False
        self.active = False
        self.paused = False
        self.preserve_status = False


@dataclass
class AnalysisState:
    busy: bool = False
    busy_fields: set[int] = field(default_factory=set)
    generation: int = 0
    generations_by_field: dict[int, int] = field(default_factory=dict)
    graph_active_fields: set[int] = field(default_factory=set)

    def begin_field(self, field_index: int) -> int:
        self.generation += 1
        self.generations_by_field[field_index] = self.generation
        self.busy_fields.add(field_index)
        self.busy = True
        self.graph_active_fields.add(field_index)
        return self.generation

    def end_field(self, field_index: int) -> None:
        self.busy_fields.discard(field_index)
        self.generations_by_field.pop(field_index, None)
        self.busy = bool(self.busy_fields)

    def cancel_all(self) -> None:
        self.generation += 1
        self.generations_by_field.clear()
        self.busy_fields.clear()
        self.busy = False

    def reset(self) -> None:
        self.generation += 1
        self.busy = False
        self.busy_fields.clear()
        self.generations_by_field.clear()
        self.graph_active_fields.clear()


@dataclass
class GraphVisualizationState:
    visualized_filename: str | None = None
    visualized_duration_ms: int | None = None
    filenames_by_field: dict[int, str] = field(default_factory=dict)
    durations_by_field: dict[int, int] = field(default_factory=dict)

    def clear_field(self, field_index: int | None) -> bool:
        needs_redraw = (
            field_index is not None
            and (field_index in self.filenames_by_field or self.visualized_filename is not None)
        )
        if needs_redraw and field_index is not None:
            self.visualized_filename = None
            self.visualized_duration_ms = None
            self.filenames_by_field.pop(field_index, None)
            self.durations_by_field.pop(field_index, None)
        return needs_redraw

    def reset(self) -> None:
        self.visualized_filename = None
        self.visualized_duration_ms = None
        self.filenames_by_field.clear()
        self.durations_by_field.clear()


@dataclass
class PostEditPlaybackState:
    generation: int = 0
    pending_field_index: int | None = None
    pending_generation: int | None = None
    pending_requires_graph_redraw: bool = False
    pending_source_filename: str | None = None

    def bump(self) -> None:
        self.generation += 1

    def reset(self) -> None:
        self.generation += 1
        self.pending_field_index = None
        self.pending_generation = None
        self.pending_requires_graph_redraw = False
        self.pending_source_filename = None


@dataclass
class EditorSession:
    """Mutable edit session for a single editor instance."""

    note_id: int | None = None
    state: AudioEditState | None = None
    field_index: int | None = None
    current_filename: str | None = None
    source_mtime_ns: int | None = None
    cursor_ms: int = 0
    undo_history: UndoHistory = field(default_factory=UndoHistory)
    redo_history: UndoHistory = field(default_factory=UndoHistory)
    processing: ProcessingState = field(default_factory=ProcessingState)
    analysis: AnalysisState = field(default_factory=AnalysisState)
    graph: GraphVisualizationState = field(default_factory=GraphVisualizationState)
    playback: PlaybackState = field(default_factory=PlaybackState)
    post_edit_playback: PostEditPlaybackState = field(default_factory=PostEditPlaybackState)
    status_summary: str = ""
    pending_status: PendingEditorStatus | None = None
    learner_recording: LearnerRecordingState = field(default_factory=LearnerRecordingState)
    learner_recording_controller: Any | None = None

    def _assert_invariants(self) -> None:
        """Debug-only cross-domain invariant checks. No-op with python -O."""
        if not __debug__:
            return
        assert not (self.processing.active and self.playback.active), \
            "X1 violated: processing and playback cannot both be active"
        assert not (self.processing.active and self.playback.paused), \
            "X1 violated: processing and playback-paused cannot both be active"
        assert self.analysis.busy == bool(self.analysis.busy_fields), \
            "D1 violated: analysis_busy must match busy_fields membership"

    def apply_edit_result(
        self,
        new_state: AudioEditState,
        new_filename: str,
        new_status_summary: str,
        *,
        update_source_mtime: bool = False,
        new_source_mtime: int | None = None,
        clear_visualization: bool = False,
    ) -> bool:
        """Apply a completed edit result. Enforces push-before-overwrite (X4),
        redo-clear-on-new-edit (X5), playback-clear-on-processing (X1),
        and post-edit generation bump (X6). Returns whether graph needs redraw."""
        self.undo_history.push(self.state, self.current_filename, self.status_summary)
        self.redo_history.clear()
        self.state = new_state
        self.current_filename = new_filename
        self.status_summary = new_status_summary
        self.processing.next_status_summary = ""
        self.processing.active = False
        self.cursor_ms = 0
        self.playback.active = False
        self.playback.paused = False
        self.post_edit_playback.bump()
        if update_source_mtime:
            self.source_mtime_ns = new_source_mtime
        needs_redraw = (
            self.field_index in self.analysis.graph_active_fields
            or self.graph.visualized_filename is not None
        )
        if clear_visualization:
            self.graph.clear_field(self.field_index)
        self._assert_invariants()
        return needs_redraw


def reset_for_note_load(session: EditorSession, note_id: int | None) -> bool:
    """Reset note-specific session state when the editor changes notes."""
    if session.note_id == note_id:
        session._assert_invariants()
        return False
    session.analysis.reset()
    session.processing.reset_generation()
    session.processing.next_status_summary = ""
    session.note_id = note_id
    session.state = None
    session.field_index = None
    session.current_filename = None
    session.undo_history.clear()
    session.redo_history.clear()
    session.processing.active = False
    session.source_mtime_ns = None
    session.cursor_ms = 0
    session.graph.reset()
    session.playback.active = False
    session.playback.paused = False
    session.playback.preparing = False
    session.playback.preserve_status = False
    session.post_edit_playback.reset()
    session.status_summary = ""
    session.pending_status = None
    clear_learner_recording_state(session)
    session._assert_invariants()
    return True


def begin_processing_guard(
    session: EditorSession,
    *,
    field_index: int,
    source_filename: str,
) -> EditorProcessingGuard:
    """Start a guarded editor mutation generation."""
    generation = session.processing.begin_guard()
    session.field_index = int(field_index)
    session._assert_invariants()
    return EditorProcessingGuard(
        generation=generation,
        note_id=session.note_id,
        field_index=int(field_index),
        source_filename=source_filename,
    )


def invalidate_processing_guard(session: EditorSession) -> None:
    """Invalidate pending editor processing completions."""
    session.processing.invalidate()


def is_current_processing_guard(session: EditorSession, guard: EditorProcessingGuard) -> bool:
    """Return whether an async processing completion still targets the same editor state."""
    return (
        session.processing.generation == guard.generation
        and session.note_id == guard.note_id
        and session.field_index == guard.field_index
        and session.current_filename == guard.source_filename
    )


def processing_guard_matches_editor(
    editor: Any,
    session: EditorSession | None,
    guard: EditorProcessingGuard,
    deps: ProcessingGuardDeps,
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
    if session is None or session.processing.generation != guard.generation:
        return False
    session.processing.active = False
    session.playback.active = False
    session.playback.paused = False
    session.processing.next_status_summary = ""
    session.pending_status = None
    session._assert_invariants()
    return True


def begin_learner_recording_state(
    session: EditorSession,
    *,
    field_index: int,
    source_filename: str,
    target_duration_ms: int,
    media_filename: str,
    media_path: Path,
    start_cursor_ms: int = 0,
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
        start_cursor_ms=start_cursor_ms,
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


def reset_learner_playback_state(session: EditorSession) -> LearnerRecordingState:
    """Stop tracked learner playback without clearing the recording sidecar."""
    state = session.learner_recording
    if (
        state.playback_status == "stopped"
        and state.playback_position_ms == 0
        and state.playback_started_at_monotonic is None
    ):
        return state
    next_state = replace(
        state,
        playback_status="stopped",
        playback_position_ms=0,
        playback_started_at_monotonic=None,
        playback_generation=state.playback_generation + 1,
    )
    session.learner_recording = next_state
    return next_state


def ready_learner_recording_media_path(session: EditorSession | None) -> Path | None:
    """Return the ready learner recording media path when its sidecar still exists."""
    if session is None:
        return None
    state = session.learner_recording
    media_path = state.media_path
    if state.status != "ready" or media_path is None or not media_path.is_file():
        return None
    return media_path


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
