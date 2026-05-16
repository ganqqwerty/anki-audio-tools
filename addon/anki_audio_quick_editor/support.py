"""Support helpers for collecting recent Sidon failures and diagnostics."""

from __future__ import annotations

import copy
import json
import shlex
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LOG_TAIL_LINE_COUNT = 200
SIDON_SUPPORT_HINT = "Open Settings > Diagnostics to copy logs for the developer."

_SUPPORT_LOCK = threading.Lock()
_LATEST_SIDON_INCIDENT: dict[str, Any] | None = None


def addon_log_path(addon_dir: str | Path) -> Path:
    """Return the add-on log file path for ``addon_dir``."""
    return Path(addon_dir) / "anki_audio_quick_editor.log"


def record_latest_sidon_support_incident(**fields: Any) -> dict[str, Any]:
    """Merge ``fields`` into the latest Sidon support incident."""
    global _LATEST_SIDON_INCIDENT

    with _SUPPORT_LOCK:
        merged = copy.deepcopy(_LATEST_SIDON_INCIDENT) if _LATEST_SIDON_INCIDENT else {}
        merged.setdefault("timestamp", datetime.now(UTC).isoformat())
        for key, value in fields.items():
            if value is None:
                continue
            if isinstance(value, str) and not value:
                continue
            if isinstance(value, list) and not value:
                continue
            if isinstance(value, dict) and not value:
                continue
            merged[key] = copy.deepcopy(value)
        _LATEST_SIDON_INCIDENT = merged
        return copy.deepcopy(merged)


def latest_sidon_support_incident() -> dict[str, Any] | None:
    """Return the latest recorded Sidon support incident, if any."""
    with _SUPPORT_LOCK:
        return copy.deepcopy(_LATEST_SIDON_INCIDENT)


def clear_latest_sidon_support_incident() -> None:
    """Clear the recorded Sidon support incident."""
    global _LATEST_SIDON_INCIDENT

    with _SUPPORT_LOCK:
        _LATEST_SIDON_INCIDENT = None


def build_command_record(
    command: tuple[str, ...],
    *,
    returncode: int | None = None,
    stdout: str = "",
    stderr: str = "",
    launch_error: str = "",
) -> dict[str, Any]:
    """Return a JSON-serializable record for one attempted external command."""
    return {
        "argv": list(command),
        "command": format_command(command),
        "returncode": returncode,
        "stdout": stdout.strip(),
        "stderr": stderr.strip(),
        "launch_error": launch_error.strip(),
    }


def format_command(command: tuple[str, ...]) -> str:
    """Render ``command`` as a shell-style string for diagnostics."""
    return " ".join(shlex.quote(part) for part in command)


def format_sidon_support_log_block(incident: dict[str, Any]) -> str:
    """Render a compact multi-line support block for logger output."""
    lines = [
        "sidon support incident:",
        f"  timestamp: {incident.get('timestamp', '')}",
        f"  operation: {incident.get('operation', '')}",
        f"  media_filename: {incident.get('media_filename', '')}",
        f"  source_path: {incident.get('source_path', '')}",
        f"  user_message: {incident.get('user_message', '')}",
        f"  exception_type: {incident.get('exception_type', '')}",
        f"  ffmpeg_path: {incident.get('ffmpeg_path', '')}",
        f"  sidon_path: {incident.get('sidon_path', '')}",
        f"  sidon_model_dir: {incident.get('sidon_model_dir', '')}",
    ]
    for index, command in enumerate(incident.get("attempted_commands", []), start=1):
        lines.append(f"  command_{index}: {command.get('command', '')}")
        lines.append(f"    returncode: {command.get('returncode')}")
        if command.get("launch_error"):
            lines.append(f"    launch_error: {command['launch_error']}")
        if command.get("stdout"):
            lines.append(f"    stdout: {command['stdout']}")
        if command.get("stderr"):
            lines.append(f"    stderr: {command['stderr']}")
    return "\n".join(lines)


def read_log_tail(log_path: Path, max_lines: int = LOG_TAIL_LINE_COUNT) -> str:
    """Return the last ``max_lines`` lines from ``log_path`` or a clear fallback."""
    try:
        text = log_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"Log file not found: {log_path}"
    except OSError as exc:
        return f"Could not read log file {log_path}: {exc}"

    lines = text.splitlines()
    if not lines:
        return "(log file is empty)"
    return "\n".join(lines[-max_lines:])


def build_support_report_text(
    *,
    version: str,
    addon_dir: str,
    log_file_path: str,
    deep_filter_health: dict[str, Any],
    sidon_health: dict[str, Any],
    incident: dict[str, Any] | None,
    log_tail: str,
) -> str:
    """Build a support report suitable for copying into a bug report."""
    sections = [
        "Anki Audio Quick Editor Support Report",
        f"Generated: {datetime.now(UTC).isoformat()}",
        f"Add-on version: {version}",
        f"Add-on folder: {addon_dir}",
        f"Log file: {log_file_path}",
        "",
        "Latest Sidon failure",
    ]
    if incident is None:
        sections.append("No Sidon failure has been captured in this session.")
    else:
        sections.extend(
            [
                f"Timestamp: {incident.get('timestamp', '')}",
                f"Operation: {incident.get('operation', '')}",
                f"Media filename: {incident.get('media_filename', '')}",
                f"Source path: {incident.get('source_path', '')}",
                f"User message: {incident.get('user_message', '')}",
                f"Exception type: {incident.get('exception_type', '')}",
                f"ffmpeg path: {incident.get('ffmpeg_path', '')}",
                f"Sidon path: {incident.get('sidon_path', '')}",
                f"Sidon model dir: {incident.get('sidon_model_dir', '')}",
                "Attempted commands:",
            ]
        )
        for index, command in enumerate(incident.get("attempted_commands", []), start=1):
            sections.append(f"{index}. {command.get('command', '')}")
            sections.append(f"   returncode: {command.get('returncode')}")
            if command.get("launch_error"):
                sections.append(f"   launch_error: {command['launch_error']}")
            if command.get("stdout"):
                sections.append(f"   stdout: {command['stdout']}")
            if command.get("stderr"):
                sections.append(f"   stderr: {command['stderr']}")
        if not incident.get("attempted_commands"):
            sections.append("(no external commands were captured)")

    sections.extend(
        [
            "",
            "Current DeepFilterNet health",
            json.dumps(deep_filter_health, indent=2, sort_keys=True),
            "",
            "Current Sidon health",
            json.dumps(sidon_health, indent=2, sort_keys=True),
            "",
            f"Recent log tail (last {LOG_TAIL_LINE_COUNT} lines)",
            log_tail,
        ]
    )
    return "\n".join(sections)
