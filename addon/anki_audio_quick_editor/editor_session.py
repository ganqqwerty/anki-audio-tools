"""Editor session state for inline audio editing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .audio_state import AudioEditState
from .editor_edit_history import UndoEntry, UndoHistory
from .editor_processing_guard import (
    EditorProcessingGuard,
    ProcessingState,
    begin_processing_guard,
    clear_processing_for_stale_guard,
    invalidate_processing_guard,
    is_current_processing_guard,
    processing_guard_matches_editor,
)
from .editor_recording_state import (
    LearnerPlaybackStatus,
    LearnerRecordingState,
    LearnerRecordingStatus,
    begin_learner_recording_state,
    clear_learner_recording_state,
    learner_recording_is_current,
    ready_learner_recording_media_path,
    reset_learner_playback_state,
)
from .editor_region_delete_request import RegionDeleteOperation, RegionDeleteRequest
from .editor_session_state import (
    AnalysisState,
    GraphVisualizationState,
    PlaybackState,
    PostEditPlaybackState,
)
from .editor_session_types import PendingEditorStatus


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

    def assert_invariants(self) -> None:
        """Debug-only cross-domain invariant checks. No-op with python -O."""
        if not __debug__:
            return
        assert not (self.processing.active and self.playback.active), \
            "X1 violated: processing and playback cannot both be active"
        assert not (self.processing.active and self.playback.paused), \
            "X1 violated: processing and playback-paused cannot both be active"
        assert self.analysis.busy == bool(self.analysis.busy_fields), \
            "D1 violated: analysis_busy must match busy_fields membership"

    def _assert_invariants(self) -> None:
        """Compatibility wrapper for existing characterization tests."""
        self.assert_invariants()

    def begin_processing(
        self,
        *,
        field_index: int,
        source_filename: str,
        next_status_summary: str | None = None,
        bump_post_edit_generation: bool = False,
    ) -> EditorProcessingGuard:
        """Start a guarded processing operation and clear incompatible playback state."""
        if bump_post_edit_generation:
            self.post_edit_playback.bump()
        if next_status_summary is not None:
            self.processing.next_status_summary = next_status_summary
        self.processing.active = True
        self.playback.active = False
        self.playback.paused = False
        guard = begin_processing_guard(
            self,
            field_index=int(field_index),
            source_filename=source_filename,
        )
        self.assert_invariants()
        return guard

    def finish_processing_without_edit(
        self,
        *,
        clear_pending_status: bool = False,
        stop_playback: bool = True,
    ) -> None:
        """Clear processing state for failure, no-op, stale, or reset paths."""
        self.processing.active = False
        self.processing.next_status_summary = ""
        if stop_playback:
            self.playback.active = False
            self.playback.paused = False
        if clear_pending_status:
            self.pending_status = None
        self.assert_invariants()

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
        """Apply a completed edit result.

        Enforces push-before-overwrite (X4), redo-clear-on-new-edit (X5),
        playback-clear-on-processing (X1), and post-edit generation bump (X6).
        Returns whether graph needs redraw.
        """
        self.undo_history.push(self.state, self.current_filename, self.status_summary)
        self.redo_history.clear()
        self.state = new_state
        self.current_filename = new_filename
        self.status_summary = new_status_summary
        self.finish_processing_without_edit()
        self.cursor_ms = 0
        self.post_edit_playback.bump()
        if update_source_mtime:
            self.source_mtime_ns = new_source_mtime
        needs_redraw = (
            self.field_index in self.analysis.graph_active_fields
            or self.graph.visualized_filename is not None
        )
        if clear_visualization:
            self.graph.clear_field(self.field_index)
        self.assert_invariants()
        return needs_redraw


def reset_for_note_load(session: EditorSession, note_id: int | None) -> bool:
    """Reset note-specific session state when the editor changes notes."""
    if session.note_id == note_id:
        session.assert_invariants()
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
    session.finish_processing_without_edit(clear_pending_status=True)
    session.source_mtime_ns = None
    session.cursor_ms = 0
    session.graph.reset()
    session.playback.preparing = False
    session.playback.preserve_status = False
    session.post_edit_playback.reset()
    session.status_summary = ""
    clear_learner_recording_state(session)
    session.assert_invariants()
    return True


__all__ = [
    "AnalysisState",
    "EditorProcessingGuard",
    "EditorSession",
    "GraphVisualizationState",
    "LearnerPlaybackStatus",
    "LearnerRecordingState",
    "LearnerRecordingStatus",
    "PendingEditorStatus",
    "PlaybackState",
    "PostEditPlaybackState",
    "ProcessingState",
    "RegionDeleteOperation",
    "RegionDeleteRequest",
    "UndoEntry",
    "UndoHistory",
    "begin_learner_recording_state",
    "begin_processing_guard",
    "clear_learner_recording_state",
    "clear_processing_for_stale_guard",
    "invalidate_processing_guard",
    "is_current_processing_guard",
    "learner_recording_is_current",
    "processing_guard_matches_editor",
    "ready_learner_recording_media_path",
    "reset_for_note_load",
    "reset_learner_playback_state",
]
