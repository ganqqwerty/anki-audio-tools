"""Tests for decoupled runtime release metadata."""

from __future__ import annotations

import copy
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest
from scripts import (
    release_archive,
    release_asset_common,
    release_assets,
    release_runtime_remote,
)
from scripts import release_runtime_metadata as runtime_metadata

from tests.release_archive_fixtures import FAKE_RELEASE_INFO, lock_with_binary_hashes


def test_runtime_release_metadata_uses_runtime_tag_not_addon_version(tmp_path: Path) -> None:
    lock = lock_with_binary_hashes()
    pack_metadata = _runtime_pack_metadata(tmp_path, lock, runtime_version="1.0")

    metadata = runtime_metadata.build_runtime_release_metadata(
        "1.0",
        lock,
        pack_metadata,
        target_keys=["macos-arm64"],
    )

    pack = metadata["targets"]["macos-arm64"]["runtime_pack"]
    assert pack["name"] == "aqe-runtime-1.0-macos-arm64.zip"
    assert "/runtime-v1.0/" in pack["url"]
    assert "/v4.2/" not in pack["url"]


def test_runtime_release_metadata_contains_expected_inner_files(tmp_path: Path) -> None:
    lock = lock_with_binary_hashes()
    pack_metadata = _runtime_pack_metadata(tmp_path, lock, runtime_version="1.0")

    metadata = runtime_metadata.build_runtime_release_metadata(
        "1.0",
        lock,
        pack_metadata,
        target_keys=["macos-arm64"],
    )

    expected_paths = set(_target_payloads(lock, "macos-arm64"))
    actual_files = metadata["targets"]["macos-arm64"]["files"]
    assert {entry["path"] for entry in actual_files} == expected_paths
    assert all(isinstance(entry["size"], int) for entry in actual_files)
    assert all(len(entry["sha256"]) == 64 for entry in actual_files)


def test_runtime_manifest_id_stays_stable_when_only_url_changes(tmp_path: Path) -> None:
    lock = lock_with_binary_hashes()
    first = _runtime_pack_metadata(tmp_path, lock, runtime_version="1.0")
    second = copy.deepcopy(first)
    second["macos-arm64"]["url"] = "https://example.invalid/runtime-v1.0/alternate.zip"

    first_metadata = runtime_metadata.build_runtime_release_metadata(
        "1.0",
        lock,
        first,
        target_keys=["macos-arm64"],
    )
    second_metadata = runtime_metadata.build_runtime_release_metadata(
        "1.0",
        lock,
        second,
        target_keys=["macos-arm64"],
        runtime_base_url="https://example.invalid/runtime-v1.0",
    )

    assert first_metadata["runtime_manifest_id"] == second_metadata["runtime_manifest_id"]


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda metadata: metadata["targets"].pop("macos-arm64"), "targets"),
        (
            lambda metadata: metadata["targets"]["macos-arm64"]["runtime_pack"].update(
                {"name": "aqe-runtime-4.2-macos-arm64.zip"}
            ),
            "runtime pack name",
        ),
        (lambda metadata: metadata.update({"runtime_tag": "v1.0"}), "runtime metadata tag"),
        (
            lambda metadata: metadata["targets"]["macos-arm64"]["files"].pop(),
            "missing runtime file",
        ),
        (
            lambda metadata: metadata["targets"]["macos-arm64"]["files"][0].update(
                {"sha256": "0" * 64}
            ),
            "checksum mismatch",
        ),
    ],
)
def test_runtime_release_metadata_rejects_stale_data(
    tmp_path: Path,
    mutate,
    message: str,
) -> None:
    lock = lock_with_binary_hashes()
    metadata = runtime_metadata.build_runtime_release_metadata(
        "1.0",
        lock,
        _runtime_pack_metadata(tmp_path, lock, runtime_version="1.0"),
        target_keys=["macos-arm64"],
    )
    mutate(metadata)

    with pytest.raises(release_assets.ReleaseAssetError, match=message):
        runtime_metadata.validate_runtime_release_metadata(
            metadata,
            lock,
            target_keys=["macos-arm64"],
        )


def test_runtime_release_metadata_rejects_changed_asset_lock(tmp_path: Path) -> None:
    lock = lock_with_binary_hashes()
    metadata = runtime_metadata.build_runtime_release_metadata(
        "1.0",
        lock,
        _runtime_pack_metadata(tmp_path, lock, runtime_version="1.0"),
        target_keys=["macos-arm64"],
    )
    changed_lock = copy.deepcopy(lock)
    changed_lock["targets"]["macos-arm64"]["tools"]["ffmpeg"]["sha256"] = "0" * 64

    with pytest.raises(release_assets.ReleaseAssetError, match="does not match"):
        runtime_metadata.validate_runtime_release_metadata(
            metadata,
            changed_lock,
            target_keys=["macos-arm64"],
        )


def test_runtime_release_archive_validation_rejects_wrong_pack_sha(tmp_path: Path) -> None:
    lock = lock_with_binary_hashes()
    metadata = runtime_metadata.build_runtime_release_metadata(
        "1.0",
        lock,
        _runtime_pack_metadata(tmp_path, lock, runtime_version="1.0"),
        target_keys=["macos-arm64"],
    )
    target_entry = metadata["targets"]["macos-arm64"]
    target_entry["runtime_pack"]["sha256"] = "0" * 64

    with pytest.raises(release_assets.ReleaseAssetError, match="checksum mismatch"):
        release_runtime_remote.validate_runtime_release_archive(
            tmp_path / "aqe-runtime-1.0-macos-arm64.zip",
            "macos-arm64",
            target_entry,
        )


def test_runtime_release_archive_validation_rejects_inner_checksum(
    tmp_path: Path,
) -> None:
    lock = lock_with_binary_hashes()
    pack_metadata = _runtime_pack_metadata(tmp_path, lock, runtime_version="1.0")
    metadata = runtime_metadata.build_runtime_release_metadata(
        "1.0",
        lock,
        pack_metadata,
        target_keys=["macos-arm64"],
    )
    archive = tmp_path / "aqe-runtime-1.0-macos-arm64.zip"
    payloads = _target_payloads(lock, "macos-arm64")
    first_path = sorted(payloads)[0]
    payloads[first_path] = b"change"
    _write_zip(archive, payloads)
    target_entry = metadata["targets"]["macos-arm64"]
    target_entry["runtime_pack"]["sha256"] = release_asset_common.sha256_file(archive)
    target_entry["runtime_pack"]["size"] = archive.stat().st_size

    with pytest.raises(release_assets.ReleaseAssetError, match="checksum mismatch"):
        release_runtime_remote.validate_runtime_release_archive(
            archive,
            "macos-arm64",
            target_entry,
        )


def test_fake_addon_version_points_to_runtime_tag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock = lock_with_binary_hashes()
    metadata = runtime_metadata.build_runtime_release_metadata(
        "1.0",
        lock,
        _runtime_pack_metadata(tmp_path, lock, runtime_version="1.0"),
        target_keys=["macos-arm64"],
    )
    pack_metadata = runtime_metadata.runtime_pack_metadata_from_release(
        metadata,
        target_keys=["macos-arm64"],
    )
    file_metadata = runtime_metadata.file_metadata_by_path(
        pack_metadata,
        target_keys=["macos-arm64"],
    )
    monkeypatch.setattr(release_archive, "stage_source_tree", lambda _staging_dir: None)
    monkeypatch.setattr(release_archive, "latest_commit_info", lambda: FAKE_RELEASE_INFO)
    monkeypatch.setattr(release_archive, "DIST_DIR", tmp_path / "dist")

    staging_dir = tmp_path / "staging"
    release_archive.stage_release_tree(
        staging_dir,
        lock=lock,
        target_keys=["macos-arm64"],
        runtime_pack_metadata=pack_metadata,
        runtime_file_metadata=file_metadata,
    )
    archive = release_archive.build_archive("4.2", staging_dir)

    with zipfile.ZipFile(archive, "r") as zf:
        manifest = json.loads(zf.read("bin/runtime_manifest.json").decode("utf-8"))

    pack = manifest["targets"]["macos-arm64"]["runtime_pack"]
    assert "/runtime-v1.0/" in pack["url"]
    assert "/v4.2/" not in pack["url"]


def _runtime_pack_metadata(
    tmp_path: Path,
    lock: dict,
    *,
    runtime_version: str,
    target: str = "macos-arm64",
) -> dict[str, dict[str, Any]]:
    payloads = _target_payloads(lock, target)
    archive = tmp_path / f"aqe-runtime-{runtime_version}-{target}.zip"
    _write_zip(archive, payloads)
    files = [
        {
            "source_path": archive,
            "path": path,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size": len(payload),
            "executable_bit": _is_executable_path(lock, target, path),
        }
        for path, payload in sorted(payloads.items())
    ]
    return {
        target: {
            "path": archive,
            "name": archive.name,
            "url": (
                f"https://github.com/ganqqwerty/anki-audio-tools/releases/download/"
                f"runtime-v{runtime_version}/{archive.name}"
            ),
            "sha256": release_asset_common.sha256_file(archive),
            "size": archive.stat().st_size,
            "files": files,
        }
    }


def _target_payloads(lock: dict, target: str) -> dict[str, bytes]:
    payloads: dict[str, bytes] = {}
    for tool_name in release_asset_common.bundled_tool_names(
        release_assets.lock_tools(lock, target),
        include_ffmpeg=True,
    ):
        tool_entry = lock["targets"][target]["tools"][tool_name]
        payloads[f"{target}/{tool_entry['executable']}"] = b"binary"
        for file_entry in release_assets.tool_runtime_files(lock, target, tool_name):
            payloads.setdefault(f"{target}/{file_entry['path']}", b"")
    for file_name in release_assets.lock_shared_files(lock):
        shared_entry = lock["shared_files"][file_name]
        payloads.setdefault(shared_entry["path"], b"")
    return payloads


def _is_executable_path(lock: dict, target: str, path: str) -> bool:
    for tool_name in release_assets.lock_tools(lock, target):
        tool_entry = lock["targets"][target]["tools"][tool_name]
        if path == f"{target}/{tool_entry['executable']}":
            return not target.startswith("windows-")
    return False


def _write_zip(path: Path, payloads: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, payload in sorted(payloads.items()):
            zf.writestr(name, payload)
