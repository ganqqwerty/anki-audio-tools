"""Persist editor split-button defaults from inline quick settings."""

from __future__ import annotations

from typing import Any

from .audio_operation_params import parameters_from_raw
from .error_codes import AQE_SETTINGS_INVALID_PAYLOAD, coded_error
from .i18n import t
from .prosody_settings import sanitize_graph_settings

MAX_REPEAT_PAUSE_SECONDS = 10.0
MAX_CHORUSING_REPEAT_COUNT = 20
MAX_RECORDING_COUNTDOWN_SECONDS = 10
PITCH_HUM_MODES = frozenset({"direct", "pitch_tier"})
SHARE_TARGETS = frozenset({"catbox", "litterbox"})
AUDIO_PARAMETER_CONFIG_KEYS = (
    ("volume_step_db", "volume_step_db"),
    ("speed_step", "speed_step"),
    ("pause_aggressiveness", "pause_aggressiveness"),
    ("denoise_algorithm", "denoise_algorithm"),
    ("dpdfnet_attn_limit_db", "dpdfnet_attn_limit_db"),
    ("size_reduction_mode", "size_reduction_mode"),
    ("size_reduction_bitrate_kbps", "size_reduction_bitrate_kbps"),
    ("size_reduction_sample_rate_hz", "size_reduction_sample_rate_hz"),
    ("size_reduction_channels", "size_reduction_channels"),
)


def save_split_defaults_from_frontend(editor: Any, deps: Any) -> None:
    """Read a pending split-default request from the editor webview and persist it."""
    expression = """
    (() => {
      return window.__aqePopPendingSplitDefaultSaveRequest
        ? window.__aqePopPendingSplitDefaultSaveRequest()
        : null;
    })()
    """

    def _continue(raw_payload: Any) -> None:
        updates = split_default_config_updates(raw_payload)
        if not updates:
            message = t("editor.status.split_defaults_invalid")
            deps.eval_status(
                editor,
                coded_error(AQE_SETTINGS_INVALID_PAYLOAD, message),
                kind="error",
            )
            return
        addon_id = editor.mw.addonManager.addonFromModule(__name__)
        config = dict(editor.mw.addonManager.getConfig(addon_id) or {})
        config.update(updates)
        editor.mw.addonManager.writeConfig(addon_id, config)
        deps.eval_status(editor, t("editor.status.split_defaults_saved"))

    deps.eval_with_callback(editor, expression, _continue)


def split_default_config_updates(raw_payload: Any) -> dict[str, object]:
    """Return sanitized config updates for one editor split-default save payload."""
    if not isinstance(raw_payload, dict):
        return {}
    raw_defaults = raw_payload.get("defaults")
    if not isinstance(raw_defaults, dict):
        return {}
    updates: dict[str, object] = {}
    updates.update(_audio_parameter_updates(raw_defaults))
    updates.update(_repeat_updates(raw_defaults))
    updates.update(_chorusing_updates(raw_defaults))
    updates.update(_recording_updates(raw_defaults))
    updates.update(_pitch_hum_updates(raw_defaults))
    updates.update(_share_updates(raw_defaults))
    updates.update(_graph_updates(raw_defaults))
    return updates


def _audio_parameter_updates(raw_defaults: dict[str, object]) -> dict[str, object]:
    updates: dict[str, object] = {}
    params = parameters_from_raw(
        volume_step_db=raw_defaults.get("volumeStepDb"),
        speed_step=raw_defaults.get("speedStep"),
        pause_aggressiveness=raw_defaults.get("pauseAggressiveness"),
        pause_detection_algorithm=raw_defaults.get("pauseDetectionAlgorithm"),
        pause_threshold=raw_defaults.get("pauseThreshold"),
        pause_min_silence_seconds=raw_defaults.get("pauseMinSilenceSeconds"),
        pause_min_speech_seconds=raw_defaults.get("pauseMinSpeechSeconds"),
        pause_preprocess_denoise=raw_defaults.get("pausePreprocessDenoise"),
        denoise_algorithm=raw_defaults.get("denoiseAlgorithm"),
        dpdfnet_attn_limit_db=raw_defaults.get("dpdfnetAttnLimitDb"),
        size_reduction_mode=raw_defaults.get("sizeReductionMode"),
        size_reduction_bitrate_kbps=raw_defaults.get("sizeReductionBitrateKbps"),
        size_reduction_sample_rate_hz=raw_defaults.get("sizeReductionSampleRateHz"),
        size_reduction_channels=raw_defaults.get("sizeReductionChannels"),
    )
    _apply_present_parameter_updates(updates, params, AUDIO_PARAMETER_CONFIG_KEYS)
    _apply_pause_detection_updates(updates, params)
    return updates


def _apply_present_parameter_updates(
    updates: dict[str, object],
    params: Any,
    fields: tuple[tuple[str, str], ...],
) -> None:
    for attr_name, config_key in fields:
        value = getattr(params, attr_name)
        if value is not None:
            updates[config_key] = value


def _apply_pause_detection_updates(updates: dict[str, object], params: Any) -> None:
    if params.pause_detection_algorithm is not None:
        updates["pause_detection_algorithm"] = params.pause_detection_algorithm
    if params.pause_detection_algorithm == "silero_vad":
        _apply_silero_pause_updates(updates, params)
    elif params.pause_detection_algorithm == "silencedetect":
        _apply_silencedetect_pause_updates(updates, params)


def _apply_silencedetect_pause_updates(
    updates: dict[str, object],
    params: Any,
) -> None:
    if params.pause_threshold is not None:
        updates["pause_silencedetect_threshold_db"] = params.pause_threshold
    if params.pause_min_silence_seconds is not None:
        updates["pause_silencedetect_min_silence_seconds"] = params.pause_min_silence_seconds
    if params.pause_min_speech_seconds is not None:
        updates["pause_silencedetect_min_speech_seconds"] = params.pause_min_speech_seconds
    if params.pause_preprocess_denoise is not None:
        updates["pause_silencedetect_preprocess_denoise"] = params.pause_preprocess_denoise


def _apply_silero_pause_updates(
    updates: dict[str, object],
    params: Any,
) -> None:
    if params.pause_threshold is not None:
        updates["pause_silero_threshold"] = params.pause_threshold
    if params.pause_min_silence_seconds is not None:
        updates["pause_silero_min_silence_seconds"] = params.pause_min_silence_seconds
    if params.pause_min_speech_seconds is not None:
        updates["pause_silero_min_speech_seconds"] = params.pause_min_speech_seconds
    if params.pause_preprocess_denoise is not None:
        updates["pause_silero_preprocess_denoise"] = params.pause_preprocess_denoise


def _repeat_updates(raw_defaults: dict[str, object]) -> dict[str, object]:
    updates: dict[str, object] = {}
    repeat_pause_seconds = _repeat_pause_seconds_or_none(
        raw_defaults.get("repeatPauseSeconds")
    )
    if repeat_pause_seconds is not None:
        updates["repeat_pause_seconds"] = repeat_pause_seconds
    repeat_playback = raw_defaults.get("repeatPlaybackByDefault")
    if isinstance(repeat_playback, bool):
        updates["repeat_playback_by_default"] = repeat_playback
    return updates


def _recording_updates(raw_defaults: dict[str, object]) -> dict[str, object]:
    countdown_seconds = _recording_countdown_seconds_or_none(
        raw_defaults.get("voiceRecordingCountdownSeconds")
    )
    if countdown_seconds is None:
        return {}
    return {"voice_recording_countdown_seconds": countdown_seconds}


def _chorusing_updates(raw_defaults: dict[str, object]) -> dict[str, object]:
    updates: dict[str, object] = {}
    chorusing_pause_seconds = _repeat_pause_seconds_or_none(
        raw_defaults.get("chorusingPauseSeconds")
    )
    if chorusing_pause_seconds is not None:
        updates["chorusing_pause_seconds"] = chorusing_pause_seconds
    chorusing_auto_advance = raw_defaults.get("chorusingAutoAdvanceByDefault")
    if isinstance(chorusing_auto_advance, bool):
        updates["chorusing_auto_advance_by_default"] = chorusing_auto_advance
    chorusing_auto_advance_repeats = _chorusing_repeat_count_or_none(
        raw_defaults.get("chorusingAutoAdvanceRepeats")
    )
    if chorusing_auto_advance_repeats is not None:
        updates["chorusing_auto_advance_repeats"] = chorusing_auto_advance_repeats
    return updates


def _pitch_hum_updates(raw_defaults: dict[str, object]) -> dict[str, object]:
    pitch_hum_mode = _enum_or_none(raw_defaults.get("pitchHumMode"), PITCH_HUM_MODES)
    return {"pitch_hum_mode": pitch_hum_mode} if pitch_hum_mode is not None else {}


def _share_updates(raw_defaults: dict[str, object]) -> dict[str, object]:
    share_target = _enum_or_none(raw_defaults.get("shareTarget"), SHARE_TARGETS)
    return {"share_target": share_target} if share_target is not None else {}


def _graph_updates(raw_defaults: dict[str, object]) -> dict[str, object]:
    return sanitize_graph_settings(
        {
            "voiceRange": raw_defaults.get("graphVoiceRange"),
            "recordingCondition": raw_defaults.get("graphRecordingCondition"),
            "smoothness": raw_defaults.get("graphSmoothness"),
            "connectShortDropoutsMs": raw_defaults.get("graphConnectShortDropoutsMs"),
            "voiceLock": raw_defaults.get("graphVoiceLock"),
        }
    )


def _enum_or_none(value: object, allowed: frozenset[str]) -> str | None:
    text = str(value)
    return text if text in allowed else None


def _repeat_pause_seconds_or_none(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return max(0.0, min(MAX_REPEAT_PAUSE_SECONDS, round(float(value), 1)))


def _recording_countdown_seconds_or_none(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return max(0, min(MAX_RECORDING_COUNTDOWN_SECONDS, int(value)))


def _chorusing_repeat_count_or_none(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return int(max(1, min(MAX_CHORUSING_REPEAT_COUNT, round(float(value)))))
