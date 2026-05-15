"""Import-safe editor command constants and edit-state transitions."""

from __future__ import annotations

from .audio_state import AudioEditState, AudioProcessingConfig

BRIDGE_COMMANDS = (
    "aqe:scan",
    "aqe:analyze",
    "aqe:set-cursor",
    "aqe:play",
    "aqe:play-ended",
    "aqe:trim-left",
    "aqe:trim-right",
    "aqe:slower",
    "aqe:faster",
    "aqe:trim-silence",
    "aqe:remove-pauses",
    "aqe:undo",
)

PROCESSING_COMMANDS = (
    "aqe:trim-left",
    "aqe:trim-right",
    "aqe:slower",
    "aqe:faster",
    "aqe:trim-silence",
    "aqe:remove-pauses",
)


def apply_processing_command(
    command: str,
    state: AudioEditState,
    config: AudioProcessingConfig,
) -> AudioEditState | None:
    """Return the edit state after applying a processing command."""
    step = config.manual_trim_small_ms
    actions = {
        "aqe:trim-left": lambda: state.trim_left(step),
        "aqe:trim-right": lambda: state.trim_right(step),
        "aqe:slower": lambda: state.slower(config),
        "aqe:faster": lambda: state.faster(config),
        "aqe:trim-silence": state.toggle_edge_trim,
        "aqe:remove-pauses": state.toggle_internal_pauses,
    }
    action = actions.get(command)
    return action() if action else None
