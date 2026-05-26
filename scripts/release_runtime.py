"""Runtime pack and manifest helpers for release packaging."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
WARN_RUNTIME_PACK_BYTES = 500 * 1024 * 1024
DEFAULT_RUNTIME_RELEASE_REPO = "https://github.com/ganqqwerty/anki-audio-tools"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release_assets  # noqa: E402
import scripts.release_asset_common as release_asset_common  # noqa: E402


def write_runtime_manifest(
    staging_bin_dir: Path,
    lock: dict,
    *,
    target_keys: list[str] | None = None,
    include_ffmpeg: bool = True,
    runtime_pack_metadata: dict[str, dict[str, Any]] | None = None,
    source_bin_dir: Path | None = None,
) -> None:
    staging_bin_dir.mkdir(parents=True, exist_ok=True)
    selected_targets = target_keys or release_assets.lock_targets(lock)
    source_bin_dir = source_bin_dir or staging_bin_dir
    manifest = {
        "schema_version": lock["schema_version"],
        "release_ready": bool(lock.get("release_ready", False)),
        "targets": {
            target: _runtime_manifest_target(
                lock,
                target,
                include_ffmpeg=include_ffmpeg,
                runtime_pack_metadata=runtime_pack_metadata,
                source_bin_dir=source_bin_dir,
            )
            for target in selected_targets
        },
        "shared_files": {
            file_name: _runtime_manifest_shared_entry(lock, file_name, source_bin_dir=source_bin_dir)
            for file_name in release_assets.lock_shared_files(lock)
        },
    }
    manifest["runtime_manifest_id"] = _runtime_manifest_id(manifest)
    (staging_bin_dir / "runtime_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def _runtime_manifest_target(
    lock: dict,
    target: str,
    *,
    include_ffmpeg: bool,
    runtime_pack_metadata: dict[str, dict[str, Any]] | None,
    source_bin_dir: Path,
) -> dict[str, Any]:
    target_entry: dict[str, Any] = {
        "tools": {
            tool_name: _runtime_manifest_tool_entry(
                lock,
                target,
                tool_name,
                source_bin_dir=source_bin_dir,
            )
            for tool_name in release_asset_common.bundled_tool_names(
                release_assets.lock_tools(lock, target),
                include_ffmpeg=include_ffmpeg,
            )
        },
        "shared_files": {
            file_name: _runtime_manifest_shared_entry(lock, file_name, source_bin_dir=source_bin_dir)
            for file_name in release_assets.lock_shared_files(lock)
        },
    }
    if runtime_pack_metadata is not None:
        pack = runtime_pack_metadata.get(target)
        if pack is None:
            raise release_assets.ReleaseAssetError(f"{target}: missing runtime pack metadata")
        target_entry["runtime_pack"] = {
            "name": pack["name"],
            "url": pack["url"],
            "sha256": pack["sha256"],
            "size": pack["size"],
        }
    return target_entry


def _runtime_manifest_tool_entry(
    lock: dict,
    target: str,
    tool_name: str,
    *,
    source_bin_dir: Path,
) -> dict[str, Any]:
    entry = lock["targets"][target]["tools"][tool_name]
    executable = entry["executable"]
    path = f"{target}/{executable}"
    result: dict[str, Any] = {
        "executable": executable,
        "path": path,
        "sha256": entry.get("sha256"),
        "diagnostic_args": entry.get("diagnostic_args"),
        "executable_bit": not target.startswith("windows-"),
        "runtime_files": [
            _runtime_manifest_support_entry(file_entry, target=target, source_bin_dir=source_bin_dir)
            for file_entry in release_assets.tool_runtime_files(lock, target, tool_name)
        ],
    }
    _add_file_size(result, source_bin_dir / path)
    return result


def _runtime_manifest_support_entry(
    file_entry: dict[str, Any],
    *,
    target: str,
    source_bin_dir: Path,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": file_entry["path"],
        "sha256": file_entry.get("sha256"),
    }
    _add_file_size(result, source_bin_dir / target / file_entry["path"])
    return result


def _runtime_manifest_shared_entry(lock: dict, file_name: str, *, source_bin_dir: Path) -> dict[str, Any]:
    entry = lock["shared_files"][file_name]
    result: dict[str, Any] = {
        "path": entry["path"],
        "sha256": entry.get("sha256"),
    }
    _add_file_size(result, source_bin_dir / entry["path"])
    return result


def _add_file_size(entry: dict[str, Any], path: Path) -> None:
    if path.is_file():
        entry["size"] = path.stat().st_size


def _runtime_manifest_id(manifest: dict[str, Any]) -> str:
    targets: dict[str, Any] = {}
    for target, target_entry in manifest["targets"].items():
        target_payload = {
            key: value
            for key, value in target_entry.items()
            if key != "runtime_pack"
        }
        targets[target] = target_payload
    payload = {
        "schema_version": manifest["schema_version"],
        "targets": targets,
        "shared_files": manifest.get("shared_files", {}),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def build_runtime_packs(
    version: str,
    lock: dict,
    *,
    source_bin_dir: Path,
    target_keys: list[str] | None,
    include_ffmpeg: bool,
    runtime_base_url: str,
) -> dict[str, dict[str, Any]]:
    DIST_DIR.mkdir(exist_ok=True)
    metadata: dict[str, dict[str, Any]] = {}
    for target in target_keys or release_assets.lock_targets(lock):
        archive = DIST_DIR / _runtime_pack_asset_name(version, target)
        file_entries = _runtime_pack_entries(
            lock,
            target,
            source_bin_dir=source_bin_dir,
            include_ffmpeg=include_ffmpeg,
        )
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_entry in file_entries:
                zf.write(file_entry["source_path"], file_entry["path"])
        size = archive.stat().st_size
        if size > WARN_RUNTIME_PACK_BYTES:
            print(f"WARNING: runtime pack {archive.name} is {size} bytes")
        metadata[target] = {
            "path": archive,
            "name": archive.name,
            "url": f"{runtime_base_url.rstrip('/')}/{archive.name}",
            "sha256": release_asset_common.sha256_file(archive),
            "size": size,
            "files": file_entries,
        }
    return metadata


def default_runtime_base_url(version: str) -> str:
    return f"{DEFAULT_RUNTIME_RELEASE_REPO}/releases/download/v{version}"


def validate_runtime_packs(runtime_pack_metadata: dict[str, dict[str, Any]]) -> None:
    for target, pack in runtime_pack_metadata.items():
        archive = Path(pack["path"])
        expected = {entry["path"]: entry for entry in pack["files"]}
        try:
            with zipfile.ZipFile(archive, "r") as zf:
                actual = {name for name in zf.namelist() if not name.endswith("/")}
                unsafe = [name for name in actual if _unsafe_runtime_pack_member(name)]
                if unsafe:
                    _validation_exit(f"{archive.name} contains unsafe member {unsafe[0]}")
                unknown = actual - set(expected)
                missing = set(expected) - actual
                if unknown:
                    _validation_exit(f"{archive.name} contains unexpected file {sorted(unknown)[0]}")
                if missing:
                    _validation_exit(f"{archive.name} is missing file {sorted(missing)[0]}")
                for name, entry in expected.items():
                    data = zf.read(name)
                    if len(data) != entry["size"]:
                        _validation_exit(f"{archive.name}:{name} size mismatch")
                    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                        _validation_exit(f"{archive.name}:{name} checksum mismatch")
        except zipfile.BadZipFile:
            _validation_exit(f"{archive.name} is not a valid zip archive")
        actual_pack_sha = release_asset_common.sha256_file(archive)
        if actual_pack_sha != pack["sha256"]:
            _validation_exit(f"{target} runtime pack checksum mismatch")


def upload_runtime_assets(version: str, runtime_pack_metadata: dict[str, dict[str, Any]]) -> None:
    tag = f"v{version}"
    pack_paths = [str(pack["path"]) for pack in runtime_pack_metadata.values()]
    command = ["gh", "release", "upload", tag, *pack_paths, "--clobber"]
    if shutil.which("gh") is None:
        print("gh not found; upload runtime packs with:")
        print(" ".join(command))
        return
    subprocess.run(command, cwd=ROOT, check=True)


def verify_runtime_urls(runtime_pack_metadata: dict[str, dict[str, Any]]) -> None:
    with tempfile.TemporaryDirectory(prefix="anki-audio-runtime-verify-") as tmp:
        tmp_dir = Path(tmp)
        for pack in runtime_pack_metadata.values():
            destination = tmp_dir / pack["name"]
            try:
                with urllib.request.urlopen(pack["url"], timeout=60) as response, destination.open("wb") as handle:  # nosec B310
                    shutil.copyfileobj(response, handle)
            except (OSError, urllib.error.URLError) as exc:
                _validation_exit(f"could not download runtime asset {pack['url']}: {exc}")
            actual_sha = release_asset_common.sha256_file(destination)
            if actual_sha != pack["sha256"]:
                _validation_exit(
                    f"runtime asset {pack['name']} is stale: expected {pack['sha256']}, got {actual_sha}"
                )


def _runtime_pack_asset_name(version: str, target: str) -> str:
    return f"aqe-runtime-{version}-{target}.zip"


def _runtime_pack_entries(
    lock: dict,
    target: str,
    *,
    source_bin_dir: Path,
    include_ffmpeg: bool,
) -> list[dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for tool_name in release_asset_common.bundled_tool_names(
        release_assets.lock_tools(lock, target),
        include_ffmpeg=include_ffmpeg,
    ):
        tool_entry = lock["targets"][target]["tools"][tool_name]
        executable_path = f"{target}/{tool_entry['executable']}"
        _add_runtime_pack_entry(
            entries,
            source_bin_dir / executable_path,
            executable_path,
            executable_bit=not target.startswith("windows-"),
        )
        for file_entry in release_assets.tool_runtime_files(lock, target, tool_name):
            support_path = f"{target}/{file_entry['path']}"
            _add_runtime_pack_entry(
                entries,
                source_bin_dir / support_path,
                support_path,
                executable_bit=False,
            )
    for file_name in release_assets.lock_shared_files(lock):
        shared_path = lock["shared_files"][file_name]["path"]
        _add_runtime_pack_entry(
            entries,
            source_bin_dir / shared_path,
            shared_path,
            executable_bit=False,
        )
    return [entries[name] for name in sorted(entries)]


def _add_runtime_pack_entry(
    entries: dict[str, dict[str, Any]],
    source: Path,
    archive_path: str,
    *,
    executable_bit: bool,
) -> None:
    if archive_path in entries:
        return
    if not source.is_file():
        raise release_assets.ReleaseAssetError(f"runtime pack source is missing: {source}")
    entries[archive_path] = {
        "source_path": source,
        "path": archive_path,
        "sha256": release_asset_common.sha256_file(source),
        "size": source.stat().st_size,
        "executable_bit": executable_bit,
    }


def _unsafe_runtime_pack_member(name: str) -> bool:
    path = Path(name)
    return path.is_absolute() or ".." in path.parts or not path.parts


def _validation_exit(message: str) -> None:
    print(f"VALIDATION ERROR: {message}")
    sys.exit(1)
