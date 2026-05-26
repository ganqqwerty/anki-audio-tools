"""Archive validation helpers for release packaging."""

from __future__ import annotations

import hashlib
import json
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
    embed_runtime: bool,
    release_manifest_files: Callable[..., list[str]],
    warn_archive_bytes: int,
    fail_archive_bytes: int,
) -> None:
    lock = lock or release_assets.load_lock()
    with zipfile.ZipFile(archive, "r") as zf:
        infos = {info.filename: info for info in zf.infolist()}
        names = set(infos)
        for required in release_manifest_files(
            lock,
            target_keys=target_keys,
            include_ffmpeg=include_ffmpeg,
            embed_runtime=embed_runtime,
        ):
            if required not in names:
                _validation_error(f"missing required file {required}")
        for name in sorted(names):
            if _is_forbidden_archive_name(name):
                _validation_error(f"unexpected file {name}")
        _validate_release_info(zf, names)
        _validate_runtime_manifest(zf, names, lock, target_keys=target_keys, thin_mode=not embed_runtime)
        if embed_runtime:
            _validate_runtime_matrix(zf, infos, lock, target_keys=target_keys, include_ffmpeg=include_ffmpeg)
            _validate_runtime_support_files(zf, infos, lock, target_keys=target_keys)
            _validate_shared_runtime_files(zf, infos, lock)
        else:
            _validate_thin_archive_excludes_runtime_payloads(names, lock)
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


def _validate_runtime_manifest(
    zf: zipfile.ZipFile,
    names: set[str],
    lock: dict,
    *,
    target_keys: list[str] | None,
    thin_mode: bool,
) -> None:
    manifest_name = "bin/runtime_manifest.json"
    if manifest_name not in names:
        _validation_error(f"missing required file {manifest_name}")
    try:
        manifest = json.loads(zf.read(manifest_name).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        _validation_error(f"{manifest_name} must be valid UTF-8 JSON")
        return
    if not isinstance(manifest, dict):
        _validation_error(f"{manifest_name} must contain a JSON object")
        return
    if manifest.get("schema_version") != 1:
        _validation_error(f"{manifest_name} must declare schema_version 1")
    manifest_id = manifest.get("runtime_manifest_id")
    if not isinstance(manifest_id, str) or not manifest_id:
        _validation_error(f"{manifest_name} must include runtime_manifest_id")
    targets = manifest.get("targets")
    if not isinstance(targets, dict):
        _validation_error(f"{manifest_name} must include targets")
        return
    selected_targets = target_keys or release_assets.lock_targets(lock)
    for target in selected_targets:
        target_entry = targets.get(target)
        if not isinstance(target_entry, dict):
            _validation_error(f"{manifest_name} missing target {target}")
            continue
        if thin_mode:
            _validate_runtime_pack_metadata(manifest_name, target, target_entry)
        _validate_runtime_manifest_files(manifest_name, target, target_entry)


def _validate_runtime_pack_metadata(manifest_name: str, target: str, target_entry: dict) -> None:
    pack = target_entry.get("runtime_pack")
    if not isinstance(pack, dict):
        _validation_error(f"{manifest_name}:{target} missing runtime_pack")
        return
    for key in ("name", "url", "sha256", "size"):
        if key not in pack:
            _validation_error(f"{manifest_name}:{target}.runtime_pack missing {key}")
    name = pack.get("name")
    if not isinstance(name, str) or not name.endswith(".zip"):
        _validation_error(f"{manifest_name}:{target}.runtime_pack.name must be a zip asset name")
    url = pack.get("url")
    if not isinstance(url, str) or not url.startswith("https://"):
        _validation_error(f"{manifest_name}:{target}.runtime_pack.url must be an https URL")
    sha256 = pack.get("sha256")
    if not isinstance(sha256, str) or not _is_sha256(sha256):
        _validation_error(f"{manifest_name}:{target}.runtime_pack.sha256 must be a SHA-256 digest")
    size = pack.get("size")
    if not isinstance(size, int) or size <= 0:
        _validation_error(f"{manifest_name}:{target}.runtime_pack.size must be a positive integer")


def _validate_runtime_manifest_files(manifest_name: str, target: str, target_entry: dict) -> None:
    tools = target_entry.get("tools")
    if not isinstance(tools, dict) or not tools:
        _validation_error(f"{manifest_name}:{target} must include tools")
        return
    for tool_name, tool_entry in tools.items():
        if not isinstance(tool_entry, dict):
            _validation_error(f"{manifest_name}:{target}.{tool_name} must be an object")
            continue
        _validate_file_manifest_entry(
            manifest_name,
            f"{target}.{tool_name}",
            tool_entry,
            require_size=True,
            require_path=True,
        )
        runtime_files = tool_entry.get("runtime_files", [])
        if not isinstance(runtime_files, list):
            _validation_error(f"{manifest_name}:{target}.{tool_name}.runtime_files must be a list")
            continue
        for index, file_entry in enumerate(runtime_files):
            _validate_file_manifest_entry(
                manifest_name,
                f"{target}.{tool_name}.runtime_files[{index}]",
                file_entry,
                require_size=True,
                require_path=True,
            )
    shared_files = target_entry.get("shared_files")
    if not isinstance(shared_files, dict) or not shared_files:
        _validation_error(f"{manifest_name}:{target} must include shared_files")
        return
    for file_name, file_entry in shared_files.items():
        _validate_file_manifest_entry(
            manifest_name,
            f"{target}.shared_files.{file_name}",
            file_entry,
            require_size=True,
            require_path=True,
        )


def _validate_file_manifest_entry(
    manifest_name: str,
    label: str,
    entry: object,
    *,
    require_size: bool,
    require_path: bool,
) -> None:
    if not isinstance(entry, dict):
        _validation_error(f"{manifest_name}:{label} must be an object")
        return
    if require_path and not isinstance(entry.get("path"), str):
        _validation_error(f"{manifest_name}:{label}.path must be a string")
    sha256 = entry.get("sha256")
    if not isinstance(sha256, str) or not _is_sha256(sha256):
        _validation_error(f"{manifest_name}:{label}.sha256 must be a SHA-256 digest")
    size = entry.get("size")
    if require_size and (not isinstance(size, int) or size < 0):
        _validation_error(f"{manifest_name}:{label}.size must be an integer")


def _validate_thin_archive_excludes_runtime_payloads(names: set[str], lock: dict) -> None:
    forbidden = set()
    forbidden.update(release_asset_common.release_runtime_executables(lock))
    forbidden.update(release_asset_common.release_runtime_support_files(lock))
    forbidden.update(release_asset_common.release_runtime_shared_files(lock))
    present = sorted(forbidden & names)
    if present:
        _validation_error(f"thin archive embeds runtime payload {present[0]}")


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


def _validate_release_info(zf: zipfile.ZipFile, names: set[str]) -> None:
    name = "release_info.json"
    if name not in names:
        _validation_error(f"missing required file {name}")
    try:
        data = json.loads(zf.read(name).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        _validation_error(f"{name} must be valid UTF-8 JSON")
        return
    if not isinstance(data, dict):
        _validation_error(f"{name} must contain a JSON object")
        return
    if data.get("schema_version") != 1:
        _validation_error(f"{name} must declare schema_version 1")
    commit_hash = data.get("commit_hash")
    if not isinstance(commit_hash, str) or not _is_git_hash(commit_hash):
        _validation_error(f"{name} must include a full git commit_hash")
    commit_message = data.get("commit_message")
    if not isinstance(commit_message, str) or not commit_message.strip():
        _validation_error(f"{name} must include commit_message")


def _is_git_hash(value: str) -> bool:
    return len(value) in {40, 64} and all(char in "0123456789abcdef" for char in value.lower())


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value.lower())


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
