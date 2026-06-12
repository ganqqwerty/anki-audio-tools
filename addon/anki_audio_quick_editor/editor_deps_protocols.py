"""Typed dependency contracts for editor workflow modules."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol


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
    persistent_undo_items: Callable[..., Any]
    main: Callable[[Any, Callable[[], None]], None]
    make_output_filename: Callable[..., str]
    render_audio_region_deleted: Callable[..., Any]
    render_audio_region_kept: Callable[..., Any]
    render_failed: Callable[..., None]
    replace_current_field_after_region_delete: Callable[..., None]
    request_history_availability_after_edit: Callable[..., None]
    request_history_snapshot_after_edit: Callable[..., None]
    request_playback_after_edit: Callable[..., None]
    request_graph_redraw: Callable[..., None]
    resolve_requested_field_media: Callable[..., Any]
    sessions: dict[Any, Any]
    set_busy: Callable[..., None]
    set_busy_for_field: Callable[..., None]
    still_processing_message: str
    stop_session_playback: Callable[[Any], None]
    temp_final_path: Callable[[str], Path]
    threading: Any
    write_generated_media: Callable[[Any, str, Path], str]
