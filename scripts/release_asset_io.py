"""Low-level path, checksum, and download helpers for release assets."""

from __future__ import annotations

import hashlib
import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import Any


def runtime_file_path(cache_dir: Path, target: str, entry: dict[str, Any]) -> Path:
    """Return the cache path for a target runtime support file entry."""

    return cache_dir / "bin" / target / _safe_relative_file(entry["path"])


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest for ``path``."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_verified(url: str, destination: Path, expected_sha: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and sha256_file(destination) == expected_sha:
        return
    tmp_path = destination.with_suffix(destination.suffix + ".download")
    request = urllib.request.Request(url, headers={"User-Agent": "anki-audio-tools-release-assets/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response, tmp_path.open("wb") as handle:  # nosec B310
            shutil.copyfileobj(response, handle)
    except OSError as exc:
        tmp_path.unlink(missing_ok=True)
        raise _release_asset_error(f"download failed for {url}: {exc}") from exc
    actual_sha = sha256_file(tmp_path)
    if actual_sha != expected_sha:
        tmp_path.unlink(missing_ok=True)
        raise _release_asset_error(f"download checksum mismatch for {url}: {actual_sha}")
    tmp_path.replace(destination)


def _extract_zip_member(archive_path: Path, archive_member: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = destination.with_suffix(destination.suffix + ".extract")
    try:
        with zipfile.ZipFile(archive_path) as zf, zf.open(archive_member) as source, tmp_path.open("wb") as target:
            shutil.copyfileobj(source, target)
    except KeyError as exc:
        tmp_path.unlink(missing_ok=True)
        raise _release_asset_error(f"{archive_path.name} is missing {archive_member}") from exc
    except zipfile.BadZipFile as exc:
        tmp_path.unlink(missing_ok=True)
        raise _release_asset_error(f"{archive_path.name} is not a valid zip archive") from exc
    tmp_path.replace(destination)


def _safe_relative_executable(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts or len(path.parts) != 1:
        raise _release_asset_error(f"unsafe executable path: {raw}")
    return path


def _safe_relative_file(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise _release_asset_error(f"unsafe shared file path: {raw}")
    return path


def _safe_archive_member(raw: str) -> str:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts or not path.name:
        raise _release_asset_error(f"unsafe archive member path: {raw}")
    return raw


def _required_string(entry: dict[str, Any], key: str, target: str, tool_name: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise _release_asset_error(f"{target}/{tool_name} must define {key}")
    return value


def _required_https_url(entry: dict[str, Any], key: str, target: str, tool_name: str) -> str:
    value = _required_string(entry, key, target, tool_name)
    if not value.startswith("https://"):
        raise _release_asset_error(f"{target}/{tool_name} must define an https {key}")
    return value


def _required_sha256(entry: dict[str, Any], key: str, target: str, tool_name: str) -> str:
    value = entry.get(key)
    if not _is_sha256(value):
        raise _release_asset_error(f"{target}/{tool_name} must define {key}")
    return value


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _validate_target(target: str) -> None:
    if target not in _target_keys():
        raise _release_asset_error(f"unknown target: {target}")


def _release_asset_error(message: str) -> RuntimeError:
    from scripts.release_asset_common import ReleaseAssetError

    return ReleaseAssetError(message)


def _target_keys() -> list[str]:
    from scripts.release_asset_common import TARGET_KEYS

    return TARGET_KEYS
