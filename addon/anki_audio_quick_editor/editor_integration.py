"""Thin Anki editor integration for inline audio editing."""

from __future__ import annotations

import logging
from typing import Any, Callable

from . import (
    editor_callbacks,
    editor_runtime,
)
from .editor_actions import (
    BRIDGE_COMMANDS,
)
from .editor_media import (
    audio_field_indices as _audio_field_indices,
)
from .editor_media import (
    audio_field_sources as _audio_field_sources,
)
from .editor_media import (
    current_field_index as _current_field_index,
)
from .editor_media import (
    resolve_requested_field_media as _resolve_requested_field_media,
)
from .editor_media import (
    session_needs_media_reset as _session_needs_media_reset,
)
from .editor_media import (
    session_original_source_path as _session_original_source_path,
)
from .editor_media import (
    sound_reference_for_field as _sound_reference_for_field,
)
from .editor_media import (
    visualized_duration_for_field as _visualized_duration_for_field,
)
from .editor_runtime import (
    CURRENT_FIELD_AUDIO_MISSING,
    REFERENCED_AUDIO_MISSING,
    STILL_PROCESSING_MESSAGE,
)
from .editor_runtime import (
    SESSIONS as _SESSIONS,
)
from .editor_runtime import (
    artifact_root as _artifact_root,
)
from .editor_runtime import (
    config as _config,
)
from .editor_runtime import (
    current_media_path as _current_media_path,
)
from .editor_runtime import (
    current_sound_reference as _current_sound_reference,
)
from .editor_runtime import (
    is_busy as _is_busy,
)
from .editor_runtime import (
    reset_session_for_media as _reset_session_for_media,
)
from .editor_runtime import (
    session_and_source as _session_and_source,
)
from .editor_session import (
    EditorSession,
    RegionDeleteRequest,
    UndoEntry,
    UndoHistory,
    reset_for_note_load,
)
from .editor_ui import injection_script

logger = logging.getLogger(__name__)

SettingsOpener = Callable[[Callable[[], None] | None], None]
_SETTINGS_OPENER: SettingsOpener | None = None
__all__ = [
    "BRIDGE_COMMANDS",
    "CURRENT_FIELD_AUDIO_MISSING",
    "EditorSession",
    "REFERENCED_AUDIO_MISSING",
    "RegionDeleteRequest",
    "STILL_PROCESSING_MESSAGE",
    "UndoEntry",
    "UndoHistory",
    "_audio_field_indices",
    "_audio_field_sources",
    "_artifact_root",
    "_config",
    "_current_field_index",
    "_current_media_path",
    "_current_sound_reference",
    "_is_busy",
    "_reset_session_for_media",
    "_resolve_requested_field_media",
    "_session_and_source",
    "_session_needs_media_reset",
    "_session_original_source_path",
    "_sound_reference_for_field",
    "_visualized_duration_for_field",
    "register_editor_hooks",
]


_handle_bridge_command = editor_callbacks._handle_bridge_command
_handle_pending_command_payload = editor_callbacks._handle_pending_command_payload
_handle_non_processing_command = editor_callbacks._handle_non_processing_command
_handle_editor_frontend_log = editor_callbacks._handle_editor_frontend_log
_log_editor_frontend_payload = editor_callbacks._log_editor_frontend_payload
_save_split_defaults_from_frontend = editor_callbacks._save_split_defaults_from_frontend
_update_state_and_render = editor_callbacks._update_state_and_render
_render_and_replace_async = editor_callbacks._render_and_replace_async
_replace_current_field_after_render = editor_callbacks._replace_current_field_after_render
_render_failed = editor_callbacks._render_failed
_denoise_standard_async = editor_callbacks._denoise_standard_async
_convert_async = editor_callbacks._convert_async
_rnnoise_async = editor_callbacks._rnnoise_async
_dpdfnet_async = editor_callbacks._dpdfnet_async
_voice_only_async = editor_callbacks._voice_only_async
_pitch_hum_async = editor_callbacks._pitch_hum_async
_run_special_audio_transform_async = editor_callbacks._run_special_audio_transform_async
_delete_selection_from_frontend = editor_callbacks._delete_selection_from_frontend
_delete_selection_with_request = editor_callbacks._delete_selection_with_request
_parse_region_delete_request = editor_callbacks._parse_region_delete_request
_required_region_delete_values = editor_callbacks._required_region_delete_values
_region_delete_source_filename = editor_callbacks._region_delete_source_filename
_region_delete_trigger = editor_callbacks._region_delete_trigger
_delete_selection_async = editor_callbacks._delete_selection_async
_replace_current_field_after_region_delete = editor_callbacks._replace_current_field_after_region_delete
_region_delete_log_context = editor_callbacks._region_delete_log_context
_replace_current_field_after_noise_removal = editor_callbacks._replace_current_field_after_noise_removal
_stop_audio_playback = editor_callbacks._stop_audio_playback
_stop_session_playback = editor_callbacks._stop_session_playback
_cleanup_temp_playback = editor_callbacks._cleanup_temp_playback
_play = editor_callbacks._play
_play_ended = editor_callbacks._play_ended
_play_with_request = editor_callbacks._play_with_request
_playback_request_values = editor_callbacks._playback_request_values
_toggle_native_pause_resume = editor_callbacks._toggle_native_pause_resume
_apply_html_playback_request = editor_callbacks._apply_html_playback_request
_start_playback_from_cursor = editor_callbacks._start_playback_from_cursor
_playback_segment_ready = editor_callbacks._playback_segment_ready
_playback_segment_failed = editor_callbacks._playback_segment_failed
_undo = editor_callbacks._undo
_redo = editor_callbacks._redo
_restore_history_entry = editor_callbacks._restore_history_entry
_open_settings_from_editor = editor_callbacks._open_settings_from_editor
_refresh_editor_after_settings_save = editor_callbacks._refresh_editor_after_settings_save
_show_current_audio_file = editor_callbacks._show_current_audio_file
_record_rnnoise_failure_context = editor_callbacks._record_rnnoise_failure_context
_record_dpdfnet_failure_context = editor_callbacks._record_dpdfnet_failure_context
_record_spleeter_failure_context = editor_callbacks._record_spleeter_failure_context
_log_special_transform_failure = editor_callbacks._log_special_transform_failure
_analyze_current_async = editor_callbacks._analyze_current_async
_analyze_field_from_frontend = editor_callbacks._analyze_field_from_frontend
_analyze_requested_field_async = editor_callbacks._analyze_requested_field_async
_parse_graph_analysis_request = editor_callbacks._parse_graph_analysis_request
_start_field_analysis_async = editor_callbacks._start_field_analysis_async
_begin_field_analysis = editor_callbacks._begin_field_analysis
_finish_ignored_field_analysis = editor_callbacks._finish_ignored_field_analysis
_fail_field_analysis_without_generation = editor_callbacks._fail_field_analysis_without_generation
_analysis_finished = editor_callbacks._analysis_finished
_analysis_failed = editor_callbacks._analysis_failed
_is_current_field_analysis = editor_callbacks._is_current_field_analysis
_end_field_analysis = editor_callbacks._end_field_analysis
_set_cursor_from_web = editor_callbacks._set_cursor_from_web
_dispose_editor_frontend_controls = editor_callbacks._dispose_editor_frontend_controls
_eval_status = editor_callbacks._eval_status
_eval_visualizer_status = editor_callbacks._eval_visualizer_status
_eval_visualizer_status_for_field = editor_callbacks._eval_visualizer_status_for_field
_eval_playback_state = editor_callbacks._eval_playback_state
_request_graph_redraw = editor_callbacks._request_graph_redraw
_schedule_graph_redraw_attempt = editor_callbacks._schedule_graph_redraw_attempt
_graph_redraw_expression = editor_callbacks._graph_redraw_expression
_retry_graph_redraw = editor_callbacks._retry_graph_redraw
_set_busy = editor_callbacks._set_busy
_set_busy_for_field = editor_callbacks._set_busy_for_field
_main = editor_callbacks._main
_eval_with_callback = editor_callbacks._eval_with_callback


def register_editor_hooks(
    gui_hooks: Any,
    *,
    settings_opener: SettingsOpener | None = None,
) -> None:
    """Register all editor hooks used by the add-on."""
    global _SETTINGS_OPENER
    _SETTINGS_OPENER = settings_opener
    editor_runtime.SETTINGS_OPENER = settings_opener
    gui_hooks.editor_did_init.append(_on_editor_did_init)
    gui_hooks.editor_will_load_note.append(_on_editor_will_load_note)


def _on_editor_did_init(editor: Any) -> None:
    for command in BRIDGE_COMMANDS:
        editor._links[command] = lambda current_editor, cmd=command: _handle_bridge_command(
            current_editor, cmd
        )


def _on_editor_will_load_note(js: str, note: Any, editor: Any) -> str:
    _reset_editor_session_for_note_load(editor, getattr(note, "id", None))
    _SESSIONS.setdefault(editor, EditorSession()).note_id = getattr(note, "id", None)
    config = _config(editor)
    audio_field_sources = _audio_field_sources(note)
    visible_editor_buttons = config.get("visible_editor_buttons", [])
    if not isinstance(visible_editor_buttons, list):
        visible_editor_buttons = []
    script = injection_script(
        list(audio_field_sources),
        audio_field_sources=audio_field_sources,
        repeat_playback_by_default=bool(config.get("repeat_playback_by_default", False)),
        show_graph_by_default=bool(config.get("show_graph_by_default", False)),
        visible_editor_buttons=[str(command) for command in visible_editor_buttons],
        split_button_defaults={
            "volumeStepDb": float(config.get("volume_step_db", 3.0)),
            "speedStep": float(config.get("speed_step", 0.05)),
            "repeatPauseSeconds": float(config.get("repeat_pause_seconds", 0.0)),
            "pauseAggressiveness": str(config.get("pause_aggressiveness", "normal")),
            "denoiseAlgorithm": str(config.get("denoise_algorithm", "standard")),
            "pitchHumMode": str(config.get("pitch_hum_mode", "direct")),
            "outputFormat": str(config.get("output_format", "mp3")),
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
    return f"{js}\n{script}"


def _reset_editor_session_for_note_load(editor: Any, note_id: int | None = None) -> None:
    session = _SESSIONS.get(editor)
    if session is None:
        return
    if not reset_for_note_load(session, note_id):
        return
    _stop_session_playback(session)
