"""Shared inline editor webview injection script builder."""

from __future__ import annotations

from typing import Any

from .editor_media import audio_field_sources as _audio_field_sources
from .editor_runtime import (
    SESSIONS as _SESSIONS,
)
from .editor_runtime import (
    config as _config,
)
from .editor_session import EditorSession
from .editor_ui import injection_script


def editor_injection_script(editor: Any, note: Any) -> str:
    """Return the shared inline controls script for one note-bearing editor surface."""
    config = _config(editor)
    audio_field_sources = _audio_field_sources(note)
    visible_editor_buttons = config.get("visible_editor_buttons", [])
    if not isinstance(visible_editor_buttons, list):
        visible_editor_buttons = []
    editor_button_modes = config.get("editor_button_modes", {})
    if not isinstance(editor_button_modes, dict):
        editor_button_modes = {}
    return injection_script(
        list(audio_field_sources),
        audio_field_metadata={},
        audio_field_sources=audio_field_sources,
        initial_status_by_field=_initial_status_by_field(_SESSIONS.get(editor)),
        pending_post_edit_playback=_pending_post_edit_playback(editor),
        repeat_playback_by_default=bool(config.get("repeat_playback_by_default", True)),
        show_graph_by_default=bool(config.get("show_graph_by_default", True)),
        visible_editor_buttons=[str(command) for command in visible_editor_buttons],
        editor_button_modes={
            str(command): str(mode)
            for command, mode in editor_button_modes.items()
            if isinstance(command, str) and isinstance(mode, str)
        },
        split_button_defaults={
            "volumeStepDb": float(config.get("volume_step_db", 15.0)),
            "speedStep": float(config.get("speed_step", 1.5)),
            "repeatPauseSeconds": float(config.get("repeat_pause_seconds", 0.0)),
            "voiceRecordingCountdownSeconds": int(
                config.get("voice_recording_countdown_seconds", 3)
            ),
            "shareTarget": str(config.get("share_target", "litterbox")),
            "pauseAggressiveness": str(config.get("pause_aggressiveness", "normal")),
            "pauseDetectionAlgorithm": str(
                config.get("pause_detection_algorithm", "silencedetect")
            ),
            "pauseSilencedetectThresholdDb": float(
                config.get("pause_silencedetect_threshold_db", -45.0)
            ),
            "pauseSilencedetectMinSilenceSeconds": float(
                config.get("pause_silencedetect_min_silence_seconds", 0.30)
            ),
            "pauseSilencedetectMinSpeechSeconds": float(
                config.get("pause_silencedetect_min_speech_seconds", 0.10)
            ),
            "pauseSilencedetectPreprocessDenoise": bool(
                config.get("pause_silencedetect_preprocess_denoise", True)
            ),
            "pauseSileroThreshold": float(config.get("pause_silero_threshold", 0.50)),
            "pauseSileroMinSilenceSeconds": float(
                config.get("pause_silero_min_silence_seconds", 0.45)
            ),
            "pauseSileroMinSpeechSeconds": float(
                config.get("pause_silero_min_speech_seconds", 0.10)
            ),
            "pauseSileroPreprocessDenoise": bool(
                config.get("pause_silero_preprocess_denoise", False)
            ),
            "denoiseAlgorithm": str(config.get("denoise_algorithm", "standard")),
            "pitchHumMode": str(config.get("pitch_hum_mode", "direct")),
            "outputFormat": str(config.get("output_format", "source")),
            "sizeReductionMode": str(config.get("size_reduction_mode", "normal")),
            "sizeReductionBitrateKbps": int(config.get("size_reduction_bitrate_kbps", 64)),
            "sizeReductionSampleRateHz": int(
                config.get("size_reduction_sample_rate_hz", 32000)
            ),
            "sizeReductionChannels": int(config.get("size_reduction_channels", 1)),
            "dpdfnetAttnLimitDb": float(config.get("dpdfnet_attn_limit_db", 12.0)),
            "graphVoiceRange": str(config.get("graph_voice_range", "general")),
            "graphRecordingCondition": str(config.get("graph_recording_condition", "auto")),
            "graphSmoothness": str(config.get("graph_smoothness", "very_smooth")),
            "graphConnectShortDropoutsMs": int(
                config.get("graph_connect_short_dropouts_ms", 240)
            ),
            "graphVoiceLock": str(config.get("graph_voice_lock", "balanced")),
        },
    )


def _initial_status_by_field(session: EditorSession | None) -> dict[int, dict[str, str]]:
    if session is None or session.pending_status is None:
        return {}
    pending = session.pending_status
    return {
        int(pending.field_index): {
            "kind": pending.kind,
            "message": pending.message,
        }
    }


def _pending_post_edit_playback(editor: Any) -> dict[str, Any] | None:
    from .editor_callbacks import _pending_post_edit_playback_payload

    return _pending_post_edit_playback_payload(_SESSIONS.get(editor))
