"""Region-delete request parsing helpers."""

from __future__ import annotations

from typing import Any, cast

from .editor_session import RegionDeleteOperation, RegionDeleteRequest
from .i18n import t
from .sound_refs import safe_media_basename

REGION_DELETE_OPERATION: RegionDeleteOperation = "delete-selection"
REGION_KEEP_OPERATION: RegionDeleteOperation = "delete-rest"
REGION_DELETE_OPERATIONS = {REGION_DELETE_OPERATION, REGION_KEEP_OPERATION}


def parse_region_delete_request(request: Any) -> RegionDeleteRequest | None:
    """Normalize a frontend region-delete request."""
    if not isinstance(request, dict):
        return None
    values = required_region_delete_values(request)
    if values is None:
        return None
    raw_ord, raw_duration, raw_start, raw_end = values
    try:
        field_index = int(raw_ord)
        duration_ms = max(0, int(round(float(raw_duration))))
        start_value = int(round(float(raw_start)))
        end_value = int(round(float(raw_end)))
        cursor_ms = int(round(float(request.get("cursorMs", 0))))
    except (TypeError, ValueError):
        return None
    if field_index < 0 or duration_ms <= 0:
        return None
    start = max(0, min(start_value, duration_ms))
    end = max(0, min(end_value, duration_ms))
    if end < start:
        start, end = end, start
    if end <= start:
        return None
    source_filename = region_delete_source_filename(request)
    if not source_filename:
        return None
    operation = region_delete_operation(request)
    if operation is None:
        return None
    return RegionDeleteRequest(
        field_index=field_index,
        source_filename=source_filename,
        selection_start_ms=start,
        selection_end_ms=end,
        cursor_ms=max(0, min(cursor_ms, duration_ms)),
        duration_ms=duration_ms,
        trigger=region_delete_trigger(request),
        playback_active=bool(request.get("playbackActive")),
        operation=operation,
    )


def required_region_delete_values(request: dict[str, Any]) -> tuple[Any, Any, Any, Any] | None:
    """Return required raw region-delete values when all are present."""
    values = (
        request.get("ord"),
        request.get("durationMs"),
        request.get("selectionStartMs"),
        request.get("selectionEndMs"),
    )
    return None if any(value is None for value in values) else cast(tuple[Any, Any, Any, Any], values)


def region_delete_source_filename(request: dict[str, Any]) -> str:
    """Return the sanitized requested source filename."""
    return safe_media_basename(str(request.get("sourceFilename") or ""))


def region_delete_trigger(request: dict[str, Any]) -> str:
    """Return a normalized region-delete trigger label."""
    trigger = str(request.get("trigger") or "")
    return trigger if trigger in {"button", "backspace"} else "unknown"


def region_delete_operation(request: dict[str, Any]) -> RegionDeleteOperation | None:
    """Return the normalized selected-region operation."""
    operation = REGION_DELETE_OPERATION if "operation" not in request else str(request["operation"])
    if operation not in REGION_DELETE_OPERATIONS:
        return None
    return operation


def region_operation_busy_message(request: RegionDeleteRequest) -> str:
    """Return the frontend busy message for a selected-region operation."""
    return t("editor.status.deleting_rest") if request.operation == REGION_KEEP_OPERATION else t("editor.status.deleting_region")


def region_operation_command_status(request: RegionDeleteRequest) -> str:
    """Return the ffmpeg status prefix for a selected-region operation."""
    return t("editor.status.deleting_rest_ffmpeg") if request.operation == REGION_KEEP_OPERATION else t("editor.status.deleting_region_ffmpeg")


def region_operation_whole_clip_message(request: RegionDeleteRequest) -> str:
    """Return the warning shown when the selected operation would be a no-op."""
    return t("editor.status.keep_whole_clip") if request.operation == REGION_KEEP_OPERATION else t("editor.status.delete_whole_clip")
