"""Import-safe data structures for Browser audio export."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

AudioExportMode = Literal["zip", "combined_mp3"]

EXPORT_MODE_ZIP: AudioExportMode = "zip"
EXPORT_MODE_COMBINED_MP3: AudioExportMode = "combined_mp3"
MAX_SILENCE_BETWEEN_CLIPS_SECONDS = 10.0


@dataclass(frozen=True)
class AudioExportFieldSelection:
    notetype_name: str
    fields: tuple[str, ...]


@dataclass(frozen=True)
class AudioExportRequest:
    mode: AudioExportMode
    destination_path: Path
    field_selections: tuple[AudioExportFieldSelection, ...]
    silence_between_clips_seconds: float = 1.0


@dataclass(frozen=True)
class AudioExportItem:
    sequence: int
    note_id: int
    notetype_name: str
    field_name: str
    field_sound_index: int
    original_filename: str
    source_path: Path


@dataclass(frozen=True)
class AudioExportNotice:
    note_id: int
    notetype_name: str
    field_name: str
    message: str
    filename: str | None = None


@dataclass(frozen=True)
class AudioExportPlan:
    items: tuple[AudioExportItem, ...]
    skipped: tuple[AudioExportNotice, ...] = ()
    failures: tuple[AudioExportNotice, ...] = ()


@dataclass
class AudioExportReport:
    total: int
    processed: int = 0
    exported: int = 0
    skipped: int = 0
    failures: int = 0
    canceled: bool = False
    output_path: str = ""
    log_lines: list[str] = field(default_factory=list)
    messages: dict[str, str] = field(default_factory=dict)

    @property
    def summary(self) -> str:
        if self.canceled:
            return self.messages.get(
                "audio_export.canceled",
                (
                    "Audio export canceled after {processed}/{total} files. "
                    "Exported: {exported}. Skipped: {skipped}. Failures: {failures}."
                ),
            ).format(
                processed=self.processed,
                total=self.total,
                exported=self.exported,
                skipped=self.skipped,
                failures=self.failures,
            )
        return self.messages.get(
            "audio_export.completed",
            (
                "Audio export completed. Exported: {exported}. "
                "Skipped: {skipped}. Failures: {failures}. Output: {output}"
            ),
        ).format(
            exported=self.exported,
            skipped=self.skipped,
            failures=self.failures,
            output=self.output_path,
        )
