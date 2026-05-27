"""Release asset path and platform helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts import release_assets_runtime_ops as _runtime_ops

ROOT = Path(__file__).resolve().parent.parent
LOCK_PATH = ROOT / "release_assets.lock.json"
CACHE_DIR = ROOT / ".release-assets"
ADDON_BIN_DIR = ROOT / "addon" / "anki_audio_quick_editor" / "bin"


def current_target_key() -> str:
    """Return the release target key for this native platform."""
    return _runtime_ops.current_target_key()


def asset_binary_path(cache_dir: Path, target: str, entry: dict[str, Any]) -> Path:
    """Return the cache path for a target executable entry."""
    return _runtime_ops.asset_binary_path(cache_dir, target, entry)


def source_tool_binary_path(
    cache_dir: Path,
    addon_bin_dir: Path,
    target: str,
    tool_name: str,
    entry: dict[str, Any],
) -> Path:
    """Return the canonical source path for a runtime executable."""
    return _runtime_ops.source_tool_binary_path(cache_dir, addon_bin_dir, target, tool_name, entry)


def ffmpeg_archive_path(cache_dir: Path, target: str, url: str) -> Path:
    """Return the cached archive path for a locked FFmpeg source URL."""
    return _runtime_ops.ffmpeg_archive_path(cache_dir, target, url)
