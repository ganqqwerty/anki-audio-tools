"""Import-safe state and contract helpers for the Browser batch dialog."""

from __future__ import annotations

from typing import Any

from .audio_operation_params import parameters_from_raw
from .audio_operations import (
    BATCH_OPERATIONS,
    OP_CONVERT,
    OP_DENOISE,
    OP_FASTER,
    OP_GRAPH,
    OP_REMOVE_PAUSES,
    OP_SLOWER,
    OP_VOLUME_DOWN,
    OP_VOLUME_UP,
    operation_label,
    requires_target_field,
)
from .audio_state import AudioProcessingConfig
from .batch_operations import BatchRunRequest, FieldGroup
from .browser_report import BatchRunReport
from .contracts_generated import BatchStartRequest
from .i18n import active_context, format_message

CONTRACT_DECODE_ERRORS = (AssertionError, TypeError, ValueError)


def build_batch_initial_state(
    *,
    note_count: int,
    groups: tuple[FieldGroup, ...],
    config: AudioProcessingConfig,
) -> dict[str, Any]:
    """Return JSON-serializable state consumed by the batch Svelte app."""
    i18n = active_context()
    messages = dict(i18n["messages"])
    return {
        "note_count": note_count,
        "operations": [_operation_option(operation, messages) for operation in BATCH_OPERATIONS],
        "field_groups": [
            {"notetype_name": group.notetype_name, "fields": list(group.fields)}
            for group in groups
        ],
        "defaults": {
            "speed_step": config.speed_step,
            "volume_step_db": config.volume_step_db,
            "pause_aggressiveness": config.pause_aggressiveness,
            "pause_detection_algorithm": config.pause_detection_algorithm,
            "pause_silencedetect_threshold_db": config.pause_silencedetect_threshold_db,
            "pause_silencedetect_min_silence_seconds": (
                config.pause_silencedetect_min_silence_seconds
            ),
            "pause_silencedetect_min_speech_seconds": (
                config.pause_silencedetect_min_speech_seconds
            ),
            "pause_silencedetect_preprocess_denoise": (
                config.pause_silencedetect_preprocess_denoise
            ),
            "pause_silero_threshold": config.pause_silero_threshold,
            "pause_silero_min_silence_seconds": config.pause_silero_min_silence_seconds,
            "pause_silero_min_speech_seconds": config.pause_silero_min_speech_seconds,
            "pause_silero_preprocess_denoise": config.pause_silero_preprocess_denoise,
            "denoise_algorithm": config.denoise_algorithm,
            "dpdfnet_attn_limit_db": config.dpdfnet_attn_limit_db,
            "output_format": config.output_format,
        },
        "locale": i18n["locale"],
        "direction": i18n["direction"],
        "messages": messages,
    }


def request_from_batch_start_payload(raw_payload: object) -> BatchRunRequest:
    """Decode and validate one frontend batch start request."""
    payload = BatchStartRequest.from_dict(raw_payload).to_dict()
    params = payload.get("parameters") or {}
    return BatchRunRequest(
        operation=str(payload.get("operation") or ""),
        source_field=str(payload.get("source_field") or ""),
        target_field=payload.get("target_field"),
        parameters=parameters_from_raw(
            speed_step=params.get("speed_step"),
            volume_step_db=params.get("volume_step_db"),
            pause_aggressiveness=params.get("pause_aggressiveness"),
            pause_detection_algorithm=params.get("pause_detection_algorithm"),
            pause_threshold=params.get("pause_threshold"),
            pause_min_silence_seconds=params.get("pause_min_silence_seconds"),
            pause_min_speech_seconds=params.get("pause_min_speech_seconds"),
            pause_preprocess_denoise=params.get("pause_preprocess_denoise"),
            denoise_algorithm=params.get("denoise_algorithm"),
            dpdfnet_attn_limit_db=params.get("dpdfnet_attn_limit_db"),
            target_format=params.get("target_format"),
        ),
    )


def batch_progress_payload(
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


def batch_finish_payload(report: BatchRunReport) -> dict[str, Any]:
    """Return the typed final payload sent to Svelte."""
    return {
        "processed": report.processed,
        "total": report.total,
        "written": report.written,
        "skipped": report.skipped,
        "failures": report.failures,
        "canceled": report.canceled,
        "summary": report.summary,
    }


def batch_error_payload(message: str, *, recoverable: bool = False) -> dict[str, Any]:
    """Return the typed error payload sent to Svelte."""
    return {
        "message": message,
        "recoverable": recoverable,
    }


def invalid_start_message() -> str:
    """Return the stable message for invalid frontend start payloads."""
    return format_message(
        dict(active_context()["messages"]),
        "batch.failed",
        {"error": "Invalid batch request"},
    )


def _operation_option(operation: str, messages: dict[str, str]) -> dict[str, Any]:
    return {
        "operation": operation,
        "label": operation_label(operation, messages),
        "requires_target_field": requires_target_field(operation),
        "parameter_kind": _parameter_kind(operation),
        "parameter_name": _parameter_name(operation),
    }


def _parameter_kind(operation: str) -> str:
    if operation in {OP_SLOWER, OP_FASTER}:
        return "speed"
    if operation in {OP_VOLUME_DOWN, OP_VOLUME_UP}:
        return "volume"
    if operation == OP_REMOVE_PAUSES:
        return "pause"
    if operation == OP_DENOISE:
        return "denoise"
    if operation == OP_CONVERT:
        return "format"
    if operation == OP_GRAPH:
        return "none"
    return "none"


def _parameter_name(operation: str) -> str:
    if operation in {OP_SLOWER, OP_FASTER}:
        return "speed_step"
    if operation in {OP_VOLUME_DOWN, OP_VOLUME_UP}:
        return "volume_step_db"
    if operation == OP_REMOVE_PAUSES:
        return "pause_aggressiveness"
    if operation == OP_DENOISE:
        return "denoise_algorithm"
    if operation == OP_CONVERT:
        return "target_format"
    return "none"
