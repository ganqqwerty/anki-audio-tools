"""Editor toolbar visibility normalization helpers."""

from __future__ import annotations

from typing import Any

RECORDING_PANEL_BUTTONS = (
    "aqe:record-voice",
    "aqe:play-recording",
    "aqe:share-recording",
    "aqe:show-recording-file",
)
ATOMIC_PANEL_BUTTON_GROUPS = (
    RECORDING_PANEL_BUTTONS,
)


def supported_visible_editor_button_order(config: dict[str, Any]) -> list[str]:
    """Return supported editor button commands in canonical toolbar order."""
    button_modes = config.get("editor_button_modes")
    if isinstance(button_modes, dict):
        return [command for command in button_modes if isinstance(command, str)]
    visible_buttons = config.get("visible_editor_buttons")
    if isinstance(visible_buttons, list):
        return [command for command in visible_buttons if isinstance(command, str)]
    return []


def normalize_visible_editor_buttons(
    visible_buttons: list[Any],
    button_order: list[str],
) -> list[str]:
    """Filter stale commands, expand atomic panels, and preserve toolbar order."""
    allowed_buttons = set(button_order)
    requested = _supported_requested_buttons(visible_buttons, allowed_buttons)
    _expand_atomic_panel_buttons(requested, allowed_buttons)
    return [button for button in button_order if button in requested]


def _supported_requested_buttons(
    visible_buttons: list[Any],
    allowed_buttons: set[str],
) -> set[str]:
    return {
        button
        for button in visible_buttons
        if isinstance(button, str) and button in allowed_buttons
    }


def _expand_atomic_panel_buttons(
    requested: set[str],
    allowed_buttons: set[str],
) -> None:
    for buttons in ATOMIC_PANEL_BUTTON_GROUPS:
        if any(button in requested for button in buttons):
            requested.update(button for button in buttons if button in allowed_buttons)
