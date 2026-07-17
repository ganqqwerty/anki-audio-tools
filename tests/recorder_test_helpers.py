from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.recorder.model import (
    BackendMediaGeneration,
    FinalizedMedia,
    LearnerTake,
    LearnerTakeId,
    RecorderTarget,
    RecordingAttemptId,
)


def learner_take(path: Path, *, editor_session_id: int) -> LearnerTake:
    return LearnerTake(
        take_id=LearnerTakeId(2),
        attempt_id=RecordingAttemptId(2),
        origin=RecorderTarget(
            editor_session_id=editor_session_id,
            note_id=1,
            field_index=0,
            source_filename="target.wav",
            backend_media_generation=BackendMediaGeneration(1),
        ),
        finalized_media=FinalizedMedia(
            path=path,
            filename=path.name,
            format="wav",
            duration_ms=1000,
            ownership="published_media",
        ),
        timeline_anchor_ms=0,
        target_duration_ms=1000,
        analysis_payload={},
    )
