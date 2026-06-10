"""Support-incident telemetry helpers for bundled noise-reduction renderers."""

from __future__ import annotations

from pathlib import Path

from .support import (
    record_latest_denoise_support_incident,
    record_latest_spleeter_support_incident,
)


def record_rnnoise_failure(
    source_path: Path,
    exc: Exception,
    *,
    ffmpeg_path: Path | None,
    rnnoise_path: Path | None,
    attempted_commands: list[dict[str, object]],
) -> None:
    record_latest_denoise_support_incident(
        operation="rnnoise_denoise",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=str(exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=str(ffmpeg_path) if ffmpeg_path is not None else "",
        rnnoise_path=str(rnnoise_path) if rnnoise_path is not None else "",
        attempted_commands=attempted_commands,
    )


def record_dpdfnet_failure(
    source_path: Path,
    exc: Exception,
    *,
    ffmpeg_path: Path | None,
    dpdfnet_path: Path | None,
    attempted_commands: list[dict[str, object]],
) -> None:
    record_latest_denoise_support_incident(
        operation="dpdfnet_denoise",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=str(exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=str(ffmpeg_path) if ffmpeg_path is not None else "",
        dpdfnet_path=str(dpdfnet_path) if dpdfnet_path is not None else "",
        attempted_commands=attempted_commands,
    )


def record_spleeter_failure(
    source_path: Path,
    exc: Exception,
    *,
    ffmpeg_path: Path | None,
    spleeter_path: Path | None,
    vocals_model_path: Path | None,
    accompaniment_model_path: Path | None,
    attempted_commands: list[dict[str, object]],
) -> None:
    record_latest_spleeter_support_incident(
        operation="voice_only",
        media_filename=source_path.name,
        source_path=str(source_path.resolve()),
        user_message=str(exc),
        exception_type=type(exc).__name__,
        ffmpeg_path=str(ffmpeg_path) if ffmpeg_path is not None else "",
        spleeter_path=str(spleeter_path) if spleeter_path is not None else "",
        vocals_model_path=str(vocals_model_path) if vocals_model_path is not None else "",
        accompaniment_model_path=str(accompaniment_model_path) if accompaniment_model_path is not None else "",
        attempted_commands=attempted_commands,
    )
