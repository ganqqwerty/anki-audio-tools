"""Managed runtime manifest parsing helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RUNTIME_MANIFEST_PATH = Path("bin") / "runtime_manifest.json"


class RuntimeInstallError(RuntimeError):
    """Raised when the managed runtime cannot be installed."""


@dataclass(frozen=True)
class RuntimeFile:
    """One expected file from a runtime pack."""

    path: str
    sha256: str
    size: int | None = None
    executable: bool = False


@dataclass(frozen=True)
class RuntimePack:
    """Download metadata for one platform runtime pack."""

    name: str
    url: str
    sha256: str
    size: int | None = None


@dataclass(frozen=True)
class RuntimeManifest:
    """Parsed runtime manifest used by add-on runtime code."""

    manifest_id: str
    schema_version: int
    targets: dict[str, dict[str, Any]]


def load_manifest(addon_dir: Path) -> RuntimeManifest | None:
    """Load the packaged runtime manifest, if available."""
    path = addon_dir / RUNTIME_MANIFEST_PATH
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeInstallError(f"Could not read runtime manifest: {exc}") from exc
    if not isinstance(raw, dict):
        raise RuntimeInstallError("Runtime manifest must be a JSON object.")
    targets = raw.get("targets")
    if not isinstance(targets, dict):
        raise RuntimeInstallError("Runtime manifest must contain targets.")
    schema_version = int(raw.get("schema_version", 1))
    manifest_id = raw.get("runtime_manifest_id")
    if not isinstance(manifest_id, str) or not manifest_id:
        manifest_id = _computed_manifest_id(raw)
    return RuntimeManifest(manifest_id=manifest_id, schema_version=schema_version, targets=targets)


def expected_files(manifest: RuntimeManifest, platform_key: str) -> list[RuntimeFile]:
    """Return expected extracted files for a platform."""
    target = manifest.targets.get(platform_key)
    if not isinstance(target, dict):
        return []
    return [
        *_expected_tool_files(target, platform_key),
        *_expected_shared_files(target),
    ]


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def target_pack(manifest: RuntimeManifest, platform_key: str) -> RuntimePack | None:
    """Return download metadata for the selected platform."""
    target = manifest.targets.get(platform_key)
    if not isinstance(target, dict):
        return None
    raw = target.get("runtime_pack") or target.get("runtimePack")
    if not isinstance(raw, dict):
        return None
    name = raw.get("name")
    url = raw.get("url")
    sha256 = raw.get("sha256")
    if not isinstance(name, str) or not isinstance(url, str) or not isinstance(sha256, str):
        return None
    size = raw.get("size")
    return RuntimePack(name=name, url=url, sha256=sha256, size=size if isinstance(size, int) else None)


def unsafe_relative_path(raw: str) -> bool:
    """Return whether a runtime archive member escapes the runtime root."""
    path = Path(raw)
    return path.is_absolute() or ".." in path.parts or not path.parts


def _expected_tool_files(target: dict[str, Any], platform_key: str) -> list[RuntimeFile]:
    tools = target.get("tools")
    if not isinstance(tools, dict):
        return []
    files: list[RuntimeFile] = []
    for entry in tools.values():
        if isinstance(entry, dict):
            files.extend(_expected_single_tool_files(entry, platform_key))
    return files


def _expected_single_tool_files(entry: dict[str, Any], platform_key: str) -> list[RuntimeFile]:
    files: list[RuntimeFile] = []
    path = entry.get("path")
    if isinstance(path, str):
        files.append(_runtime_file_from_entry(entry, path))
    elif isinstance(entry.get("executable"), str):
        files.append(_runtime_file_from_entry(entry, f"{platform_key}/{entry['executable']}"))
    runtime_files = entry.get("runtime_files", [])
    if isinstance(runtime_files, list):
        files.extend(_expected_runtime_support_files(runtime_files, platform_key))
    return files


def _expected_runtime_support_files(entries: list[Any], platform_key: str) -> list[RuntimeFile]:
    return [
        _runtime_file_from_entry(file_entry, f"{platform_key}/{file_entry['path']}")
        for file_entry in entries
        if isinstance(file_entry, dict) and isinstance(file_entry.get("path"), str)
    ]


def _expected_shared_files(target: dict[str, Any]) -> list[RuntimeFile]:
    shared = target.get("shared_files")
    if not isinstance(shared, dict):
        shared = target.get("sharedFiles")
    if not isinstance(shared, dict):
        return []
    return [
        _runtime_file_from_entry(entry, entry["path"])
        for entry in shared.values()
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    ]


def _runtime_file_from_entry(entry: dict[str, Any], path: str) -> RuntimeFile:
    sha256 = entry.get("sha256")
    if not isinstance(sha256, str):
        sha256 = ""
    size = entry.get("size")
    executable = bool(entry.get("executable_bit", entry.get("executableBit", False)))
    return RuntimeFile(
        path=_safe_relative_path(path),
        sha256=sha256,
        size=size if isinstance(size, int) else None,
        executable=executable,
    )


def _computed_manifest_id(raw: dict[str, Any]) -> str:
    payload = {
        "targets": raw.get("targets", {}),
        "shared_files": raw.get("shared_files", {}),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _safe_relative_path(raw: str) -> str:
    if unsafe_relative_path(raw):
        raise RuntimeInstallError(f"Unsafe runtime path: {raw}")
    return raw
