"""Editor session state for inline audio editing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .audio_state import AudioEditState

RegionDeleteOperation = Literal["delete-selection", "delete-rest"]


@dataclass(frozen=True)
class UndoEntry:
    """A field reference and edit state that can be restored by Undo."""

    state: AudioEditState
    filename: str


@dataclass
class UndoHistory:
    """Undo stack for generated audio references."""

    entries: list[UndoEntry] = field(default_factory=list)

    def push(self, state: AudioEditState | None, filename: str | None) -> None:
        """Remember the current generated/reference state before rendering."""
        if state is not None and filename:
            self.entries.append(UndoEntry(state, filename))

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
    playback_generation: int = 0
    temp_playback_path: Path | None = None


def reset_for_note_load(session: EditorSession, note_id: int | None) -> bool:
    """Reset note-specific session state when the editor changes notes."""
    if session.note_id == note_id:
        return False
    session.analysis_generation += 1
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
    return True
