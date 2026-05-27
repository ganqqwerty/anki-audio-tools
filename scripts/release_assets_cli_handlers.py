"""CLI handlers for release asset commands."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from scripts import release_assets_commands as _cmds
from scripts import release_assets_runtime_ops as _runtime_ops
from scripts.release_asset_common import TARGET_KEYS, TOOL_NAMES, ReleaseAssetError
from scripts.release_assets_cli import build_parser
from scripts.release_assets_paths import LOCK_PATH, ROOT


def select_targets(value: str, *, current_target_key) -> list[str]:
    """Return selected release asset target keys for a CLI target value."""
    return _runtime_ops.target_selection(value, target_keys=TARGET_KEYS, current_target=current_target_key)


def append_diagnostic_report(
    path: Path,
    entry: dict[str, Any],
    reports: list[str],
    errors: list[str],
    target: str,
    tool_name: str,
) -> None:
    """Append a diagnostic command report for one executable."""
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


def run_build_script(script: Path, target: str) -> None:
    """Run a release asset build script."""
    _runtime_ops.run_build_script(ROOT, script, target)


def build_script_name(target: str) -> str:
    """Return the RNNoise build script name for a target."""
    return _runtime_ops.build_script_name(target)


def cmd_verify(args: argparse.Namespace, *, load_lock, verify_assets, target_selector) -> int:
    """Run the release asset verify CLI command."""
    result = _cmds.cmd_verify(
        args,
        load_lock=load_lock,
        verify_assets=verify_assets,
        target_selection=target_selector,
    )
    if result != 0:
        lock = load_lock()
        verify_result = verify_assets(
            lock,
            target_keys=target_selector(args.target),
            run_diagnostics=bool(args.diagnostics),
        )
        for error in verify_result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
    return result


def cmd_stage(args: argparse.Namespace, *, load_lock, stage_assets, target_selector) -> int:
    return _cmds.cmd_stage(
        args,
        load_lock=load_lock,
        stage_assets=stage_assets,
        target_selection=target_selector,
    )


def cmd_fetch_deepfilter(args: argparse.Namespace, *, load_lock, fetch_deepfilter, target_selector) -> int:
    return _cmds.cmd_fetch_deepfilter(
        args,
        load_lock=load_lock,
        fetch_deepfilter=fetch_deepfilter,
        target_selection=target_selector,
    )


def cmd_fetch_ffmpeg(args: argparse.Namespace, *, load_lock, fetch_ffmpeg, target_selector) -> int:
    return _cmds.cmd_fetch_ffmpeg(
        args,
        load_lock=load_lock,
        fetch_ffmpeg=fetch_ffmpeg,
        target_selection=target_selector,
    )


def cmd_fetch_sherpa_spleeter(
    args: argparse.Namespace,
    *,
    load_lock,
    fetch_sherpa_spleeter,
    target_selector,
) -> int:
    return _cmds.cmd_fetch_sherpa_spleeter(
        args,
        load_lock=load_lock,
        fetch_sherpa_spleeter=fetch_sherpa_spleeter,
        target_selection=target_selector,
    )


def cmd_fetch_spleeter_models(args: argparse.Namespace, *, load_lock, fetch_spleeter_models) -> int:
    return _cmds.cmd_fetch_spleeter_models(
        args,
        load_lock=load_lock,
        fetch_spleeter_models=fetch_spleeter_models,
    )


def cmd_fetch_silero_vad(args: argparse.Namespace, *, load_lock, fetch_silero_vad, target_selector) -> int:
    return _cmds.cmd_fetch_silero_vad(
        args,
        load_lock=load_lock,
        fetch_silero_vad=fetch_silero_vad,
        target_selection=target_selector,
    )


def cmd_fetch_silero_vad_model(args: argparse.Namespace, *, load_lock, fetch_silero_vad_model) -> int:
    return _cmds.cmd_fetch_silero_vad_model(
        args,
        load_lock=load_lock,
        fetch_silero_vad_model=fetch_silero_vad_model,
    )


def cmd_lock_checksums(_args: argparse.Namespace, *, lock_checksums) -> int:
    lock_checksums()
    print(f"updated {LOCK_PATH.relative_to(ROOT)}")
    return 0


def cmd_build_rnnoise(args: argparse.Namespace, *, current_target_key) -> int:
    target = current_target_key() if args.target == "current" else args.target
    run_build_script(ROOT / "scripts" / "rnnoise_cli" / build_script_name(target), target)
    return 0


def build_release_assets_parser(**handlers):
    """Build the release assets CLI parser."""
    return build_parser(tool_names=TOOL_NAMES, **handlers)


def handle_release_asset_error(exc: ReleaseAssetError) -> int:
    """Print a CLI release asset error and return failure."""
    print(f"ERROR: {exc}", file=sys.stderr)
    return 1
