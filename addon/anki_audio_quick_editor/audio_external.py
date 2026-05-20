"""External audio command execution helpers."""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404
import time
from pathlib import Path
from typing import Any

from .audio_state import AudioProcessingConfig
from .audio_tools import find_ffmpeg, find_ffprobe
from .diagnostics_runtime import is_debug_enabled, new_operation_id, record_breadcrumb
from .errors import AudioProcessingError


def _is_windows() -> bool:
    return os.name == "nt"


def _external_command_run_kwargs() -> dict[str, Any]:
    if not _is_windows() or is_debug_enabled():
        return {}
    return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}


def probe_duration_ms(source_path: Path, config: AudioProcessingConfig) -> int:
    """Inspect an audio file duration with ffprobe."""
    operation_id = new_operation_id("ffprobe")
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
    started = time.monotonic()
    record_breadcrumb(
        "external.command.started",
        source="external",
        operation="external.ffprobe",
        operation_id=operation_id,
        context={"argv": cmd, "source_path": str(source_path)},
    )
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        **_external_command_run_kwargs(),
    )  # nosec B603
    record_breadcrumb(
        "external.command.finished",
        source="external",
        level="error" if result.returncode != 0 else "debug",
        operation="external.ffprobe",
        operation_id=operation_id,
        context={
            "argv": cmd,
            "returncode": result.returncode,
            "duration_seconds": round(time.monotonic() - started, 6),
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-2000:],
        },
        flush=result.returncode != 0,
    )
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
    timeout_seconds: float | None = None,
) -> subprocess.CompletedProcess[str]:
    operation_id = new_operation_id("external")
    started = time.monotonic()
    record_breadcrumb(
        "external.command.started",
        source="external",
        operation="external.command",
        operation_id=operation_id,
        context={"argv": list(command)},
    )
    try:
        run_kwargs = _external_command_run_kwargs()
        if timeout_seconds is not None:
            run_kwargs["timeout"] = timeout_seconds
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
            **run_kwargs,
        )  # nosec B603
        record_breadcrumb(
            "external.command.finished",
            source="external",
            level="error" if result.returncode != 0 else "debug",
            operation="external.command",
            operation_id=operation_id,
            context={
                "argv": list(command),
                "returncode": result.returncode,
                "duration_seconds": round(time.monotonic() - started, 6),
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-2000:],
            },
            flush=result.returncode != 0,
        )
        return result
    except subprocess.TimeoutExpired as exc:
        timeout_label = "unknown" if timeout_seconds is None else f"{timeout_seconds:g}"
        timeout_message = f"{launch_error_message} Timed out after {timeout_label} seconds."
        record_breadcrumb(
            "external.command.timed_out",
            source="external",
            level="error",
            operation="external.command",
            operation_id=operation_id,
            context={
                "argv": list(command),
                "duration_seconds": round(time.monotonic() - started, 6),
                "timeout_seconds": timeout_seconds,
                "stdout": str(exc.stdout or "")[-2000:],
                "stderr": str(exc.stderr or "")[-2000:],
            },
            flush=True,
        )
        raise AudioProcessingError(timeout_message) from exc
    except OSError as exc:
        record_breadcrumb(
            "external.command.launch_failed",
            source="external",
            level="error",
            operation="external.command",
            operation_id=operation_id,
            context={
                "argv": list(command),
                "duration_seconds": round(time.monotonic() - started, 6),
                "launch_error": str(exc),
            },
            flush=True,
        )
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
