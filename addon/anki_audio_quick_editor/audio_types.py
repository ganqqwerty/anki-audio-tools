"""Shared audio processing result types."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioProcessingResult:
    """Rendered audio metadata."""

    output_path: Path
    command: tuple[str, ...]
    duration_ms: int | None = None
    artifact_manifest_path: Path | None = None


@dataclass(frozen=True)
class RegionDeletePlan:
    """Filter plan for deleting one region from a clip timeline."""

    selection_start_ms: int
    selection_end_ms: int
    duration_ms: int
    filter_complex: str

    @property
    def removed_duration_ms(self) -> int:
        """Return the selected duration removed by this plan."""
        return self.selection_end_ms - self.selection_start_ms

    @property
    def expected_duration_ms(self) -> int:
        """Return the approximate output duration before encoder tolerance."""
        return self.duration_ms - self.removed_duration_ms


@dataclass(frozen=True)
class RegionKeepPlan:
    """Filter plan for keeping one selected region from a clip timeline."""

    selection_start_ms: int
    selection_end_ms: int
    duration_ms: int
    filter_complex: str

    @property
    def kept_duration_ms(self) -> int:
        """Return the selected duration kept by this plan."""
        return self.selection_end_ms - self.selection_start_ms

    @property
    def removed_duration_ms(self) -> int:
        """Return the approximate duration removed by this plan."""
        return self.duration_ms - self.kept_duration_ms

    @property
    def expected_duration_ms(self) -> int:
        """Return the approximate output duration before encoder tolerance."""
        return self.kept_duration_ms
