"""Archive validation helpers for release packaging."""

from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path
from typing import Callable

import release_assets
import scripts.release_asset_common as release_asset_common


def validate_archive(
    archive: Path,
    *,
    allow_large_archive: bool,
    lock: dict | None,
    target_keys: list[str] | None,
    include_ffmpeg: bool,
    release_manifest_files: Callable[..., list[str]],
    warn_archive_bytes: int,
    fail_archive_bytes: int,
) -> None:
    lock = lock or release_assets.load_lock()
    with zipfile.ZipFile(archive, "r") as zf:
        infos = {info.filename: info for info in zf.infolist()}
        names = set(infos)
        for required in release_manifest_files(lock, target_keys=target_keys, include_ffmpeg=include_ffmpeg):
            if required not in names:
                _validation_error(f"missing required file {required}")
        for name in sorted(names):
            if _is_forbidden_archive_name(name):
                _validation_error(f"unexpected file {name}")
        _validate_runtime_matrix(zf, infos, lock, target_keys=target_keys, include_ffmpeg=include_ffmpeg)
        _validate_runtime_support_files(zf, infos, lock, target_keys=target_keys)
        _validate_shared_runtime_files(zf, infos, lock)
        _validate_notices(zf, names, include_ffmpeg=include_ffmpeg)
    _validate_archive_size(archive, allow_large_archive=allow_large_archive, warn_archive_bytes=warn_archive_bytes, fail_archive_bytes=fail_archive_bytes)


def selected_release_targets(value: str, lock: dict) -> tuple[list[str] | None, str]:
    if value == "all":
        return None, "all"
    if value == "current":
        target = release_assets.current_target_key()
        return [target], target
    if value not in release_assets.lock_targets(lock):
        choices = ", ".join(["all", "current", *release_assets.lock_targets(lock)])
        print(f"ERROR: unknown release target {value!r}; expected one of {choices}")
        sys.exit(1)
    return [value], value


def _validate_runtime_matrix(
    zf: zipfile.ZipFile,
    infos: dict[str, zipfile.ZipInfo],
    lock: dict,
    *,
    target_keys: list[str] | None,
    include_ffmpeg: bool,
) -> None:
    for target in target_keys or release_assets.lock_targets(lock):
        for tool_name in release_asset_common.bundled_tool_names(
            release_assets.lock_tools(lock, target),
            include_ffmpeg=include_ffmpeg,
        ):
            entry = lock["targets"][target]["tools"][tool_name]
            executable = entry["executable"]
            name = f"bin/{target}/{executable}"
            if target.startswith("windows-") and not executable.endswith(".exe"):
                _validation_error(f"{name} must use a .exe filename for Windows")
            if target.startswith("macos-") and executable.endswith(".exe"):
                _validation_error(f"{name} must not use a .exe filename for macOS")
            if target.startswith("macos-") and not _zipinfo_has_executable_bit(infos[name]):
                _validation_error(f"{name} is missing executable mode bits")
            expected_sha = entry.get("sha256")
            if not expected_sha:
                _validation_error(f"{name} is missing sha256 in release_assets.lock.json")
            if hashlib.sha256(zf.read(name)).hexdigest() != expected_sha:
                _validation_error(f"{name} checksum mismatch")


def _validate_shared_runtime_files(
    zf: zipfile.ZipFile,
    infos: dict[str, zipfile.ZipInfo],
    lock: dict,
) -> None:
    for file_name in release_assets.lock_shared_files(lock):
        entry = lock["shared_files"][file_name]
        name = f"bin/{entry['path']}"
        if name not in infos:
            _validation_error(f"missing required file {name}")
        expected_sha = entry.get("sha256")
        if not expected_sha:
            _validation_error(f"{name} is missing sha256 in release_assets.lock.json")
        if hashlib.sha256(zf.read(name)).hexdigest() != expected_sha:
            _validation_error(f"{name} checksum mismatch")


def _validate_runtime_support_files(
    zf: zipfile.ZipFile,
    infos: dict[str, zipfile.ZipInfo],
    lock: dict,
    *,
    target_keys: list[str] | None,
) -> None:
    for target in target_keys or release_assets.lock_targets(lock):
        for tool_name in release_assets.lock_tools(lock, target):
            for file_entry in release_assets.tool_runtime_files(lock, target, tool_name):
                name = f"bin/{target}/{file_entry['path']}"
                if name not in infos:
                    _validation_error(f"missing required file {name}")
                expected_sha = file_entry.get("sha256")
                if not expected_sha:
                    _validation_error(f"{name} is missing sha256 in release_assets.lock.json")
                if hashlib.sha256(zf.read(name)).hexdigest() != expected_sha:
                    _validation_error(f"{name} checksum mismatch")


def _validate_notices(zf: zipfile.ZipFile, names: set[str], *, include_ffmpeg: bool) -> None:
    notice_name = "bin/THIRD_PARTY_NOTICES.md"
    if notice_name not in names:
        _validation_error(f"missing required file {notice_name}")
    notice_text = zf.read(notice_name).decode("utf-8", errors="replace")
    required_notices = ["DeepFilterNet", "RNNoise", "DPDFNet", "Sherpa", "Spleeter"]
    if include_ffmpeg:
        required_notices[:0] = ["FFmpeg", "LAME"]
    for required in required_notices:
        if required not in notice_text:
            _validation_error(f"{notice_name} is missing {required} notice")


def _validate_archive_size(
    archive: Path,
    *,
    allow_large_archive: bool,
    warn_archive_bytes: int,
    fail_archive_bytes: int,
) -> None:
    size = archive.stat().st_size
    if size > fail_archive_bytes and not allow_large_archive:
        _validation_error(f"archive is {size} bytes, above the {fail_archive_bytes} byte release gate")
    if size > warn_archive_bytes:
        print(f"WARNING: archive is {size} bytes, above the {warn_archive_bytes} byte warning gate")


def _zipinfo_has_executable_bit(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0o777
    return bool(mode & 0o111)


def _is_forbidden_archive_name(name: str) -> bool:
    parts = Path(name).parts
    if name == ".DS_Store" or name.endswith(".DS_Store"):
        return True
    if "node_modules" in parts or "__pycache__" in parts or "aqe_artifacts" in parts:
        return True
    if ".release-assets" in parts or name == "meta.json":
        return True
    return name.endswith((".pyc", ".so", ".pyd", ".tar", ".tar.gz", ".zip"))


def _validation_error(message: str) -> None:
    print(f"VALIDATION ERROR: {message}")
    sys.exit(1)
