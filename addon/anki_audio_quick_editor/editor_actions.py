"""Import-safe editor bridge commands and shared operation mapping."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from .audio_operation_params import (
    AudioOperationParameters,
    effective_config_for_operation,
    parameters_from_raw,
)
from .audio_operations import (
    OP_CONVERT,
    OP_FASTER,
    OP_REMOVE_PAUSES,
    OP_SLOWER,
    OP_VOLUME_DOWN,
    OP_VOLUME_UP,
    apply_audio_operation,
)
from .audio_state import AudioEditState, AudioProcessingConfig

CMD_SLOWER = "aqe:slower"
CMD_FASTER = "aqe:faster"
CMD_VOLUME_DOWN = "aqe:volume-down"
CMD_VOLUME_UP = "aqe:volume-up"
CMD_REMOVE_PAUSES = "aqe:remove-pauses"
CMD_CONVERT = "aqe:convert"
CMD_DENOISE_STANDARD = "aqe:denoise-standard"
CMD_RNNOISE = "aqe:rnnoise"
CMD_DPDFNET = "aqe:dpdfnet"
CMD_VOICE_ONLY = "aqe:voice-only"
CMD_PITCH_HUM = "aqe:pitch-hum"
CMD_DELETE_SELECTION = "aqe:delete-selection"
CMD_DELETE_REST = "aqe:delete-rest"
CMD_ANALYZE_FIELD = "aqe:analyze-field"
CMD_COMMAND_PAYLOAD = "aqe:command-payload"
CMD_SAVE_SPLIT_DEFAULTS = "aqe:save-split-defaults"
CMD_STOP_PLAYBACK = "aqe:stop-playback"
CMD_SETTINGS = "aqe:settings"
CMD_REDO = "aqe:redo"
CMD_SHARE = "aqe:share"
CMD_OPEN_URL = "aqe:open-url"
CMD_RECORD_VOICE = "aqe:record-voice"
CMD_STOP_RECORDING = "aqe:stop-recording"
CMD_PLAY_RECORDING = "aqe:play-recording"
CMD_POST_EDIT_PLAYBACK_READY = "aqe:post-edit-playback-ready"

TRUSTED_EXTERNAL_URL_HOST = "ganqqwerty.github.io"
TRUSTED_EXTERNAL_URL_PATH = "/anki-audio-tools"
TRUSTED_EXTERNAL_URL_PATH_PREFIX = f"{TRUSTED_EXTERNAL_URL_PATH}/"

BRIDGE_COMMANDS = (
    "aqe:scan",
    "aqe:analyze",
    CMD_ANALYZE_FIELD,
    CMD_COMMAND_PAYLOAD,
    CMD_SAVE_SPLIT_DEFAULTS,
    CMD_STOP_PLAYBACK,
    "aqe:set-cursor",
    "aqe:play",
    "aqe:play-ended",
    "aqe:frontend-log",
    CMD_POST_EDIT_PLAYBACK_READY,
    "aqe:show-file",
    CMD_SHARE,
    CMD_OPEN_URL,
    CMD_RECORD_VOICE,
    CMD_STOP_RECORDING,
    CMD_PLAY_RECORDING,
    CMD_SLOWER,
    CMD_FASTER,
    CMD_VOLUME_DOWN,
    CMD_VOLUME_UP,
    CMD_REMOVE_PAUSES,
    CMD_CONVERT,
    CMD_DENOISE_STANDARD,
    CMD_RNNOISE,
    CMD_DPDFNET,
    CMD_VOICE_ONLY,
    CMD_PITCH_HUM,
    CMD_DELETE_SELECTION,
    CMD_DELETE_REST,
    "aqe:undo",
    CMD_REDO,
    CMD_SETTINGS,
)

PROCESSING_COMMANDS = (
    CMD_SLOWER,
    CMD_FASTER,
    CMD_VOLUME_DOWN,
    CMD_VOLUME_UP,
    CMD_REMOVE_PAUSES,
)

BRIDGE_COMMAND_TO_OPERATION = {
    CMD_SLOWER: OP_SLOWER,
    CMD_FASTER: OP_FASTER,
    CMD_VOLUME_DOWN: OP_VOLUME_DOWN,
    CMD_VOLUME_UP: OP_VOLUME_UP,
    CMD_REMOVE_PAUSES: OP_REMOVE_PAUSES,
    CMD_CONVERT: OP_CONVERT,
}


@dataclass(frozen=True)
class EditorCommandOverrides:
    """Validated local editor command override values."""

    volume_step_db: float | None = None
    speed_step: float | None = None
    pause_aggressiveness: str | None = None
    pause_detection_algorithm: str | None = None
    pause_threshold: float | None = None
    pause_min_silence_seconds: float | None = None
    pause_min_speech_seconds: float | None = None
    pause_preprocess_denoise: bool | None = None
    denoise_algorithm: str | None = None
    dpdfnet_attn_limit_db: float | None = None
    target_format: str | None = None
    pitch_hum_mode: str | None = None


@dataclass(frozen=True)
class EditorCommandPayload:
    """Normalized editor bridge command data."""

    command: str
    field_ord: int | None = None
    overrides: EditorCommandOverrides = EditorCommandOverrides()
    graph_settings: dict[str, object] | None = None
    generation: int | None = None
    share_target: str | None = None
    source_filename: str | None = None
    url: str | None = None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _overrides_from_raw(raw: Any) -> EditorCommandOverrides:
    if not isinstance(raw, dict):
        return EditorCommandOverrides()
    params = parameters_from_raw(
        volume_step_db=raw.get("volumeStepDb"),
        speed_step=raw.get("speedStep"),
        pause_aggressiveness=raw.get("pauseAggressiveness"),
        pause_detection_algorithm=raw.get("pauseDetectionAlgorithm"),
        pause_threshold=raw.get("pauseThreshold"),
        pause_min_silence_seconds=raw.get("pauseMinSilenceSeconds"),
        pause_min_speech_seconds=raw.get("pauseMinSpeechSeconds"),
        pause_preprocess_denoise=raw.get("pausePreprocessDenoise"),
        denoise_algorithm=raw.get("denoiseAlgorithm"),
        dpdfnet_attn_limit_db=raw.get("dpdfnetAttnLimitDb"),
        target_format=raw.get("targetFormat"),
    )
    return EditorCommandOverrides(
        volume_step_db=params.volume_step_db,
        speed_step=params.speed_step,
        pause_aggressiveness=params.pause_aggressiveness,
        pause_detection_algorithm=params.pause_detection_algorithm,
        pause_threshold=params.pause_threshold,
        pause_min_silence_seconds=params.pause_min_silence_seconds,
        pause_min_speech_seconds=params.pause_min_speech_seconds,
        pause_preprocess_denoise=params.pause_preprocess_denoise,
        denoise_algorithm=params.denoise_algorithm,
        dpdfnet_attn_limit_db=params.dpdfnet_attn_limit_db,
        target_format=params.target_format,
        pitch_hum_mode=_pitch_hum_mode_or_none(raw.get("pitchHumMode")),
    )


def _graph_settings_from_raw(raw: Any) -> dict[str, object] | None:
    if not isinstance(raw, dict):
        return None
    return dict(raw)


def _str_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _pitch_hum_mode_or_none(value: Any) -> str | None:
    text = str(value)
    return text if text in {"direct", "pitch_tier"} else None


def _share_target_or_none(value: Any) -> str | None:
    text = str(value)
    return text if text in {"catbox", "litterbox"} else None


def _external_url_or_none(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    if parsed.scheme != "https":
        return None
    if parsed.hostname != TRUSTED_EXTERNAL_URL_HOST:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    if parsed.path != TRUSTED_EXTERNAL_URL_PATH and not parsed.path.startswith(TRUSTED_EXTERNAL_URL_PATH_PREFIX):
        return None
    return value


def decode_editor_command_payload(raw_command: str | EditorCommandPayload) -> EditorCommandPayload:
    """Return normalized editor command data from a bridge string or JSON payload."""
    if isinstance(raw_command, EditorCommandPayload):
        return raw_command
    if not raw_command.lstrip().startswith("{"):
        return EditorCommandPayload(command=raw_command)
    try:
        raw_payload = json.loads(raw_command)
    except json.JSONDecodeError:
        return EditorCommandPayload(command=raw_command)
    if not isinstance(raw_payload, dict):
        return EditorCommandPayload(command=raw_command)
    command = raw_payload.get("command")
    if not isinstance(command, str):
        return EditorCommandPayload(command=raw_command)
    return EditorCommandPayload(
        command=command,
        field_ord=_int_or_none(raw_payload.get("fieldOrd")),
        overrides=_overrides_from_raw(raw_payload.get("overrides")),
        graph_settings=_graph_settings_from_raw(raw_payload.get("graphSettings")),
        generation=_int_or_none(raw_payload.get("generation")),
        share_target=_share_target_or_none(raw_payload.get("shareTarget")),
        source_filename=_str_or_none(raw_payload.get("sourceFilename")),
        url=_external_url_or_none(raw_payload.get("url")),
    )


def operation_for_command(command: str) -> str | None:
    """Return the shared audio operation for one editor bridge command."""
    return BRIDGE_COMMAND_TO_OPERATION.get(command)


def processing_config_for_command(
    command: str | EditorCommandPayload,
    config: AudioProcessingConfig,
) -> AudioProcessingConfig:
    """Return the effective render config for a local editor command."""
    payload = decode_editor_command_payload(command)
    operation = operation_for_command(payload.command)
    if operation is None:
        return config
    return effective_config_for_operation(
        operation,
        config,
        AudioOperationParameters(
            volume_step_db=payload.overrides.volume_step_db,
            speed_step=payload.overrides.speed_step,
            pause_aggressiveness=payload.overrides.pause_aggressiveness,
            pause_detection_algorithm=payload.overrides.pause_detection_algorithm,
            pause_threshold=payload.overrides.pause_threshold,
            pause_min_silence_seconds=payload.overrides.pause_min_silence_seconds,
            pause_min_speech_seconds=payload.overrides.pause_min_speech_seconds,
            pause_preprocess_denoise=payload.overrides.pause_preprocess_denoise,
            target_format=payload.overrides.target_format,
        ),
    )


def apply_processing_command(
    command: str | EditorCommandPayload,
    state: AudioEditState,
    config: AudioProcessingConfig,
) -> AudioEditState | None:
    """Return the edit state after applying a processing command."""
    payload = decode_editor_command_payload(command)
    effective_config = processing_config_for_command(payload, config)
    operation = operation_for_command(payload.command)
    if operation is None:
        return None
    if operation == OP_CONVERT:
        return None
    return apply_audio_operation(operation, state, effective_config)
