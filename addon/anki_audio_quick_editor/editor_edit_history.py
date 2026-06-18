"""Inline editor undo and redo stack state."""

from __future__ import annotations

from dataclasses import dataclass, field

from .audio_state import AudioEditState
from .editor_history_settings import (
    DEFAULT_EDITOR_HISTORY_SIZE,
    normalize_editor_history_size,
)


@dataclass(frozen=True)
class UndoEntry:
    """A field reference and edit state that can be restored by Undo."""

    state: AudioEditState
    filename: str
    status_summary: str = ""


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
