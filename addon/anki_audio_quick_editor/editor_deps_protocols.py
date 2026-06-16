"""Typed dependency contracts for editor workflow modules."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol


class FrontendDeps(Protocol):
    eval_with_callback: Callable[..., Any]
    graph_redraw_expression: Callable[..., str]
    history_availability_expression: Callable[..., str]
    history_snapshot_expression: Callable[..., str]
    pending_post_edit_playback_payload: Callable[..., Any]
    playback_after_edit_expression: Callable[..., str]
    request_history_availability_after_edit: Callable[..., None]
    request_history_snapshot_after_edit: Callable[..., None]
    retry_graph_redraw: Callable[..., None]
    retry_history_availability: Callable[..., None]
    retry_history_snapshot: Callable[..., None]
    schedule_graph_redraw_attempt: Callable[..., None]
    schedule_history_availability_attempt: Callable[..., None]
    schedule_history_snapshot_attempt: Callable[..., None]
    sessions: dict[Any, Any]
    set_busy_for_field: Callable[..., None]


class BridgeDeps(Protocol):
    analyze_current_async: Callable[..., None]
    analyze_field_from_frontend: Callable[..., None]
    config: Callable[[Any], dict[str, Any]]
    convert_async: Callable[..., None]
    delete_selection_from_frontend: Callable[..., None]
    denoise_standard_async: Callable[..., None]
    dpdfnet_async: Callable[..., None]
    eval_status: Callable[..., None]
    eval_with_callback: Callable[..., None]
    handle_bridge_command: Callable[..., None]
    handle_editor_frontend_log: Callable[..., None]
    handle_non_processing_command: Callable[..., bool]
    handle_pending_command_payload: Callable[..., None]
    handle_post_edit_playback_ready: Callable[..., None]
    history_jump: Callable[..., None]
    log_editor_frontend_payload: Callable[..., None]
    main: Callable[[Any, Callable[[], None]], None]
    open_external_url: Callable[..., None]
    open_settings_from_editor: Callable[..., None]
    pitch_hum_async: Callable[..., None]
    play: Callable[..., None]
    play_ended: Callable[..., None]
    play_learner_recording: Callable[..., None]
    probe_audio_metadata: Callable[..., Any]
    record_learner_voice: Callable[..., None]
    redo: Callable[..., None]
    reduce_size_async: Callable[..., None]
    request_source_metadata: Callable[..., None]
    resolve_requested_field_media: Callable[..., Any]
    rnnoise_async: Callable[..., None]
    run_processing_preset_async: Callable[..., None]
    save_split_defaults_from_frontend: Callable[..., None]
    set_busy: Callable[..., None]
    set_cursor_from_web: Callable[..., None]
    share_current_audio_file: Callable[..., None]
    share_learner_recording_file: Callable[..., None]
    show_current_audio_file: Callable[..., None]
    show_learner_recording_file: Callable[..., None]
    stop_learner_recording: Callable[..., None]
    stop_playback: Callable[..., Any]
    threading: Any
    undo: Callable[..., None]
    update_state_and_render: Callable[..., None]
    voice_only_async: Callable[..., None]


class RecordingDeps(Protocol):
    analyze_prosody_cached: Callable[..., Any]
    config: Callable[[Any], dict[str, Any]]
    current_field_index: Callable[[Any], int]
    eval_status: Callable[..., None]
    is_busy: Callable[[Any], bool]
    main: Callable[[Any, Callable[[], None]], None]
    recorder_factory: Callable[..., Any]
    resolve_requested_field_media: Callable[..., Any]
    sessions: dict[Any, Any]
    set_busy_for_field: Callable[..., None]
    still_processing_message: str
    stop_session_playback: Callable[[Any], None]
    threading: Any


class ShareDeps(Protocol):
    current_media_path: Callable[[Any], tuple[Any, Path]]
    eval_status: Callable[..., None]
    finish_shared_audio: Callable[..., None]
    is_busy: Callable[[Any], bool]
    logger: Any
    main: Callable[[Any, Callable[[], None]], None]
    sessions: dict[Any, Any]
    set_busy: Callable[..., None]
    share_failed: Callable[..., None]
    still_processing_message: str
    t: Callable[..., str]
    upload_file: Callable[..., str]


class HistoryDeps(Protocol):
    can_persistent_undo: Callable[..., bool]
    config: Callable[[Any], dict[str, Any]]
    current_field_audio_missing: str
    current_field_index: Callable[[Any], int]
    dispose_editor_frontend_controls: Callable[[Any], None]
    eval_history_availability: Callable[..., None]
    eval_history_snapshot: Callable[..., None]
    eval_playback_state: Callable[..., None]
    eval_status: Callable[..., None]
    is_busy: Callable[[Any], bool]
    latest_persistent_undo_item: Callable[..., Any]
    persistent_undo_items: Callable[..., Any]
    request_graph_redraw: Callable[..., None]
    request_history_availability_after_edit: Callable[..., None]
    request_history_snapshot_after_edit: Callable[..., None]
    request_playback_after_edit: Callable[..., None]
    restore_history_entry: Callable[..., None]
    restore_persistent_undo: Callable[..., bool]
    restore_persistent_undo_steps: Callable[..., bool]
    session_and_source: Callable[[Any], tuple[Any, Path]]
    still_processing_message: str
    stop_session_playback: Callable[[Any], None]


class ProcessingDeps(Protocol):
    analyze_current_async: Callable[..., None]
    analyze_prosody_cached: Callable[..., Any]
    artifact_root: Callable[[Any], Path | None]
    can_persistent_undo: Callable[..., bool]
    config: Callable[[Any], dict[str, Any]]
    current_field_audio_missing: str
    current_field_index: Callable[[Any], int]
    current_media_path: Callable[[Any], tuple[Any, Path]]
    dispose_editor_frontend_controls: Callable[[Any], None]
    eval_history_availability: Callable[..., None]
    eval_history_snapshot: Callable[..., None]
    eval_playback_state: Callable[..., None]
    eval_status: Callable[..., None]
    format_ffmpeg_command: Callable[[tuple[str, ...]], str]
    is_busy: Callable[[Any], bool]
    latest_persistent_undo_item: Callable[..., Any]
    log_special_transform_failure: Callable[..., None]
    main: Callable[[Any, Callable[[], None]], None]
    make_output_filename: Callable[..., str]
    persistent_undo_items: Callable[..., Any]
    record_dpdfnet_failure_context: Callable[..., None]
    record_rnnoise_failure_context: Callable[..., None]
    record_spleeter_failure_context: Callable[..., None]
    record_standard_persistent_undo: Callable[..., Any]
    render_and_replace_async: Callable[..., None]
    render_audio: Callable[..., Any]
    render_converted_audio: Callable[..., Any]
    render_dpdfnet_audio: Callable[..., Any]
    render_failed: Callable[..., None]
    render_noise_reduced_audio: Callable[..., Any]
    render_pitch_hum_audio: Callable[..., Any]
    render_pitch_tier_hum_audio: Callable[..., Any]
    render_rnnoise_audio: Callable[..., Any]
    render_size_reduced_audio: Callable[..., Any]
    render_voice_only_audio: Callable[..., Any]
    replace_current_field_after_noise_removal: Callable[..., None]
    replace_current_field_after_render: Callable[..., None]
    request_graph_redraw: Callable[..., None]
    request_history_availability_after_edit: Callable[..., None]
    request_history_snapshot_after_edit: Callable[..., None]
    request_playback_after_edit: Callable[..., None]
    run_special_audio_transform_async: Callable[..., None]
    session_and_source: Callable[[Any], tuple[Any, Path]]
    sessions: dict[Any, Any]
    set_busy: Callable[..., None]
    set_busy_for_field: Callable[..., None]
    still_processing_message: str
    stop_session_playback: Callable[[Any], None]
    support_report_hint: str
    temp_final_path: Callable[[str], Path]
    threading: Any
    write_generated_media: Callable[[Any, str, Path], str]


class SettingsActionDeps(Protocol):
    current_field_index: Callable[[Any], int]
    current_media_path: Callable[[Any], tuple[Any, Path]]
    dispose_editor_frontend_controls: Callable[[Any], None]
    eval_status: Callable[..., None]
    is_busy: Callable[[Any], bool]
    refresh_editor_after_settings_save: Callable[..., None]
    sessions: dict[Any, Any]
    still_processing_message: str
    stop_session_playback: Callable[[Any], None]


class PlaybackDeps(Protocol):
    can_persistent_undo: Callable[..., bool]
    cleanup_temp_playback: Callable[..., None]
    config: Callable[[Any], dict[str, Any]]
    current_field_audio_missing: str
    current_field_index: Callable[[Any], int]
    eval_learner_recording_state: Callable[..., None]
    eval_playback_state: Callable[..., None]
    eval_status: Callable[..., None]
    eval_with_callback: Callable[..., None]
    format_ffmpeg_command: Callable[[tuple[str, ...]], str]
    is_busy: Callable[[Any], bool]
    main: Callable[[Any, Callable[[], None]], None]
    play_with_request: Callable[..., None]
    playback_segment_failed: Callable[..., None]
    playback_segment_ready: Callable[..., None]
    referenced_audio_missing: str
    render_playback_segment: Callable[..., Any]
    session_and_source: Callable[[Any], tuple[Any, Path]]
    sessions: dict[Any, Any]
    set_busy: Callable[..., None]
    start_playback_from_cursor: Callable[..., None]
    still_processing_message: str
    stop_audio_playback: Callable[[], None]
    stop_session_playback: Callable[[Any], None]
    threading: Any
    visualized_duration_for_field: Callable[..., int | None]


class AnalysisDeps(Protocol):
    analysis_failed: Callable[..., None]
    analysis_finished: Callable[..., None]
    analyze_prosody_cached: Callable[..., Any]
    analyze_requested_field_async: Callable[..., None]
    config: Callable[[Any], dict[str, Any]]
    current_field_audio_missing: str
    current_field_index: Callable[[Any], int]
    current_sound_reference: Callable[..., tuple[str, Path]]
    eval_status: Callable[..., None]
    eval_visualizer_status: Callable[..., None]
    eval_visualizer_status_for_field: Callable[..., None]
    eval_with_callback: Callable[..., None]
    fail_field_analysis_without_generation: Callable[..., None]
    finish_ignored_field_analysis: Callable[..., None]
    is_busy: Callable[[Any], bool]
    main: Callable[[Any, Callable[[], None]], None]
    referenced_audio_missing: str
    resolve_requested_field_media: Callable[..., Any]
    sessions: dict[Any, Any]
    set_busy_for_field: Callable[..., None]
    start_field_analysis_async: Callable[..., None]
    still_processing_message: str
    threading: Any


class RegionDeleteDeps(Protocol):
    can_persistent_undo: Callable[..., bool]
    config: Callable[[Any], dict[str, Any]]
    current_field_audio_missing: str
    current_field_index: Callable[[Any], int]
    current_media_path: Callable[[Any], tuple[Any, Path]]
    delete_selection_with_request: Callable[[Any, Any], None]
    dispose_editor_frontend_controls: Callable[[Any], None]
    eval_history_availability: Callable[..., None]
    eval_history_snapshot: Callable[..., None]
    eval_playback_state: Callable[..., None]
    eval_status: Callable[..., None]
    eval_with_callback: Callable[..., None]
    format_ffmpeg_command: Callable[[tuple[str, ...]], str]
    is_busy: Callable[[Any], bool]
    latest_persistent_undo_item: Callable[..., Any]
    main: Callable[[Any, Callable[[], None]], None]
    make_output_filename: Callable[..., str]
    persistent_undo_items: Callable[..., Any]
    record_standard_persistent_undo: Callable[..., Any]
    render_audio_region_deleted: Callable[..., Any]
    render_audio_region_kept: Callable[..., Any]
    render_failed: Callable[..., None]
    replace_current_field_after_region_delete: Callable[..., None]
    request_graph_redraw: Callable[..., None]
    request_history_availability_after_edit: Callable[..., None]
    request_history_snapshot_after_edit: Callable[..., None]
    request_playback_after_edit: Callable[..., None]
    resolve_requested_field_media: Callable[..., Any]
    sessions: dict[Any, Any]
    set_busy: Callable[..., None]
    set_busy_for_field: Callable[..., None]
    still_processing_message: str
    stop_session_playback: Callable[[Any], None]
    temp_final_path: Callable[[str], Path]
    threading: Any
    write_generated_media: Callable[[Any, str, Path], str]


class EditorReloadDeps(Protocol):
    dispose_editor_frontend_controls: Callable[[Any], None]


class EditorMediaReplacementDeps(Protocol):
    write_generated_media: Callable[[Any, str, Path], str]


class ProcessingSharedDeps(Protocol):
    can_persistent_undo: Callable[..., bool]
    config: Callable[[Any], dict[str, Any]]
    current_field_index: Callable[[Any], int]
    eval_history_availability: Callable[..., None]
    eval_history_snapshot: Callable[..., None]
    latest_persistent_undo_item: Callable[..., Any]
    persistent_undo_items: Callable[..., Any]
    request_history_availability_after_edit: Callable[..., None]
    request_history_snapshot_after_edit: Callable[..., None]
    set_busy_for_field: Callable[..., None]


class PersistentUndoDeps(Protocol):
    current_field_index: Callable[[Any], int]
    dispose_editor_frontend_controls: Callable[[Any], None]
    eval_playback_state: Callable[..., None]
    eval_status: Callable[..., None]
    request_playback_after_edit: Callable[..., None]
    stop_session_playback: Callable[[Any], None]


class ProcessingGuardDeps(Protocol):
    current_field_index: Callable[[Any], int]
