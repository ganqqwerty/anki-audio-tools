"""Stable digest helpers for runtime release payloads."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from scripts import release_asset_common, release_assets


def runtime_payload_digest(
    lock: dict[str, Any],
    *,
    target_keys: list[str] | None = None,
    include_ffmpeg: bool = True,
) -> str:
    """Return a stable digest for the locked runtime payload matrix."""

    release_assets.validate_lock(lock)
    targets = target_keys or release_assets.lock_targets(lock)
    payload = {
        "schema_version": lock["schema_version"],
        "include_ffmpeg": include_ffmpeg,
        "targets": {
            target: _payload_target(lock, target, include_ffmpeg=include_ffmpeg)
            for target in targets
        },
        "shared_files": _payload_shared_files(lock),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload_target(lock: dict[str, Any], target: str, *, include_ffmpeg: bool) -> dict[str, Any]:
    return {
        "tools": {
            tool_name: _payload_tool(lock, target, tool_name)
            for tool_name in release_asset_common.bundled_tool_names(
                release_assets.lock_tools(lock, target),
                include_ffmpeg=include_ffmpeg,
            )
        },
        "shared_files": _payload_shared_files(lock),
    }


def _payload_tool(lock: dict[str, Any], target: str, tool_name: str) -> dict[str, Any]:
    entry = lock["targets"][target]["tools"][tool_name]
    return {
        "executable": entry["executable"],
        "sha256": entry.get("sha256"),
        "diagnostic_args": entry.get("diagnostic_args"),
        "runtime_files": [
            {
                "path": file_entry["path"],
                "sha256": file_entry.get("sha256"),
            }
            for file_entry in release_assets.tool_runtime_files(lock, target, tool_name)
        ],
    }


def _payload_shared_files(lock: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        file_name: {
            "path": lock["shared_files"][file_name]["path"],
            "sha256": lock["shared_files"][file_name].get("sha256"),
        }
        for file_name in release_assets.lock_shared_files(lock)
    }
