from __future__ import annotations

import os
import subprocess
from pathlib import Path

import numpy as np

from .audio import MODEL_SAMPLE_RATE


def ffmpeg_binary() -> str:
    return os.environ.get("DPDFNET_FFMPEG", "ffmpeg")


def build_decode_command(input_path: Path, sample_rate: int = MODEL_SAMPLE_RATE) -> list[str]:
    return [
        ffmpeg_binary(),
        "-hide_banner",
        "-nostdin",
        "-v",
        "error",
        "-i",
        str(Path(input_path)),
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "-ac",
        "1",
        "-ar",
        str(int(sample_rate)),
        "pipe:1",
    ]


def decode_audio(input_path: Path, sample_rate: int = MODEL_SAMPLE_RATE) -> np.ndarray:
    path = Path(input_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")

    command = build_decode_command(path, sample_rate=sample_rate)
    try:
        result = subprocess.run(command, check=False, capture_output=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "ffmpeg was not found on PATH. Install ffmpeg or set DPDFNET_FFMPEG to its executable path."
        ) from exc

    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"ffmpeg failed to decode '{path}': {detail or 'unknown error'}")

    return np.frombuffer(result.stdout, dtype="<f4").astype(np.float32, copy=True)
