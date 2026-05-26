"""Import-safe batch operation data contracts."""

from __future__ import annotations

from dataclasses import dataclass, field

from .audio_operation_params import AudioOperationParameters
from .audio_operations import requires_target_field, validate_operation


@dataclass(frozen=True)
class BatchRunRequest:
    """One validated batch operation request selected by the Browser UI."""

    operation: str
    source_field: str
    target_field: str | None = None
    parameters: AudioOperationParameters = field(default_factory=AudioOperationParameters)

    def __post_init__(self) -> None:
        operation = validate_operation(self.operation)
        object.__setattr__(self, "operation", operation)
        if not self.source_field:
            raise ValueError("Choose a source field before starting.")
        if requires_target_field(operation) and not self.target_field:
            raise ValueError("Choose a target field before starting.")


@dataclass(frozen=True)
class BatchNoteSnapshot:
    """Minimal note data needed by import-safe batch logic."""

    note_id: int
    notetype_name: str
    fields: dict[str, str]


@dataclass(frozen=True)
class FieldGroup:
    """Fields available on one note type in the current batch selection."""

    notetype_name: str
    fields: tuple[str, ...]


@dataclass(frozen=True)
class BatchNoteResult:
    """Outcome of processing one note snapshot."""

    note_id: int
    status: str
    message: str
    target_field: str | None = None
    target_html: str | None = None
    audio_filename: str | None = None
    image_filename: str | None = None
    written_filename: str | None = None

    @property
    def written(self) -> bool:
        """Return true when the caller should persist ``target_html``."""
        return self.status == "written"

    @property
    def failure(self) -> bool:
        """Return true when this result should increment the failure count."""
        return self.status == "failed"
