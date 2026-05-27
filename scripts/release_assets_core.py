"""Core release asset verification, staging, locking, and fetch operations."""

from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path
from typing import Any

from scripts import release_asset_common as _asset_common
from scripts import release_assets_runtime_ops as _runtime_ops
from scripts import release_sherpa_assets as _sherpa_assets
from scripts import release_silero_assets as _silero_assets
from scripts.release_asset_common import (
    SHARED_FILE_NAMES,
    TARGET_KEYS,
    ReleaseAssetError,
    VerificationResult,
    _safe_relative_executable,
    _shared_file_entry,
    _stage_shared_files,
    _stage_tool_runtime_files,
    _tool_entry,
    _validate_target,
    bundled_tool_names,
    sha256_file,
    tool_runtime_files,
    tracked_runtime_file_path,
    tracked_shared_asset_path,
    validate_lock,
)
from scripts.release_asset_common import lock_shared_files as _lock_shared_files
from scripts.release_asset_common import lock_targets as _lock_targets
from scripts.release_asset_common import lock_tools as _lock_tools
from scripts.release_asset_verify import verify_assets as verify_release_assets
from scripts.release_assets_paths import (
    ADDON_BIN_DIR,
    CACHE_DIR,
    LOCK_PATH,
    source_tool_binary_path,
)

tracked_tool_binary_path = _asset_common.tracked_tool_binary_path
_download_verified = _asset_common.download_verified


def set_download_verified(download_verified) -> None:
    """Set the download hook used by runtime fetch helpers."""
    global _download_verified
    _download_verified = download_verified


def load_lock(path: Path = LOCK_PATH) -> dict[str, Any]:
    """Load the release asset lock file."""
    return json.loads(path.read_text(encoding="utf-8"))


def lock_targets(lock: dict[str, Any]) -> list[str]:
    """Return target keys in lock-file order."""
    return _lock_targets(lock)


def lock_tools(lock: dict[str, Any], target: str) -> list[str]:
    """Return canonical tool names for ``target``."""
    return _lock_tools(lock, target)


def lock_shared_files(lock: dict[str, Any]) -> list[str]:
    """Return canonical shared runtime file names."""
    return _lock_shared_files(lock)


def verify_assets(
    lock: dict[str, Any],
    *,
    cache_dir: Path = CACHE_DIR,
    addon_bin_dir: Path = ADDON_BIN_DIR,
    target_keys: list[str] | None = None,
    run_diagnostics: bool = True,
    current_target_key,
    append_diagnostic_report,
) -> VerificationResult:
    """Verify cached runtime assets and optionally run their diagnostic commands."""
    validate_lock(lock)
    if not run_diagnostics:
        return verify_release_assets(
            lock,
            cache_dir=cache_dir,
            addon_bin_dir=addon_bin_dir,
            target_keys=target_keys or TARGET_KEYS,
            run_diagnostics=False,
            lock_tools=lock_tools,
            tool_runtime_files=tool_runtime_files,
            source_tool_binary_path=source_tool_binary_path,
            current_target_key=lambda: "",
            append_diagnostic_report=lambda *args, **kwargs: None,
        )
    return verify_release_assets(
        lock,
        cache_dir=cache_dir,
        addon_bin_dir=addon_bin_dir,
        target_keys=target_keys or TARGET_KEYS,
        run_diagnostics=True,
        lock_tools=lock_tools,
        tool_runtime_files=tool_runtime_files,
        source_tool_binary_path=source_tool_binary_path,
        current_target_key=current_target_key,
        append_diagnostic_report=append_diagnostic_report,
    )


def stage_assets(
    lock: dict[str, Any],
    *,
    cache_dir: Path = CACHE_DIR,
    addon_bin_dir: Path = ADDON_BIN_DIR,
    destination: Path,
    target_keys: list[str] | None = None,
    tool_names: list[str] | None = None,
    include_shared: bool | None = None,
    include_ffmpeg: bool = True,
) -> list[Path]:
    """Copy verified runtime executables into a staged ``bin`` directory."""
    validate_lock(lock)
    staged: list[Path] = []
    selected_targets = target_keys or TARGET_KEYS
    for target in selected_targets:
        _validate_target(target)
        target_tools = bundled_tool_names(lock_tools(lock, target), include_ffmpeg=include_ffmpeg)
        for tool_name in tool_names or target_tools:
            if tool_name not in target_tools:
                raise ReleaseAssetError(f"unknown tool: {tool_name}")
            entry = _tool_entry(lock, target, tool_name)
            executable = _safe_relative_executable(entry["executable"])
            expected_sha = entry.get("sha256")
            if not expected_sha:
                raise ReleaseAssetError(f"{target}/{tool_name}: missing sha256 in release_assets.lock.json")
            source = source_tool_binary_path(cache_dir, addon_bin_dir, target, tool_name, entry)
            if not source.is_file():
                raise ReleaseAssetError(f"{target}/{tool_name}: missing binary at {source}")
            actual_sha = sha256_file(source)
            if actual_sha != expected_sha:
                raise ReleaseAssetError(f"{target}/{tool_name}: checksum mismatch")
            target_path = destination / target / executable
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target_path)
            if not target.startswith("windows-"):
                target_path.chmod(target_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            staged.append(target_path)
            staged.extend(
                _stage_tool_runtime_files(
                    lock,
                    source_dir=addon_bin_dir,
                    destination=destination,
                    target=target,
                    tool_name=tool_name,
                )
            )
    should_stage_shared = tool_names is None if include_shared is None else include_shared
    if should_stage_shared:
        staged.extend(_stage_shared_files(lock, source_dir=addon_bin_dir, destination=destination))
    return staged


def lock_checksums(
    *,
    lock_path: Path = LOCK_PATH,
    cache_dir: Path = CACHE_DIR,
    addon_bin_dir: Path = ADDON_BIN_DIR,
) -> dict[str, Any]:
    """Update lock-file checksums for the mixed tracked/cache runtime layout."""
    lock = load_lock(lock_path)
    validate_lock(lock)
    for target in TARGET_KEYS:
        for tool_name in lock_tools(lock, target):
            entry = _tool_entry(lock, target, tool_name)
            path = source_tool_binary_path(cache_dir, addon_bin_dir, target, tool_name, entry)
            if path.is_file():
                entry["sha256"] = sha256_file(path)
            for file_entry in tool_runtime_files(lock, target, tool_name):
                runtime_path = tracked_runtime_file_path(addon_bin_dir, target, file_entry)
                if runtime_path.is_file():
                    file_entry["sha256"] = sha256_file(runtime_path)
    for file_name in SHARED_FILE_NAMES:
        entry = _shared_file_entry(lock, file_name)
        path = tracked_shared_asset_path(addon_bin_dir, entry)
        if path.is_file():
            entry["sha256"] = sha256_file(path)
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return lock


def fetch_deepfilter(lock: dict[str, Any], *, target_keys: list[str], cache_dir: Path = CACHE_DIR) -> list[Path]:
    """Fetch locked DeepFilterNet executable assets."""
    validate_lock(lock)
    _runtime_ops._download_verified = _download_verified
    return _runtime_ops.fetch_deepfilter(lock, target_keys=target_keys, cache_dir=cache_dir, tool_entry=_tool_entry)


def fetch_ffmpeg(
    lock: dict[str, Any],
    *,
    target_keys: list[str],
    tool_names: list[str] | None = None,
    cache_dir: Path = CACHE_DIR,
) -> list[Path]:
    """Fetch locked FFmpeg and FFprobe executable assets."""
    validate_lock(lock)
    _runtime_ops._download_verified = _download_verified
    return _runtime_ops.fetch_ffmpeg(
        lock,
        target_keys=target_keys,
        tool_names=tool_names,
        cache_dir=cache_dir,
        tool_entry=_tool_entry,
    )


def fetch_sherpa_spleeter(lock: dict[str, Any], *, target_keys: list[str], cache_dir: Path = CACHE_DIR) -> list[Path]:
    """Fetch locked Sherpa Spleeter runtime assets."""
    validate_lock(lock)
    return _sherpa_assets.fetch_sherpa_spleeter(lock, target_keys=target_keys, cache_dir=cache_dir)


def fetch_spleeter_models(lock: dict[str, Any], *, cache_dir: Path = CACHE_DIR) -> list[Path]:
    """Fetch locked shared Spleeter model assets."""
    validate_lock(lock)
    return _sherpa_assets.fetch_spleeter_models(lock, cache_dir=cache_dir)


def fetch_silero_vad(
    lock: dict[str, Any],
    *,
    target_keys: list[str],
    cache_dir: Path = CACHE_DIR,
    addon_bin_dir: Path = ADDON_BIN_DIR,
) -> list[Path]:
    """Fetch locked Sherpa ONNX VAD executable assets."""
    validate_lock(lock)
    return _silero_assets.fetch_silero_vad(
        lock,
        target_keys=target_keys,
        cache_dir=cache_dir,
        addon_bin_dir=addon_bin_dir,
    )


def fetch_silero_vad_model(
    lock: dict[str, Any],
    *,
    cache_dir: Path = CACHE_DIR,
    addon_bin_dir: Path = ADDON_BIN_DIR,
) -> list[Path]:
    """Fetch locked shared Silero VAD model asset."""
    validate_lock(lock)
    return _silero_assets.fetch_silero_vad_model(lock, cache_dir=cache_dir, addon_bin_dir=addon_bin_dir)
