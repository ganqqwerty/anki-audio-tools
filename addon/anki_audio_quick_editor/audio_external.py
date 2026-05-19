"""External audio command execution helpers."""

from __future__ import annotations

import json
import subprocess  # nosec B404
from pathlib import Path

from .audio_state import AudioProcessingConfig
from .audio_tools import find_ffmpeg, find_ffprobe
from .errors import AudioProcessingError


def probe_duration_ms(source_path: Path, config: AudioProcessingConfig) -> int:
    """Inspect an audio file duration with ffprobe."""
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    ffprobe_path = find_ffprobe(ffmpeg_path)
    cmd = [
        str(ffprobe_path),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(source_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # nosec B603
    if result.returncode != 0:
        raise AudioProcessingError(result.stderr.strip() or "Could not inspect audio duration.")
    try:
        seconds = float(json.loads(result.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AudioProcessingError("Could not parse audio duration.") from exc
    return max(0, round(seconds * 1000))


def _run_external_command(
    command: tuple[str, ...],
    launch_error_message: str,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
        )  # nosec B603
    except OSError as exc:
        raise AudioProcessingError(f"{launch_error_message} {exc}") from exc


def _render_external_error_message(
    result: subprocess.CompletedProcess[str],
    default_message: str,
) -> str:
    for candidate in (result.stderr.strip(), result.stdout.strip()):
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            return candidate
        if isinstance(parsed, dict):
            error = parsed.get("error")
            if isinstance(error, str) and error.strip():
                return error.strip()
        return candidate
    return default_message

