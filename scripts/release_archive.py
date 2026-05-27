"""Release source staging, archive writing, and archive validation."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

from scripts import release_assets, release_validation
from scripts.release_manifest_selection import (
    ADDON_DIR,
    ROOT,
    release_manifest_files,
    should_include,
)
from scripts.release_runtime import write_runtime_manifest

DIST_DIR = ROOT / "dist"
WARN_ARCHIVE_BYTES = 125 * 1024 * 1024
FAIL_ARCHIVE_BYTES = 200 * 1024 * 1024


def stage_source_tree(staging_dir: Path) -> None:
    """Copy packageable add-on source files into the staging directory."""
    for path in sorted(ADDON_DIR.rglob("*")):
        if path.is_file() and should_include(path):
            target = staging_dir / path.relative_to(ADDON_DIR)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def latest_commit_info() -> dict[str, object]:
    """Return release metadata for the current HEAD commit."""
    result = subprocess.run(
        ["git", "show", "-s", "--format=%H%n%B", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        print(f"ERROR: Could not read latest git commit metadata{': ' + detail if detail else ''}")
        sys.exit(1)
    commit_hash, _, commit_message = result.stdout.partition("\n")
    commit_message = commit_message.strip()
    if not commit_hash or not commit_message:
        print("ERROR: Latest git commit metadata is incomplete")
        sys.exit(1)
    return {
        "schema_version": 1,
        "commit_hash": commit_hash,
        "commit_message": commit_message,
    }


def write_release_info(staging_dir: Path) -> None:
    """Write release metadata into a staged add-on tree."""
    staging_dir.mkdir(parents=True, exist_ok=True)
    (staging_dir / "release_info.json").write_text(
        json.dumps(latest_commit_info(), indent=2) + "\n",
        encoding="utf-8",
    )


def stage_release_tree(
    staging_dir: Path,
    *,
    lock: dict,
    target_keys: list[str] | None = None,
    include_ffmpeg: bool = True,
    embed_runtime: bool = False,
    runtime_pack_metadata: dict[str, dict[str, Any]] | None = None,
    runtime_source_bin_dir: Path | None = None,
) -> None:
    """Stage source, release metadata, optional embedded runtime, and runtime manifest."""
    stage_source_tree(staging_dir)
    write_release_info(staging_dir)
    staging_bin_dir = staging_dir / "bin"
    if embed_runtime:
        release_assets.stage_assets(
            lock,
            destination=staging_bin_dir,
            target_keys=target_keys,
            include_ffmpeg=include_ffmpeg,
        )
        runtime_source_bin_dir = staging_bin_dir
    write_runtime_manifest(
        staging_bin_dir,
        lock,
        target_keys=target_keys,
        include_ffmpeg=include_ffmpeg,
        runtime_pack_metadata=runtime_pack_metadata,
        source_bin_dir=runtime_source_bin_dir,
    )


def build_archive(
    version: str,
    staging_dir: Path,
    *,
    target_label: str = "all",
    include_ffmpeg: bool = True,
) -> Path:
    """Write a staged add-on tree to an `.ankiaddon` archive."""
    DIST_DIR.mkdir(exist_ok=True)
    suffix = "" if target_label == "all" else f"-{target_label}"
    if not include_ffmpeg:
        suffix = f"{suffix}-external-ffmpeg" if suffix else "-external-ffmpeg"
    archive = DIST_DIR / f"anki-audio-quick-editor-{version}{suffix}.ankiaddon"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(staging_dir.rglob("*")):
            if path.is_file():
                zf.write(path, str(path.relative_to(staging_dir)))
    return archive


def validate_archive(
    archive: Path,
    *,
    allow_large_archive: bool = False,
    lock: dict | None = None,
    target_keys: list[str] | None = None,
    include_ffmpeg: bool = True,
    embed_runtime: bool = False,
) -> None:
    """Validate release archive contents and size gates."""
    release_validation.validate_archive(
        archive,
        allow_large_archive=allow_large_archive,
        lock=lock,
        target_keys=target_keys,
        include_ffmpeg=include_ffmpeg,
        embed_runtime=embed_runtime,
        release_manifest_files=release_manifest_files,
        warn_archive_bytes=WARN_ARCHIVE_BYTES,
        fail_archive_bytes=FAIL_ARCHIVE_BYTES,
    )
