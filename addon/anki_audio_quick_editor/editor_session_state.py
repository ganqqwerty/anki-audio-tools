"""Domain sub-state objects for inline editor sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


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

    def request(
        self,
        field_index: int,
        source_filename: str | None,
        *,
        require_graph_redraw: bool = False,
    ) -> None:
        self.pending_field_index = int(field_index)
        self.pending_generation = self.generation
        self.pending_requires_graph_redraw = bool(require_graph_redraw)
        self.pending_source_filename = source_filename

    def clear_pending(self) -> None:
        self.pending_field_index = None
        self.pending_generation = None
        self.pending_requires_graph_redraw = False
        self.pending_source_filename = None

    def reset(self) -> None:
        self.generation += 1
        self.clear_pending()
