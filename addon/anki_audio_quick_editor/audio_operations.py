"""Shared import-safe audio operation definitions and state transitions."""

from __future__ import annotations

from .audio_state import AudioEditState, AudioProcessingConfig

OP_GRAPH = "graph"
OP_TRIM_SILENCE = "trim_silence"
OP_REMOVE_PAUSES = "remove_pauses"
OP_SLOWER = "slower"
OP_FASTER = "faster"
OP_VOLUME_DOWN = "volume_down"
OP_VOLUME_UP = "volume_up"

TRANSFORM_OPERATIONS = (
    OP_TRIM_SILENCE,
    OP_REMOVE_PAUSES,
    OP_SLOWER,
    OP_FASTER,
    OP_VOLUME_DOWN,
    OP_VOLUME_UP,
)

BATCH_OPERATIONS = (OP_GRAPH,) + TRANSFORM_OPERATIONS

OPERATION_LABELS: dict[str, str] = {
    OP_GRAPH: "Graph",
    OP_TRIM_SILENCE: "Trim Silence",
    OP_REMOVE_PAUSES: "Remove Pauses",
    OP_SLOWER: "Slower",
    OP_FASTER: "Faster",
    OP_VOLUME_DOWN: "Volume -",
    OP_VOLUME_UP: "Volume +",
}


def is_transform_operation(operation: str) -> bool:
    """Return true when ``operation`` produces a transformed audio file."""
    return operation in TRANSFORM_OPERATIONS


def requires_target_field(operation: str) -> bool:
    """Return true when ``operation`` needs a target field selection."""
    return operation == OP_GRAPH


def validate_operation(operation: str) -> str:
    """Return ``operation`` when supported, otherwise raise ``ValueError``."""
    if operation not in BATCH_OPERATIONS:
        raise ValueError(f"Unsupported audio operation: {operation}")
    return operation


def apply_audio_operation(
    operation: str,
    state: AudioEditState,
    config: AudioProcessingConfig,
) -> AudioEditState:
    """Return the next edit state after applying one shared audio operation."""
    validate_operation(operation)
    actions = {
        OP_TRIM_SILENCE: state.toggle_edge_trim,
        OP_REMOVE_PAUSES: state.toggle_internal_pauses,
        OP_SLOWER: lambda: state.slower(config),
        OP_FASTER: lambda: state.faster(config),
        OP_VOLUME_DOWN: lambda: state.volume_down(config),
        OP_VOLUME_UP: lambda: state.volume_up(config),
    }
    action = actions.get(operation)
    if action is None:
        raise ValueError(f"Operation does not produce audio transforms: {operation}")
    return action()
