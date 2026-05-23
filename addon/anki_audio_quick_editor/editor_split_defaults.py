"""Persist editor split-button defaults from inline quick settings."""

from __future__ import annotations

from typing import Any

from .audio_operation_params import parameters_from_raw
from .i18n import t
from .prosody_settings import sanitize_graph_settings

MAX_REPEAT_PAUSE_SECONDS = 10.0
PITCH_HUM_MODES = frozenset({"direct", "pitch_tier"})


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
            deps.eval_status(editor, t("editor.status.split_defaults_invalid"), kind="error")
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
    updates.update(_pitch_hum_updates(raw_defaults))
    updates.update(_graph_updates(raw_defaults))
    return updates


def _audio_parameter_updates(raw_defaults: dict[str, object]) -> dict[str, object]:
    updates: dict[str, object] = {}
    params = parameters_from_raw(
        volume_step_db=raw_defaults.get("volumeStepDb"),
        speed_step=raw_defaults.get("speedStep"),
        pause_aggressiveness=raw_defaults.get("pauseAggressiveness"),
        denoise_algorithm=raw_defaults.get("denoiseAlgorithm"),
        dpdfnet_attn_limit_db=raw_defaults.get("dpdfnetAttnLimitDb"),
    )
    if params.volume_step_db is not None:
        updates["volume_step_db"] = params.volume_step_db
    if params.speed_step is not None:
        updates["speed_step"] = params.speed_step
    if params.pause_aggressiveness is not None:
        updates["pause_aggressiveness"] = params.pause_aggressiveness
    if params.denoise_algorithm is not None:
        updates["denoise_algorithm"] = params.denoise_algorithm
    if params.dpdfnet_attn_limit_db is not None:
        updates["dpdfnet_attn_limit_db"] = params.dpdfnet_attn_limit_db
    return updates


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


def _pitch_hum_updates(raw_defaults: dict[str, object]) -> dict[str, object]:
    pitch_hum_mode = _enum_or_none(raw_defaults.get("pitchHumMode"), PITCH_HUM_MODES)
    return {"pitch_hum_mode": pitch_hum_mode} if pitch_hum_mode is not None else {}


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
