"""Browser batch report formatting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .batch_operations import BatchNoteResult
from .i18n import format_message


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
    messages: Mapping[str, str] = field(default_factory=dict)

    def add(self, line: str) -> None:
        """Append one human-readable log line."""
        self.log_lines.append(line)

    @property
    def summary(self) -> str:
        """Return the final user-facing summary."""
        key = "batch.summary.canceled" if self.canceled else "batch.summary.completed"
        return format_message(
            self.messages,
            key,
            {
                "processed": self.processed,
                "total": self.total,
                "written": self.written,
                "skipped": self.skipped,
                "failures": self.failures,
            },
        )



def format_result_line(result: BatchNoteResult, messages: Mapping[str, str] | None = None) -> str:
    prefix = {
        "written": format_message(messages or {}, "batch.result.wrote"),
        "skipped": format_message(messages or {}, "batch.result.skip"),
        "failed": format_message(messages or {}, "batch.result.fail"),
    }.get(result.status, result.status.upper())
    audio = f" ({result.audio_filename})" if result.audio_filename else ""
    return format_message(
        messages or {},
        "batch.result.line",
        {
            "prefix": prefix,
            "note_id": result.note_id,
            "audio": audio,
            "message": result.message,
        },
    )
