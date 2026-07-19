"""Shared trigger job and result types."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .batch_operation_types import BatchNoteResult
from .trigger_rules import AudioTriggerRule, first_supported_sound_filename
from .trigger_state import TriggerStateKey

TriggerEventName = Literal["add", "edit"]
TRIGGER_UPDATE_INITIATOR = object()
STALE_TRIGGER_COMPLETION_MESSAGE = "stale trigger completion"


@dataclass(frozen=True)
class TriggerJob:
    """One queued trigger execution."""

    note_id: int
    rule: AudioTriggerRule
    state_key: TriggerStateKey
    state_path: Path
    generation_token: str
    input_filename: str
    action_fingerprint: str


@dataclass(frozen=True)
class TriggerExecutionResult:
    """A trigger result plus optional Anki collection changes to publish."""

    result: BatchNoteResult
    changes: Any | None = None


def trigger_source_filename(field_html: str) -> str | None:
    """Return the supported source filename represented by trigger field HTML."""
    return first_supported_sound_filename(field_html)
