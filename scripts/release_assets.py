#!/usr/bin/env python3
"""Prepare, verify, and stage locked native release assets."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

if __package__ in {None, ""}:  # pragma: no cover - used in direct script mode
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.release_asset_common import (
    SHARED_FILE_NAMES,
    TARGET_KEYS,
    TOOL_NAMES,
    ReleaseAssetError,
    VerificationResult,
    _download_verified,
    _extract_zip_member,
    _required_https_url,
    _required_sha256,
    _required_string,
    _safe_archive_member,
    _safe_relative_executable,
    _shared_file_entry,
    _stage_shared_files,
    _stage_tool_runtime_files,
    _tool_entry,
    _validate_target,
    runtime_file_path,
    sha256_file,
    shared_asset_path,
    tool_runtime_files,
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
from scripts.release_sherpa_assets import (
    append_sherpa_spleeter_smoke_report,
    fetch_sherpa_spleeter,
    fetch_spleeter_models,
)

ROOT = Path(__file__).resolve().parent.parent
LOCK_PATH = ROOT / "release_assets.lock.json"
CACHE_DIR = ROOT / ".release-assets"


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
    target_keys: list[str] | None = None,
    run_diagnostics: bool = True,
) -> VerificationResult:
    """Verify cached runtime assets and optionally run their diagnostic commands."""

    validate_lock(lock)
    errors: list[str] = []
    reports: list[str] = []
    selected_targets = target_keys or TARGET_KEYS
    for target in selected_targets:
        _validate_target(target)
        for tool_name in lock_tools(lock, target):
            _verify_tool_asset(lock, cache_dir, reports, errors, target, tool_name, run_diagnostics)
            _verify_tool_runtime_files(lock, cache_dir, reports, errors, target, tool_name)
    for file_name in SHARED_FILE_NAMES:
        _verify_shared_asset(lock, cache_dir, reports, errors, file_name)
    if run_diagnostics:
        append_sherpa_spleeter_smoke_report(
            lock,
            cache_dir=cache_dir,
            target_keys=selected_targets,
            current_target=current_target_key(),
            reports=reports,
            errors=errors,
        )
    return VerificationResult(errors=errors, reports=reports)


def _verify_tool_asset(
    lock: dict[str, Any],
    cache_dir: Path,
    reports: list[str],
    errors: list[str],
    target: str,
    tool_name: str,
    run_diagnostics: bool,
) -> None:
    entry = _tool_entry(lock, target, tool_name)
    path = asset_binary_path(cache_dir, target, entry)
    expected_sha = entry.get("sha256")
    actual_sha = _verified_asset_sha(path, expected_sha, errors, f"{target}/{tool_name}", "binary")
    if actual_sha is None:
        return
    reports.append(f"{target}/{tool_name}: {path} sha256={actual_sha}")
    if run_diagnostics and target == current_target_key():
        _append_diagnostic_report(path, entry, reports, errors, target, tool_name)


def _verify_shared_asset(
    lock: dict[str, Any],
    cache_dir: Path,
    reports: list[str],
    errors: list[str],
    file_name: str,
) -> None:
    entry = _shared_file_entry(lock, file_name)
    path = shared_asset_path(cache_dir, entry)
    actual_sha = _verified_asset_sha(path, entry.get("sha256"), errors, f"shared/{file_name}", "file")
    if actual_sha is not None:
        reports.append(f"shared/{file_name}: {path} sha256={actual_sha}")


def _verify_tool_runtime_files(
    lock: dict[str, Any],
    cache_dir: Path,
    reports: list[str],
    errors: list[str],
    target: str,
    tool_name: str,
) -> None:
    for file_entry in tool_runtime_files(lock, target, tool_name):
        label = f"{target}/{tool_name}/{file_entry['path']}"
        path = runtime_file_path(cache_dir, target, file_entry)
        actual_sha = _verified_asset_sha(path, file_entry.get("sha256"), errors, label, "file")
        if actual_sha is not None:
            reports.append(f"{label}: {path} sha256={actual_sha}")


def _verified_asset_sha(
    path: Path,
    expected_sha: object,
    errors: list[str],
    label: str,
    asset_kind: str,
) -> str | None:
    if not path.is_file():
        errors.append(f"{label}: missing {asset_kind} at {path}")
        return None
    if not expected_sha:
        errors.append(f"{label}: missing sha256 in release_assets.lock.json")
        return None
    actual_sha = sha256_file(path)
    if actual_sha != expected_sha:
        errors.append(f"{label}: checksum mismatch (expected {expected_sha}, got {actual_sha})")
        return None
    return actual_sha


def stage_assets(
    lock: dict[str, Any],
    *,
    cache_dir: Path = CACHE_DIR,
    destination: Path,
    target_keys: list[str] | None = None,
    tool_names: list[str] | None = None,
    include_shared: bool | None = None,
) -> list[Path]:
    """Copy verified runtime executables into a staged ``bin`` directory."""

    validate_lock(lock)
    staged: list[Path] = []
    selected_targets = target_keys or TARGET_KEYS
    for target in selected_targets:
        _validate_target(target)
        target_tools = lock_tools(lock, target)
        for tool_name in tool_names or target_tools:
            if tool_name not in target_tools:
                raise ReleaseAssetError(f"unknown tool: {tool_name}")
            entry = _tool_entry(lock, target, tool_name)
            executable = _safe_relative_executable(entry["executable"])
            expected_sha = entry.get("sha256")
            if not expected_sha:
                raise ReleaseAssetError(f"{target}/{tool_name}: missing sha256 in release_assets.lock.json")
            source = asset_binary_path(cache_dir, target, entry)
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
                    cache_dir=cache_dir,
                    destination=destination,
                    target=target,
                    tool_name=tool_name,
                )
            )
    should_stage_shared = tool_names is None if include_shared is None else include_shared
    if should_stage_shared:
        staged.extend(_stage_shared_files(lock, cache_dir=cache_dir, destination=destination))
    return staged


def lock_checksums(*, lock_path: Path = LOCK_PATH, cache_dir: Path = CACHE_DIR) -> dict[str, Any]:
    """Update lock-file checksums for cached binaries that are present."""

    lock = load_lock(lock_path)
    validate_lock(lock)
    for target in TARGET_KEYS:
        for tool_name in lock_tools(lock, target):
            entry = _tool_entry(lock, target, tool_name)
            path = asset_binary_path(cache_dir, target, entry)
            if path.is_file():
                entry["sha256"] = sha256_file(path)
            for file_entry in tool_runtime_files(lock, target, tool_name):
                runtime_path = runtime_file_path(cache_dir, target, file_entry)
                if runtime_path.is_file():
                    file_entry["sha256"] = sha256_file(runtime_path)
    for file_name in SHARED_FILE_NAMES:
        entry = _shared_file_entry(lock, file_name)
        path = shared_asset_path(cache_dir, entry)
        if path.is_file():
            entry["sha256"] = sha256_file(path)
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return lock


def fetch_deepfilter(lock: dict[str, Any], *, target_keys: list[str], cache_dir: Path = CACHE_DIR) -> list[Path]:
    """Fetch locked DeepFilterNet executable assets."""

    validate_lock(lock)
    fetched: list[Path] = []
    for target in target_keys:
        entry = _tool_entry(lock, target, "deep-filter")
        expected_sha = entry.get("sha256")
        if not expected_sha:
            raise ReleaseAssetError(f"{target}/deep-filter cannot be fetched without locked sha256")
        destination = asset_binary_path(cache_dir, target, entry)
        _download_verified(entry["download_url"], destination, expected_sha)
        if not target.startswith("windows-"):
            destination.chmod(destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        fetched.append(destination)
    return fetched


def fetch_ffmpeg(
    lock: dict[str, Any], *, target_keys: list[str], tool_names: list[str] | None = None, cache_dir: Path = CACHE_DIR
) -> list[Path]:
    validate_lock(lock)
    selected_tools = tool_names or ["ffmpeg", "ffprobe"]
    fetched: list[Path] = []
    for target in target_keys:
        _validate_target(target)
        for tool_name in selected_tools:
            if tool_name not in {"ffmpeg", "ffprobe"}:
                raise ReleaseAssetError(f"fetch-ffmpeg cannot fetch {tool_name}")
            entry = _tool_entry(lock, target, tool_name)
            archive_url = _required_https_url(entry, "download_url", target, tool_name)
            archive_sha = _required_sha256(entry, "download_sha256", target, tool_name)
            archive_member = _safe_archive_member(_required_string(entry, "archive_member", target, tool_name))
            archive_path = _ffmpeg_archive_path(cache_dir, target, archive_url)
            _download_verified(archive_url, archive_path, archive_sha)
            destination = asset_binary_path(cache_dir, target, entry)
            _extract_zip_member(archive_path, archive_member, destination)
            if not target.startswith("windows-"):
                destination.chmod(destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            expected_sha = _required_sha256(entry, "sha256", target, tool_name)
            actual_sha = sha256_file(destination)
            if actual_sha != expected_sha:
                raise ReleaseAssetError(
                    f"{target}/{tool_name}: extracted checksum mismatch "
                    f"(expected {expected_sha}, got {actual_sha})"
                )
            fetched.append(destination)
    return fetched


def current_target_key() -> str:
    """Return the release target key for this native platform."""

    system = platform.system()
    machine = platform.machine().lower()
    if system == "Darwin" and machine in {"arm64", "aarch64"}:
        return "macos-arm64"
    if system == "Darwin" and machine == "x86_64":
        return "macos-x86_64"
    if system == "Windows" and machine in {"amd64", "x86_64", "64bit"}:
        return "windows-x86_64"
    raise ReleaseAssetError(f"unsupported release asset platform: {system} {platform.machine()}")


def asset_binary_path(cache_dir: Path, target: str, entry: dict[str, Any]) -> Path:
    """Return the cache path for a target executable entry."""

    executable = _safe_relative_executable(entry["executable"])
    return cache_dir / "bin" / target / executable


def _target_selection(value: str) -> list[str]:
    if value == "all":
        return TARGET_KEYS
    if value == "current":
        return [current_target_key()]
    _validate_target(value)
    return [value]


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
    name = Path(urlparse(url).path).name
    if not name:
        raise ReleaseAssetError(f"FFmpeg archive URL has no filename: {url}")
    return cache_dir / "sources" / "ffmpeg" / f"{target}-{name}"


def _run_build_script(script: Path, target: str) -> None:
    if not script.is_file():
        raise ReleaseAssetError(f"build script not found: {script.relative_to(ROOT)}")
    command = [str(script), target] if script.suffix != ".ps1" else ["pwsh", "-File", str(script), "-Target", target]
    result = subprocess.run(command, cwd=ROOT, text=True, check=False)  # nosec B603
    if result.returncode != 0:
        raise ReleaseAssetError(f"{script.name} failed with exit code {result.returncode}")


def _cmd_verify(args: argparse.Namespace) -> int:
    lock = load_lock()
    result = verify_assets(lock, target_keys=_target_selection(args.target))
    for report in result.reports:
        print(report)
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result.ok else 1


def _cmd_stage(args: argparse.Namespace) -> int:
    lock = load_lock()
    staged = stage_assets(
        lock,
        destination=Path(args.destination),
        target_keys=_target_selection(args.target),
        tool_names=args.tools,
    )
    for path in staged:
        print(path)
    return 0


def _cmd_fetch_deepfilter(args: argparse.Namespace) -> int:
    lock = load_lock()
    fetched = fetch_deepfilter(lock, target_keys=_target_selection(args.target))
    for path in fetched:
        print(path)
    return 0


def _cmd_fetch_ffmpeg(args: argparse.Namespace) -> int:
    lock = load_lock()
    fetched = fetch_ffmpeg(lock, target_keys=_target_selection(args.target))
    for path in fetched:
        print(path)
    return 0


def _cmd_fetch_sherpa_spleeter(args: argparse.Namespace) -> int:
    lock = load_lock()
    fetched = fetch_sherpa_spleeter(lock, target_keys=_target_selection(args.target))
    for path in fetched:
        print(path)
    return 0


def _cmd_fetch_spleeter_models(_args: argparse.Namespace) -> int:
    lock = load_lock()
    fetched = fetch_spleeter_models(lock)
    for path in fetched:
        print(path)
    return 0


def _cmd_lock_checksums(_args: argparse.Namespace) -> int:
    lock_checksums()
    print(f"updated {LOCK_PATH.relative_to(ROOT)}")
    return 0


def _cmd_build_rnnoise(args: argparse.Namespace) -> int:
    target = current_target_key() if args.target == "current" else args.target
    _run_build_script(ROOT / "scripts" / "rnnoise_cli" / _build_script_name(target), target)
    return 0


def _build_script_name(target: str) -> str:
    _validate_target(target)
    if target.startswith("windows-"):
        return "build_windows.ps1" if platform.system() == "Windows" else "build_windows_cross.sh"
    return "build_macos.sh"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare locked native release assets")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, func in (
        ("fetch-deepfilter", _cmd_fetch_deepfilter),
        ("fetch-ffmpeg", _cmd_fetch_ffmpeg),
        ("fetch-sherpa-spleeter", _cmd_fetch_sherpa_spleeter),
        ("build-rnnoise", _cmd_build_rnnoise),
        ("verify", _cmd_verify),
    ):
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--target", default="current")
        subparser.set_defaults(func=func)

    subparsers.add_parser("fetch-spleeter-models").set_defaults(func=_cmd_fetch_spleeter_models)
    subparsers.add_parser("lock-checksums").set_defaults(func=_cmd_lock_checksums)

    stage = subparsers.add_parser("stage")
    stage.add_argument("--target", default="all")
    stage.add_argument("--tool", action="append", choices=TOOL_NAMES, dest="tools")
    stage.add_argument("--destination", required=True)
    stage.set_defaults(func=_cmd_stage)

    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ReleaseAssetError as exc:
        # noinspection PyStringConversionWithoutDunderMethod
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
