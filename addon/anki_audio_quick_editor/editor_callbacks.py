"""Callback wrappers published by the editor integration facade."""

from __future__ import annotations

from functools import wraps
from types import SimpleNamespace
from typing import Any, Callable, TypeVar

from . import (
    editor_analysis,
    editor_bridge,
    editor_conversion,
    editor_cursor_bridge,
    editor_dependencies,
    editor_deps_protocols,
    editor_frontend_callbacks,
    editor_history,
    editor_persistent_undo,
    editor_presets,
    editor_processing,
    editor_recording,
    editor_region_delete,
    editor_runtime,
    editor_settings_actions,
    editor_sharing,
    editor_source_metadata,
    editor_special_transforms,
    editor_split_defaults,
    editor_transform_failure_support,
    editor_transform_orchestration,
    editor_transform_post_processing,
)

_dispose_editor_frontend_controls = editor_frontend_callbacks._dispose_editor_frontend_controls
_eval_history_availability = editor_frontend_callbacks._eval_history_availability
_eval_history_snapshot = editor_frontend_callbacks._eval_history_snapshot
_eval_status = editor_frontend_callbacks._eval_status
_eval_visualizer_status = editor_frontend_callbacks._eval_visualizer_status
_eval_visualizer_status_for_field = editor_frontend_callbacks._eval_visualizer_status_for_field
_eval_with_callback = editor_frontend_callbacks._eval_with_callback
_eval_learner_recording_state = editor_frontend_callbacks._eval_learner_recording_state
_graph_redraw_expression = editor_frontend_callbacks._graph_redraw_expression
_history_availability_expression = editor_frontend_callbacks._history_availability_expression
_history_snapshot_expression = editor_frontend_callbacks._history_snapshot_expression
_main = editor_frontend_callbacks._main
pending_editor_intent_payload = editor_frontend_callbacks._pending_editor_intent_payload
_request_history_availability_after_edit = editor_frontend_callbacks._request_history_availability_after_edit
_request_history_snapshot_after_edit = editor_frontend_callbacks._request_history_snapshot_after_edit
_request_playback_after_edit = editor_frontend_callbacks._request_playback_after_edit
_request_graph_redraw = editor_frontend_callbacks._request_graph_redraw
_retry_history_availability = editor_frontend_callbacks._retry_history_availability
_retry_history_snapshot = editor_frontend_callbacks._retry_history_snapshot
_retry_graph_redraw = editor_frontend_callbacks._retry_graph_redraw
_schedule_graph_redraw_attempt = editor_frontend_callbacks._schedule_graph_redraw_attempt
_schedule_history_availability_attempt = editor_frontend_callbacks._schedule_history_availability_attempt
_schedule_history_snapshot_attempt = editor_frontend_callbacks._schedule_history_snapshot_attempt
_set_busy = editor_frontend_callbacks._set_busy
_set_busy_for_field = editor_frontend_callbacks._set_busy_for_field


_EXPORT_NAMES = (
    "analysis_failed", "analysis_finished", "analyze_current_async",
    "analyze_field_from_frontend", "analyze_requested_field_async", "begin_field_analysis",
    "can_persistent_undo", "convert_async",
    "delete_selection_from_frontend", "delete_selection_with_request", "denoise_standard_async",
    "dispose_editor_frontend_controls", "dpdfnet_async", "end_field_analysis",
    "eval_history_availability", "eval_history_snapshot", "eval_learner_recording_state",
    "eval_status", "eval_visualizer_status",
    "eval_visualizer_status_for_field", "eval_with_callback", "fail_field_analysis_without_generation",
    "finish_ignored_field_analysis", "finish_shared_audio", "graph_redraw_expression",
    "handle_bridge_command", "handle_editor_frontend_log", "handle_non_processing_command",
    "handle_pending_command_payload", "history_availability_expression",
    "history_jump", "history_snapshot_expression", "is_current_field_analysis",
    "latest_persistent_undo_item", "log_editor_frontend_payload", "log_special_transform_failure",
    "main", "open_external_url", "open_settings_from_editor",
    "parse_graph_analysis_request", "parse_region_delete_request", "pending_editor_intent_payload",
    "persistent_undo_items", "pitch_hum_async",
    "record_dpdfnet_failure_context", "record_learner_voice", "record_rnnoise_failure_context",
    "record_spleeter_failure_context", "record_standard_persistent_undo", "redo",
    "reduce_size_async", "refresh_editor_after_settings_save", "region_delete_log_context",
    "region_delete_source_filename",
    "region_delete_trigger", "render_and_replace_async", "render_failed",
    "replace_current_field_after_noise_removal", "replace_current_field_after_region_delete",
    "replace_current_field_after_render", "replace_current_field_after_special_transform",
    "request_graph_redraw", "request_history_availability_after_edit",
    "request_history_snapshot_after_edit", "request_playback_after_edit", "request_source_metadata",
    "required_region_delete_values", "restore_history_entry", "restore_persistent_undo",
    "restore_persistent_undo_steps", "retry_graph_redraw", "retry_history_availability",
    "retry_history_snapshot", "rnnoise_async", "run_processing_preset_async",
    "run_special_audio_transform_async", "save_split_defaults_from_frontend",
    "schedule_graph_redraw_attempt", "schedule_history_availability_attempt",
    "schedule_history_snapshot_attempt", "set_busy", "set_busy_for_field",
    "set_cursor_from_web", "share_current_audio_file", "share_failed",
    "share_learner_recording_file", "show_current_audio_file", "show_learner_recording_file",
    "start_field_analysis_async", "stop_learner_recording",
    "undo", "update_state_and_render", "voice_only_async", "write_generated_media",
)
DepsT = TypeVar("DepsT")


def _exports() -> SimpleNamespace:
    return SimpleNamespace(**{name: _export_value(name) for name in _EXPORT_NAMES})


def _export_value(name: str) -> Any:
    value = globals().get(name)
    if value is not None:
        return value
    return globals()[f"_{name}"]


def _deps(builder: Callable[[Any, Any], DepsT]) -> DepsT:  # noqa: UP047 - system dev runner parses this with Python 3.9
    """Build a dependency namespace for the given builder.

    Passes the same ``_exports()`` namespace to both ``callbacks`` and
    ``frontend_callbacks`` parameters.  The builders use separate parameter
    names for readability and to document which side of the concern boundary
    each dependency serves, but the underlying namespace is shared because
    ``_exports()`` publishes an explicit callback surface shared by both
    dependency namespaces.
    """
    exports = _exports()
    return builder(exports, exports)


def _bridge_deps() -> editor_deps_protocols.BridgeDeps:
    return _deps(editor_dependencies.bridge_deps)


def _processing_deps() -> editor_deps_protocols.ProcessingDeps:
    return _deps(editor_dependencies.processing_deps)


def _region_delete_deps() -> editor_deps_protocols.RegionDeleteDeps:
    exports = _exports()
    return editor_dependencies.region_delete_deps(exports, exports)


def _cursor_deps() -> editor_deps_protocols.CursorDeps:
    return _deps(editor_dependencies.cursor_deps)


def _history_deps() -> editor_deps_protocols.HistoryDeps:
    return _deps(editor_dependencies.history_deps)


def _settings_action_deps() -> editor_deps_protocols.SettingsActionDeps:
    return _deps(editor_dependencies.settings_action_deps)


def _analysis_deps() -> editor_deps_protocols.AnalysisDeps:
    return _deps(editor_dependencies.analysis_deps)


def _recording_deps() -> editor_deps_protocols.RecordingDeps:
    return _deps(editor_dependencies.recording_deps)


def _share_deps() -> editor_deps_protocols.ShareDeps:
    return _deps(editor_dependencies.share_deps)


def _with_deps(func: Callable[..., Any], deps_builder: Callable[[], Any]) -> Callable[..., Any]:
    @wraps(func)
    def _wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, deps_builder(), **kwargs)

    return _wrapper


def _with_keyword_deps(
    func: Callable[..., Any],
    deps_builder: Callable[[], Any],
) -> Callable[..., Any]:
    @wraps(func)
    def _wrapper(*args: Any, **kwargs: Any) -> Any:
        kwargs["deps"] = deps_builder()
        return func(*args, **kwargs)

    return _wrapper


handle_bridge_command = _with_deps(editor_bridge.handle_bridge_command, _bridge_deps)
_handle_pending_command_payload = _with_deps(editor_bridge.handle_pending_command_payload, _bridge_deps)
_handle_non_processing_command = _with_deps(editor_bridge.handle_non_processing_command, _bridge_deps)
_handle_editor_frontend_log = _with_deps(editor_bridge.handle_editor_frontend_log, _bridge_deps)
_log_editor_frontend_payload = editor_bridge.log_editor_frontend_payload
_save_split_defaults_from_frontend = _with_deps(
    editor_split_defaults.save_split_defaults_from_frontend,
    _bridge_deps,
)
_request_source_metadata = _with_deps(
    editor_source_metadata.request_source_metadata,
    _bridge_deps,
)

_update_state_and_render = _with_deps(editor_processing.update_state_and_render, _processing_deps)
_render_and_replace_async = _with_deps(editor_processing.render_and_replace_async, _processing_deps)
_replace_current_field_after_render = _with_deps(
    editor_processing.replace_current_field_after_render,
    _processing_deps,
)
_write_generated_media = _with_deps(editor_processing.write_generated_media, _processing_deps)
_record_standard_persistent_undo = editor_persistent_undo.record_standard_persistent_undo
_can_persistent_undo = editor_persistent_undo.can_persistent_undo
_latest_persistent_undo_item = editor_persistent_undo.latest_persistent_undo_item
_persistent_undo_items = editor_persistent_undo.persistent_undo_items
_restore_persistent_undo = _with_deps(editor_persistent_undo.restore_persistent_undo, _history_deps)
_restore_persistent_undo_steps = _with_deps(
    editor_persistent_undo.restore_persistent_undo_steps,
    _history_deps,
)
_render_failed = _with_deps(editor_processing.render_failed, _processing_deps)
_denoise_standard_async = _with_deps(editor_special_transforms.denoise_standard_async, _processing_deps)
_convert_async = _with_deps(editor_conversion.convert_async, _processing_deps)
_rnnoise_async = _with_deps(editor_special_transforms.rnnoise_async, _processing_deps)
_dpdfnet_async = _with_deps(editor_special_transforms.dpdfnet_async, _processing_deps)
_voice_only_async = _with_deps(editor_special_transforms.voice_only_async, _processing_deps)
_pitch_hum_async = _with_deps(editor_special_transforms.pitch_hum_async, _processing_deps)
_run_processing_preset_async = _with_deps(
    editor_presets.run_processing_preset_async,
    _processing_deps,
)
_reduce_size_async = _with_deps(editor_special_transforms.reduce_size_async, _processing_deps)
_run_special_audio_transform_async = _with_keyword_deps(
    editor_transform_orchestration.run_special_audio_transform_async,
    _processing_deps,
)
_replace_current_field_after_special_transform = _with_deps(
    editor_transform_post_processing.replace_current_field_after_special_transform,
    _processing_deps,
)
_replace_current_field_after_noise_removal = _replace_current_field_after_special_transform
_record_rnnoise_failure_context = editor_transform_failure_support.record_rnnoise_failure_context
_record_dpdfnet_failure_context = editor_transform_failure_support.record_dpdfnet_failure_context
_record_spleeter_failure_context = editor_transform_failure_support.record_spleeter_failure_context
_log_special_transform_failure = editor_transform_failure_support.log_special_transform_failure

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

_record_learner_voice = _with_keyword_deps(
    editor_recording.record_learner_voice,
    _recording_deps,
)
_stop_learner_recording = _with_deps(
    editor_recording.stop_learner_recording,
    _recording_deps,
)
_cancel_learner_recording = _with_keyword_deps(
    editor_recording.cancel_learner_recording,
    _recording_deps,
)

# Public lifecycle-envelope façade. Ordinary editor links still dispatch through
# the dependency namespace above; generated envelopes call these same wrappers.
record_learner_voice = _record_learner_voice
stop_learner_recording = _stop_learner_recording
cancel_learner_recording = _cancel_learner_recording
convert_async = _convert_async
_undo = _with_deps(editor_history.undo, _history_deps)
_redo = _with_deps(editor_history.redo, _history_deps)
_history_jump = _with_deps(editor_history.history_jump, _history_deps)
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


def _show_learner_recording_file(editor: Any) -> None:
    editor_settings_actions.show_learner_recording_file(editor, _settings_action_deps())


def _open_external_url(url: str) -> None:
    editor_settings_actions.open_external_url(url)


_share_current_audio_file = _with_deps(editor_sharing.share_current_audio_file, _share_deps)
_share_learner_recording_file = _with_deps(editor_sharing.share_learner_recording_file, _share_deps)
_finish_shared_audio = _with_deps(editor_sharing.finish_shared_audio, _share_deps)
_share_failed = _with_deps(editor_sharing.share_failed, _share_deps)

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
_set_cursor_from_web = _with_deps(editor_cursor_bridge.set_cursor_from_web, _cursor_deps)
