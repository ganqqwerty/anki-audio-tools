"""Initial state builder for the settings UI."""

from __future__ import annotations

import json
import os
from typing import Any


def build_initial_state(config: dict[str, Any]) -> str:
    """Build the JSON blob embedded into ``window.__INITIAL_STATE__``."""
    from aqt import mw

    from .._version import __version__

    addon_id = mw.addonManager.addonFromModule(__name__)
    addon_dir = mw.addonManager.addonsFolder(addon_id)
    state = {
        "config": config,
        "version": __version__,
        "addon_dir": addon_dir,
        "log_file_path": os.path.join(addon_dir, "anki_audio_quick_editor.log"),
        "diagnostics": {
            "addon_id": addon_id,
            "collection_available": mw.col is not None,
        },
    }
    return json.dumps(state)
