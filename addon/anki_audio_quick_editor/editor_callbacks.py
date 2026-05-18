"""Callback wrappers published by the editor integration facade."""

from __future__ import annotations

from pathlib import Path
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
)
from .audio_processor import AudioProcessingResult
from .audio_state import AudioEditState, AudioProcessingConfig
from .editor_actions import EditorCommandPayload
from .editor_session import EditorSession, RegionDeleteRequest, UndoEntry
from .prosody_types import ProsodyTrack

_dispose_editor_frontend_controls = editor_frontend_callbacks._dispose_editor_frontend_controls
_eval_playback_state = editor_frontend_callbacks._eval_playback_state
_eval_status = editor_frontend_callbacks._eval_status
_eval_visualizer_status = editor_frontend_callbacks._eval_visualizer_status
_eval_visualizer_status_for_field = editor_frontend_callbacks._eval_visualizer_status_for_field
_eval_with_callback = editor_frontend_callbacks._eval_with_callback
_graph_redraw_expression = editor_frontend_callbacks._graph_redraw_expression
_main = editor_frontend_callbacks._main
_request_graph_redraw = editor_frontend_callbacks._request_graph_redraw
_retry_graph_redraw = editor_frontend_callbacks._retry_graph_redraw
_schedule_graph_redraw_attempt = editor_frontend_callbacks._schedule_graph_redraw_attempt
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


def _handle_bridge_command(editor: Any, command: str) -> None:
    editor_bridge.handle_bridge_command(editor, command, _bridge_deps())


def _handle_pending_command_payload(editor: Any) -> None:
    editor_bridge.handle_pending_command_payload(editor, _bridge_deps())


def _handle_non_processing_command(editor: Any, command: str) -> bool:
    return editor_bridge.handle_non_processing_command(editor, command, _bridge_deps())


def _handle_editor_frontend_log(editor: Any) -> None:
    editor_bridge.handle_editor_frontend_log(editor, _bridge_deps())


def _log_editor_frontend_payload(raw_payload: Any) -> None:
    editor_bridge.log_editor_frontend_payload(raw_payload)


def _update_state_and_render(editor: Any, command: str | EditorCommandPayload) -> None:
    editor_processing.update_state_and_render(editor, command, _processing_deps())


def _render_and_replace_async(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    updated_state: AudioEditState,
    config: AudioProcessingConfig,
) -> None:
    editor_processing.render_and_replace_async(
        editor,
        session,
        source_path,
        updated_state,
        config,
        _processing_deps(),
    )


def _replace_current_field_after_render(
    editor: Any,
    updated_state: AudioEditState,
    saved_name: str,
) -> None:
    editor_processing.replace_current_field_after_render(
        editor,
        updated_state,
        saved_name,
        _processing_deps(),
    )


def _render_failed(editor: Any, message: str) -> None:
    editor_processing.render_failed(editor, message, _processing_deps())


def _denoise_standard_async(editor: Any) -> None:
    editor_processing.denoise_standard_async(editor, _processing_deps())


def _rnnoise_async(editor: Any) -> None:
    editor_processing.rnnoise_async(editor, _processing_deps())


def _run_special_audio_transform_async(
    editor: Any,
    *,
    label: str,
    failure_log_label: str,
    renderer: Callable[..., AudioProcessingResult],
    support_hint: str = "",
    failure_context_recorder: Callable[[Path, AudioProcessingConfig, Exception], None] | None = None,
) -> None:
    editor_processing.run_special_audio_transform_async(
        editor,
        label=label,
        failure_log_label=failure_log_label,
        renderer=renderer,
        support_hint=support_hint,
        failure_context_recorder=failure_context_recorder,
        deps=_processing_deps(),
    )


def _delete_selection_from_frontend(editor: Any) -> None:
    editor_region_delete.delete_selection_from_frontend(editor, _region_delete_deps())


def _delete_selection_with_request(editor: Any, request: Any) -> None:
    editor_region_delete.delete_selection_with_request(editor, request, _region_delete_deps())


def _parse_region_delete_request(request: Any) -> RegionDeleteRequest | None:
    return editor_region_delete.parse_region_delete_request(request)


def _required_region_delete_values(request: dict[str, Any]) -> tuple[Any, Any, Any, Any] | None:
    return editor_region_delete.required_region_delete_values(request)


def _region_delete_source_filename(request: dict[str, Any]) -> str:
    return editor_region_delete.region_delete_source_filename(request)


def _region_delete_trigger(request: dict[str, Any]) -> str:
    return editor_region_delete.region_delete_trigger(request)


def _delete_selection_async(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    request: RegionDeleteRequest,
    config: AudioProcessingConfig,
) -> None:
    editor_region_delete.delete_selection_async(
        editor,
        session,
        source_path,
        request,
        config,
        _region_delete_deps(),
    )


def _replace_current_field_after_region_delete(
    editor: Any,
    request: RegionDeleteRequest,
    saved_name: str,
    output_duration_ms: int | None,
    started_at: float,
) -> None:
    editor_region_delete.replace_current_field_after_region_delete(
        editor,
        request,
        saved_name,
        output_duration_ms,
        started_at,
        _region_delete_deps(),
    )


def _region_delete_log_context(request: RegionDeleteRequest) -> dict[str, object]:
    return editor_region_delete.region_delete_log_context(request)


def _replace_current_field_after_noise_removal(editor: Any, saved_name: str) -> None:
    editor_processing.replace_current_field_after_noise_removal(
        editor,
        saved_name,
        _processing_deps(),
    )


def _stop_audio_playback() -> None:
    editor_playback.stop_audio_playback()


def _stop_session_playback(session: EditorSession) -> None:
    editor_runtime.stop_session_playback(session)


def _cleanup_temp_playback(session: EditorSession) -> None:
    editor_playback.cleanup_temp_playback(session)


def _play(editor: Any) -> None:
    editor_playback.play(editor, _playback_deps())


def _play_ended(editor: Any) -> None:
    editor_playback.play_ended(editor, _playback_deps())


def _play_with_request(editor: Any, request: Any) -> None:
    editor_playback.play_with_request(editor, request, _playback_deps())


def _playback_request_values(
    session: EditorSession,
    request: Any,
    field_index: int,
) -> tuple[str, str, int]:
    return editor_playback.playback_request_values(session, request, field_index, _playback_deps())


def _toggle_native_pause_resume(
    editor: Any,
    session: EditorSession,
    field_index: int,
    action: str,
    cursor_ms: int,
) -> bool:
    return editor_playback.toggle_native_pause_resume(
        editor,
        session,
        field_index,
        action,
        cursor_ms,
        _playback_deps(),
    )


def _apply_html_playback_request(
    editor: Any,
    session: EditorSession,
    field_index: int,
    action: str,
    cursor_ms: int,
) -> None:
    editor_playback.apply_html_playback_request(
        editor,
        session,
        field_index,
        action,
        cursor_ms,
        _playback_deps(),
    )


def _start_playback_from_cursor(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    field_index: int,
    cursor_ms: int,
) -> None:
    editor_playback.start_playback_from_cursor(
        editor,
        session,
        source_path,
        field_index,
        cursor_ms,
        _playback_deps(),
    )


def _playback_segment_ready(
    editor: Any,
    generation: int,
    field_index: int,
    cursor_ms: int,
    playback_path: Path,
) -> None:
    editor_playback.playback_segment_ready(
        editor,
        generation,
        field_index,
        cursor_ms,
        playback_path,
        _playback_deps(),
    )


def _playback_segment_failed(editor: Any, generation: int, message: str) -> None:
    editor_playback.playback_segment_failed(editor, generation, message, _playback_deps())


def _undo(editor: Any) -> None:
    editor_history.undo(editor, _history_deps())


def _redo(editor: Any) -> None:
    editor_history.redo(editor, _history_deps())


def _restore_history_entry(
    editor: Any,
    session: EditorSession,
    entry: UndoEntry,
    *,
    redo_current: bool,
    status: str,
) -> None:
    editor_history.restore_history_entry(
        editor,
        session,
        entry,
        redo_current=redo_current,
        status=status,
        deps=_history_deps(),
    )


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


def _record_rnnoise_failure_context(
    source_path: Path,
    config: AudioProcessingConfig,
    exc: Exception,
) -> None:
    editor_processing.record_rnnoise_failure_context(source_path, config, exc)


def _log_special_transform_failure(failure_log_label: str, message: str) -> None:
    editor_processing.log_special_transform_failure(failure_log_label, message)


def _analyze_current_async(editor: Any) -> None:
    editor_analysis.analyze_current_async(editor, _analysis_deps())


def _analyze_field_from_frontend(editor: Any) -> None:
    editor_analysis.analyze_field_from_frontend(editor, _analysis_deps())


def _analyze_requested_field_async(editor: Any, request: Any) -> None:
    editor_analysis.analyze_requested_field_async(editor, request, _analysis_deps())


def _parse_graph_analysis_request(request: Any) -> tuple[int, str] | None:
    return editor_analysis.parse_graph_analysis_request(request)


def _start_field_analysis_async(
    editor: Any,
    field_index: int,
    filename: str,
    media_path: Path,
) -> None:
    editor_analysis.start_field_analysis_async(editor, field_index, filename, media_path, _analysis_deps())


def _begin_field_analysis(session: EditorSession, field_index: int, filename: str) -> int:
    return editor_analysis.begin_field_analysis(session, field_index, filename)


def _finish_ignored_field_analysis(editor: Any, field_index: int) -> None:
    editor_analysis.finish_ignored_field_analysis(editor, field_index, _analysis_deps())


def _fail_field_analysis_without_generation(editor: Any, field_index: int, message: str) -> None:
    editor_analysis.fail_field_analysis_without_generation(editor, field_index, message, _analysis_deps())


def _analysis_finished(
    editor: Any,
    generation: int,
    field_index: int,
    track: ProsodyTrack,
) -> None:
    editor_analysis.analysis_finished(editor, generation, field_index, track, _analysis_deps())


def _analysis_failed(editor: Any, generation: int, field_index: int, message: str) -> None:
    editor_analysis.analysis_failed(editor, generation, field_index, message, _analysis_deps())


def _is_current_field_analysis(
    session: EditorSession,
    field_index: int,
    generation: int,
) -> bool:
    return editor_analysis.is_current_field_analysis(session, field_index, generation)


def _end_field_analysis(session: EditorSession, field_index: int) -> None:
    editor_analysis.end_field_analysis(session, field_index)


def _set_cursor_from_web(editor: Any) -> None:
    editor_playback.set_cursor_from_web(editor, _playback_deps())
