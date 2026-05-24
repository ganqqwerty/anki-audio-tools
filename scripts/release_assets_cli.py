"""CLI parser construction for release asset workflows."""

from __future__ import annotations

import argparse
from collections.abc import Callable


def build_parser(
    *,
    cmd_fetch_deepfilter: Callable[[argparse.Namespace], int],
    cmd_fetch_ffmpeg: Callable[[argparse.Namespace], int],
    cmd_fetch_sherpa_spleeter: Callable[[argparse.Namespace], int],
    cmd_build_rnnoise: Callable[[argparse.Namespace], int],
    cmd_verify: Callable[[argparse.Namespace], int],
    cmd_fetch_spleeter_models: Callable[[argparse.Namespace], int],
    cmd_lock_checksums: Callable[[argparse.Namespace], int],
    cmd_stage: Callable[[argparse.Namespace], int],
    tool_names: list[str],
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare locked native release assets")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, func in (
        ("fetch-deepfilter", cmd_fetch_deepfilter),
        ("fetch-ffmpeg", cmd_fetch_ffmpeg),
        ("fetch-sherpa-spleeter", cmd_fetch_sherpa_spleeter),
        ("build-rnnoise", cmd_build_rnnoise),
        ("verify", cmd_verify),
    ):
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--target", default="current")
        if name == "verify":
            subparser.add_argument(
                "--diagnostics",
                action="store_true",
                help="Also run current-host runtime diagnostics after checksum verification",
            )
        subparser.set_defaults(func=func)
    subparsers.add_parser("fetch-spleeter-models").set_defaults(func=cmd_fetch_spleeter_models)
    subparsers.add_parser("lock-checksums").set_defaults(func=cmd_lock_checksums)
    stage = subparsers.add_parser("stage")
    stage.add_argument("--target", default="all")
    stage.add_argument("--tool", action="append", choices=tool_names, dest="tools")
    stage.add_argument("--destination", required=True)
    stage.set_defaults(func=cmd_stage)
    return parser
