"""Remote upload and verification helpers for runtime releases."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from scripts import release_asset_common, release_assets

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"


def verify_runtime_release_urls(metadata: dict[str, Any]) -> None:
    """Download runtime packs and validate whole archives plus inner members."""

    with tempfile.TemporaryDirectory(prefix="anki-audio-runtime-verify-") as tmp:
        tmp_dir = Path(tmp)
        for target, target_entry in metadata["targets"].items():
            pack = target_entry["runtime_pack"]
            destination = tmp_dir / pack["name"]
            try:
                with (
                    urllib.request.urlopen(pack["url"], timeout=60) as response,  # nosec B310
                    destination.open("wb") as handle,
                ):
                    shutil.copyfileobj(response, handle)
            except (OSError, urllib.error.URLError) as exc:
                raise release_assets.ReleaseAssetError(
                    f"could not download runtime asset {pack['url']}: {exc}"
                ) from exc
            validate_runtime_release_archive(destination, target, target_entry)


def validate_runtime_release_archive(
    archive: Path,
    target: str,
    target_entry: dict[str, Any],
) -> None:
    """Validate a runtime pack archive against tracked metadata."""

    pack = target_entry["runtime_pack"]
    actual_pack_sha = release_asset_common.sha256_file(archive)
    if actual_pack_sha != pack["sha256"]:
        raise release_assets.ReleaseAssetError(
            f"{target} runtime pack checksum mismatch: expected {pack['sha256']}, "
            f"got {actual_pack_sha}"
        )
    if archive.stat().st_size != pack["size"]:
        raise release_assets.ReleaseAssetError(f"{target} runtime pack size mismatch")
    expected = {entry["path"]: entry for entry in target_entry["files"]}
    try:
        _validate_runtime_zip_members(archive, expected)
    except zipfile.BadZipFile as exc:
        raise release_assets.ReleaseAssetError(
            f"{archive.name} is not a valid zip archive"
        ) from exc


def upload_runtime_release_assets(
    metadata: dict[str, Any],
    *,
    dist_dir: Path = DIST_DIR,
) -> None:
    """Upload locally built runtime packs to the immutable runtime release tag."""

    pack_paths: list[str] = []
    for target, target_entry in metadata["targets"].items():
        archive = dist_dir / target_entry["runtime_pack"]["name"]
        if not archive.is_file():
            raise release_assets.ReleaseAssetError(f"missing runtime pack {archive}")
        validate_runtime_release_archive(archive, target, target_entry)
        pack_paths.append(str(archive))
    command = ["gh", "release", "upload", metadata["runtime_tag"], *pack_paths]
    if shutil.which("gh") is None:
        print("gh not found; upload runtime packs with:")
        print(" ".join(command))
        return
    subprocess.run(command, cwd=ROOT, check=True)


def _validate_runtime_zip_members(
    archive: Path,
    expected: dict[str, dict[str, Any]],
) -> None:
    with zipfile.ZipFile(archive, "r") as zf:
        actual = {name for name in zf.namelist() if not name.endswith("/")}
        unsafe = [name for name in actual if _unsafe_runtime_pack_member(name)]
        if unsafe:
            raise release_assets.ReleaseAssetError(
                f"{archive.name} contains unsafe member {unsafe[0]}"
            )
        unknown = actual - set(expected)
        missing = set(expected) - actual
        if unknown:
            raise release_assets.ReleaseAssetError(
                f"{archive.name} contains unexpected file {sorted(unknown)[0]}"
            )
        if missing:
            raise release_assets.ReleaseAssetError(
                f"{archive.name} is missing file {sorted(missing)[0]}"
            )
        for name, entry in expected.items():
            data = zf.read(name)
            if len(data) != entry["size"]:
                raise release_assets.ReleaseAssetError(
                    f"{archive.name}:{name} size mismatch"
                )
            actual_sha = hashlib.sha256(data).hexdigest()
            if actual_sha != entry["sha256"]:
                raise release_assets.ReleaseAssetError(
                    f"{archive.name}:{name} checksum mismatch"
                )


def _unsafe_runtime_pack_member(name: str) -> bool:
    path = Path(name)
    return path.is_absolute() or ".." in path.parts or not path.parts
