#!/usr/bin/env python3
"""Build a validated .ankiaddon package for Anki Audio Quick Editor."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import release_assets  # noqa: E402
import scripts.release_bundle_freshness as release_bundle_freshness  # noqa: E402
import scripts.release_manifest_selection as release_manifest_selection  # noqa: E402
import scripts.release_validation as release_validation  # noqa: E402
from dev import _find_anki_python  # noqa: E402
from scripts.release_archive import (
    build_archive as _build_archive,
)
from scripts.release_archive import (
    stage_release_tree as _stage_release_tree,
)
from scripts.release_archive import (
    validate_archive as _validate_archive,
)
from scripts.release_runtime import (
    build_runtime_packs as _build_runtime_packs,  # noqa: E402
)
from scripts.release_runtime import (
    default_runtime_base_url as _default_runtime_base_url,
)
from scripts.release_runtime import upload_runtime_assets as _upload_runtime_assets
from scripts.release_runtime import validate_runtime_packs as _validate_runtime_packs
from scripts.release_runtime import verify_runtime_urls as _verify_runtime_urls

_should_include = release_manifest_selection.should_include
release_manifest_files = release_manifest_selection.release_manifest_files
release_runtime_executables = release_manifest_selection.release_runtime_executables
release_runtime_shared_files = release_manifest_selection.release_runtime_shared_files
release_runtime_support_files = release_manifest_selection.release_runtime_support_files


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
        "--target",
        default="all",
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
