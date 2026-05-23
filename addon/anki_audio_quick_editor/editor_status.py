"""User-facing editor status summaries for completed operations."""

from __future__ import annotations

from .audio_formats import format_label
from .audio_state import AudioProcessingConfig
from .dpdfnet_settings import normalize_dpdfnet_attn_limit_db
from .editor_actions import (
    CMD_CONVERT,
    CMD_DENOISE_STANDARD,
    CMD_DPDFNET,
    CMD_FASTER,
    CMD_PITCH_HUM,
    CMD_REMOVE_PAUSES,
    CMD_RNNOISE,
    CMD_SLOWER,
    CMD_VOICE_ONLY,
    CMD_VOLUME_DOWN,
    CMD_VOLUME_UP,
    EditorCommandPayload,
    decode_editor_command_payload,
    processing_config_for_command,
)
from .editor_session import RegionDeleteRequest, UndoEntry
from .i18n import t


def original_audio_status_summary() -> str:
    """Return the status summary for an unmodified source file."""
    return t("editor.status.original_audio")


def command_status_summary(
    command: str | EditorCommandPayload,
    config: AudioProcessingConfig,
) -> str:
    """Return the final status summary for one completed editor command."""
    payload = decode_editor_command_payload(command)
    if _is_denoise_command(payload.command):
        return _denoise_status_summary(payload, config)
    return _simple_command_status_summary(payload, config)


def region_operation_status_summary(request: RegionDeleteRequest) -> str:
    """Return the final status summary for one completed region delete action."""
    if request.operation == "delete-rest":
        return t(
            "editor.status.operation.delete_rest",
            {"range": _selection_range(request.selection_start_ms, request.selection_end_ms)},
        )
    return t(
        "editor.status.operation.delete_selection",
        {"range": _selection_range(request.selection_start_ms, request.selection_end_ms)},
    )


def restored_status_summary(entry: UndoEntry) -> str:
    """Return a stored history summary or a safe fallback."""
    if entry.status_summary:
        return entry.status_summary
    if entry.filename == entry.state.source_file:
        return original_audio_status_summary()
    return entry.filename


def undo_status_message(entry: UndoEntry) -> str:
    """Return the final user-facing undo status."""
    return t("editor.status.operation.undo", {"summary": restored_status_summary(entry)})


def redo_status_message(entry: UndoEntry) -> str:
    """Return the final user-facing redo status."""
    return t("editor.status.operation.redo", {"summary": restored_status_summary(entry)})


def _denoise_status_summary(
    payload: EditorCommandPayload,
    config: AudioProcessingConfig,
) -> str:
    algorithm = _denoise_algorithm(payload, config)
    if algorithm == "dpdfnet":
        level = _pause_aggressiveness_label(
            _dpdfnet_aggressiveness(
                payload.overrides.dpdfnet_attn_limit_db
                if payload.overrides.dpdfnet_attn_limit_db is not None
                else config.dpdfnet_attn_limit_db
            )
        )
        return t(
            "editor.status.operation.denoise_dpdfnet",
            {"algorithm": _denoise_algorithm_label(algorithm), "level": level},
        )
    return t(
        "editor.status.operation.denoise",
        {"algorithm": _denoise_algorithm_label(algorithm)},
    )


def _simple_command_status_summary(
    payload: EditorCommandPayload,
    config: AudioProcessingConfig,
) -> str:
    effective_config = processing_config_for_command(payload, config)
    if payload.command in {CMD_VOLUME_UP, CMD_VOLUME_DOWN}:
        return _volume_status_summary(payload.command, effective_config)
    if payload.command in {CMD_FASTER, CMD_SLOWER}:
        return _speed_status_summary(payload.command, effective_config)
    if payload.command == CMD_REMOVE_PAUSES:
        return t(
            "editor.status.operation.remove_pauses",
            {"level": _pause_aggressiveness_label(effective_config.pause_aggressiveness)},
        )
    if payload.command == CMD_CONVERT:
        return t(
            "editor.status.operation.convert",
            {"format": format_label(payload.overrides.target_format or config.output_format)},
        )
    if payload.command == CMD_PITCH_HUM:
        return t(
            "editor.status.operation.pitch_hum",
            {"mode": _pitch_hum_mode_label(payload.overrides.pitch_hum_mode or config.pitch_hum_mode)},
        )
    return ""


def _volume_status_summary(command: str, config: AudioProcessingConfig) -> str:
    key = "editor.status.operation.volume_up" if command == CMD_VOLUME_UP else "editor.status.operation.volume_down"
    return t(key, {"value": _format_db(config.volume_step_db)})


def _speed_status_summary(command: str, config: AudioProcessingConfig) -> str:
    key = "editor.status.operation.faster" if command == CMD_FASTER else "editor.status.operation.slower"
    return t(key, {"value": _format_speed_multiplier(command, config.speed_step)})


def _is_denoise_command(command: str) -> bool:
    return command in {
        CMD_DENOISE_STANDARD,
        CMD_RNNOISE,
        CMD_DPDFNET,
        CMD_VOICE_ONLY,
    }


def _denoise_algorithm(payload: EditorCommandPayload, config: AudioProcessingConfig) -> str:
    if payload.command == CMD_RNNOISE:
        return "rnnoise"
    if payload.command == CMD_DPDFNET:
        return "dpdfnet"
    if payload.command == CMD_VOICE_ONLY:
        return "voice_only"
    return payload.overrides.denoise_algorithm or config.denoise_algorithm


def _denoise_algorithm_label(algorithm: str) -> str:
    if algorithm == "rnnoise":
        return t("settings.denoise_algorithm.rnnoise")
    if algorithm == "dpdfnet":
        return t("settings.denoise_algorithm.dpdfnet")
    if algorithm == "voice_only":
        return t("settings.denoise_algorithm.voice_only")
    return t("settings.denoise_algorithm.standard")


def _dpdfnet_aggressiveness(value: float) -> str:
    level = normalize_dpdfnet_attn_limit_db(value)
    if level == 6:
        return "gentle"
    if level == 18:
        return "aggressive"
    return "normal"


def _pause_aggressiveness_label(value: str) -> str:
    if value == "gentle":
        return t("settings.pause_aggressiveness.gentle")
    if value == "aggressive":
        return t("settings.pause_aggressiveness.aggressive")
    return t("settings.pause_aggressiveness.normal")


def _pitch_hum_mode_label(value: str) -> str:
    if value == "pitch_tier":
        return t("editor.pitch_hum.mode.pitch_tier")
    return t("editor.pitch_hum.mode.direct")


def _format_db(value: float) -> str:
    rounded = round(float(value), 1)
    return f"{rounded:.0f} dB" if rounded.is_integer() else f"{rounded:.1f} dB"


def _format_speed_multiplier(command: str, speed_step: float) -> str:
    multiplier = 1 - speed_step if command == CMD_SLOWER else 1 + speed_step
    return f"x{multiplier:.2f}"


def _selection_range(start_ms: int, end_ms: int) -> str:
    return f"{start_ms}-{end_ms} ms"
