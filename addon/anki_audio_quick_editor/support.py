"""Support helpers for collecting external-runtime failures and diagnostics."""

from __future__ import annotations

import copy
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import support_reporting as _support_reporting
from .i18n import t

build_command_record = _support_reporting.build_command_record
build_support_report_text = _support_reporting.build_support_report_text
format_denoise_support_log_block = _support_reporting.format_denoise_support_log_block
format_rnnoise_support_log_block = _support_reporting.format_rnnoise_support_log_block
format_spleeter_support_log_block = _support_reporting.format_spleeter_support_log_block
read_log_tail = _support_reporting.read_log_tail

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
