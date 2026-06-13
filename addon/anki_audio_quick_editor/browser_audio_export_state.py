"""Import-safe state and contract helpers for Browser audio export."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .audio_export_planning import default_audio_field_selections
from .audio_export_types import (
    EXPORT_MODE_COMBINED_MP3,
    EXPORT_MODE_ZIP,
    MAX_SILENCE_BETWEEN_CLIPS_SECONDS,
    AudioExportFieldSelection,
    AudioExportMode,
    AudioExportReport,
    AudioExportRequest,
)
from .batch_operations import BatchNoteSnapshot, FieldGroup
from .contracts_generated import AudioExportStartRequest
from .i18n import active_context

CONTRACT_DECODE_ERRORS = (AssertionError, TypeError, ValueError)
_DEFAULT_SILENCE_BETWEEN_CLIPS_SECONDS = 1.0


def build_audio_export_initial_state(
    note_count: int,
    groups: tuple[FieldGroup, ...],
    snapshots: tuple[BatchNoteSnapshot, ...] | list[BatchNoteSnapshot],
) -> dict[str, Any]:
    """Return JSON-serializable state consumed by the audio export surface."""
    i18n = active_context()
    messages = dict(i18n["messages"])
    return {
        "surface": "audio_export",
        "note_count": note_count,
        "field_groups": [_field_group_payload(group) for group in groups],
        "default_field_selections": [
            _field_selection_payload(selection)
            for selection in default_audio_field_selections(snapshots)
        ],
        "defaults": {
            "mode": EXPORT_MODE_ZIP,
            "silence_between_clips_seconds": _DEFAULT_SILENCE_BETWEEN_CLIPS_SECONDS,
        },
        "locale": i18n["locale"],
        "direction": i18n["direction"],
        "messages": messages,
    }


def request_from_audio_export_start_payload(raw_payload: object) -> AudioExportRequest:
    """Decode and validate one frontend audio export start request."""
    try:
        payload = AudioExportStartRequest.from_dict(raw_payload).to_dict()
    except CONTRACT_DECODE_ERRORS as exc:
        raise ValueError("Choose an export mode before starting.") from exc

    mode = _export_mode(payload.get("mode"))

    destination_path = str(payload.get("destination_path") or "").strip()
    if not destination_path or Path(destination_path) == Path():
        raise ValueError("Choose a destination before starting.")

    field_selections = _field_selections(payload.get("field_selections"))
    if not field_selections:
        raise ValueError("Choose at least one field before starting.")

    silence_between_clips_seconds = float(payload["silence_between_clips_seconds"])
    if (
        not math.isfinite(silence_between_clips_seconds)
        or silence_between_clips_seconds < 0
        or silence_between_clips_seconds > MAX_SILENCE_BETWEEN_CLIPS_SECONDS
    ):
        raise ValueError("Silence between clips must be between 0 and 10 seconds.")

    return AudioExportRequest(
        mode=mode,
        destination_path=Path(destination_path),
        field_selections=field_selections,
        silence_between_clips_seconds=silence_between_clips_seconds,
    )


def audio_export_progress_payload(
    *,
    processed: int,
    total: int,
    current_audio: str,
    failures: int,
    message: str,
) -> dict[str, Any]:
    """Return the typed progress payload sent to Svelte."""
    return {
        "processed": processed,
        "total": total,
        "current_audio": current_audio,
        "failures": failures,
        "message": message,
    }


def audio_export_finish_payload(report: AudioExportReport) -> dict[str, Any]:
    """Return the typed final payload sent to Svelte."""
    return {
        "processed": report.processed,
        "total": report.total,
        "exported": report.exported,
        "skipped": report.skipped,
        "failures": report.failures,
        "canceled": report.canceled,
        "output_path": report.output_path,
        "summary": report.summary,
    }


def _field_selections(raw: object) -> tuple[AudioExportFieldSelection, ...]:
    if not isinstance(raw, list):
        return ()
    return tuple(
        selection
        for entry in raw
        if (selection := _field_selection_from_payload(entry)) is not None
    )


def _field_selection_from_payload(entry: object) -> AudioExportFieldSelection | None:
    if not isinstance(entry, dict):
        return None
    notetype_name = str(entry.get("notetype_name") or "")
    fields = entry.get("fields")
    if not notetype_name or not isinstance(fields, list):
        return None
    selected_fields = tuple(field for field in fields if isinstance(field, str) and field)
    if not selected_fields:
        return None
    return AudioExportFieldSelection(notetype_name, selected_fields)


def _export_mode(raw: object) -> AudioExportMode:
    mode = str(raw or "")
    if mode == EXPORT_MODE_ZIP:
        return EXPORT_MODE_ZIP
    if mode == EXPORT_MODE_COMBINED_MP3:
        return EXPORT_MODE_COMBINED_MP3
    raise ValueError("Choose an export mode before starting.")


def _field_group_payload(group: FieldGroup) -> dict[str, Any]:
    return {"notetype_name": group.notetype_name, "fields": list(group.fields)}


def _field_selection_payload(selection: AudioExportFieldSelection) -> dict[str, Any]:
    return {"notetype_name": selection.notetype_name, "fields": list(selection.fields)}
