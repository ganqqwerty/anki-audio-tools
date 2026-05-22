"""Callback wrappers published by the editor integration facade."""

from __future__ import annotations

from functools import wraps
from types import SimpleNamespace
from typing import Any, Callable

from . import (
    editor_analysis,
    editor_bridge,
    editor_dependencies,
    editor_frontend_callbacks,
    editor_history,
    editor_playback,
    editor_processing,
    editor_region_delete,
    editor_runtime,
    editor_settings_actions,
    editor_split_defaults,
)

_dispose_editor_frontend_controls = editor_frontend_callbacks._dispose_editor_frontend_controls
_eval_playback_state = editor_frontend_callbacks._eval_playback_state
_eval_status = editor_frontend_callbacks._eval_status
_eval_visualizer_status = editor_frontend_callbacks._eval_visualizer_status
_eval_visualizer_status_for_field = editor_frontend_callbacks._eval_visualizer_status_for_field
_eval_with_callback = editor_frontend_callbacks._eval_with_callback
_graph_redraw_expression = editor_frontend_callbacks._graph_redraw_expression
_main = editor_frontend_callbacks._main
_playback_after_edit_expression = editor_frontend_callbacks._playback_after_edit_expression
_request_playback_after_edit = editor_frontend_callbacks._request_playback_after_edit
_request_graph_redraw = editor_frontend_callbacks._request_graph_redraw
_retry_playback_after_edit = editor_frontend_callbacks._retry_playback_after_edit
_retry_graph_redraw = editor_frontend_callbacks._retry_graph_redraw
_schedule_graph_redraw_attempt = editor_frontend_callbacks._schedule_graph_redraw_attempt
_schedule_playback_after_edit_attempt = editor_frontend_callbacks._schedule_playback_after_edit_attempt
_set_busy = editor_frontend_callbacks._set_busy
_set_busy_for_field = editor_frontend_callbacks._set_busy_for_field


def _exports() -> SimpleNamespace:
    return SimpleNamespace(
        **{
            name[1:]: value
            for name, value in globals().items()
            if name.startswith("_") and callable(value)
        }
    )


def _deps(builder: Callable[[Any, Any], SimpleNamespace]) -> SimpleNamespace:
    exports = _exports()
    return builder(exports, exports)


def _bridge_deps() -> SimpleNamespace:
    return _deps(editor_dependencies.bridge_deps)


def _processing_deps() -> SimpleNamespace:
    return _deps(editor_dependencies.processing_deps)


def _region_delete_deps() -> SimpleNamespace:
    return _deps(editor_dependencies.region_delete_deps)


def _playback_deps() -> SimpleNamespace:
    return _deps(editor_dependencies.playback_deps)


def _history_deps() -> SimpleNamespace:
    return _deps(editor_dependencies.history_deps)


def _settings_action_deps() -> SimpleNamespace:
    return _deps(editor_dependencies.settings_action_deps)


def _analysis_deps() -> SimpleNamespace:
    return _deps(editor_dependencies.analysis_deps)


def _with_deps(func: Callable[..., Any], deps_builder: Callable[[], SimpleNamespace]) -> Callable[..., Any]:
    @wraps(func)
    def _wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, deps_builder(), **kwargs)

    return _wrapper


def _with_keyword_deps(
    func: Callable[..., Any],
    deps_builder: Callable[[], SimpleNamespace],
) -> Callable[..., Any]:
    @wraps(func)
    def _wrapper(*args: Any, **kwargs: Any) -> Any:
        kwargs["deps"] = deps_builder()
        return func(*args, **kwargs)

    return _wrapper


_handle_bridge_command = _with_deps(editor_bridge.handle_bridge_command, _bridge_deps)
_handle_pending_command_payload = _with_deps(editor_bridge.handle_pending_command_payload, _bridge_deps)
_handle_non_processing_command = _with_deps(editor_bridge.handle_non_processing_command, _bridge_deps)
_handle_editor_frontend_log = _with_deps(editor_bridge.handle_editor_frontend_log, _bridge_deps)
_log_editor_frontend_payload = editor_bridge.log_editor_frontend_payload
_save_split_defaults_from_frontend = _with_deps(
    editor_split_defaults.save_split_defaults_from_frontend,
    _bridge_deps,
)

_update_state_and_render = _with_deps(editor_processing.update_state_and_render, _processing_deps)
_render_and_replace_async = _with_deps(editor_processing.render_and_replace_async, _processing_deps)
_replace_current_field_after_render = _with_deps(
    editor_processing.replace_current_field_after_render,
    _processing_deps,
)
_render_failed = _with_deps(editor_processing.render_failed, _processing_deps)
_denoise_standard_async = _with_deps(editor_processing.denoise_standard_async, _processing_deps)
_convert_async = _with_deps(editor_processing.convert_async, _processing_deps)
_rnnoise_async = _with_deps(editor_processing.rnnoise_async, _processing_deps)
_dpdfnet_async = _with_deps(editor_processing.dpdfnet_async, _processing_deps)
_voice_only_async = _with_deps(editor_processing.voice_only_async, _processing_deps)
_pitch_hum_async = _with_deps(editor_processing.pitch_hum_async, _processing_deps)
_run_special_audio_transform_async = _with_keyword_deps(
    editor_processing.run_special_audio_transform_async,
    _processing_deps,
)
_replace_current_field_after_noise_removal = _with_deps(
    editor_processing.replace_current_field_after_noise_removal,
    _processing_deps,
)
_record_rnnoise_failure_context = editor_processing.record_rnnoise_failure_context
_record_dpdfnet_failure_context = editor_processing.record_dpdfnet_failure_context
_record_spleeter_failure_context = editor_processing.record_spleeter_failure_context
_log_special_transform_failure = editor_processing.log_special_transform_failure

_delete_selection_from_frontend = _with_deps(
    editor_region_delete.delete_selection_from_frontend,
    _region_delete_deps,
)
_delete_selection_with_request = _with_deps(
    editor_region_delete.delete_selection_with_request,
    _region_delete_deps,
)
_delete_selection_async = _with_deps(editor_region_delete.delete_selection_async, _region_delete_deps)
_replace_current_field_after_region_delete = _with_deps(
    editor_region_delete.replace_current_field_after_region_delete,
    _region_delete_deps,
)
_parse_region_delete_request = editor_region_delete.parse_region_delete_request
_required_region_delete_values = editor_region_delete.required_region_delete_values
_region_delete_source_filename = editor_region_delete.region_delete_source_filename
_region_delete_trigger = editor_region_delete.region_delete_trigger
_region_delete_log_context = editor_region_delete.region_delete_log_context

_stop_audio_playback = editor_playback.stop_audio_playback
_stop_session_playback = editor_runtime.stop_session_playback
_cleanup_temp_playback = editor_playback.cleanup_temp_playback
_play = _with_deps(editor_playback.play, _playback_deps)
_play_ended = _with_deps(editor_playback.play_ended, _playback_deps)
_play_with_request = _with_deps(editor_playback.play_with_request, _playback_deps)
_playback_request_values = _with_deps(editor_playback.playback_request_values, _playback_deps)
_toggle_native_pause_resume = _with_deps(editor_playback.toggle_native_pause_resume, _playback_deps)
_apply_html_playback_request = _with_deps(editor_playback.apply_html_playback_request, _playback_deps)
_start_playback_from_cursor = _with_deps(editor_playback.start_playback_from_cursor, _playback_deps)
_playback_segment_ready = _with_deps(editor_playback.playback_segment_ready, _playback_deps)
_playback_segment_failed = _with_deps(editor_playback.playback_segment_failed, _playback_deps)

_undo = _with_deps(editor_history.undo, _history_deps)
_redo = _with_deps(editor_history.redo, _history_deps)
_restore_history_entry = _with_keyword_deps(editor_history.restore_history_entry, _history_deps)


def _open_settings_from_editor(editor: Any) -> None:
    editor_settings_actions.open_settings_from_editor(
        editor,
        editor_runtime.SETTINGS_OPENER,
        _settings_action_deps(),
    )


def _refresh_editor_after_settings_save(editor: Any) -> None:
    editor_settings_actions.refresh_editor_after_settings_save(editor, _settings_action_deps())


def _show_current_audio_file(editor: Any) -> None:
    editor_settings_actions.show_current_audio_file(editor, _settings_action_deps())


_analyze_current_async = _with_deps(editor_analysis.analyze_current_async, _analysis_deps)
_analyze_field_from_frontend = _with_deps(editor_analysis.analyze_field_from_frontend, _analysis_deps)
_analyze_requested_field_async = _with_deps(editor_analysis.analyze_requested_field_async, _analysis_deps)
_start_field_analysis_async = _with_deps(editor_analysis.start_field_analysis_async, _analysis_deps)
_finish_ignored_field_analysis = _with_deps(editor_analysis.finish_ignored_field_analysis, _analysis_deps)
_fail_field_analysis_without_generation = _with_deps(
    editor_analysis.fail_field_analysis_without_generation,
    _analysis_deps,
)
_analysis_finished = _with_deps(editor_analysis.analysis_finished, _analysis_deps)
_analysis_failed = _with_deps(editor_analysis.analysis_failed, _analysis_deps)
_parse_graph_analysis_request = editor_analysis.parse_graph_analysis_request
_begin_field_analysis = editor_analysis.begin_field_analysis
_is_current_field_analysis = editor_analysis.is_current_field_analysis
_end_field_analysis = editor_analysis.end_field_analysis
_set_cursor_from_web = _with_deps(editor_playback.set_cursor_from_web, _playback_deps)
