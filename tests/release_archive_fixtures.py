from __future__ import annotations

import copy
import hashlib
import json
import zipfile
from pathlib import Path

from scripts import release, release_assets

FAKE_COMMIT_HASH = "a" * 40
FAKE_RELEASE_INFO = {
    "schema_version": 1,
    "commit_hash": FAKE_COMMIT_HASH,
    "commit_message": "Package release metadata",
}


def write_archive(
    path: Path,
    names: list[str],
    executable_names: set[str] | None = None,
    *,
    release_info: bytes | None = None,
    runtime_manifest: bytes | None = None,
) -> None:
    executable_names = executable_names or set()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in names:
            info = zipfile.ZipInfo(name)
            info.external_attr = ((0o755 if name in executable_names else 0o644) & 0xFFFF) << 16
            if name in executable_names:
                content = b"binary"
            elif name == "bin/THIRD_PARTY_NOTICES.md":
                content = b"FFmpeg LAME DeepFilterNet RNNoise DPDFNet Sherpa Spleeter Silero"
            elif name == "release_info.json":
                content = release_info or (json.dumps(FAKE_RELEASE_INFO) + "\n").encode()
            elif name == "bin/runtime_manifest.json":
                content = runtime_manifest or runtime_manifest_bytes()
            else:
                content = b""
            zf.writestr(info, content)


def complete_manifest_names() -> list[str]:
    return release.release_manifest_files(release_assets.load_lock())


def complete_embedded_manifest_names() -> list[str]:
    return release.release_manifest_files(release_assets.load_lock(), embed_runtime=True)


def complete_executable_names() -> set[str]:
    return set(release.release_runtime_executables(release_assets.load_lock()))


def external_ffmpeg_manifest_names() -> list[str]:
    return release.release_manifest_files(release_assets.load_lock(), include_ffmpeg=False, embed_runtime=True)


def external_ffmpeg_executable_names() -> set[str]:
    return set(release.release_runtime_executables(release_assets.load_lock(), include_ffmpeg=False))


def lock_with_binary_hashes(content: bytes = b"binary") -> dict:
    lock = copy.deepcopy(release_assets.load_lock())
    digest = hashlib.sha256(content).hexdigest()
    for target in release_assets.lock_targets(lock):
        for tool_name in release_assets.lock_tools(lock, target):
            lock["targets"][target]["tools"][tool_name]["sha256"] = digest
    empty_digest = hashlib.sha256(b"").hexdigest()
    for target in release_assets.lock_targets(lock):
        for tool_name in release_assets.lock_tools(lock, target):
            for file_entry in release_assets.tool_runtime_files(lock, target, tool_name):
                file_entry["sha256"] = empty_digest
    for file_name in release_assets.lock_shared_files(lock):
        lock["shared_files"][file_name]["sha256"] = empty_digest
    return lock


def runtime_manifest_bytes(lock: dict | None = None) -> bytes:
    lock = lock or lock_with_binary_hashes()
    manifest = {
        "schema_version": 1,
        "runtime_manifest_id": "test-runtime",
        "targets": {},
        "shared_files": {},
    }
    for target in release_assets.lock_targets(lock):
        target_entry = {
            "runtime_pack": {
                "name": f"aqe-runtime-test-{target}.zip",
                "url": f"https://example.com/aqe-runtime-test-{target}.zip",
                "sha256": "f" * 64,
                "size": 1,
            },
            "tools": {},
            "shared_files": {},
        }
        for tool_name in release_assets.lock_tools(lock, target):
            tool_entry = lock["targets"][target]["tools"][tool_name]
            target_entry["tools"][tool_name] = {
                "executable": tool_entry["executable"],
                "path": f"{target}/{tool_entry['executable']}",
                "sha256": tool_entry["sha256"],
                "size": len(b"binary"),
                "executable_bit": not target.startswith("windows-"),
                "diagnostic_args": tool_entry.get("diagnostic_args"),
                "runtime_files": [
                    {
                        "path": file_entry["path"],
                        "sha256": file_entry["sha256"],
                        "size": 0,
                    }
                    for file_entry in release_assets.tool_runtime_files(lock, target, tool_name)
                ],
            }
        for file_name in release_assets.lock_shared_files(lock):
            shared_entry = lock["shared_files"][file_name]
            target_entry["shared_files"][file_name] = {
                "path": shared_entry["path"],
                "sha256": shared_entry["sha256"],
                "size": 0,
            }
        manifest["targets"][target] = target_entry
    for file_name in release_assets.lock_shared_files(lock):
        shared_entry = lock["shared_files"][file_name]
        manifest["shared_files"][file_name] = {
            "path": shared_entry["path"],
            "sha256": shared_entry["sha256"],
            "size": 0,
        }
    return (json.dumps(manifest) + "\n").encode()
