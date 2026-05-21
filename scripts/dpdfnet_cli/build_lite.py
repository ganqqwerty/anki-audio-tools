#!/usr/bin/env python3
"""Build the small DPDFNet TFLite standalone CLI."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR / "lite_src"
MODEL_NAME = "dpdfnet4"
MODEL_FILENAME = f"{MODEL_NAME}.tflite"
MODEL_URL = f"https://huggingface.co/Ceva-IP/DPDFNet/resolve/main/{MODEL_FILENAME}?download=true"
MODEL_SHA256 = "d544a0f9e65180b0f67d1442cb9d33cec33347076dc427af97a461a75dd19c06"
MODEL_BYTES = 13_515_600

EXCLUDED_MODULES = [
    "tensorflow",
    "onnxruntime",
    "librosa",
    "scipy",
    "soundfile",
    "torch",
    "PyQt5",
]


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest for ``path``."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_model(path: Path) -> None:
    """Validate the locked Lite model payload."""
    if not path.is_file():
        raise FileNotFoundError(f"Model file not found: {path}")
    size = path.stat().st_size
    if size != MODEL_BYTES:
        raise RuntimeError(f"Unexpected {MODEL_FILENAME} size: {size}; expected {MODEL_BYTES}.")
    digest = sha256_file(path)
    if digest != MODEL_SHA256:
        raise RuntimeError(f"Unexpected {MODEL_FILENAME} sha256: {digest}; expected {MODEL_SHA256}.")


def download_model(model_path: Path, *, force: bool = False) -> Path:
    """Download the locked Lite model when it is not already cached."""
    model_path.parent.mkdir(parents=True, exist_ok=True)
    if model_path.is_file() and not force:
        verify_model(model_path)
        return model_path

    temp_path = model_path.with_suffix(model_path.suffix + ".tmp")
    print(f"Downloading {MODEL_FILENAME} from {MODEL_URL}")
    with urlopen(MODEL_URL, timeout=120) as response, temp_path.open("wb") as out:  # nosec B310
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    temp_path.replace(model_path)
    verify_model(model_path)
    return model_path


def build_pyinstaller_args(args: argparse.Namespace, model_path: Path) -> list[str]:
    """Return the PyInstaller command for the Lite CLI."""
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--console",
        "--name",
        args.name,
    ]
    if sys.platform == "darwin" and args.target_arch:
        command.extend(["--target-architecture", args.target_arch])
    command.extend(
        [
            "--distpath",
            str(args.dist_dir),
            "--workpath",
            str(args.work_dir),
            "--specpath",
            str(args.spec_dir),
            "--paths",
            str(SRC_DIR),
            "--add-data",
            f"{model_path}{os.pathsep}dpdfnet_lite/assets",
            "--collect-binaries",
            "ai_edge_litert",
            "--collect-data",
            "ai_edge_litert",
            "--hidden-import",
            "ai_edge_litert.interpreter",
        ]
    )
    for module in EXCLUDED_MODULES:
        command.extend(["--exclude-module", module])
    command.append(str(SRC_DIR / "dpdfnet_lite" / "__main__.py"))
    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="dpdfnet", help="Executable name.")
    parser.add_argument("--model", default=MODEL_NAME, help="Model name to bundle. Only dpdfnet4 is supported.")
    parser.add_argument(
        "--model-path",
        type=Path,
        default=ROOT / ".release-assets" / "sources" / "dpdfnet" / MODEL_FILENAME,
        help="Where to store/use the bundled TFLite model.",
    )
    parser.add_argument("--force-download", action="store_true", help="Redownload the bundled model.")
    parser.add_argument("--download-only", action="store_true", help="Download and verify the model, then exit.")
    parser.add_argument("--dist-dir", type=Path, required=True, help="PyInstaller dist dir.")
    parser.add_argument("--work-dir", type=Path, required=True, help="PyInstaller work dir.")
    parser.add_argument("--spec-dir", type=Path, required=True, help="PyInstaller spec dir.")
    parser.add_argument(
        "--target-arch",
        choices=("arm64", "x86_64"),
        help="macOS target architecture passed to PyInstaller.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.model != MODEL_NAME:
        raise RuntimeError(f"Unsupported Lite model {args.model!r}; expected {MODEL_NAME!r}.")
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError(
            "Standalone Lite builds are pinned to Python 3.11. "
            f"Current interpreter is {sys.version_info.major}.{sys.version_info.minor}."
        )

    model_path = download_model(args.model_path.expanduser().resolve(), force=args.force_download)
    print(f"Verified {model_path} ({model_path.stat().st_size} bytes)")

    if args.download_only:
        return 0

    for directory in (args.dist_dir, args.work_dir, args.spec_dir):
        directory.mkdir(parents=True, exist_ok=True)

    command = build_pyinstaller_args(args, model_path)
    print("Running:", " ".join(command))
    subprocess.run(command, check=True)  # nosec B603

    suffix = ".exe" if sys.platform == "win32" else ""
    artifact = args.dist_dir / f"{args.name}{suffix}"
    if not artifact.is_file():
        raise FileNotFoundError(f"Expected PyInstaller artifact not found: {artifact}")
    print(f"Built {artifact} ({artifact.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
