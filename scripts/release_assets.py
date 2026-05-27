#!/usr/bin/env python3
"""Prepare, verify, and stage locked native release assets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:  # pragma: no cover - used in direct script mode
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import release_asset_common as _asset_common
from scripts import release_assets_cli_handlers as _cli
from scripts import release_assets_core as _core
from scripts import release_assets_paths as _paths

ReleaseAssetError = _asset_common.ReleaseAssetError
VerificationResult = _asset_common.VerificationResult
SHARED_FILE_NAMES = _asset_common.SHARED_FILE_NAMES
TARGET_KEYS = _asset_common.TARGET_KEYS
TOOL_NAMES = _asset_common.TOOL_NAMES
_download_verified = _asset_common.download_verified
bundled_tool_names = _asset_common.bundled_tool_names
sha256_file = _asset_common.sha256_file
tool_runtime_files = _asset_common.tool_runtime_files
tracked_runtime_file_path = _asset_common.tracked_runtime_file_path
tracked_shared_asset_path = _asset_common.tracked_shared_asset_path
validate_lock = _asset_common.validate_lock

ROOT = _paths.ROOT
LOCK_PATH = _paths.LOCK_PATH
CACHE_DIR = _paths.CACHE_DIR
ADDON_BIN_DIR = _paths.ADDON_BIN_DIR
tracked_tool_binary_path = _core.tracked_tool_binary_path

load_lock = _core.load_lock
lock_targets = _core.lock_targets
lock_tools = _core.lock_tools
lock_shared_files = _core.lock_shared_files
stage_assets = _core.stage_assets
lock_checksums = _core.lock_checksums
fetch_sherpa_spleeter = _core.fetch_sherpa_spleeter
fetch_spleeter_models = _core.fetch_spleeter_models
fetch_silero_vad = _core.fetch_silero_vad
fetch_silero_vad_model = _core.fetch_silero_vad_model

current_target_key = _paths.current_target_key
asset_binary_path = _paths.asset_binary_path
source_tool_binary_path = _paths.source_tool_binary_path
_ffmpeg_archive_path = _paths.ffmpeg_archive_path


def verify_assets(
    lock: dict[str, Any],
    *,
    cache_dir: Path = CACHE_DIR,
    addon_bin_dir: Path = ADDON_BIN_DIR,
    target_keys: list[str] | None = None,
    run_diagnostics: bool = True,
) -> VerificationResult:
    """Verify cached runtime assets and optionally run their diagnostic commands."""
    return _core.verify_assets(
        lock,
        cache_dir=cache_dir,
        addon_bin_dir=addon_bin_dir,
        target_keys=target_keys,
        run_diagnostics=run_diagnostics,
        current_target_key=current_target_key,
        append_diagnostic_report=_append_diagnostic_report,
    )


def fetch_deepfilter(lock: dict[str, Any], *, target_keys: list[str], cache_dir: Path = CACHE_DIR) -> list[Path]:
    """Fetch locked DeepFilterNet executable assets."""
    _core.set_download_verified(_download_verified)
    return _core.fetch_deepfilter(lock, target_keys=target_keys, cache_dir=cache_dir)


def fetch_ffmpeg(
    lock: dict[str, Any],
    *,
    target_keys: list[str],
    tool_names: list[str] | None = None,
    cache_dir: Path = CACHE_DIR,
) -> list[Path]:
    """Fetch locked FFmpeg and FFprobe executable assets."""
    _core.set_download_verified(_download_verified)
    return _core.fetch_ffmpeg(
        lock,
        target_keys=target_keys,
        tool_names=tool_names,
        cache_dir=cache_dir,
    )


def _target_selection(value: str) -> list[str]:
    return _cli.select_targets(value, current_target_key=current_target_key)


def _append_diagnostic_report(
    path: Path,
    entry: dict[str, Any],
    reports: list[str],
    errors: list[str],
    target: str,
    tool_name: str,
) -> None:
    _cli.append_diagnostic_report(path, entry, reports, errors, target, tool_name)


def _run_build_script(script: Path, target: str) -> None:
    _cli.run_build_script(script, target)


def _cmd_verify(args: argparse.Namespace) -> int:
    return _cli.cmd_verify(
        args,
        load_lock=load_lock,
        verify_assets=verify_assets,
        target_selector=_target_selection,
    )


def _cmd_stage(args: argparse.Namespace) -> int:
    return _cli.cmd_stage(
        args,
        load_lock=load_lock,
        stage_assets=stage_assets,
        target_selector=_target_selection,
    )


def _cmd_fetch_deepfilter(args: argparse.Namespace) -> int:
    return _cli.cmd_fetch_deepfilter(
        args,
        load_lock=load_lock,
        fetch_deepfilter=fetch_deepfilter,
        target_selector=_target_selection,
    )


def _cmd_fetch_ffmpeg(args: argparse.Namespace) -> int:
    return _cli.cmd_fetch_ffmpeg(
        args,
        load_lock=load_lock,
        fetch_ffmpeg=fetch_ffmpeg,
        target_selector=_target_selection,
    )


def _cmd_fetch_sherpa_spleeter(args: argparse.Namespace) -> int:
    return _cli.cmd_fetch_sherpa_spleeter(
        args,
        load_lock=load_lock,
        fetch_sherpa_spleeter=fetch_sherpa_spleeter,
        target_selector=_target_selection,
    )


def _cmd_fetch_spleeter_models(args: argparse.Namespace) -> int:
    return _cli.cmd_fetch_spleeter_models(
        args,
        load_lock=load_lock,
        fetch_spleeter_models=fetch_spleeter_models,
    )


def _cmd_fetch_silero_vad(args: argparse.Namespace) -> int:
    return _cli.cmd_fetch_silero_vad(
        args,
        load_lock=load_lock,
        fetch_silero_vad=fetch_silero_vad,
        target_selector=_target_selection,
    )


def _cmd_fetch_silero_vad_model(args: argparse.Namespace) -> int:
    return _cli.cmd_fetch_silero_vad_model(
        args,
        load_lock=load_lock,
        fetch_silero_vad_model=fetch_silero_vad_model,
    )


def _cmd_lock_checksums(args: argparse.Namespace) -> int:
    return _cli.cmd_lock_checksums(args, lock_checksums=lock_checksums)


def _cmd_build_rnnoise(args: argparse.Namespace) -> int:
    return _cli.cmd_build_rnnoise(args, current_target_key=current_target_key)


def _build_script_name(target: str) -> str:
    return _cli.build_script_name(target)


def main(argv: list[str] | None = None) -> int:
    parser = _cli.build_release_assets_parser(
        cmd_fetch_deepfilter=_cmd_fetch_deepfilter,
        cmd_fetch_ffmpeg=_cmd_fetch_ffmpeg,
        cmd_fetch_sherpa_spleeter=_cmd_fetch_sherpa_spleeter,
        cmd_fetch_silero_vad=_cmd_fetch_silero_vad,
        cmd_build_rnnoise=_cmd_build_rnnoise,
        cmd_verify=_cmd_verify,
        cmd_fetch_spleeter_models=_cmd_fetch_spleeter_models,
        cmd_fetch_silero_vad_model=_cmd_fetch_silero_vad_model,
        cmd_lock_checksums=_cmd_lock_checksums,
        cmd_stage=_cmd_stage,
    )
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ReleaseAssetError as exc:
        return _cli.handle_release_asset_error(exc)


if __name__ == "__main__":
    raise SystemExit(main())
