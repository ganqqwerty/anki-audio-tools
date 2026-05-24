"""Runtime asset path and fetch helpers."""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from scripts.release_asset_common import (
    ReleaseAssetError,
    _download_verified,
    _extract_zip_member,
    _required_https_url,
    _required_sha256,
    _required_string,
    _safe_archive_member,
    _safe_relative_executable,
    _validate_target,
    sha256_file,
    tool_uses_cached_binary,
    tracked_tool_binary_path,
)


def current_target_key() -> str:
    """Return the release target key for this native platform."""
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Darwin" and machine in {"arm64", "aarch64"}:
        return "macos-arm64"
    if system == "Darwin" and machine == "x86_64":
        return "macos-x86_64"
    if system == "Windows" and machine in {"amd64", "x86_64", "64bit"}:
        return "windows-x86_64"
    raise ReleaseAssetError(f"unsupported release asset platform: {system} {platform.machine()}")


def asset_binary_path(cache_dir: Path, target: str, entry: dict[str, Any]) -> Path:
    """Return the cache path for a target executable entry."""
    return cache_dir / "bin" / target / _safe_relative_executable(entry["executable"])


def source_tool_binary_path(
    cache_dir: Path,
    addon_bin_dir: Path,
    target: str,
    tool_name: str,
    entry: dict[str, Any],
) -> Path:
    """Return the canonical source path for a runtime executable."""
    return asset_binary_path(cache_dir, target, entry) if tool_uses_cached_binary(tool_name) else tracked_tool_binary_path(addon_bin_dir, target, entry)


def target_selection(value: str, *, target_keys: list[str], current_target) -> list[str]:
    if value == "all":
        return target_keys
    if value == "current":
        return [current_target()]
    _validate_target(value)
    return [value]


def ffmpeg_archive_path(cache_dir: Path, target: str, url: str) -> Path:
    name = Path(urlparse(url).path).name
    if not name:
        raise ReleaseAssetError(f"FFmpeg archive URL has no filename: {url}")
    return cache_dir / "sources" / "ffmpeg" / f"{target}-{name}"


def run_build_script(root: Path, script: Path, target: str) -> None:
    if not script.is_file():
        raise ReleaseAssetError(f"build script not found: {script.relative_to(root)}")
    command = [str(script), target] if script.suffix != ".ps1" else ["pwsh", "-File", str(script), "-Target", target]
    result = subprocess.run(command, cwd=root, text=True, check=False)  # nosec B603
    if result.returncode != 0:
        raise ReleaseAssetError(f"{script.name} failed with exit code {result.returncode}")


def build_script_name(target: str) -> str:
    _validate_target(target)
    return "build_windows.ps1" if target.startswith("windows-") and platform.system() == "Windows" else ("build_windows_cross.sh" if target.startswith("windows-") else "build_macos.sh")


def fetch_deepfilter(lock: dict[str, Any], *, target_keys: list[str], cache_dir: Path, tool_entry) -> list[Path]:
    fetched: list[Path] = []
    for target in target_keys:
        entry = tool_entry(lock, target, "deep-filter")
        expected_sha = entry.get("sha256")
        if not expected_sha:
            raise ReleaseAssetError(f"{target}/deep-filter cannot be fetched without locked sha256")
        destination = asset_binary_path(cache_dir, target, entry)
        _download_verified(entry["download_url"], destination, expected_sha)
        if not target.startswith("windows-"):
            destination.chmod(destination.stat().st_mode | 0o111)
        fetched.append(destination)
    return fetched


def fetch_ffmpeg(lock: dict[str, Any], *, target_keys: list[str], tool_names: list[str] | None, cache_dir: Path, tool_entry) -> list[Path]:
    selected_tools = tool_names or ["ffmpeg", "ffprobe"]
    fetched: list[Path] = []
    for target in target_keys:
        _validate_target(target)
        for tool_name in selected_tools:
            if tool_name not in {"ffmpeg", "ffprobe"}:
                raise ReleaseAssetError(f"fetch-ffmpeg cannot fetch {tool_name}")
            entry = tool_entry(lock, target, tool_name)
            archive_url = _required_https_url(entry, "download_url", target, tool_name)
            archive_sha = _required_sha256(entry, "download_sha256", target, tool_name)
            archive_member = _safe_archive_member(_required_string(entry, "archive_member", target, tool_name))
            archive_path = ffmpeg_archive_path(cache_dir, target, archive_url)
            _download_verified(archive_url, archive_path, archive_sha)
            destination = asset_binary_path(cache_dir, target, entry)
            _extract_zip_member(archive_path, archive_member, destination)
            if not target.startswith("windows-"):
                destination.chmod(destination.stat().st_mode | 0o111)
            expected_sha = _required_sha256(entry, "sha256", target, tool_name)
            actual_sha = sha256_file(destination)
            if actual_sha != expected_sha:
                raise ReleaseAssetError(f"{target}/{tool_name}: extracted checksum mismatch (expected {expected_sha}, got {actual_sha})")
            fetched.append(destination)
    return fetched
