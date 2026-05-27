"""Runtime state and status payload helpers."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .runtime_manifest import RuntimeFile, RuntimeManifest
from .runtime_paths import managed_runtime_root, runtime_state_path

RUNTIME_SOURCE_MANAGED = "managed"
RUNTIME_PHASE_READY = "ready"
RUNTIME_PHASE_MISSING = "missing"
RUNTIME_PHASE_DOWNLOADING = "downloading"
RUNTIME_PHASE_ERROR = "error"
RUNTIME_PHASE_UNSUPPORTED = "unsupported"


def read_state(addon_dir: Path) -> dict[str, Any]:
    """Read persisted runtime state."""
    path = runtime_state_path(addon_dir)
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def write_ready_state(
    addon_dir: Path,
    manifest: RuntimeManifest,
    platform_key: str,
    files: list[RuntimeFile],
) -> None:
    """Persist the installed runtime state after successful verification."""
    state = {
        "schema_version": 1,
        "runtime_manifest_id": manifest.manifest_id,
        "platform": platform_key,
        "runtime_root": str(managed_runtime_root(addon_dir, manifest.manifest_id)),
        "installed_files": {file_entry.path: file_entry.sha256 for file_entry in files},
    }
    path = runtime_state_path(addon_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def status(
    phase: str,
    *,
    manifest: RuntimeManifest | None = None,
    platform_key: str,
    runtime_root: str = "",
    message: str = "",
    error: str = "",
    progress: int = 0,
) -> dict[str, Any]:
    """Build a settings/runtime status payload."""
    return {
        "phase": phase,
        "runtime_manifest_id": manifest.manifest_id if manifest is not None else "",
        "platform": platform_key,
        "runtime_root": runtime_root,
        "progress": progress,
        "message": message,
        "error": error,
    }


def notify(notify_fn: Callable[[dict[str, Any]], None] | None, payload: dict[str, Any]) -> None:
    """Notify a runtime status listener with an isolated payload copy."""
    if notify_fn is not None:
        notify_fn(dict(payload))
