"""Frontend publication helpers for recorder projections and learner takes."""

from __future__ import annotations

import json
from typing import Any

from .contracts_generated import ProsodyPayload, RecorderSnapshot, Status
from .editor_recording_state import RecorderProjection
from .prosody_types import ProsodyTrack
from .recorder.model import LearnerTake


def learner_prosody_payload(track: ProsodyTrack) -> dict[str, object]:
    """Return the frontend-safe learner prosody payload."""
    return ProsodyPayload.from_dict(track.to_payload()).to_dict()


def eval_learner_recording_state(
    editor: Any,
    state: RecorderProjection,
    take: LearnerTake | None = None,
) -> None:
    """Publish a service projection plus the independent finalized take."""
    ready_take = take if state.status == "idle" else None
    snapshot = RecorderSnapshot(
        schema_version=1,
        start_cursor_ms=ready_take.timeline_anchor_ms if ready_take else state.start_cursor_ms,
        status=Status.READY if ready_take else Status(state.status),
        attempt_id=int(ready_take.attempt_id) if ready_take else state.attempt_id,
        failure_message=state.failure_message,
        field_ord=ready_take.origin.field_index if ready_take else state.field_index,
        media_filename=ready_take.finalized_media.filename if ready_take else None,
        recording_duration_ms=ready_take.finalized_media.duration_ms if ready_take else None,
        target_duration_ms=ready_take.target_duration_ms if ready_take else state.target_duration_ms,
    )
    editor.web.eval(
        "window.__aqeSetLearnerRecordingState && window.__aqeSetLearnerRecordingState("
        f"{json.dumps(snapshot.to_dict())})"
    )


def eval_learner_visualizer(editor: Any, field_index: int, payload: dict[str, object]) -> None:
    """Publish learner pitch data to the frontend overlay renderer."""
    editor.web.eval(
        "window.__aqeSetLearnerVisualizer && window.__aqeSetLearnerVisualizer("
        f"{json.dumps(int(field_index))}, {json.dumps(payload)})"
    )
