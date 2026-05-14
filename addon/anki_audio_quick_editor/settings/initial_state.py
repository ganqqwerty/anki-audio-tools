"""Thin Anki wrapper for settings UI initial state."""

from __future__ import annotations

from typing import Any


def build_initial_state(config: dict[str, Any]) -> str:
    """Build the JSON blob embedded into ``window.__INITIAL_STATE__``."""
    from aqt import mw

    from .._version import __version__
    from ..settings_state import build_initial_state_payload, encode_initial_state

    addon_id = mw.addonManager.addonFromModule(__name__)
    addon_dir = mw.addonManager.addonsFolder(addon_id)
    state = build_initial_state_payload(
        config,
        version=__version__,
        addon_id=addon_id,
        addon_dir=addon_dir,
        collection_available=mw.col is not None,
    )
    return encode_initial_state(state)
