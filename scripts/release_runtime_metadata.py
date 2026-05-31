"""Tracked metadata for decoupled runtime releases."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from scripts import release_asset_common, release_assets, release_runtime
from scripts.release_runtime_payload import runtime_payload_digest

ROOT = Path(__file__).resolve().parent.parent
RUNTIME_RELEASE_LOCK_PATH = ROOT / "runtime_release.lock.json"
RUNTIME_RELEASE_SCHEMA_VERSION = 1
RUNTIME_TAG_PREFIX = "runtime-v"


def runtime_tag(runtime_version: str) -> str:
    """Return the immutable GitHub release tag for a runtime version."""

    return f"{RUNTIME_TAG_PREFIX}{runtime_version}"


def default_runtime_base_url(runtime_version: str) -> str:
    """Return the default GitHub release asset base URL for a runtime version."""

    return release_runtime.default_runtime_base_url(runtime_tag(runtime_version))


def load_runtime_release_lock(path: Path = RUNTIME_RELEASE_LOCK_PATH) -> dict[str, Any]:
    """Load tracked runtime release metadata."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise release_assets.ReleaseAssetError(f"could not read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise release_assets.ReleaseAssetError(f"{path} must contain a JSON object")
    return data


def write_runtime_release_lock(
    metadata: dict[str, Any],
    path: Path = RUNTIME_RELEASE_LOCK_PATH,
) -> None:
    """Write tracked runtime release metadata."""

    path.write_text(json.dumps(metadata, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def build_runtime_release_metadata(
    runtime_version: str,
    lock: dict[str, Any],
    runtime_pack_metadata: dict[str, dict[str, Any]],
    *,
    target_keys: list[str] | None = None,
    include_ffmpeg: bool = True,
    runtime_base_url: str | None = None,
) -> dict[str, Any]:
    """Build tracked metadata for a published runtime release."""

    targets = target_keys or release_assets.lock_targets(lock)
    base_url = (runtime_base_url or default_runtime_base_url(runtime_version)).rstrip("/")
    tag = runtime_tag(runtime_version)
    manifest = release_runtime.runtime_manifest_data(
        lock,
        target_keys=targets,
        include_ffmpeg=include_ffmpeg,
        runtime_pack_metadata=runtime_pack_metadata,
        runtime_file_metadata=file_metadata_by_path(runtime_pack_metadata, target_keys=targets),
    )
    metadata: dict[str, Any] = {
        "schema_version": RUNTIME_RELEASE_SCHEMA_VERSION,
        "runtime_version": runtime_version,
        "runtime_tag": tag,
        "runtime_base_url": base_url,
        "runtime_payload_digest": runtime_payload_digest(
            lock,
            target_keys=targets,
            include_ffmpeg=include_ffmpeg,
        ),
        "runtime_manifest_id": manifest["runtime_manifest_id"],
        "targets": {},
    }
    for target in targets:
        pack = runtime_pack_metadata[target]
        metadata["targets"][target] = {
            "runtime_pack": {
                "name": pack["name"],
                "url": f"{base_url}/{pack['name']}",
                "sha256": pack["sha256"],
                "size": pack["size"],
            },
            "files": _metadata_files(pack["files"]),
        }
    return metadata


def validate_runtime_release_metadata(
    metadata: dict[str, Any],
    lock: dict[str, Any],
    *,
    target_keys: list[str] | None = None,
    include_ffmpeg: bool = True,
) -> None:
    """Validate tracked runtime metadata against the current asset lock."""

    if metadata.get("schema_version") != RUNTIME_RELEASE_SCHEMA_VERSION:
        raise release_assets.ReleaseAssetError("runtime metadata schema_version must be 1")
    runtime_version = _required_str(metadata, "runtime_version")
    expected_tag = runtime_tag(runtime_version)
    if metadata.get("runtime_tag") != expected_tag:
        raise release_assets.ReleaseAssetError(
            f"runtime metadata tag must be {expected_tag}"
        )
    runtime_base_url = _required_str(metadata, "runtime_base_url").rstrip("/")
    if not runtime_base_url.startswith("https://"):
        raise release_assets.ReleaseAssetError("runtime_base_url must be an https URL")
    targets = metadata.get("targets")
    if not isinstance(targets, dict) or not targets:
        raise release_assets.ReleaseAssetError("runtime metadata must contain targets")
    selected_targets = target_keys or release_assets.lock_targets(lock)
    metadata_targets = list(targets)
    expected_digest = runtime_payload_digest(
        lock,
        target_keys=metadata_targets,
        include_ffmpeg=include_ffmpeg,
    )
    if metadata.get("runtime_payload_digest") != expected_digest:
        raise release_assets.ReleaseAssetError(
            "runtime metadata does not match release_assets.lock.json"
        )
    for target in selected_targets:
        if target not in targets:
            raise release_assets.ReleaseAssetError(
                f"runtime metadata missing target {target}"
            )
        _validate_target_metadata(
            metadata,
            lock,
            target,
            runtime_version=runtime_version,
            runtime_base_url=runtime_base_url,
            include_ffmpeg=include_ffmpeg,
        )
    _validate_manifest_id(metadata, lock, target_keys=metadata_targets, include_ffmpeg=include_ffmpeg)


def runtime_pack_metadata_from_release(
    metadata: dict[str, Any],
    *,
    target_keys: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Return release-runtime metadata in the shape used by manifest generation."""

    targets = metadata["targets"]
    selected_targets = target_keys or list(targets)
    return {
        target: {
            **targets[target]["runtime_pack"],
            "files": targets[target]["files"],
        }
        for target in selected_targets
    }


def file_metadata_by_path(
    runtime_pack_metadata: dict[str, dict[str, Any]],
    *,
    target_keys: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Return runtime pack file metadata keyed by archive path."""

    selected_targets = target_keys or list(runtime_pack_metadata)
    by_path: dict[str, dict[str, Any]] = {}
    for target in selected_targets:
        for file_entry in runtime_pack_metadata[target]["files"]:
            previous = by_path.get(file_entry["path"])
            if previous is not None and previous != file_entry:
                raise release_assets.ReleaseAssetError(
                    f"runtime metadata has conflicting entries for {file_entry['path']}"
                )
            by_path[file_entry["path"]] = file_entry
    return by_path


def _metadata_files(file_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "path": entry["path"],
            "sha256": entry["sha256"],
            "size": entry["size"],
            "executable_bit": bool(entry.get("executable_bit", False)),
        }
        for entry in sorted(file_entries, key=lambda item: item["path"])
    ]


def _validate_target_metadata(
    metadata: dict[str, Any],
    lock: dict[str, Any],
    target: str,
    *,
    runtime_version: str,
    runtime_base_url: str,
    include_ffmpeg: bool,
) -> None:
    target_entry = metadata["targets"][target]
    if not isinstance(target_entry, dict):
        raise release_assets.ReleaseAssetError(f"{target} metadata must be an object")
    pack = target_entry.get("runtime_pack")
    if not isinstance(pack, dict):
        raise release_assets.ReleaseAssetError(f"{target} metadata missing runtime_pack")
    expected_name = release_runtime.runtime_pack_asset_name(runtime_version, target)
    if pack.get("name") != expected_name:
        raise release_assets.ReleaseAssetError(
            f"{target} runtime pack name must be {expected_name}"
        )
    if pack.get("url") != f"{runtime_base_url}/{expected_name}":
        raise release_assets.ReleaseAssetError(f"{target} runtime pack URL is stale")
    _validate_sha(pack.get("sha256"), f"{target} runtime pack")
    if not isinstance(pack.get("size"), int) or pack["size"] <= 0:
        raise release_assets.ReleaseAssetError(f"{target} runtime pack size is invalid")
    expected_files = _expected_file_metadata(lock, target, include_ffmpeg=include_ffmpeg)
    _validate_file_list(target_entry.get("files"), expected_files, target)


def _validate_manifest_id(
    metadata: dict[str, Any],
    lock: dict[str, Any],
    *,
    target_keys: list[str],
    include_ffmpeg: bool,
) -> None:
    pack_metadata = runtime_pack_metadata_from_release(metadata, target_keys=target_keys)
    manifest = release_runtime.runtime_manifest_data(
        lock,
        target_keys=target_keys,
        include_ffmpeg=include_ffmpeg,
        runtime_pack_metadata=pack_metadata,
        runtime_file_metadata=file_metadata_by_path(pack_metadata, target_keys=target_keys),
    )
    if metadata.get("runtime_manifest_id") != manifest["runtime_manifest_id"]:
        raise release_assets.ReleaseAssetError("runtime_manifest_id is stale")


def _expected_file_metadata(
    lock: dict[str, Any],
    target: str,
    *,
    include_ffmpeg: bool,
) -> dict[str, dict[str, Any]]:
    expected: dict[str, dict[str, Any]] = {}
    for tool_name in release_asset_common.bundled_tool_names(
        release_assets.lock_tools(lock, target),
        include_ffmpeg=include_ffmpeg,
    ):
        tool_entry = lock["targets"][target]["tools"][tool_name]
        executable_path = f"{target}/{tool_entry['executable']}"
        _add_expected_file(
            expected,
            executable_path,
            tool_entry.get("sha256"),
            executable_bit=not target.startswith("windows-"),
        )
        for file_entry in release_assets.tool_runtime_files(lock, target, tool_name):
            _add_expected_file(
                expected,
                f"{target}/{file_entry['path']}",
                file_entry.get("sha256"),
                executable_bit=False,
            )
    for file_name in release_assets.lock_shared_files(lock):
        entry = lock["shared_files"][file_name]
        _add_expected_file(
            expected,
            entry["path"],
            entry.get("sha256"),
            executable_bit=False,
        )
    return expected


def _add_expected_file(
    expected: dict[str, dict[str, Any]],
    path: str,
    sha256: object,
    *,
    executable_bit: bool,
) -> None:
    if not isinstance(sha256, str):
        raise release_assets.ReleaseAssetError(f"{path}: missing sha256")
    existing = expected.get(path)
    entry = {"sha256": sha256, "executable_bit": executable_bit}
    if existing is not None and existing != entry:
        raise release_assets.ReleaseAssetError(f"conflicting runtime metadata for {path}")
    expected[path] = entry


def _validate_file_list(
    files: object,
    expected_files: dict[str, dict[str, Any]],
    target: str,
) -> None:
    if not isinstance(files, list):
        raise release_assets.ReleaseAssetError(f"{target} metadata files must be a list")
    actual: dict[str, dict[str, Any]] = {}
    for raw_entry in files:
        path, entry = _validated_file_entry(raw_entry, target)
        if path in actual:
            raise release_assets.ReleaseAssetError(f"{target} duplicate runtime file {path}")
        actual[path] = entry
    missing = set(expected_files) - set(actual)
    unknown = set(actual) - set(expected_files)
    if missing:
        raise release_assets.ReleaseAssetError(
            f"{target} metadata missing runtime file {sorted(missing)[0]}"
        )
    if unknown:
        raise release_assets.ReleaseAssetError(
            f"{target} metadata has unexpected runtime file {sorted(unknown)[0]}"
        )
    for path, expected in expected_files.items():
        entry = actual[path]
        if entry["sha256"] != expected["sha256"]:
            raise release_assets.ReleaseAssetError(f"{target}:{path} checksum mismatch")
        if entry["executable_bit"] != expected["executable_bit"]:
            raise release_assets.ReleaseAssetError(
                f"{target}:{path} executable_bit mismatch"
            )


def _validated_file_entry(raw_entry: object, target: str) -> tuple[str, dict[str, Any]]:
    if not isinstance(raw_entry, dict):
        raise release_assets.ReleaseAssetError(f"{target} file metadata must be an object")
    path = _required_str(raw_entry, "path")
    _validate_sha(raw_entry.get("sha256"), f"{target}:{path}")
    if not isinstance(raw_entry.get("size"), int) or raw_entry["size"] < 0:
        raise release_assets.ReleaseAssetError(f"{target}:{path} size is invalid")
    if not isinstance(raw_entry.get("executable_bit"), bool):
        raise release_assets.ReleaseAssetError(
            f"{target}:{path} executable_bit must be a boolean"
        )
    return path, raw_entry


def _validate_sha(value: object, label: str) -> None:
    if not isinstance(value, str) or not _is_sha256(value):
        raise release_assets.ReleaseAssetError(f"{label} sha256 is invalid")


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise release_assets.ReleaseAssetError(f"runtime metadata missing {key}")
    return value


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value.lower())


def handle_release_asset_error(exc: release_assets.ReleaseAssetError) -> int:
    print(f"ERROR: {exc}", file=sys.stderr)
    return 1
