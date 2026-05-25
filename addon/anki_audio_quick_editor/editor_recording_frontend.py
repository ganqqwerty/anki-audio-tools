"""Frontend publication helpers for learner recording state."""

from __future__ import annotations

import json
from typing import Any

from .contracts_generated import ProsodyPayload
from .editor_session import LearnerRecordingState
from .prosody_types import ProsodyTrack


def learner_prosody_payload(track: ProsodyTrack) -> dict[str, object]:
    """Return the frontend-safe learner prosody payload."""
    return ProsodyPayload.from_dict(track.to_payload()).to_dict()


def eval_learner_recording_state(editor: Any, state: LearnerRecordingState) -> None:
    """Publish learner recording state to the frontend if it has installed a handler."""
    payload = {
        "status": state.status,
        "fieldOrd": state.field_index,
        "generation": state.generation,
        "targetDurationMs": state.target_duration_ms,
        "mediaFilename": state.media_filename,
        "recordingDurationMs": state.recording_duration_ms,
        "failureMessage": state.failure_message,
    }
    editor.web.eval(
        "window.__aqeSetLearnerRecordingState && window.__aqeSetLearnerRecordingState("
        f"{json.dumps(payload)})"
    )


def eval_learner_visualizer(editor: Any, field_index: int, payload: dict[str, object]) -> None:
    """Publish learner pitch data to the frontend overlay renderer."""
    editor.web.eval(
        "window.__aqeSetLearnerVisualizer && window.__aqeSetLearnerVisualizer("
        f"{json.dumps(int(field_index))}, {json.dumps(payload)})"
    )
