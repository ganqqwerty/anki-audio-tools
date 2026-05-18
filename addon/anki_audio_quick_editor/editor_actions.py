"""Import-safe editor bridge commands and shared operation mapping."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .audio_operations import (
    OP_FASTER,
    OP_REMOVE_PAUSES,
    OP_SLOWER,
    OP_VOLUME_DOWN,
    OP_VOLUME_UP,
    apply_audio_operation,
)
from .audio_state import AudioEditState, AudioProcessingConfig

CMD_TRIM_LEFT = "aqe:trim-left"
CMD_TRIM_RIGHT = "aqe:trim-right"
CMD_SLOWER = "aqe:slower"
CMD_FASTER = "aqe:faster"
CMD_VOLUME_DOWN = "aqe:volume-down"
CMD_VOLUME_UP = "aqe:volume-up"
CMD_REMOVE_PAUSES = "aqe:remove-pauses"
CMD_DENOISE_STANDARD = "aqe:denoise-standard"
CMD_RNNOISE = "aqe:rnnoise"
CMD_DELETE_SELECTION = "aqe:delete-selection"
CMD_ANALYZE_FIELD = "aqe:analyze-field"
CMD_SETTINGS = "aqe:settings"
CMD_REDO = "aqe:redo"
MIN_TRIM_OVERRIDE_MS = 50
MAX_TRIM_OVERRIDE_MS = 10_000

BRIDGE_COMMANDS = (
    "aqe:scan",
    "aqe:analyze",
    CMD_ANALYZE_FIELD,
    "aqe:set-cursor",
    "aqe:play",
    "aqe:play-ended",
    "aqe:frontend-log",
    "aqe:show-file",
    CMD_TRIM_LEFT,
    CMD_TRIM_RIGHT,
    CMD_SLOWER,
    CMD_FASTER,
    CMD_VOLUME_DOWN,
    CMD_VOLUME_UP,
    CMD_REMOVE_PAUSES,
    CMD_DENOISE_STANDARD,
    CMD_RNNOISE,
    CMD_DELETE_SELECTION,
    "aqe:undo",
    CMD_REDO,
    CMD_SETTINGS,
)

PROCESSING_COMMANDS = (
    CMD_TRIM_LEFT,
    CMD_TRIM_RIGHT,
    CMD_SLOWER,
    CMD_FASTER,
    CMD_VOLUME_DOWN,
    CMD_VOLUME_UP,
    CMD_REMOVE_PAUSES,
)

BRIDGE_COMMAND_TO_OPERATION = {
    CMD_SLOWER: OP_SLOWER,
    CMD_FASTER: OP_FASTER,
    CMD_VOLUME_DOWN: OP_VOLUME_DOWN,
    CMD_VOLUME_UP: OP_VOLUME_UP,
    CMD_REMOVE_PAUSES: OP_REMOVE_PAUSES,
}


@dataclass(frozen=True)
class EditorCommandOverrides:
    """Validated local editor command override values."""

    trim_step_ms: int | None = None


@dataclass(frozen=True)
class EditorCommandPayload:
    """Normalized editor bridge command data."""

    command: str
    field_ord: int | None = None
    overrides: EditorCommandOverrides = EditorCommandOverrides()


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _clamp_trim_step_ms(value: int | None) -> int | None:
    if value is None:
        return None
    return max(MIN_TRIM_OVERRIDE_MS, min(MAX_TRIM_OVERRIDE_MS, value))


def _overrides_from_raw(raw: Any) -> EditorCommandOverrides:
    if not isinstance(raw, dict):
        return EditorCommandOverrides()
    return EditorCommandOverrides(
        trim_step_ms=_clamp_trim_step_ms(_int_or_none(raw.get("trimStepMs")))
    )


def decode_editor_command_payload(raw_command: str | EditorCommandPayload) -> EditorCommandPayload:
    """Return normalized editor command data from a bridge string or JSON payload."""
    if isinstance(raw_command, EditorCommandPayload):
        return raw_command
    if not raw_command.lstrip().startswith("{"):
        return EditorCommandPayload(command=raw_command)
    try:
        raw_payload = json.loads(raw_command)
    except json.JSONDecodeError:
        return EditorCommandPayload(command=raw_command)
    if not isinstance(raw_payload, dict):
        return EditorCommandPayload(command=raw_command)
    command = raw_payload.get("command")
    if not isinstance(command, str):
        return EditorCommandPayload(command=raw_command)
    return EditorCommandPayload(
        command=command,
        field_ord=_int_or_none(raw_payload.get("fieldOrd")),
        overrides=_overrides_from_raw(raw_payload.get("overrides")),
    )


def operation_for_command(command: str) -> str | None:
    """Return the shared audio operation for one editor bridge command."""
    return BRIDGE_COMMAND_TO_OPERATION.get(command)


def apply_processing_command(
    command: str | EditorCommandPayload,
    state: AudioEditState,
    config: AudioProcessingConfig,
) -> AudioEditState | None:
    """Return the edit state after applying a processing command."""
    payload = decode_editor_command_payload(command)
    step = payload.overrides.trim_step_ms or config.manual_trim_small_ms
    if payload.command == CMD_TRIM_LEFT:
        return state.trim_left(step)
    if payload.command == CMD_TRIM_RIGHT:
        return state.trim_right(step)
    operation = operation_for_command(payload.command)
    if operation is None:
        return None
    return apply_audio_operation(operation, state, config)
