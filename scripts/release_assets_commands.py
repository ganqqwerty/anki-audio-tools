"""CLI subcommand helpers for release assets."""

from __future__ import annotations

import argparse
from pathlib import Path


def cmd_verify(args: argparse.Namespace, *, load_lock, verify_assets, target_selection) -> int:
    lock = load_lock()
    result = verify_assets(lock, target_keys=target_selection(args.target), run_diagnostics=bool(args.diagnostics))
    for report in result.reports:
        print(report)
    return 0 if result.ok else 1


def cmd_stage(args: argparse.Namespace, *, load_lock, stage_assets, target_selection) -> int:
    lock = load_lock()
    staged = stage_assets(lock, destination=Path(args.destination), target_keys=target_selection(args.target), tool_names=args.tools)
    for path in staged:
        print(path)
    return 0


def cmd_fetch_deepfilter(args: argparse.Namespace, *, load_lock, fetch_deepfilter, target_selection) -> int:
    lock = load_lock()
    for path in fetch_deepfilter(lock, target_keys=target_selection(args.target)):
        print(path)
    return 0


def cmd_fetch_ffmpeg(args: argparse.Namespace, *, load_lock, fetch_ffmpeg, target_selection) -> int:
    lock = load_lock()
    for path in fetch_ffmpeg(lock, target_keys=target_selection(args.target)):
        print(path)
    return 0


def cmd_fetch_sherpa_spleeter(args: argparse.Namespace, *, load_lock, fetch_sherpa_spleeter, target_selection) -> int:
    lock = load_lock()
    for path in fetch_sherpa_spleeter(lock, target_keys=target_selection(args.target)):
        print(path)
    return 0


def cmd_fetch_spleeter_models(_args: argparse.Namespace, *, load_lock, fetch_spleeter_models) -> int:
    lock = load_lock()
    for path in fetch_spleeter_models(lock):
        print(path)
    return 0
