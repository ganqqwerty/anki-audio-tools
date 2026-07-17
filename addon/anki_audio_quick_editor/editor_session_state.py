"""Domain sub-state objects for inline editor sessions."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BackendMediaTarget:
    """One backend-observed field source with its immutable generation identity."""

    field_index: int
    source_filename: str
    source_mtime_ns: int | None
    generation: int


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
