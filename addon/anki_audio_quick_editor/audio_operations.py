"""Shared import-safe audio operation definitions and state transitions."""

from __future__ import annotations

from typing import Mapping

from .audio_state import AudioEditState, AudioProcessingConfig
from .i18n import format_message

OP_GRAPH = "graph"
OP_CONVERT = "convert"
OP_DENOISE = "denoise"
OP_REMOVE_PAUSES = "remove_pauses"
OP_SLOWER = "slower"
OP_FASTER = "faster"
OP_VOLUME_DOWN = "volume_down"
OP_VOLUME_UP = "volume_up"

TRANSFORM_OPERATIONS = (
    OP_CONVERT,
    OP_DENOISE,
    OP_REMOVE_PAUSES,
    OP_SLOWER,
    OP_FASTER,
    OP_VOLUME_DOWN,
    OP_VOLUME_UP,
)

BATCH_OPERATIONS = (OP_GRAPH,) + TRANSFORM_OPERATIONS

OPERATION_LABELS: dict[str, str] = {
    OP_GRAPH: "Graph",
    OP_CONVERT: "Convert",
    OP_DENOISE: "Denoise",
    OP_REMOVE_PAUSES: "Shorten Pauses",
    OP_SLOWER: "Slower",
    OP_FASTER: "Faster",
    OP_VOLUME_DOWN: "Volume -",
    OP_VOLUME_UP: "Volume +",
}

OPERATION_LABEL_KEYS: dict[str, str] = {
    OP_GRAPH: "operation.graph",
    OP_CONVERT: "operation.convert",
    OP_DENOISE: "operation.denoise",
    OP_REMOVE_PAUSES: "operation.remove_pauses",
    OP_SLOWER: "operation.slower",
    OP_FASTER: "operation.faster",
    OP_VOLUME_DOWN: "operation.volume_down",
    OP_VOLUME_UP: "operation.volume_up",
}


def operation_label(operation: str, messages: Mapping[str, str] | None = None) -> str:
    """Return a localized label for a supported batch/editor operation."""
    key = OPERATION_LABEL_KEYS.get(operation)
    if key is None:
        return operation
    return format_message(messages or {}, key)


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
