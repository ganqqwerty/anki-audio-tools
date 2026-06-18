"""Post-edit media replacement for special transforms."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .audio_state import AudioEditState
from .editor_media_replacement import (
    persist_generated_media,
    replace_first_sound_reference_in_field,
)
from .editor_processing_guard import (
    EditorProcessingGuard,
    clear_processing_for_stale_guard,
    processing_guard_matches_editor,
)
from .editor_processing_shared import (
    request_history_availability_after_edit,
    resolved_field_index,
    sync_history_availability,
)
from .editor_reload_status import reload_editor_with_pending_status
from .editor_session import EditorSession
from .media_paths import existing_media_file_path

if TYPE_CHECKING:
    from .editor_deps_protocols import ProcessingDeps


def replace_current_field_after_noise_removal(
    editor: Any,
    saved_name: str,
    deps: ProcessingDeps,
    *,
    guard: EditorProcessingGuard | None = None,
    output_path: Path | None = None,
) -> None:
    session = deps.sessions.get(editor)
    if guard is not None and not processing_guard_matches_editor(editor, session, guard, deps):
        if clear_processing_for_stale_guard(session, guard):
            deps.set_busy(editor, False)
        return
    saved_name = persist_generated_media(editor, saved_name, output_path, deps)
    field_index = resolved_field_index(session, editor, deps)
    replace_first_sound_reference_in_field(
        editor, field_index=field_index, saved_name=saved_name, missing_message=deps.current_field_audio_missing,
    )
    should_redraw_graph = _replace_noise_reduction_session_state(editor, session, field_index, saved_name)
    deps.request_playback_after_edit(
        editor,
        field_index,
        require_graph_redraw=should_redraw_graph,
    )
    reload_editor_with_pending_status(
        editor,
        session,
        field_index,
        message=session.status_summary if session is not None else "",
        deps=deps,
    )
    sync_history_availability(editor, session, deps)
    request_history_availability_after_edit(editor, session, deps)
    deps.eval_playback_state(editor, field_index, "stopped", 0)
    if should_redraw_graph:
        deps.request_graph_redraw(editor, saved_name, preserve_learner_overlay=True)
    else:
        deps.set_busy(editor, False)


def _replace_noise_reduction_session_state(
    editor: Any,
    session: EditorSession | None,
    field_index: int,
    saved_name: str,
) -> bool:
    if session is None:
        return False
    session.field_index = field_index
    saved_path = existing_media_file_path(Path(editor.mw.col.media.dir()), saved_name)
    mtime = saved_path.stat().st_mtime_ns if saved_path is not None else None
    return session.apply_edit_result(
        AudioEditState(source_file=saved_name),
        saved_name,
        session.processing.next_status_summary or session.status_summary,
        update_source_mtime=True,
        new_source_mtime=mtime,
        clear_visualization=True,
    )
