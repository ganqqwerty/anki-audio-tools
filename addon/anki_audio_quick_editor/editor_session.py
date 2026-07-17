"""Editor session state for inline audio editing."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count

from .audio_state import AudioEditState
from .contracts_generated import PendingEditorIntent
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
    RecorderProjection,
    RecorderProjectionStatus,
    clear_recorder_projection,
    ready_learner_recording_media_path,
)
from .editor_region_delete_request import RegionDeleteOperation, RegionDeleteRequest
from .editor_session_state import (
    AnalysisState,
    BackendMediaTarget,
    GraphVisualizationState,
)
from .editor_session_types import PendingEditorStatus, PostEditAutoplayPreference
from .recorder.model import LearnerTake
from .recorder.runtime import RECORDER_SERVICE

_EDITOR_SESSION_IDS = count(1)


@dataclass
class EditorSession:
    """Mutable edit session for a single editor instance."""

    editor_session_id: int = field(default_factory=lambda: next(_EDITOR_SESSION_IDS))
    note_id: int | None = None
    state: AudioEditState | None = None
    field_index: int | None = None
    current_filename: str | None = None
    source_mtime_ns: int | None = None
    backend_media_generation: int = 0
    backend_media_targets: dict[int, BackendMediaTarget] = field(default_factory=dict)
    cursor_ms: int = 0
    undo_history: UndoHistory = field(default_factory=UndoHistory)
    redo_history: UndoHistory = field(default_factory=UndoHistory)
    processing: ProcessingState = field(default_factory=ProcessingState)
    analysis: AnalysisState = field(default_factory=AnalysisState)
    graph: GraphVisualizationState = field(default_factory=GraphVisualizationState)
    pending_editor_intent: PendingEditorIntent | None = None
    post_edit_autoplay_by_field: dict[int, PostEditAutoplayPreference] = field(default_factory=dict)
    editor_intent_sequence: int = 0
    status_summary: str = ""
    pending_status: PendingEditorStatus | None = None
    recorder: RecorderProjection = field(default_factory=RecorderProjection)
    learner_take: LearnerTake | None = None

    def assert_invariants(self) -> None:
        """Debug-only cross-domain invariant checks. No-op with python -O."""
        if not __debug__:
            return
        assert self.analysis.busy == bool(self.analysis.busy_fields), \
            "D1 violated: analysis_busy must match busy_fields membership"
        assert all(
            field_index == target.field_index
            and target.generation <= self.backend_media_generation
            for field_index, target in self.backend_media_targets.items()
        ), "backend media targets must belong to this session generation sequence"

    def bind_backend_media_target(
        self,
        field_index: int,
        source_filename: str,
        source_mtime_ns: int | None,
        *,
        force_replacement: bool = False,
    ) -> BackendMediaTarget:
        """Bind one field source and allocate identity only for a real replacement."""
        normalized_field = int(field_index)
        existing = self.backend_media_targets.get(normalized_field)
        if (
            not force_replacement
            and existing is not None
            and existing.source_filename == source_filename
            and existing.source_mtime_ns == source_mtime_ns
        ):
            return existing
        self.backend_media_generation += 1
        target = BackendMediaTarget(
            field_index=normalized_field,
            source_filename=source_filename,
            source_mtime_ns=source_mtime_ns,
            generation=self.backend_media_generation,
        )
        self.backend_media_targets[normalized_field] = target
        self.assert_invariants()
        return target

    def backend_media_target(
        self,
        field_index: int,
        source_filename: str | None = None,
    ) -> BackendMediaTarget | None:
        """Return the current target when its optional source identity still matches."""
        target = self.backend_media_targets.get(int(field_index))
        if target is None or (
            source_filename is not None and target.source_filename != source_filename
        ):
            return None
        return target

    def backend_media_generation_for(self, field_index: int, source_filename: str) -> int:
        """Return a field target generation, with legacy-session fallback for tests."""
        target = self.backend_media_target(field_index, source_filename)
        return target.generation if target is not None else self.backend_media_generation

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
        from .errors import AudioProcessingError

        if RECORDER_SERVICE.is_busy or self.recorder.status in {
            "starting", "recording", "stopping", "finalizing", "analyzing",
        }:
            raise AudioProcessingError("Audio processing cannot start while voice recording is active.")
        if bump_post_edit_generation:
            self.pending_editor_intent = None
        if next_status_summary is not None:
            self.processing.next_status_summary = next_status_summary
        self.processing.active = True
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
    ) -> None:
        """Clear processing state for failure, no-op, stale, or reset paths."""
        self.processing.active = False
        self.processing.next_status_summary = ""
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
        backend_source_mtime_ns: int | None = None,
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
        if self.field_index is None:
            self.backend_media_generation += 1
        else:
            self.bind_backend_media_target(
                self.field_index,
                new_filename,
                (
                    backend_source_mtime_ns
                    if backend_source_mtime_ns is not None
                    else new_source_mtime if update_source_mtime else None
                ),
                force_replacement=True,
            )
        clear_recorder_projection(self)
        self.status_summary = new_status_summary
        self.finish_processing_without_edit()
        self.cursor_ms = 0
        self.pending_editor_intent = None
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
    RECORDER_SERVICE.clear_owner(session.editor_session_id, "note_changed")
    session.analysis.reset()
    session.processing.reset_generation()
    session.processing.next_status_summary = ""
    session.note_id = note_id
    session.state = None
    session.field_index = None
    session.current_filename = None
    session.backend_media_generation += 1
    session.backend_media_targets.clear()
    session.undo_history.clear()
    session.redo_history.clear()
    session.finish_processing_without_edit(clear_pending_status=True)
    session.source_mtime_ns = None
    session.cursor_ms = 0
    session.graph.reset()
    session.pending_editor_intent = None
    session.post_edit_autoplay_by_field.clear()
    session.status_summary = ""
    clear_recorder_projection(session)
    session.assert_invariants()
    return True


__all__ = [
    "AnalysisState",
    "BackendMediaTarget",
    "EditorProcessingGuard",
    "EditorSession",
    "GraphVisualizationState",
    "LearnerTake",
    "PendingEditorStatus",
    "ProcessingState",
    "RegionDeleteOperation",
    "RegionDeleteRequest",
    "UndoEntry",
    "UndoHistory",
    "begin_processing_guard",
    "clear_recorder_projection",
    "clear_processing_for_stale_guard",
    "invalidate_processing_guard",
    "is_current_processing_guard",
    "processing_guard_matches_editor",
    "ready_learner_recording_media_path",
    "reset_for_note_load",
    "RecorderProjection",
    "RecorderProjectionStatus",
]
