from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Sequence

from . import __version__
from .audio import MODEL_SAMPLE_RATE, validate_attn_limit_db
from .model import MODEL_NAME, build_interpreter, bundled_model_path
from .pipeline import enhance_file


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--attn-limit-db",
        "--attn_limit_db",
        dest="attn_limit_db",
        type=float,
        default=None,
        help="Offline attenuation limit in dB. Higher values allow stronger denoising.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dpdfnet",
        description="Small DPDFNet TFLite speech enhancement CLI. Requires ffmpeg on PATH.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"dpdfnet-lite {__version__} ({MODEL_NAME}, {MODEL_SAMPLE_RATE} Hz)",
    )

    subparsers = parser.add_subparsers(dest="command")

    p_enhance = subparsers.add_parser("enhance", help="Enhance one audio file.")
    p_enhance.add_argument("input", type=Path, help="Input audio file readable by ffmpeg.")
    p_enhance.add_argument("output", type=Path, help="Output mono 16 kHz PCM16 WAV path.")
    _add_common_args(p_enhance)

    p_enhance_dir = subparsers.add_parser(
        "enhance-dir",
        help="Enhance all regular files in one directory (non-recursive).",
    )
    p_enhance_dir.add_argument("input_dir", type=Path, help="Input directory.")
    p_enhance_dir.add_argument("output_dir", type=Path, help="Output directory.")
    p_enhance_dir.add_argument(
        "--workers",
        type=int,
        default=None,
        metavar="N",
        help="Number of parallel workers. Defaults to CPU count.",
    )
    _add_common_args(p_enhance_dir)

    return parser


def _iter_input_files(input_dir: Path) -> list[Path]:
    directory = input_dir.expanduser().resolve()
    if not directory.is_dir():
        raise FileNotFoundError(f"Input directory not found: {directory}")
    files = sorted(path for path in directory.iterdir() if path.is_file() and not path.name.startswith("."))
    if not files:
        raise FileNotFoundError(f"No input files found in {directory}")
    return files


def _run_enhance(args: argparse.Namespace) -> int:
    attn_limit_db = validate_attn_limit_db(args.attn_limit_db)
    runtime = build_interpreter()
    stats = enhance_file(
        input_path=args.input,
        output_path=args.output,
        interpreter=runtime,
        attn_limit_db=attn_limit_db,
    )
    print(f"Wrote enhanced audio: {stats.output_path}")
    print(
        f"frames={stats.frames} avg_frame={stats.avg_frame_ms:.4f}ms "
        f"rtf={stats.rtf:.6f}"
    )
    return 0


def _run_enhance_dir(args: argparse.Namespace) -> int:
    attn_limit_db = validate_attn_limit_db(args.attn_limit_db)
    input_files = _iter_input_files(args.input_dir)
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    n_workers = args.workers or (os.cpu_count() or 1)
    if n_workers < 1:
        raise ValueError("--workers must be at least 1")

    print(f"Model : {MODEL_NAME}")
    print(f"Model file: {bundled_model_path()}")
    print(f"Output: {output_dir}")
    print(f"Found {len(input_files)} file(s). Enhancing with {n_workers} worker(s)...")

    def _process(input_path: Path):
        output_path = output_dir / f"{input_path.stem}_enhanced.wav"
        return enhance_file(
            input_path=input_path,
            output_path=output_path,
            interpreter=build_interpreter(),
            attn_limit_db=attn_limit_db,
        )

    errors: list[tuple[Path, BaseException]] = []
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        future_to_path = {pool.submit(_process, path): path for path in input_files}
        for future in as_completed(future_to_path):
            source = future_to_path[future]
            exc = future.exception()
            if exc is not None:
                errors.append((source, exc))
                print(f"[FAIL] {source.name}: {exc}", file=sys.stderr)
                continue
            stats = future.result()
            print(
                f"[OK] {source.name} -> {stats.output_path.name} "
                f"frames={stats.frames} rtf={stats.rtf:.6f}"
            )

    if errors:
        messages = "\n".join(f"  {path}: {exc}" for path, exc in errors)
        raise RuntimeError(f"Errors during processing:\n{messages}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    try:
        if args.command == "enhance":
            return _run_enhance(args)
        if args.command == "enhance-dir":
            return _run_enhance_dir(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    parser.print_help()
    return 2
