"""Processing generation guards for asynchronous editor mutations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .editor_deps_protocols import ProcessingGuardDeps


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


@dataclass(frozen=True)
class EditorProcessingGuard:
    """Identity for one async editor operation that may later mutate the note."""

    generation: int
    note_id: int | None
    field_index: int
    source_filename: str


def begin_processing_guard(
    session: Any,
    *,
    field_index: int,
    source_filename: str,
) -> EditorProcessingGuard:
    """Start a guarded editor mutation generation."""
    generation = session.processing.begin_guard()
    session.field_index = int(field_index)
    session.assert_invariants()
    return EditorProcessingGuard(
        generation=generation,
        note_id=session.note_id,
        field_index=int(field_index),
        source_filename=source_filename,
    )


def invalidate_processing_guard(session: Any) -> None:
    """Invalidate pending editor processing completions."""
    session.processing.invalidate()


def is_current_processing_guard(session: Any, guard: EditorProcessingGuard) -> bool:
    """Return whether an async processing completion still targets the same editor state."""
    return bool(
        session.processing.generation == guard.generation
        and session.note_id == guard.note_id
        and session.field_index == guard.field_index
        and session.current_filename == guard.source_filename
    )


def processing_guard_matches_editor(
    editor: Any,
    session: Any | None,
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


def clear_processing_for_stale_guard(session: Any | None, guard: EditorProcessingGuard) -> bool:
    """Clear stale processing state only when no newer processing generation exists."""
    if session is None or session.processing.generation != guard.generation:
        return False
    session.processing.active = False
    session.playback.active = False
    session.playback.paused = False
    session.processing.next_status_summary = ""
    session.pending_status = None
    session.assert_invariants()
    return True
