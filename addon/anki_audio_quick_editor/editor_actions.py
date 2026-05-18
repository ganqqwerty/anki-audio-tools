"""Import-safe editor bridge commands and shared operation mapping."""

from __future__ import annotations

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


def operation_for_command(command: str) -> str | None:
    """Return the shared audio operation for one editor bridge command."""
    return BRIDGE_COMMAND_TO_OPERATION.get(command)


def apply_processing_command(
    command: str,
    state: AudioEditState,
    config: AudioProcessingConfig,
) -> AudioEditState | None:
    """Return the edit state after applying a processing command."""
    step = config.manual_trim_small_ms
    if command == CMD_TRIM_LEFT:
        return state.trim_left(step)
    if command == CMD_TRIM_RIGHT:
        return state.trim_right(step)
    operation = operation_for_command(command)
    if operation is None:
        return None
    return apply_audio_operation(operation, state, config)
