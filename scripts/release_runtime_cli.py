#!/usr/bin/env python3
"""Build, upload, and verify decoupled runtime release assets."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:  # pragma: no cover - direct script mode
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import (
    release_assets,
    release_runtime,
    release_runtime_metadata,
    release_runtime_remote,
)
from scripts.release_validation import selected_release_targets


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        if args.command == "build":
            return _cmd_build(args)
        if args.command == "upload":
            return _cmd_upload(args)
        if args.command == "verify":
            return _cmd_verify(args)
    except release_assets.ReleaseAssetError as exc:
        return release_runtime_metadata.handle_release_asset_error(exc)
    parser.print_help()
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Audio Quick Editor runtime releases")
    subparsers = parser.add_subparsers(dest="command")

    build = subparsers.add_parser("build", help="Build runtime packs and metadata")
    build.add_argument("--runtime-version", required=True, help="Runtime version, e.g. 1.0")
    build.add_argument(
        "--target",
        default="all",
        help="Runtime target to package: all, current, macos-arm64, macos-x86_64, or windows-x86_64",
    )
    build.add_argument(
        "--metadata",
        default=str(release_runtime_metadata.RUNTIME_RELEASE_LOCK_PATH),
        help="Path to write runtime release metadata",
    )
    build.add_argument(
        "--runtime-base-url",
        help="Override runtime asset base URL; defaults to the runtime-vN GitHub release",
    )

    upload = subparsers.add_parser("upload", help="Upload built runtime packs")
    upload.add_argument(
        "--metadata",
        default=str(release_runtime_metadata.RUNTIME_RELEASE_LOCK_PATH),
        help="Path to runtime release metadata",
    )

    verify = subparsers.add_parser("verify", help="Verify uploaded runtime packs")
    verify.add_argument(
        "--metadata",
        default=str(release_runtime_metadata.RUNTIME_RELEASE_LOCK_PATH),
        help="Path to runtime release metadata",
    )
    return parser


def _cmd_build(args: argparse.Namespace) -> int:
    lock = release_assets.load_lock()
    target_keys, _target_label = selected_release_targets(args.target, lock)
    runtime_base_url = args.runtime_base_url or release_runtime_metadata.default_runtime_base_url(
        args.runtime_version
    )
    with tempfile.TemporaryDirectory(prefix="anki-audio-runtime-release-") as tmp:
        source_bin_dir = Path(tmp) / "runtime-bin"
        release_assets.stage_assets(
            lock,
            destination=source_bin_dir,
            target_keys=target_keys,
            include_ffmpeg=True,
        )
        runtime_pack_metadata = release_runtime.build_runtime_packs(
            args.runtime_version,
            lock,
            source_bin_dir=source_bin_dir,
            target_keys=target_keys,
            include_ffmpeg=True,
            runtime_base_url=runtime_base_url,
        )
        release_runtime.validate_runtime_packs(runtime_pack_metadata)
        metadata = release_runtime_metadata.build_runtime_release_metadata(
            args.runtime_version,
            lock,
            runtime_pack_metadata,
            target_keys=target_keys,
            include_ffmpeg=True,
            runtime_base_url=runtime_base_url,
        )
        release_runtime_metadata.validate_runtime_release_metadata(
            metadata,
            lock,
            target_keys=target_keys,
            include_ffmpeg=True,
        )
        release_runtime_metadata.write_runtime_release_lock(metadata, Path(args.metadata))
    print(f"Wrote {args.metadata}")
    _print_runtime_pack_summary(metadata)
    return 0


def _cmd_upload(args: argparse.Namespace) -> int:
    lock = release_assets.load_lock()
    metadata = release_runtime_metadata.load_runtime_release_lock(Path(args.metadata))
    release_runtime_metadata.validate_runtime_release_metadata(metadata, lock)
    release_runtime_remote.upload_runtime_release_assets(metadata)
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    lock = release_assets.load_lock()
    metadata = release_runtime_metadata.load_runtime_release_lock(Path(args.metadata))
    release_runtime_metadata.validate_runtime_release_metadata(metadata, lock)
    release_runtime_remote.verify_runtime_release_urls(metadata)
    print(f"Verified runtime release {metadata['runtime_tag']}")
    return 0


def _print_runtime_pack_summary(metadata: dict[str, Any]) -> None:
    print(f"Runtime tag: {metadata['runtime_tag']}")
    for target, target_entry in metadata["targets"].items():
        pack = target_entry["runtime_pack"]
        print(f"{target}: {pack['name']} sha256={pack['sha256']} size={pack['size']}")


if __name__ == "__main__":
    raise SystemExit(main())
