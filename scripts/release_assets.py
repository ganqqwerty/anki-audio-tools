#!/usr/bin/env python3
"""Prepare, verify, and stage locked native release assets."""

from __future__ import annotations

import argparse
import json
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:  # pragma: no cover - used in direct script mode
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import release_asset_common as _asset_common
from scripts import release_assets_commands as _cmds
from scripts import release_assets_runtime_ops as _runtime_ops
from scripts import release_sherpa_assets as _sherpa_assets
from scripts import release_silero_assets as _silero_assets
from scripts.release_asset_common import (
    SHARED_FILE_NAMES,
    TARGET_KEYS,
    TOOL_NAMES,
    ReleaseAssetError,
    VerificationResult,
    _download_verified,
    _safe_relative_executable,
    _shared_file_entry,
    _stage_shared_files,
    _stage_tool_runtime_files,
    _tool_entry,
    _validate_target,
    bundled_tool_names,
    sha256_file,
    tool_runtime_files,
    tracked_runtime_file_path,
    tracked_shared_asset_path,
    validate_lock,
)
from scripts.release_asset_common import (
    lock_shared_files as _lock_shared_files,
)
from scripts.release_asset_common import (
    lock_targets as _lock_targets,
)
from scripts.release_asset_common import (
    lock_tools as _lock_tools,
)
from scripts.release_asset_verify import verify_assets as verify_release_assets
from scripts.release_assets_cli import build_parser

tracked_tool_binary_path = _asset_common.tracked_tool_binary_path

ROOT = Path(__file__).resolve().parent.parent
LOCK_PATH = ROOT / "release_assets.lock.json"
CACHE_DIR = ROOT / ".release-assets"
ADDON_BIN_DIR = ROOT / "addon" / "anki_audio_quick_editor" / "bin"


def load_lock(path: Path = LOCK_PATH) -> dict[str, Any]:
    """Load the release asset lock file."""

    return json.loads(path.read_text(encoding="utf-8"))


def lock_targets(lock: dict[str, Any]) -> list[str]:
    """Return target keys in lock-file order."""

    return _lock_targets(lock)


def lock_tools(lock: dict[str, Any], target: str) -> list[str]:
    """Return canonical tool names for ``target``."""

    return _lock_tools(lock, target)


def lock_shared_files(lock: dict[str, Any]) -> list[str]:
    """Return canonical shared runtime file names."""

    return _lock_shared_files(lock)


def verify_assets(
    lock: dict[str, Any],
    *,
    cache_dir: Path = CACHE_DIR,
    addon_bin_dir: Path = ADDON_BIN_DIR,
    target_keys: list[str] | None = None,
    run_diagnostics: bool = True,
) -> VerificationResult:
    """Verify cached runtime assets and optionally run their diagnostic commands."""
    validate_lock(lock)
    if not run_diagnostics:
        return verify_release_assets(
            lock,
            cache_dir=cache_dir,
            addon_bin_dir=addon_bin_dir,
            target_keys=target_keys or TARGET_KEYS,
            run_diagnostics=False,
            lock_tools=lock_tools,
            tool_runtime_files=tool_runtime_files,
            source_tool_binary_path=source_tool_binary_path,
            current_target_key=lambda: "",
            append_diagnostic_report=lambda *args, **kwargs: None,
        )
    return verify_release_assets(
        lock,
        cache_dir=cache_dir,
        addon_bin_dir=addon_bin_dir,
        target_keys=target_keys or TARGET_KEYS,
        run_diagnostics=True,
        lock_tools=lock_tools,
        tool_runtime_files=tool_runtime_files,
        source_tool_binary_path=source_tool_binary_path,
        current_target_key=current_target_key,
        append_diagnostic_report=_append_diagnostic_report,
    )


def stage_assets(
    lock: dict[str, Any],
    *,
    cache_dir: Path = CACHE_DIR,
    addon_bin_dir: Path = ADDON_BIN_DIR,
    destination: Path,
    target_keys: list[str] | None = None,
    tool_names: list[str] | None = None,
    include_shared: bool | None = None,
    include_ffmpeg: bool = True,
) -> list[Path]:
    """Copy verified runtime executables into a staged ``bin`` directory."""

    validate_lock(lock)
    staged: list[Path] = []
    selected_targets = target_keys or TARGET_KEYS
    for target in selected_targets:
        _validate_target(target)
        target_tools = bundled_tool_names(lock_tools(lock, target), include_ffmpeg=include_ffmpeg)
        for tool_name in tool_names or target_tools:
            if tool_name not in target_tools:
                raise ReleaseAssetError(f"unknown tool: {tool_name}")
            entry = _tool_entry(lock, target, tool_name)
            executable = _safe_relative_executable(entry["executable"])
            expected_sha = entry.get("sha256")
            if not expected_sha:
                raise ReleaseAssetError(f"{target}/{tool_name}: missing sha256 in release_assets.lock.json")
            source = source_tool_binary_path(cache_dir, addon_bin_dir, target, tool_name, entry)
            if not source.is_file():
                raise ReleaseAssetError(f"{target}/{tool_name}: missing binary at {source}")
            actual_sha = sha256_file(source)
            if actual_sha != expected_sha:
                raise ReleaseAssetError(f"{target}/{tool_name}: checksum mismatch")
            target_path = destination / target / executable
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target_path)
            if not target.startswith("windows-"):
                target_path.chmod(target_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            staged.append(target_path)
            staged.extend(
                _stage_tool_runtime_files(
                    lock,
                    source_dir=addon_bin_dir,
                    destination=destination,
                    target=target,
                    tool_name=tool_name,
                )
            )
    should_stage_shared = tool_names is None if include_shared is None else include_shared
    if should_stage_shared:
        staged.extend(_stage_shared_files(lock, source_dir=addon_bin_dir, destination=destination))
    return staged


def lock_checksums(
    *,
    lock_path: Path = LOCK_PATH,
    cache_dir: Path = CACHE_DIR,
    addon_bin_dir: Path = ADDON_BIN_DIR,
) -> dict[str, Any]:
    """Update lock-file checksums for the mixed tracked/cache runtime layout."""

    lock = load_lock(lock_path)
    validate_lock(lock)
    for target in TARGET_KEYS:
        for tool_name in lock_tools(lock, target):
            entry = _tool_entry(lock, target, tool_name)
            path = source_tool_binary_path(cache_dir, addon_bin_dir, target, tool_name, entry)
            if path.is_file():
                entry["sha256"] = sha256_file(path)
            for file_entry in tool_runtime_files(lock, target, tool_name):
                runtime_path = tracked_runtime_file_path(addon_bin_dir, target, file_entry)
                if runtime_path.is_file():
                    file_entry["sha256"] = sha256_file(runtime_path)
    for file_name in SHARED_FILE_NAMES:
        entry = _shared_file_entry(lock, file_name)
        path = tracked_shared_asset_path(addon_bin_dir, entry)
        if path.is_file():
            entry["sha256"] = sha256_file(path)
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return lock


def fetch_deepfilter(lock: dict[str, Any], *, target_keys: list[str], cache_dir: Path = CACHE_DIR) -> list[Path]:
    """Fetch locked DeepFilterNet executable assets."""
    validate_lock(lock)
    _runtime_ops._download_verified = _download_verified
    return _runtime_ops.fetch_deepfilter(lock, target_keys=target_keys, cache_dir=cache_dir, tool_entry=_tool_entry)


def fetch_ffmpeg(
    lock: dict[str, Any], *, target_keys: list[str], tool_names: list[str] | None = None, cache_dir: Path = CACHE_DIR
) -> list[Path]:
    validate_lock(lock)
    _runtime_ops._download_verified = _download_verified
    return _runtime_ops.fetch_ffmpeg(lock, target_keys=target_keys, tool_names=tool_names, cache_dir=cache_dir, tool_entry=_tool_entry)


def fetch_sherpa_spleeter(lock: dict[str, Any], *, target_keys: list[str], cache_dir: Path = CACHE_DIR) -> list[Path]:
    """Fetch locked Sherpa Spleeter runtime assets."""
    validate_lock(lock)
    return _sherpa_assets.fetch_sherpa_spleeter(lock, target_keys=target_keys, cache_dir=cache_dir)


def fetch_spleeter_models(lock: dict[str, Any], *, cache_dir: Path = CACHE_DIR) -> list[Path]:
    """Fetch locked shared Spleeter model assets."""
    validate_lock(lock)
    return _sherpa_assets.fetch_spleeter_models(lock, cache_dir=cache_dir)


def fetch_silero_vad(
    lock: dict[str, Any],
    *,
    target_keys: list[str],
    cache_dir: Path = CACHE_DIR,
    addon_bin_dir: Path = ADDON_BIN_DIR,
) -> list[Path]:
    """Fetch locked Sherpa ONNX VAD executable assets."""
    validate_lock(lock)
    return _silero_assets.fetch_silero_vad(
        lock,
        target_keys=target_keys,
        cache_dir=cache_dir,
        addon_bin_dir=addon_bin_dir,
    )


def fetch_silero_vad_model(
    lock: dict[str, Any],
    *,
    cache_dir: Path = CACHE_DIR,
    addon_bin_dir: Path = ADDON_BIN_DIR,
) -> list[Path]:
    """Fetch locked shared Silero VAD model asset."""
    validate_lock(lock)
    return _silero_assets.fetch_silero_vad_model(lock, cache_dir=cache_dir, addon_bin_dir=addon_bin_dir)


def current_target_key() -> str:
    """Return the release target key for this native platform."""
    return _runtime_ops.current_target_key()


def asset_binary_path(cache_dir: Path, target: str, entry: dict[str, Any]) -> Path:
    """Return the cache path for a target executable entry."""
    return _runtime_ops.asset_binary_path(cache_dir, target, entry)


def source_tool_binary_path(
    cache_dir: Path,
    addon_bin_dir: Path,
    target: str,
    tool_name: str,
    entry: dict[str, Any],
) -> Path:
    """Return the canonical source path for a runtime executable."""
    return _runtime_ops.source_tool_binary_path(cache_dir, addon_bin_dir, target, tool_name, entry)


def _target_selection(value: str) -> list[str]:
    return _runtime_ops.target_selection(value, target_keys=TARGET_KEYS, current_target=current_target_key)


def _append_diagnostic_report(
    path: Path,
    entry: dict[str, Any],
    reports: list[str],
    errors: list[str],
    target: str,
    tool_name: str,
) -> None:
    command = [str(path), *entry.get("diagnostic_args", ["--version"])]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)  # nosec B603
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"{target}/{tool_name}: diagnostic failed: {exc}")
        return
    output = (result.stdout or result.stderr).strip()
    if result.returncode != 0:
        errors.append(f"{target}/{tool_name}: diagnostic exited {result.returncode}: {output}")
        return
    reports.append(f"{target}/{tool_name}: diagnostic ok: {output}")


def _ffmpeg_archive_path(cache_dir: Path, target: str, url: str) -> Path:
    return _runtime_ops.ffmpeg_archive_path(cache_dir, target, url)


def _run_build_script(script: Path, target: str) -> None:
    _runtime_ops.run_build_script(ROOT, script, target)


def _cmd_verify(args: argparse.Namespace) -> int:
    result = _cmds.cmd_verify(
        args,
        load_lock=load_lock,
        verify_assets=verify_assets,
        target_selection=_target_selection,
    )
    if result != 0:
        lock = load_lock()
        verify_result = verify_assets(
            lock,
            target_keys=_target_selection(args.target),
            run_diagnostics=bool(args.diagnostics),
        )
        for error in verify_result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
    return result


def _cmd_stage(args: argparse.Namespace) -> int:
    return _cmds.cmd_stage(
        args,
        load_lock=load_lock,
        stage_assets=stage_assets,
        target_selection=_target_selection,
    )


def _cmd_fetch_deepfilter(args: argparse.Namespace) -> int:
    return _cmds.cmd_fetch_deepfilter(
        args,
        load_lock=load_lock,
        fetch_deepfilter=fetch_deepfilter,
        target_selection=_target_selection,
    )


def _cmd_fetch_ffmpeg(args: argparse.Namespace) -> int:
    return _cmds.cmd_fetch_ffmpeg(
        args,
        load_lock=load_lock,
        fetch_ffmpeg=fetch_ffmpeg,
        target_selection=_target_selection,
    )


def _cmd_fetch_sherpa_spleeter(args: argparse.Namespace) -> int:
    return _cmds.cmd_fetch_sherpa_spleeter(
        args,
        load_lock=load_lock,
        fetch_sherpa_spleeter=fetch_sherpa_spleeter,
        target_selection=_target_selection,
    )


def _cmd_fetch_spleeter_models(_args: argparse.Namespace) -> int:
    return _cmds.cmd_fetch_spleeter_models(
        _args,
        load_lock=load_lock,
        fetch_spleeter_models=fetch_spleeter_models,
    )


def _cmd_fetch_silero_vad(args: argparse.Namespace) -> int:
    return _cmds.cmd_fetch_silero_vad(
        args,
        load_lock=load_lock,
        fetch_silero_vad=fetch_silero_vad,
        target_selection=_target_selection,
    )


def _cmd_fetch_silero_vad_model(_args: argparse.Namespace) -> int:
    return _cmds.cmd_fetch_silero_vad_model(
        _args,
        load_lock=load_lock,
        fetch_silero_vad_model=fetch_silero_vad_model,
    )


def _cmd_lock_checksums(_args: argparse.Namespace) -> int:
    lock_checksums()
    print(f"updated {LOCK_PATH.relative_to(ROOT)}")
    return 0


def _cmd_build_rnnoise(args: argparse.Namespace) -> int:
    target = current_target_key() if args.target == "current" else args.target
    _run_build_script(ROOT / "scripts" / "rnnoise_cli" / _build_script_name(target), target)
    return 0


def _build_script_name(target: str) -> str:
    return _runtime_ops.build_script_name(target)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser(
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
        tool_names=TOOL_NAMES,
    )
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ReleaseAssetError as exc:
        # noinspection PyStringConversionWithoutDunderMethod
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
