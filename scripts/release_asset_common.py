"""Shared release asset lock helpers."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts import release_asset_io as _asset_io
from scripts.release_asset_io import (
    _is_sha256,
    _safe_archive_member,
    _safe_relative_executable,
    _safe_relative_file,
    sha256_file,
)

urllib = _asset_io.urllib


def _module_member(module: Any, name: str) -> Any:
    return getattr(module, name)


def _download_verified(url: str, destination: Path, expected_sha: str) -> None:
    download = _module_member(_asset_io, "_download_verified")
    download(url, destination, expected_sha)


download_verified = _download_verified


def _extract_zip_member(archive_path: Path, member: str, destination: Path) -> None:
    extract = _module_member(_asset_io, "_extract_zip_member")
    extract(archive_path, member, destination)


def _required_https_url(entry: dict[str, Any], key: str, target: str, tool_name: str) -> str:
    required = _module_member(_asset_io, "_required_https_url")
    return required(entry, key, target, tool_name)


def _required_sha256(entry: dict[str, Any], key: str, target: str, tool_name: str) -> str:
    required = _module_member(_asset_io, "_required_sha256")
    return required(entry, key, target, tool_name)


def _required_string(entry: dict[str, Any], key: str, target: str, tool_name: str) -> str:
    required = _module_member(_asset_io, "_required_string")
    return required(entry, key, target, tool_name)


def _validate_target(target: str) -> None:
    validate = _module_member(_asset_io, "_validate_target")
    validate(target)


def runtime_file_path(cache_dir: Path, target: str, entry: dict[str, Any]) -> Path:
    return _asset_io.runtime_file_path(cache_dir, target, entry)

TARGET_KEYS = ["macos-arm64", "macos-x86_64", "windows-x86_64"]
BASE_TOOL_NAMES = ["deep-filter", "ffmpeg", "ffprobe", "rnnoise-cli", "sherpa-spleeter", "silero-vad"]
TARGET_TOOL_NAMES = {
    "macos-arm64": [*BASE_TOOL_NAMES, "dpdfnet"],
    "macos-x86_64": [*BASE_TOOL_NAMES, "dpdfnet"],
    "windows-x86_64": [*BASE_TOOL_NAMES, "dpdfnet"],
}
TOOL_NAMES = sorted({tool for tools in TARGET_TOOL_NAMES.values() for tool in tools})
SHARED_FILE_NAMES = ["spleeter-vocals", "spleeter-accompaniment", "silero-vad-model"]
CACHED_TOOL_NAMES = {"ffmpeg", "ffprobe"}


class ReleaseAssetError(RuntimeError):
    """Raised when release asset preparation cannot continue."""

    def __str__(self) -> str:
        return str(self.args[0]) if self.args else self.__class__.__name__


@dataclass(frozen=True)
class VerificationResult:
    """Collected verification messages for a target/tool matrix."""

    errors: list[str]
    reports: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def lock_shared_files(lock: dict[str, Any]) -> list[str]:
    """Return canonical shared runtime file names."""

    shared_files = lock.get("shared_files")
    if not isinstance(shared_files, dict):
        raise ReleaseAssetError("release asset lock must contain a shared_files object")
    return [file_name for file_name in SHARED_FILE_NAMES if file_name in shared_files]


def lock_targets(lock: dict[str, Any]) -> list[str]:
    """Return target keys in lock-file order."""

    targets = lock.get("targets")
    if not isinstance(targets, dict):
        raise ReleaseAssetError("release asset lock must contain a targets object")
    return list(targets)


def lock_tools(lock: dict[str, Any], target: str) -> list[str]:
    """Return canonical tool names for ``target``."""

    tools = _target_tools(lock, target)
    return [tool for tool in TARGET_TOOL_NAMES[target] if tool in tools]


def validate_lock(lock: dict[str, Any]) -> None:
    """Validate lock-file structure and release-ready checksum completeness."""

    if lock.get("schema_version") != 1:
        raise ReleaseAssetError("release asset lock schema_version must be 1")
    if lock_targets(lock) != TARGET_KEYS:
        raise ReleaseAssetError(f"release asset lock targets must be exactly {', '.join(TARGET_KEYS)}")
    release_ready = bool(lock.get("release_ready", False))
    for target in TARGET_KEYS:
        _validate_target_tool_matrix(lock, target)
        for tool_name in TARGET_TOOL_NAMES[target]:
            _validate_tool_lock_entry(lock, target, tool_name, release_ready)
    shared_files = lock_shared_files(lock)
    if sorted(shared_files) != sorted(SHARED_FILE_NAMES):
        raise ReleaseAssetError(f"shared files must be exactly {', '.join(SHARED_FILE_NAMES)}")
    for file_name in SHARED_FILE_NAMES:
        _validate_shared_lock_entry(lock, file_name, release_ready)


def _target_tools(lock: dict[str, Any], target: str) -> dict[str, Any]:
    targets = lock.get("targets")
    if not isinstance(targets, dict) or target not in targets:
        raise ReleaseAssetError(f"unknown target: {target}")
    target_entry = targets[target]
    tools = target_entry.get("tools") if isinstance(target_entry, dict) else None
    if not isinstance(tools, dict):
        raise ReleaseAssetError(f"{target} must contain a tools object")
    return tools


def _tool_entry(lock: dict[str, Any], target: str, tool_name: str) -> dict[str, Any]:
    tools = _target_tools(lock, target)
    if tool_name not in tools:
        raise ReleaseAssetError(f"{target} is missing {tool_name}")
    entry = tools[tool_name]
    if not isinstance(entry, dict):
        raise ReleaseAssetError(f"{target}/{tool_name} entry must be an object")
    return entry


def tool_runtime_files(lock: dict[str, Any], target: str, tool_name: str) -> list[dict[str, Any]]:
    """Return runtime support file entries for ``target/tool_name``."""

    runtime_files = _tool_entry(lock, target, tool_name).get("runtime_files", [])
    if not isinstance(runtime_files, list):
        raise ReleaseAssetError(f"{target}/{tool_name} runtime_files must be a list")
    for file_entry in runtime_files:
        if not isinstance(file_entry, dict):
            raise ReleaseAssetError(f"{target}/{tool_name} runtime file entry must be an object")
    return runtime_files


def release_runtime_executables(
    lock: dict[str, Any],
    *,
    target_keys: list[str] | None = None,
) -> list[str]:
    """Return required runtime executable archive paths from the asset lock."""

    names: list[str] = []
    for target in target_keys or lock_targets(lock):
        for tool_name in lock_tools(lock, target):
            executable = lock["targets"][target]["tools"][tool_name]["executable"]
            names.append(f"bin/{target}/{executable}")
    return sorted(names)


def release_runtime_shared_files(lock: dict[str, Any]) -> list[str]:
    """Return required shared runtime asset archive paths from the asset lock."""

    return sorted(
        f"bin/{lock['shared_files'][file_name]['path']}"
        for file_name in lock_shared_files(lock)
    )


def release_runtime_support_files(
    lock: dict[str, Any],
    *,
    target_keys: list[str] | None = None,
) -> list[str]:
    """Return required target-specific runtime support file archive paths."""

    names: list[str] = []
    for target in target_keys or lock_targets(lock):
        for tool_name in lock_tools(lock, target):
            names.extend(
                f"bin/{target}/{file_entry['path']}"
                for file_entry in tool_runtime_files(lock, target, tool_name)
            )
    return sorted(names)


def tool_uses_cached_binary(tool_name: str) -> bool:
    """Return whether ``tool_name`` is sourced from the external cache."""

    return tool_name in CACHED_TOOL_NAMES


def bundled_tool_names(tool_names: list[str], *, include_ffmpeg: bool) -> list[str]:
    """Return runtime tool names included in a packaged archive."""

    if include_ffmpeg:
        return list(tool_names)
    return [tool_name for tool_name in tool_names if not tool_uses_cached_binary(tool_name)]


def tracked_tool_binary_path(addon_bin_dir: Path, target: str, entry: dict[str, Any]) -> Path:
    """Return the canonical tracked source path for a target executable entry."""

    executable = _safe_relative_executable(entry["executable"])
    return addon_bin_dir / target / executable


def tracked_runtime_file_path(addon_bin_dir: Path, target: str, entry: dict[str, Any]) -> Path:
    """Return the canonical tracked source path for a target runtime support file entry."""

    return addon_bin_dir / target / _safe_relative_file(entry["path"])


def tracked_shared_asset_path(addon_bin_dir: Path, entry: dict[str, Any]) -> Path:
    """Return the canonical tracked source path for a shared runtime asset entry."""

    return addon_bin_dir / _safe_relative_file(entry["path"])


def _validate_target_tool_matrix(lock: dict[str, Any], target: str) -> None:
    tools = _target_tools(lock, target)
    expected_tools = TARGET_TOOL_NAMES[target]
    if sorted(tools) != sorted(expected_tools):
        raise ReleaseAssetError(f"{target} tools must be exactly {', '.join(expected_tools)}")


def _validate_tool_lock_entry(lock: dict[str, Any], target: str, tool_name: str, release_ready: bool) -> None:
    entry = _tool_entry(lock, target, tool_name)
    executable = entry.get("executable")
    if not isinstance(executable, str) or not executable:
        raise ReleaseAssetError(f"{target}/{tool_name} must define executable")
    _safe_relative_executable(executable)
    source_url = entry.get("source_url")
    if not isinstance(source_url, str) or not source_url.startswith("https://"):
        raise ReleaseAssetError(f"{target}/{tool_name} must define an https source_url")
    checksum = entry.get("sha256")
    if release_ready and not checksum:
        raise ReleaseAssetError(f"{target}/{tool_name} is release-ready but missing sha256")
    if checksum is not None and not _is_sha256(checksum):
        raise ReleaseAssetError(f"{target}/{tool_name} has invalid sha256")
    for file_entry in tool_runtime_files(lock, target, tool_name):
        _validate_tool_runtime_file_entry(target, tool_name, file_entry, release_ready)


def _validate_tool_runtime_file_entry(
    target: str,
    tool_name: str,
    file_entry: dict[str, Any],
    release_ready: bool,
) -> None:
    path = file_entry.get("path")
    if not isinstance(path, str) or not path:
        raise ReleaseAssetError(f"{target}/{tool_name} runtime file must define path")
    _safe_relative_file(path)
    archive_member = file_entry.get("archive_member")
    if archive_member is not None:
        if not isinstance(archive_member, str) or not archive_member:
            raise ReleaseAssetError(f"{target}/{tool_name} runtime file has invalid archive_member")
        _safe_archive_member(archive_member)
    checksum = file_entry.get("sha256")
    if release_ready and not checksum:
        raise ReleaseAssetError(f"{target}/{tool_name}/{path} is release-ready but missing sha256")
    if checksum is not None and not _is_sha256(checksum):
        raise ReleaseAssetError(f"{target}/{tool_name}/{path} has invalid sha256")


def _validate_shared_lock_entry(lock: dict[str, Any], file_name: str, release_ready: bool) -> None:
    entry = _shared_file_entry(lock, file_name)
    path = entry.get("path")
    if not isinstance(path, str) or not path:
        raise ReleaseAssetError(f"shared/{file_name} must define path")
    _safe_relative_file(path)
    source_url = entry.get("source_url")
    if not isinstance(source_url, str) or not source_url.startswith("https://"):
        raise ReleaseAssetError(f"shared/{file_name} must define an https source_url")
    checksum = entry.get("sha256")
    if release_ready and not checksum:
        raise ReleaseAssetError(f"shared/{file_name} is release-ready but missing sha256")
    if checksum is not None and not _is_sha256(checksum):
        raise ReleaseAssetError(f"shared/{file_name} has invalid sha256")


def shared_asset_path(cache_dir: Path, entry: dict[str, Any]) -> Path:
    """Return the cache path for a shared runtime asset entry."""

    return cache_dir / "shared" / _safe_relative_file(entry["path"])


def _stage_shared_files(
    lock: dict[str, Any],
    *,
    source_dir: Path,
    destination: Path,
) -> list[Path]:
    staged: list[Path] = []
    for file_name in SHARED_FILE_NAMES:
        entry = _shared_file_entry(lock, file_name)
        expected_sha = entry.get("sha256")
        if not expected_sha:
            raise ReleaseAssetError(f"shared/{file_name}: missing sha256 in release_assets.lock.json")
        source = tracked_shared_asset_path(source_dir, entry)
        if not source.is_file():
            raise ReleaseAssetError(f"shared/{file_name}: missing file at {source}")
        actual_sha = sha256_file(source)
        if actual_sha != expected_sha:
            raise ReleaseAssetError(f"shared/{file_name}: checksum mismatch")
        target_path = destination / _safe_relative_file(entry["path"])
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target_path)
        staged.append(target_path)
    return staged


def _stage_tool_runtime_files(
    lock: dict[str, Any],
    *,
    source_dir: Path,
    destination: Path,
    target: str,
    tool_name: str,
) -> list[Path]:
    staged: list[Path] = []
    for file_entry in tool_runtime_files(lock, target, tool_name):
        expected_sha = file_entry.get("sha256")
        if not expected_sha:
            raise ReleaseAssetError(f"{target}/{tool_name}/{file_entry['path']}: missing sha256")
        source = tracked_runtime_file_path(source_dir, target, file_entry)
        if not source.is_file():
            raise ReleaseAssetError(f"{target}/{tool_name}/{file_entry['path']}: missing file at {source}")
        actual_sha = sha256_file(source)
        if actual_sha != expected_sha:
            raise ReleaseAssetError(f"{target}/{tool_name}/{file_entry['path']}: checksum mismatch")
        target_path = destination / target / _safe_relative_file(file_entry["path"])
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target_path)
        staged.append(target_path)
    return staged


def _shared_file_entry(lock: dict[str, Any], file_name: str) -> dict[str, Any]:
    shared_files = lock.get("shared_files")
    if not isinstance(shared_files, dict) or file_name not in shared_files:
        raise ReleaseAssetError(f"shared files are missing {file_name}")
    entry = shared_files[file_name]
    if not isinstance(entry, dict):
        raise ReleaseAssetError(f"shared/{file_name} entry must be an object")
    return entry
