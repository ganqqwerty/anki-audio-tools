"""Failure diagnostics and support incident recording for special transforms."""

from __future__ import annotations

import logging
from pathlib import Path

from .audio_state import AudioProcessingConfig
from .permission_guidance import message_with_permission_guidance
from .support import (
    format_denoise_support_log_block,
    format_spleeter_support_log_block,
    latest_denoise_support_incident,
    latest_spleeter_support_incident,
    record_latest_denoise_support_incident,
    record_latest_spleeter_support_incident,
)

logger = logging.getLogger(__name__)


def record_rnnoise_failure_context(source_path: Path, config: AudioProcessingConfig, exc: Exception) -> None:
    record_latest_denoise_support_incident(
        operation="rnnoise_denoise",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=message_with_permission_guidance(str(exc), exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=config.ffmpeg_path,
    )


def record_dpdfnet_failure_context(source_path: Path, config: AudioProcessingConfig, exc: Exception) -> None:
    record_latest_denoise_support_incident(
        operation="dpdfnet_denoise",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=message_with_permission_guidance(str(exc), exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=config.ffmpeg_path,
    )


def record_spleeter_failure_context(source_path: Path, config: AudioProcessingConfig, exc: Exception) -> None:
    record_latest_spleeter_support_incident(
        operation="voice_only",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=message_with_permission_guidance(str(exc), exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=config.ffmpeg_path,
    )


def log_special_transform_failure(failure_log_label: str, message: str) -> None:
    if failure_log_label in {"rnnoise denoise failed", "dpdfnet denoise failed"}:
        incident = latest_denoise_support_incident()
        if incident:
            logger.exception("%s: %s\n%s", failure_log_label, message, format_denoise_support_log_block(incident))
            return
        logger.exception("%s: %s", failure_log_label, message)
        return
    if failure_log_label == "voice only failed":
        incident = latest_spleeter_support_incident()
        if incident:
            logger.exception("%s: %s\n%s", failure_log_label, message, format_spleeter_support_log_block(incident))
            return
        logger.exception("%s: %s", failure_log_label, message)
        return
    logger.exception("%s: %s", failure_log_label, message)
