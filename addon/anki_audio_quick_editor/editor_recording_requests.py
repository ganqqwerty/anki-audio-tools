"""Request reconstruction for learner recording flows."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .editor_session import EditorSession, LearnerRecordingState
from .errors import AudioProcessingError
from .i18n import t
from .sound_refs import safe_media_basename

_FILENAME_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")

if TYPE_CHECKING:
    from .editor_deps_protocols import RecordingDeps


@dataclass(frozen=True)
class LearnerRecordingRequest:
    """Validated learner recording request for the active target graph."""

    field_index: int
    source_filename: str
    source_path: Path
    target_duration_ms: int
    output_filename: str
    output_path: Path
    start_cursor_ms: int = 0
    graph_settings: dict[str, object] | None = None


def learner_recording_request(
    editor: Any,
    session: EditorSession,
    graph_settings: dict[str, object] | None,
    start_cursor_ms: int | None,
    deps: RecordingDeps,
) -> LearnerRecordingRequest:
    """Validate that the current field still matches a target graph."""
    field_index = deps.current_field_index(editor)
    source_filename = session.visualized_filenames_by_field.get(field_index)
    target_duration_ms = session.visualized_durations_by_field.get(field_index)
    if not source_filename or target_duration_ms is None or target_duration_ms <= 0:
        raise AudioProcessingError(t("editor.status.graph_inactive"))
    resolved = deps.resolve_requested_field_media(editor, field_index, source_filename)
    if resolved is None:
        raise AudioProcessingError(t("editor.status.graph_audio_mismatch"))
    filename, source_path = resolved
    media_dir = Path(editor.mw.col.media.dir())
    generation = session.learner_recording.generation + 1
    output_filename = make_learner_recording_filename(filename, generation)
    return LearnerRecordingRequest(
        field_index=field_index,
        source_filename=filename,
        source_path=source_path,
        target_duration_ms=int(target_duration_ms),
        start_cursor_ms=_clamp_ms(start_cursor_ms, int(target_duration_ms)),
        output_filename=output_filename,
        output_path=media_dir / output_filename,
        graph_settings=graph_settings,
    )


def learner_recording_request_from_state(
    editor: Any,
    state: LearnerRecordingState,
) -> LearnerRecordingRequest | None:
    """Rebuild the active request from persisted session state."""
    if (
        state.field_index is None
        or not state.source_filename
        or not state.media_filename
        or state.media_path is None
        or state.target_duration_ms is None
    ):
        return None
    return LearnerRecordingRequest(
        field_index=state.field_index,
        source_filename=state.source_filename,
        source_path=Path(editor.mw.col.media.dir()) / state.source_filename,
        target_duration_ms=state.target_duration_ms,
        start_cursor_ms=state.start_cursor_ms,
        output_filename=state.media_filename,
        output_path=state.media_path,
        graph_settings=state.graph_settings,
    )


def make_learner_recording_filename(
    source_filename: str,
    generation: int,
    *,
    now_ns: int | None = None,
) -> str:
    """Return an add-on-owned WAV filename for a learner recording."""
    safe_name = safe_media_basename(source_filename)
    stem = _FILENAME_SAFE_RE.sub("_", Path(safe_name).stem).strip("._") or "recording"
    trimmed_stem = stem[:48]
    stamp = now_ns if now_ns is not None else time.time_ns()
    return f"{trimmed_stem}__aqe_voice_{stamp}_{generation}.wav"


def _clamp_ms(value: int | None, duration_ms: int) -> int:
    if value is None:
        return 0
    return max(0, min(int(value), max(0, int(duration_ms))))


def recording_parent(editor: Any) -> Any:
    return getattr(editor, "parentWindow", None) or getattr(editor, "widget", None) or editor.web
