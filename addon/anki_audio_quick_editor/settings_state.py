"""Import-safe settings initial state construction."""

from __future__ import annotations

import json
import os
from typing import Any

from .contracts_generated import InitialState


def build_initial_state_payload(
    config: dict[str, Any],
    *,
    version: str,
    addon_id: str,
    addon_dir: str,
    collection_available: bool,
) -> dict[str, Any]:
    """Build the JSON-serializable state consumed by the settings webview."""
    return {
        "config": config,
        "version": version,
        "addon_dir": addon_dir,
        "log_file_path": os.path.join(addon_dir, "anki_audio_quick_editor.log"),
        "diagnostics": {
            "addon_id": addon_id,
            "collection_available": collection_available,
        },
    }


def encode_initial_state(payload: dict[str, Any]) -> str:
    """Encode a settings initial-state payload as JSON."""
    return json.dumps(InitialState.from_dict(payload).to_dict())
