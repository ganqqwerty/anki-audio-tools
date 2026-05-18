"""Browser batch report formatting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .batch_operations import BatchNoteResult


@dataclass
class BatchRunReport:
    """Summary returned from a completed batch run."""

    total: int
    processed: int = 0
    written: int = 0
    skipped: int = 0
    failures: int = 0
    canceled: bool = False
    log_lines: list[str] = field(default_factory=list)
    changes: Any = None

    def add(self, line: str) -> None:
        """Append one human-readable log line."""
        self.log_lines.append(line)

    @property
    def summary(self) -> str:
        """Return the final user-facing summary."""
        state = "Canceled" if self.canceled else "Completed"
        return (
            f"{state}: {self.processed}/{self.total} notes processed, "
            f"{self.written} written, {self.skipped} skipped, {self.failures} failures."
        )



def format_result_line(result: BatchNoteResult) -> str:
    prefix = {
        "written": "WROTE",
        "skipped": "SKIP",
        "failed": "FAIL",
    }.get(result.status, result.status.upper())
    audio = f" ({result.audio_filename})" if result.audio_filename else ""
    return f"{prefix} note {result.note_id}{audio}: {result.message}"
