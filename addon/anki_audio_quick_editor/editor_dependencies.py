"""Dependency namespace builders for editor callback modules."""

from __future__ import annotations

import threading
from types import SimpleNamespace
from typing import Any

from .audio_processor import (
    format_ffmpeg_command,
    make_output_filename,
    render_audio,
    render_audio_region_deleted,
    render_audio_region_kept,
    render_dpdfnet_audio,
    render_noise_reduced_audio,
    render_playback_segment,
    render_rnnoise_audio,
    render_voice_only_audio,
    temp_final_path,
)
from .editor_media import (
    current_field_index,
    resolve_requested_field_media,
    visualized_duration_for_field,
)
from .prosody_cache import analyze_prosody_cached
from .support import SUPPORT_REPORT_HINT


def frontend_deps(frontend_callbacks: Any) -> SimpleNamespace:
    from . import editor_runtime

    return SimpleNamespace(
        eval_with_callback=frontend_callbacks.eval_with_callback,
        graph_redraw_expression=frontend_callbacks.graph_redraw_expression,
        retry_graph_redraw=frontend_callbacks.retry_graph_redraw,
        schedule_graph_redraw_attempt=frontend_callbacks.schedule_graph_redraw_attempt,
        sessions=editor_runtime.SESSIONS,
        set_busy_for_field=frontend_callbacks.set_busy_for_field,
    )


def bridge_deps(callbacks: Any, frontend_callbacks: Any) -> SimpleNamespace:
    return SimpleNamespace(
        analyze_current_async=callbacks.analyze_current_async,
        analyze_field_from_frontend=callbacks.analyze_field_from_frontend,
        delete_selection_from_frontend=callbacks.delete_selection_from_frontend,
        denoise_standard_async=callbacks.denoise_standard_async,
        dpdfnet_async=callbacks.dpdfnet_async,
        eval_status=frontend_callbacks.eval_status,
        eval_with_callback=frontend_callbacks.eval_with_callback,
        handle_bridge_command=callbacks.handle_bridge_command,
        handle_editor_frontend_log=callbacks.handle_editor_frontend_log,
        handle_non_processing_command=callbacks.handle_non_processing_command,
        handle_pending_command_payload=callbacks.handle_pending_command_payload,
        log_editor_frontend_payload=callbacks.log_editor_frontend_payload,
        open_settings_from_editor=callbacks.open_settings_from_editor,
        play=callbacks.play,
        play_ended=callbacks.play_ended,
        redo=callbacks.redo,
        rnnoise_async=callbacks.rnnoise_async,
        set_busy=frontend_callbacks.set_busy,
        set_cursor_from_web=callbacks.set_cursor_from_web,
        show_current_audio_file=callbacks.show_current_audio_file,
        undo=callbacks.undo,
        update_state_and_render=callbacks.update_state_and_render,
        voice_only_async=callbacks.voice_only_async,
    )


def history_deps(callbacks: Any, frontend_callbacks: Any) -> SimpleNamespace:
    from . import editor_runtime

    return SimpleNamespace(
        current_field_audio_missing=editor_runtime.CURRENT_FIELD_AUDIO_MISSING,
        current_field_index=current_field_index,
        dispose_editor_frontend_controls=frontend_callbacks.dispose_editor_frontend_controls,
        eval_playback_state=frontend_callbacks.eval_playback_state,
        eval_status=frontend_callbacks.eval_status,
        is_busy=editor_runtime.is_busy,
        request_graph_redraw=frontend_callbacks.request_graph_redraw,
        restore_history_entry=callbacks.restore_history_entry,
        session_and_source=editor_runtime.session_and_source,
        still_processing_message=editor_runtime.STILL_PROCESSING_MESSAGE,
        stop_session_playback=editor_runtime.stop_session_playback,
    )


def processing_deps(callbacks: Any, frontend_callbacks: Any) -> SimpleNamespace:
    from . import editor_runtime

    return SimpleNamespace(
        artifact_root=editor_runtime.artifact_root,
        config=editor_runtime.config,
        current_field_audio_missing=editor_runtime.CURRENT_FIELD_AUDIO_MISSING,
        current_field_index=current_field_index,
        current_media_path=editor_runtime.current_media_path,
        dispose_editor_frontend_controls=frontend_callbacks.dispose_editor_frontend_controls,
        eval_playback_state=frontend_callbacks.eval_playback_state,
        eval_status=frontend_callbacks.eval_status,
        format_ffmpeg_command=format_ffmpeg_command,
        is_busy=editor_runtime.is_busy,
        log_special_transform_failure=callbacks.log_special_transform_failure,
        main=frontend_callbacks.main,
        make_output_filename=make_output_filename,
        record_dpdfnet_failure_context=callbacks.record_dpdfnet_failure_context,
        record_rnnoise_failure_context=callbacks.record_rnnoise_failure_context,
        record_spleeter_failure_context=callbacks.record_spleeter_failure_context,
        render_and_replace_async=callbacks.render_and_replace_async,
        render_audio=render_audio,
        render_failed=callbacks.render_failed,
        render_dpdfnet_audio=render_dpdfnet_audio,
        render_noise_reduced_audio=render_noise_reduced_audio,
        render_rnnoise_audio=render_rnnoise_audio,
        render_voice_only_audio=render_voice_only_audio,
        replace_current_field_after_noise_removal=callbacks.replace_current_field_after_noise_removal,
        replace_current_field_after_render=callbacks.replace_current_field_after_render,
        request_graph_redraw=frontend_callbacks.request_graph_redraw,
        run_special_audio_transform_async=callbacks.run_special_audio_transform_async,
        session_and_source=editor_runtime.session_and_source,
        sessions=editor_runtime.SESSIONS,
        set_busy=frontend_callbacks.set_busy,
        set_busy_for_field=frontend_callbacks.set_busy_for_field,
        still_processing_message=editor_runtime.STILL_PROCESSING_MESSAGE,
        stop_session_playback=editor_runtime.stop_session_playback,
        support_report_hint=SUPPORT_REPORT_HINT,
        temp_final_path=temp_final_path,
        threading=threading,
    )


def settings_action_deps(callbacks: Any, frontend_callbacks: Any) -> SimpleNamespace:
    from . import editor_runtime

    return SimpleNamespace(
        current_field_index=current_field_index,
        current_media_path=editor_runtime.current_media_path,
        dispose_editor_frontend_controls=frontend_callbacks.dispose_editor_frontend_controls,
        eval_status=frontend_callbacks.eval_status,
        is_busy=editor_runtime.is_busy,
        refresh_editor_after_settings_save=callbacks.refresh_editor_after_settings_save,
        sessions=editor_runtime.SESSIONS,
        still_processing_message=editor_runtime.STILL_PROCESSING_MESSAGE,
        stop_session_playback=editor_runtime.stop_session_playback,
    )


def playback_deps(callbacks: Any, frontend_callbacks: Any) -> SimpleNamespace:
    from . import editor_runtime

    return SimpleNamespace(
        cleanup_temp_playback=callbacks.cleanup_temp_playback,
        config=editor_runtime.config,
        current_field_index=current_field_index,
        eval_playback_state=frontend_callbacks.eval_playback_state,
        eval_status=frontend_callbacks.eval_status,
        eval_with_callback=frontend_callbacks.eval_with_callback,
        format_ffmpeg_command=format_ffmpeg_command,
        is_busy=editor_runtime.is_busy,
        main=frontend_callbacks.main,
        playback_segment_failed=callbacks.playback_segment_failed,
        playback_segment_ready=callbacks.playback_segment_ready,
        play_with_request=callbacks.play_with_request,
        render_playback_segment=render_playback_segment,
        session_and_source=editor_runtime.session_and_source,
        sessions=editor_runtime.SESSIONS,
        set_busy=frontend_callbacks.set_busy,
        start_playback_from_cursor=callbacks.start_playback_from_cursor,
        still_processing_message=editor_runtime.STILL_PROCESSING_MESSAGE,
        stop_audio_playback=callbacks.stop_audio_playback,
        stop_session_playback=editor_runtime.stop_session_playback,
        threading=threading,
        visualized_duration_for_field=visualized_duration_for_field,
    )


def analysis_deps(callbacks: Any, frontend_callbacks: Any) -> SimpleNamespace:
    from . import editor_runtime

    return SimpleNamespace(
        analysis_failed=callbacks.analysis_failed,
        analysis_finished=callbacks.analysis_finished,
        analyze_prosody_cached=analyze_prosody_cached,
        analyze_requested_field_async=callbacks.analyze_requested_field_async,
        config=editor_runtime.config,
        current_field_index=current_field_index,
        current_sound_reference=editor_runtime.current_sound_reference,
        eval_status=frontend_callbacks.eval_status,
        eval_visualizer_status=frontend_callbacks.eval_visualizer_status,
        eval_visualizer_status_for_field=frontend_callbacks.eval_visualizer_status_for_field,
        eval_with_callback=frontend_callbacks.eval_with_callback,
        fail_field_analysis_without_generation=callbacks.fail_field_analysis_without_generation,
        finish_ignored_field_analysis=callbacks.finish_ignored_field_analysis,
        is_busy=editor_runtime.is_busy,
        main=frontend_callbacks.main,
        referenced_audio_missing=editor_runtime.REFERENCED_AUDIO_MISSING,
        resolve_requested_field_media=resolve_requested_field_media,
        sessions=editor_runtime.SESSIONS,
        set_busy_for_field=frontend_callbacks.set_busy_for_field,
        start_field_analysis_async=callbacks.start_field_analysis_async,
        still_processing_message=editor_runtime.STILL_PROCESSING_MESSAGE,
        threading=threading,
    )


def region_delete_deps(callbacks: Any, frontend_callbacks: Any) -> SimpleNamespace:
    from . import editor_runtime

    return SimpleNamespace(
        config=editor_runtime.config,
        current_field_audio_missing=editor_runtime.CURRENT_FIELD_AUDIO_MISSING,
        current_field_index=current_field_index,
        current_media_path=editor_runtime.current_media_path,
        delete_selection_with_request=callbacks.delete_selection_with_request,
        dispose_editor_frontend_controls=frontend_callbacks.dispose_editor_frontend_controls,
        eval_playback_state=frontend_callbacks.eval_playback_state,
        eval_status=frontend_callbacks.eval_status,
        eval_with_callback=frontend_callbacks.eval_with_callback,
        format_ffmpeg_command=format_ffmpeg_command,
        is_busy=editor_runtime.is_busy,
        main=frontend_callbacks.main,
        make_output_filename=make_output_filename,
        render_audio_region_deleted=render_audio_region_deleted,
        render_audio_region_kept=render_audio_region_kept,
        render_failed=callbacks.render_failed,
        replace_current_field_after_region_delete=callbacks.replace_current_field_after_region_delete,
        request_graph_redraw=frontend_callbacks.request_graph_redraw,
        resolve_requested_field_media=resolve_requested_field_media,
        sessions=editor_runtime.SESSIONS,
        set_busy=frontend_callbacks.set_busy,
        set_busy_for_field=frontend_callbacks.set_busy_for_field,
        still_processing_message=editor_runtime.STILL_PROCESSING_MESSAGE,
        stop_session_playback=editor_runtime.stop_session_playback,
        temp_final_path=temp_final_path,
        threading=threading,
    )
