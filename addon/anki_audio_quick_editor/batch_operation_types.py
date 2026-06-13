"""Import-safe batch operation data contracts."""

from __future__ import annotations

from dataclasses import dataclass, field

from .audio_operation_params import AudioOperationParameters
from .audio_operations import OP_PRESET, requires_target_field, validate_operation
from .audio_processing_presets import AudioProcessingPreset


@dataclass(frozen=True)
class BatchRunRequest:
    """One validated batch operation request selected by the Browser UI."""

    operation: str
    source_field: str
    target_field: str | None = None
    parameters: AudioOperationParameters = field(default_factory=AudioOperationParameters)
    preset_id: str | None = None
    audio_target_field: str | None = None
    graph_target_field: str | None = None
    preset: AudioProcessingPreset | None = None

    def __post_init__(self) -> None:
        operation = _validated_batch_operation(self.operation)
        object.__setattr__(self, "operation", operation)
        _validate_batch_request(self)


def _validated_batch_operation(operation: str) -> str:
    if operation == OP_PRESET:
        return OP_PRESET
    return validate_operation(operation)


def _validate_batch_request(request: BatchRunRequest) -> None:
    if not request.source_field:
        raise ValueError("Choose a source field before starting.")
    if request.operation == OP_PRESET:
        _validate_preset_request(request)
        return
    if requires_target_field(request.operation) and not request.target_field:
        raise ValueError("Choose a target field before starting.")


def _validate_preset_request(request: BatchRunRequest) -> None:
    if not request.preset_id:
        raise ValueError("Choose a preset before starting.")
    if request.preset is None:
        raise ValueError("Selected preset is unavailable.")
    if request.preset.has_transforms and not request.audio_target_field:
        raise ValueError("Choose an audio target field before starting.")
    if request.preset.graph.enabled and not request.graph_target_field:
        raise ValueError("Choose a graph target field before starting.")


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
    original_target_html: str | None = None
    field_updates: dict[str, str] | None = None
    original_field_html: dict[str, str] | None = None

    @property
    def written(self) -> bool:
        """Return true when the caller should persist ``target_html``."""
        return self.status == "written"

    @property
    def failure(self) -> bool:
        """Return true when this result should increment the failure count."""
        return self.status == "failed"
