"""Release provenance helpers for packaged add-ons."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RELEASE_INFO_FILENAME = "release_info.json"


def empty_release_info() -> dict[str, str]:
    """Return the stable empty release-info shape used outside packaged releases."""
    return {
        "commit_hash": "",
        "commit_message": "",
    }


def read_release_info(addon_dir: str | Path | None = None) -> dict[str, str]:
    """Read packaged release provenance from ``release_info.json``."""
    path = _release_info_path(addon_dir)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return empty_release_info()
    if not isinstance(raw, dict):
        return empty_release_info()
    return _normalize_release_info(raw)


def _release_info_path(addon_dir: str | Path | None) -> Path:
    root = Path(addon_dir) if addon_dir is not None else Path(__file__).resolve().parent
    return root / RELEASE_INFO_FILENAME


def _normalize_release_info(raw: dict[str, Any]) -> dict[str, str]:
    info = empty_release_info()
    for key in info:
        value = raw.get(key)
        if isinstance(value, str):
            info[key] = value.strip()
    return info
