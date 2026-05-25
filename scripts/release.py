#!/usr/bin/env python3
"""Build a validated .ankiaddon package for Anki Audio Quick Editor."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"
DIST_DIR = ROOT / "dist"
INCLUDE_EXTENSIONS = {".py", ".html", ".json", ".pyi", ".typed", ".js", ".css"}
SOURCE_BIN_FILES = {
    "bin/README.md",
    "bin/THIRD_PARTY_NOTICES.md",
}
EXCLUDE_DIRS = {"aqe_artifacts"}
BASE_REQUIRED_ARCHIVE_FILES = (
    "__init__.py",
    "manifest.json",
    "release_info.json",
    "config.json",
    "config.schema.json",
    "contracts_generated.py",
    "templates/settings/settings_bundle.js",
    "templates/settings/settings_bundle.css",
    "templates/editor/editor_bundle.js",
    "templates/editor/editor_bundle.css",
    "templates/batch/batch_bundle.js",
    "templates/batch/batch_bundle.css",
    "bin/README.md",
    "bin/THIRD_PARTY_NOTICES.md",
    "bin/runtime_manifest.json",
)
WARN_ARCHIVE_BYTES = 125 * 1024 * 1024
FAIL_ARCHIVE_BYTES = 200 * 1024 * 1024

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release_assets  # noqa: E402
import scripts.release_asset_common as release_asset_common  # noqa: E402
import scripts.release_bundle_freshness as release_bundle_freshness  # noqa: E402
import scripts.release_validation as release_validation  # noqa: E402
from dev import _find_anki_python  # noqa: E402
from scripts.release_runtime import (  # noqa: E402
    build_runtime_packs as _build_runtime_packs,
)
from scripts.release_runtime import (
    default_runtime_base_url as _default_runtime_base_url,
)
from scripts.release_runtime import (
    upload_runtime_assets as _upload_runtime_assets,
)
from scripts.release_runtime import (
    validate_runtime_packs as _validate_runtime_packs,
)
from scripts.release_runtime import (
    verify_runtime_urls as _verify_runtime_urls,
)
from scripts.release_runtime import (
    write_runtime_manifest as _write_runtime_manifest,
)


def _read_pyproject_version() -> str:
    match = re.search(r'^version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.MULTILINE)
    if match is None:
        print("ERROR: Could not find version in pyproject.toml")
        sys.exit(1)
    return match.group(1)


def _read_package_version() -> str:
    match = re.search(
        r'^__version__\s*=\s*"([^"]+)"',
        (ADDON_DIR / "_version.py").read_text(),
        re.MULTILINE,
    )
    if match is None:
        print("ERROR: Could not find __version__ in _version.py")
        sys.exit(1)
    return match.group(1)


def _verify_versions(version: str) -> None:
    pyproject_ver = _read_pyproject_version()
    package_ver = _read_package_version()
    if pyproject_ver != version or package_ver != version:
        print(
            "ERROR: version mismatch "
            f"(pyproject={pyproject_ver!r}, package={package_ver!r}, requested={version!r})"
        )
        sys.exit(1)


def _run_checks(*, full: bool) -> None:
    release_bundle_freshness.run_checks(ROOT, full=full)


def _build_required_artifacts() -> None:
    release_bundle_freshness.build_required_artifacts(ROOT, ADDON_DIR)


def _should_include(path: Path) -> bool:
    if path.name == "meta.json" or "__pycache__" in path.parts:
        return False
    if path.name == ".DS_Store" or path.suffix in {".pyc", ".so", ".pyd", ".c"}:
        return False
    rel = path.relative_to(ADDON_DIR)
    if rel.parts and rel.parts[0] in EXCLUDE_DIRS:
        return False
    if rel.parts and rel.parts[0] == "bin":
        return rel.as_posix() in SOURCE_BIN_FILES
    if rel.parts and rel.parts[0] == "vendor":
        return True
    return path.suffix in INCLUDE_EXTENSIONS


def release_runtime_executables(
    lock: dict | None = None,
    *,
    target_keys: list[str] | None = None,
    include_ffmpeg: bool = True,
) -> list[str]:
    """Return required runtime executable archive paths from the asset lock."""
    lock = lock or release_assets.load_lock()
    names: list[str] = []
    for target in target_keys or release_assets.lock_targets(lock):
        for tool_name in release_asset_common.bundled_tool_names(
            release_assets.lock_tools(lock, target),
            include_ffmpeg=include_ffmpeg,
        ):
            executable = lock["targets"][target]["tools"][tool_name]["executable"]
            names.append(f"bin/{target}/{executable}")
    return sorted(names)


def release_runtime_shared_files(lock: dict | None = None) -> list[str]:
    """Return required shared runtime asset archive paths from the asset lock."""
    return release_asset_common.release_runtime_shared_files(lock or release_assets.load_lock())


def release_runtime_support_files(
    lock: dict | None = None,
    *,
    target_keys: list[str] | None = None,
) -> list[str]:
    """Return required target-specific runtime support file archive paths."""

    return release_asset_common.release_runtime_support_files(lock or release_assets.load_lock(), target_keys=target_keys)


def release_manifest_files(
    lock: dict | None = None,
    *,
    target_keys: list[str] | None = None,
    include_ffmpeg: bool = True,
    embed_runtime: bool = False,
) -> list[str]:
    """Return archive files required for a self-sufficient release."""
    required = set(BASE_REQUIRED_ARCHIVE_FILES)
    if embed_runtime:
        required.update(release_runtime_executables(lock, target_keys=target_keys, include_ffmpeg=include_ffmpeg))
        required.update(release_runtime_support_files(lock, target_keys=target_keys))
        required.update(release_runtime_shared_files(lock))
    for path in ADDON_DIR.rglob("*"):
        if path.is_file() and _should_include(path):
            required.add(path.relative_to(ADDON_DIR).as_posix())
    return sorted(required)


def _stage_source_tree(staging_dir: Path) -> None:
    for path in sorted(ADDON_DIR.rglob("*")):
        if path.is_file() and _should_include(path):
            target = staging_dir / path.relative_to(ADDON_DIR)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def _latest_commit_info() -> dict[str, object]:
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


def _write_release_info(staging_dir: Path) -> None:
    staging_dir.mkdir(parents=True, exist_ok=True)
    (staging_dir / "release_info.json").write_text(
        json.dumps(_latest_commit_info(), indent=2) + "\n",
        encoding="utf-8",
    )


def _stage_release_tree(
    staging_dir: Path,
    *,
    lock: dict,
    target_keys: list[str] | None = None,
    include_ffmpeg: bool = True,
    embed_runtime: bool = False,
    runtime_pack_metadata: dict[str, dict[str, Any]] | None = None,
    runtime_source_bin_dir: Path | None = None,
) -> None:
    _stage_source_tree(staging_dir)
    _write_release_info(staging_dir)
    staging_bin_dir = staging_dir / "bin"
    if embed_runtime:
        release_assets.stage_assets(
            lock,
            destination=staging_bin_dir,
            target_keys=target_keys,
            include_ffmpeg=include_ffmpeg,
        )
        runtime_source_bin_dir = staging_bin_dir
    _write_runtime_manifest(
        staging_bin_dir,
        lock,
        target_keys=target_keys,
        include_ffmpeg=include_ffmpeg,
        runtime_pack_metadata=runtime_pack_metadata,
        source_bin_dir=runtime_source_bin_dir,
    )


def _build_archive(
    version: str,
    staging_dir: Path,
    *,
    target_label: str = "all",
    include_ffmpeg: bool = True,
) -> Path:
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


def _validate_archive(
    archive: Path,
    *,
    allow_large_archive: bool = False,
    lock: dict | None = None,
    target_keys: list[str] | None = None,
    include_ffmpeg: bool = True,
    embed_runtime: bool = False,
) -> None:
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


def _selected_release_targets(value: str, lock: dict) -> tuple[list[str] | None, str]:
    return release_validation.selected_release_targets(value, lock)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build .ankiaddon package")
    parser.add_argument("--version", help="Override version")
    parser.add_argument(
        "--skip-quality-checks",
        action="store_true",
        help="Skip expensive QC, but still generate artifacts, stage assets, and validate the archive",
    )
    parser.add_argument("--skip-checks", action="store_true", help="Deprecated alias for --skip-quality-checks")
    parser.add_argument("--full", action="store_true", help="Run e2e tests and Sonar quality gate before packaging")
    parser.add_argument("--allow-large-archive", metavar="REASON", help="Allow archives above the hard size gate")
    parser.add_argument(
        "--target", default="all",
        help="Release target to package: all, current, macos-arm64, macos-x86_64, or windows-x86_64",
    )
    parser.add_argument(
        "--no-bundle-ffmpeg",
        action="store_true",
        help="Build a release variant that omits bundled ffmpeg and ffprobe and expects external binaries",
    )
    parser.add_argument(
        "--embed-runtime",
        action="store_true",
        help="Embed runtime executables/models into the .ankiaddon for local/offline validation",
    )
    parser.add_argument(
        "--runtime-base-url",
        help="Base URL where runtime pack assets will be uploaded; defaults to the versioned GitHub Release URL",
    )
    parser.add_argument(
        "--upload-assets",
        action="store_true",
        help="Upload generated runtime packs with gh release upload after local validation",
    )
    parser.add_argument(
        "--verify-runtime-urls",
        action="store_true",
        help="Download manifest runtime URLs and verify their SHA-256 digests after upload",
    )
    args = parser.parse_args()
    skip_quality_checks = args.skip_quality_checks or args.skip_checks
    if skip_quality_checks and args.full:
        parser.error("--full cannot be used with --skip-quality-checks")
    if args.no_bundle_ffmpeg and not args.embed_runtime:
        parser.error("--no-bundle-ffmpeg is only supported with --embed-runtime")
    if args.allow_large_archive:
        print(f"Large archive override reason: {args.allow_large_archive}")

    version = args.version or _read_pyproject_version()
    _verify_versions(version)

    if not skip_quality_checks:
        _find_anki_python()
        _run_checks(full=args.full)
    _build_required_artifacts()
    lock = release_assets.load_lock()
    target_keys, target_label = _selected_release_targets(args.target, lock)
    include_ffmpeg = not args.no_bundle_ffmpeg
    runtime_base_url = args.runtime_base_url or _default_runtime_base_url(version)
    runtime_pack_metadata: dict[str, dict[str, Any]] = {}

    with tempfile.TemporaryDirectory(prefix="anki-audio-release-") as tmp:
        staging_dir = Path(tmp) / "addon"
        runtime_source_bin_dir = Path(tmp) / "runtime-bin"
        try:
            if not args.embed_runtime:
                release_assets.stage_assets(
                    lock,
                    destination=runtime_source_bin_dir,
                    target_keys=target_keys,
                    include_ffmpeg=True,
                )
                runtime_pack_metadata = _build_runtime_packs(
                    version,
                    lock,
                    source_bin_dir=runtime_source_bin_dir,
                    target_keys=target_keys,
                    include_ffmpeg=True,
                    runtime_base_url=runtime_base_url,
                )
            _stage_release_tree(
                staging_dir,
                lock=lock,
                target_keys=target_keys,
                include_ffmpeg=include_ffmpeg,
                embed_runtime=args.embed_runtime,
                runtime_pack_metadata=runtime_pack_metadata or None,
                runtime_source_bin_dir=runtime_source_bin_dir if runtime_pack_metadata else None,
            )
        except release_assets.ReleaseAssetError as exc:
            # noinspection PyStringConversionWithoutDunderMethod
            print(f"ERROR: {exc}")
            sys.exit(1)
        archive = _build_archive(version, staging_dir, target_label=target_label, include_ffmpeg=include_ffmpeg)
        if runtime_pack_metadata:
            _validate_runtime_packs(runtime_pack_metadata)
    _validate_archive(
        archive,
        allow_large_archive=bool(args.allow_large_archive),
        lock=lock,
        target_keys=target_keys,
        include_ffmpeg=include_ffmpeg,
        embed_runtime=args.embed_runtime,
    )
    if runtime_pack_metadata and args.upload_assets:
        _upload_runtime_assets(version, runtime_pack_metadata)
    if runtime_pack_metadata and args.verify_runtime_urls:
        _verify_runtime_urls(runtime_pack_metadata)
    print(f"Done: {archive}")


if __name__ == "__main__":
    main()
