"""Import-safe runtime diagnostic helpers."""

from __future__ import annotations

import subprocess
from typing import Any


def build_deep_filter_health(config: dict[str, Any]) -> dict[str, Any]:
    """Return DeepFilterNet executable availability and version details."""
    from .audio_processor import find_deep_filter

    configured_path = str(config.get("deep_filter_path", ""))
    try:
        deep_filter_path = find_deep_filter(configured_path)
    except Exception as exc:
        return {
            "available": False,
            "path": configured_path,
            "version": "",
            "error": str(exc),
        }

    command = (str(deep_filter_path), "--version")
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )  # nosec B603
    except OSError as exc:
        return {
            "available": False,
            "path": str(deep_filter_path),
            "version": "",
            "error": str(exc),
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "path": str(deep_filter_path),
            "version": "",
            "error": "deep-filter --version timed out.",
        }

    version = (result.stdout or result.stderr).strip()
    return {
        "available": result.returncode == 0,
        "path": str(deep_filter_path),
        "version": version if result.returncode == 0 else "",
        "error": "" if result.returncode == 0 else version or "deep-filter --version failed.",
    }
