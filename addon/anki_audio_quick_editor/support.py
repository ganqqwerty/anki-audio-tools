"""Support helpers for collecting external-runtime failures and diagnostics."""

from __future__ import annotations

import copy
import json
import shlex
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .i18n import t

LOG_TAIL_LINE_COUNT = 200

SUPPORT_REPORT_HINT = t("support.report_hint")

_SUPPORT_LOCK = threading.Lock()
_LATEST_DENOISE_INCIDENT: dict[str, Any] | None = None
_LATEST_SPLEETER_INCIDENT: dict[str, Any] | None = None
_LATEST_PAUSE_PIPELINE_INCIDENT: dict[str, Any] | None = None
_INCIDENT_IDENTITY_FIELDS = ("operation", "source_path", "user_message", "exception_type")


def addon_log_path(addon_dir: str | Path) -> Path:
    """Return the add-on log file path for ``addon_dir``."""
    return Path(addon_dir) / "anki_audio_quick_editor.log"


def _merge_support_fields(
    existing: dict[str, Any] | None,
    fields: dict[str, Any],
    *,
    start_new_on_identity_change: bool = True,
) -> dict[str, Any]:
    starts_new = start_new_on_identity_change and _starts_new_incident(existing, fields)
    base = None if starts_new else existing
    merged = copy.deepcopy(base) if base else {}
    merged.setdefault("timestamp", datetime.now(UTC).isoformat())
    for key, value in fields.items():
        if _is_empty_support_field(key, value, starts_new=starts_new):
            continue
        merged[key] = copy.deepcopy(value)
    return merged


def _is_empty_support_field(key: str, value: Any, *, starts_new: bool) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value
    if isinstance(value, list):
        return not value and not _keeps_empty_attempted_commands(key, starts_new)
    if isinstance(value, dict):
        return not value
    return False


def _keeps_empty_attempted_commands(key: str, starts_new: bool) -> bool:
    return starts_new and key == "attempted_commands"


def _starts_new_incident(existing: dict[str, Any] | None, fields: dict[str, Any]) -> bool:
    if existing is None:
        return False
    for key in _INCIDENT_IDENTITY_FIELDS:
        value = fields.get(key)
        if not isinstance(value, str) or not value:
            continue
        existing_value = existing.get(key)
        if isinstance(existing_value, str) and existing_value and existing_value != value:
            return True
    return False


# noinspection PyInconsistentReturns
def record_latest_denoise_support_incident(**fields: Any) -> dict[str, Any]:
    """Merge ``fields`` into the latest external-denoise support incident."""
    global _LATEST_DENOISE_INCIDENT

    with _SUPPORT_LOCK:
        _LATEST_DENOISE_INCIDENT = _merge_support_fields(_LATEST_DENOISE_INCIDENT, fields)
        return copy.deepcopy(_LATEST_DENOISE_INCIDENT)


# noinspection PyInconsistentReturns
def latest_denoise_support_incident() -> dict[str, Any] | None:
    """Return the latest recorded external-denoise support incident, if any."""
    with _SUPPORT_LOCK:
        return copy.deepcopy(_LATEST_DENOISE_INCIDENT)


def clear_latest_denoise_support_incident() -> None:
    """Clear the recorded external-denoise support incident."""
    global _LATEST_DENOISE_INCIDENT

    with _SUPPORT_LOCK:
        _LATEST_DENOISE_INCIDENT = None


# noinspection PyInconsistentReturns
def record_latest_rnnoise_support_incident(**fields: Any) -> dict[str, Any]:
    """Compatibility wrapper for callers that still name RNNoise specifically."""
    return record_latest_denoise_support_incident(**fields)


# noinspection PyInconsistentReturns
def latest_rnnoise_support_incident() -> dict[str, Any] | None:
    """Compatibility wrapper for the latest external-denoise support incident."""
    return latest_denoise_support_incident()


def clear_latest_rnnoise_support_incident() -> None:
    """Compatibility wrapper for clearing external-denoise support context."""
    clear_latest_denoise_support_incident()


# noinspection PyInconsistentReturns
def record_latest_spleeter_support_incident(**fields: Any) -> dict[str, Any]:
    """Merge ``fields`` into the latest Sherpa Spleeter support incident."""
    global _LATEST_SPLEETER_INCIDENT

    with _SUPPORT_LOCK:
        _LATEST_SPLEETER_INCIDENT = _merge_support_fields(_LATEST_SPLEETER_INCIDENT, fields)
        return copy.deepcopy(_LATEST_SPLEETER_INCIDENT)


# noinspection PyInconsistentReturns
def latest_spleeter_support_incident() -> dict[str, Any] | None:
    """Return the latest recorded Sherpa Spleeter support incident, if any."""
    with _SUPPORT_LOCK:
        return copy.deepcopy(_LATEST_SPLEETER_INCIDENT)


def clear_latest_spleeter_support_incident() -> None:
    """Clear the recorded Sherpa Spleeter support incident."""
    global _LATEST_SPLEETER_INCIDENT

    with _SUPPORT_LOCK:
        _LATEST_SPLEETER_INCIDENT = None


# noinspection PyInconsistentReturns
def record_latest_pause_pipeline_support_incident(**fields: Any) -> dict[str, Any]:
    """Merge ``fields`` into the latest pause-pipeline support incident."""
    global _LATEST_PAUSE_PIPELINE_INCIDENT

    with _SUPPORT_LOCK:
        _LATEST_PAUSE_PIPELINE_INCIDENT = _merge_support_fields(
            _LATEST_PAUSE_PIPELINE_INCIDENT,
            fields,
            start_new_on_identity_change=False,
        )
        return copy.deepcopy(_LATEST_PAUSE_PIPELINE_INCIDENT)


# noinspection PyInconsistentReturns
def latest_pause_pipeline_support_incident() -> dict[str, Any] | None:
    """Return the latest recorded pause-pipeline support incident, if any."""
    with _SUPPORT_LOCK:
        return copy.deepcopy(_LATEST_PAUSE_PIPELINE_INCIDENT)


def clear_latest_pause_pipeline_support_incident() -> None:
    """Clear the recorded pause-pipeline support incident."""
    global _LATEST_PAUSE_PIPELINE_INCIDENT

    with _SUPPORT_LOCK:
        _LATEST_PAUSE_PIPELINE_INCIDENT = None


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


def format_denoise_support_log_block(incident: dict[str, Any]) -> str:
    """Render a compact multi-line external-denoise support block for logger output."""
    lines = [
        "denoise support incident:",
        f"  timestamp: {incident.get('timestamp', '')}",
        f"  operation: {incident.get('operation', '')}",
        f"  media_filename: {incident.get('media_filename', '')}",
        f"  source_path: {incident.get('source_path', '')}",
        f"  user_message: {incident.get('user_message', '')}",
        f"  exception_type: {incident.get('exception_type', '')}",
        f"  ffmpeg_path: {incident.get('ffmpeg_path', '')}",
    ]
    for key in ("rnnoise_path", "dpdfnet_path"):
        value = incident.get(key)
        if value:
            lines.append(f"  {key}: {value}")
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


def format_rnnoise_support_log_block(incident: dict[str, Any]) -> str:
    """Compatibility wrapper for the generic external-denoise support block."""
    return format_denoise_support_log_block(incident)


def format_spleeter_support_log_block(incident: dict[str, Any]) -> str:
    """Render a compact multi-line Sherpa Spleeter support block for logger output."""
    lines = [
        "sherpa spleeter support incident:",
        f"  timestamp: {incident.get('timestamp', '')}",
        f"  operation: {incident.get('operation', '')}",
        f"  media_filename: {incident.get('media_filename', '')}",
        f"  source_path: {incident.get('source_path', '')}",
        f"  user_message: {incident.get('user_message', '')}",
        f"  exception_type: {incident.get('exception_type', '')}",
        f"  ffmpeg_path: {incident.get('ffmpeg_path', '')}",
        f"  spleeter_path: {incident.get('spleeter_path', '')}",
        f"  vocals_model_path: {incident.get('vocals_model_path', '')}",
        f"  accompaniment_model_path: {incident.get('accompaniment_model_path', '')}",
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


def _append_attempted_command_report(
    sections: list[str],
    incident: dict[str, Any],
) -> None:
    attempted_commands = incident.get("attempted_commands", [])
    for index, command in enumerate(attempted_commands, start=1):
        sections.append(f"{index}. {command.get('command', '')}")
        sections.append(f"   returncode: {command.get('returncode')}")
        if command.get("launch_error"):
            sections.append(f"   launch_error: {command['launch_error']}")
        if command.get("stdout"):
            sections.append(f"   stdout: {command['stdout']}")
        if command.get("stderr"):
            sections.append(f"   stderr: {command['stderr']}")
    if not attempted_commands:
        sections.append("(no external commands were captured)")


def _append_incident_report_section(
    sections: list[str],
    *,
    title: str,
    incident: dict[str, Any] | None,
    missing_message: str,
    runtime_fields: tuple[tuple[str, str], ...],
) -> None:
    sections.extend(["", title])
    if incident is None:
        sections.append(missing_message)
        return

    sections.extend(
        [
            f"Timestamp: {incident.get('timestamp', '')}",
            f"Operation: {incident.get('operation', '')}",
            f"Media filename: {incident.get('media_filename', '')}",
            f"Source path: {incident.get('source_path', '')}",
            f"User message: {incident.get('user_message', '')}",
            f"Exception type: {incident.get('exception_type', '')}",
            f"ffmpeg path: {incident.get('ffmpeg_path', '')}",
        ]
    )
    for label, key in runtime_fields:
        value = incident.get(key)
        if value:
            sections.append(f"{label}: {value}")
    sections.append("Attempted commands:")
    _append_attempted_command_report(sections, incident)


def build_support_report_text(
    *,
    version: str,
    addon_dir: str,
    log_file_path: str,
    deep_filter_health: dict[str, Any],
    rnnoise_health: dict[str, Any],
    dpdfnet_health: dict[str, Any] | None = None,
    denoise_incident: dict[str, Any] | None,
    pause_pipeline_incident: dict[str, Any] | None,
    log_tail: str,
    spleeter_health: dict[str, Any] | None = None,
    spleeter_incident: dict[str, Any] | None = None,
    diagnostics_context: dict[str, Any] | None = None,
) -> str:
    """Build a support report suitable for copying into a bug report."""
    sections = [
        "Anki Audio Quick Editor Support Report",
        f"Generated: {datetime.now(UTC).isoformat()}",
        f"Add-on version: {version}",
        f"Add-on folder: {addon_dir}",
        f"Log file: {log_file_path}",
    ]
    _append_general_diagnostics_sections(sections, diagnostics_context)
    _append_incident_report_section(
        sections,
        title="Latest denoise failure",
        incident=denoise_incident,
        missing_message="No external denoise failure has been captured in this session.",
        runtime_fields=(("RNNoise path", "rnnoise_path"), ("DPDFNet path", "dpdfnet_path")),
    )
    _append_incident_report_section(
        sections,
        title="Latest Voice Only failure",
        incident=spleeter_incident,
        missing_message="No Voice Only failure has been captured in this session.",
        runtime_fields=(
            ("Sherpa Spleeter path", "spleeter_path"),
            ("Vocals model path", "vocals_model_path"),
            ("Accompaniment model path", "accompaniment_model_path"),
        ),
    )
    _append_incident_report_section(
        sections,
        title="Latest pause-shortening failure",
        incident=pause_pipeline_incident,
        missing_message="No pause-shortening failure has been captured in this session.",
        runtime_fields=(
            ("DeepFilterNet path", "deep_filter_path"),
            ("Artifact dir", "artifact_dir"),
            ("Manifest path", "manifest_path"),
        ),
    )

    sections.extend(
        [
            "",
            "Current DeepFilterNet health",
            json.dumps(deep_filter_health, indent=2, sort_keys=True),
            "",
            "Current RNNoise health",
            json.dumps(rnnoise_health, indent=2, sort_keys=True),
            "",
            "Current DPDFNet health",
            json.dumps(dpdfnet_health or {}, indent=2, sort_keys=True),
            "",
            "Current Sherpa Spleeter health",
            json.dumps(spleeter_health or {"available": False}, indent=2, sort_keys=True),
            "",
            f"Recent log tail (last {LOG_TAIL_LINE_COUNT} lines)",
            log_tail,
        ]
    )
    return "\n".join(sections)


def _append_general_diagnostics_sections(
    sections: list[str],
    diagnostics_context: dict[str, Any] | None,
) -> None:
    context = diagnostics_context or {}
    _append_latest_error_section(sections, _dict_or_none(context.get("latest_error")))
    recent_events = context.get("recent_events")
    _append_recent_events_section(
        sections,
        recent_events if isinstance(recent_events, list) else [],
    )
    _append_crash_forensics_section(sections, _dict_or_none(context.get("crash_forensics")) or {})


def _append_latest_error_section(
    sections: list[str],
    incident: dict[str, Any] | None,
) -> None:
    sections.extend(["", "Latest captured error"])
    if incident is None:
        sections.append("No general error boundary has captured a failure in this session.")
        return
    sections.extend(
        [
            f"Timestamp: {incident.get('timestamp', '')}",
            f"Session: {incident.get('session_id', '')}",
            f"Operation: {incident.get('operation', '')}",
            f"Operation id: {incident.get('operation_id', '')}",
            f"Boundary: {incident.get('boundary', '')}",
            f"Exception type: {incident.get('exception_type', '')}",
            f"User-visible message: {incident.get('user_message', '')}",
            f"Context: {json.dumps(incident.get('context', {}), sort_keys=True)}",
        ]
    )
    traceback_text = str(incident.get("traceback", "")).strip()
    if traceback_text:
        sections.extend(["Traceback:", traceback_text])


def _append_recent_events_section(sections: list[str], recent_events: list[Any]) -> None:
    sections.extend(["", "Recent event sequence"])
    if not recent_events:
        sections.append("No diagnostics breadcrumbs have been captured in this session.")
        return
    for event in recent_events[-40:]:
        if not isinstance(event, dict):
            continue
        context = event.get("context")
        rendered_context = f" | {json.dumps(context, sort_keys=True)}" if context else ""
        sections.append(
            f"{event.get('seq', '')}. {event.get('timestamp', '')} "
            f"{event.get('source', '')}:{event.get('event', '')} "
            f"operation={event.get('operation', '')} "
            f"operation_id={event.get('operation_id', '')} "
            f"boundary={event.get('boundary', '')}{rendered_context}"
        )


def _append_crash_forensics_section(
    sections: list[str],
    crash_forensics: dict[str, Any],
) -> None:
    previous_dirty = crash_forensics.get("previous_dirty_session")
    previous_clean = "unknown"
    if isinstance(previous_dirty, dict):
        previous_clean = "no"
    elif crash_forensics:
        previous_clean = "yes"
    sections.extend(
        [
            "",
            "Crash forensics",
            f"Previous session ended cleanly: {previous_clean}",
            f"Current session id: {crash_forensics.get('session_id', '')}",
            f"Debug enabled: {crash_forensics.get('debug_enabled', '')}",
            f"Event log path: {crash_forensics.get('event_log_path', '')}",
            f"Crash log path: {crash_forensics.get('crash_log_path', '')}",
            f"Session marker path: {crash_forensics.get('session_marker_path', '')}",
        ]
    )
    if isinstance(previous_dirty, dict):
        sections.append(f"Last dirty-session marker: {json.dumps(previous_dirty, sort_keys=True)}")


def _dict_or_none(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None
