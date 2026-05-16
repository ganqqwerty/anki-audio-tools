"""Import-safe editor command constants and edit-state transitions."""

from __future__ import annotations

from .audio_state import AudioEditState, AudioProcessingConfig

CMD_TRIM_LEFT = "aqe:trim-left"
CMD_TRIM_RIGHT = "aqe:trim-right"
CMD_SLOWER = "aqe:slower"
CMD_FASTER = "aqe:faster"
CMD_VOLUME_DOWN = "aqe:volume-down"
CMD_VOLUME_UP = "aqe:volume-up"
CMD_TRIM_SILENCE = "aqe:trim-silence"
CMD_REMOVE_PAUSES = "aqe:remove-pauses"

BRIDGE_COMMANDS = (
    "aqe:scan",
    "aqe:analyze",
    "aqe:set-cursor",
    "aqe:play",
    "aqe:play-ended",
    "aqe:show-file",
    CMD_TRIM_LEFT,
    CMD_TRIM_RIGHT,
    CMD_SLOWER,
    CMD_FASTER,
    CMD_VOLUME_DOWN,
    CMD_VOLUME_UP,
    CMD_TRIM_SILENCE,
    CMD_REMOVE_PAUSES,
    "aqe:undo",
)

PROCESSING_COMMANDS = (
    CMD_TRIM_LEFT,
    CMD_TRIM_RIGHT,
    CMD_SLOWER,
    CMD_FASTER,
    CMD_VOLUME_DOWN,
    CMD_VOLUME_UP,
    CMD_TRIM_SILENCE,
    CMD_REMOVE_PAUSES,
)


def apply_processing_command(
    command: str,
    state: AudioEditState,
    config: AudioProcessingConfig,
) -> AudioEditState | None:
    """Return the edit state after applying a processing command."""
    step = config.manual_trim_small_ms
    actions = {
        CMD_TRIM_LEFT: lambda: state.trim_left(step),
        CMD_TRIM_RIGHT: lambda: state.trim_right(step),
        CMD_SLOWER: lambda: state.slower(config),
        CMD_FASTER: lambda: state.faster(config),
        CMD_VOLUME_DOWN: lambda: state.volume_down(config),
        CMD_VOLUME_UP: lambda: state.volume_up(config),
        CMD_TRIM_SILENCE: state.toggle_edge_trim,
        CMD_REMOVE_PAUSES: state.toggle_internal_pauses,
    }
    action = actions.get(command)
    return action() if action else None
