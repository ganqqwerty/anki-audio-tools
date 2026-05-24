"""Shared helpers for release asset tests."""

from __future__ import annotations

import hashlib
import io
import tarfile
from pathlib import Path

from scripts import release_assets


def write_tar_bz2(path: Path, files: dict[str, bytes]) -> None:
    with tarfile.open(path, "w:bz2") as tf:
        for name, payload in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            tf.addfile(info, io.BytesIO(payload))


def write_verified_target_sources(lock: dict, cache_dir: Path, addon_bin_dir: Path, target: str) -> None:
    for tool_name in release_assets.lock_tools(lock, target):
        entry = lock["targets"][target]["tools"][tool_name]
        payload = f"{target}/{tool_name}".encode()
        write_locked_file(release_assets.source_tool_binary_path(cache_dir, addon_bin_dir, target, tool_name, entry), payload, entry)
        for file_entry in release_assets.tool_runtime_files(lock, target, tool_name):
            runtime_payload = f"{target}/{tool_name}/{file_entry['path']}".encode()
            write_locked_file(release_assets.tracked_runtime_file_path(addon_bin_dir, target, file_entry), runtime_payload, file_entry)
    for file_name in release_assets.SHARED_FILE_NAMES:
        entry = lock["shared_files"][file_name]
        write_locked_file(release_assets.tracked_shared_asset_path(addon_bin_dir, entry), f"shared/{file_name}".encode(), entry)


def write_verified_target_tracked_files(lock: dict, addon_bin_dir: Path, target: str) -> None:
    for tool_name in release_assets.lock_tools(lock, target):
        if tool_name in {"ffmpeg", "ffprobe"}:
            continue
        entry = lock["targets"][target]["tools"][tool_name]
        write_locked_file(release_assets.tracked_tool_binary_path(addon_bin_dir, target, entry), f"{target}/{tool_name}".encode(), entry)
        for file_entry in release_assets.tool_runtime_files(lock, target, tool_name):
            runtime_payload = f"{target}/{tool_name}/{file_entry['path']}".encode()
            write_locked_file(release_assets.tracked_runtime_file_path(addon_bin_dir, target, file_entry), runtime_payload, file_entry)
    for file_name in release_assets.SHARED_FILE_NAMES:
        entry = lock["shared_files"][file_name]
        write_locked_file(release_assets.tracked_shared_asset_path(addon_bin_dir, entry), f"shared/{file_name}".encode(), entry)


def write_locked_file(path: Path, payload: bytes, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    entry["sha256"] = hashlib.sha256(payload).hexdigest()


def write_spleeter_smoke_outputs(command: list[str]) -> None:
    for arg in command:
        if arg.startswith("--output-vocals-wav=") or arg.startswith("--output-accompaniment-wav="):
            Path(arg.split("=", 1)[1]).write_bytes(b"stem wav")
