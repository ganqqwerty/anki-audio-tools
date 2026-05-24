"""Platform-specific defaults for external ffmpeg tools."""

from __future__ import annotations

import copy
import platform
from typing import Any


def default_ffmpeg_path() -> str:
    """Return the persisted default ffmpeg executable for this platform."""
    system = platform.system()
    if system == "Darwin":
        return "/opt/homebrew/bin/ffmpeg"
    if system == "Windows":
        return "ffmpeg.exe"
    return "ffmpeg"


def with_platform_ffmpeg_default(config: dict[str, Any]) -> dict[str, Any]:
    """Return a config copy with the current platform's ffmpeg default filled in."""
    updated = copy.deepcopy(config)
    updated["ffmpeg_path"] = default_ffmpeg_path()
    return updated
