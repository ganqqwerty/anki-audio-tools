from __future__ import annotations

from pathlib import Path

import pytest

from anki_audio_quick_editor.recorder.model import (
    AnalysisCompleted,
    Analyzing,
    BackendMediaGeneration,
    CancelRequested,
    CaptureCompleted,
    CaptureSpec,
    Failed,
    FinalizedMedia,
    Finalizing,
    Idle,
    PersistenceCompleted,
    RecorderEffect,
    RecorderFailure,
    RecorderTarget,
    RecorderTransition,
    Recording,
    RecordingAttempt,
    RecordingAttemptId,
    Started,
    Starting,
    StartRequested,
    Stopping,
    StopRequested,
    _analysis_transition,
    _cancel_transition,
    _effect,
    _matches,
    _persistence_transition,
    _terminal_effects,
    reduce_recorder,
)
from anki_audio_quick_editor.recorder.validation import (
    RecorderViolation,
    validate_recorder_state,
)


def _attempt(tmp_path: Path) -> RecordingAttempt:
    return RecordingAttempt(
        attempt_id=RecordingAttemptId(1),
        target=RecorderTarget(
            editor_session_id=1,
            note_id=2,
            field_index=0,
            source_filename="source.wav",
            backend_media_generation=BackendMediaGeneration(3),
        ),
        capture=CaptureSpec(
            output_filename="take.wav",
            output_path=tmp_path / "take.wav",
            target_duration_ms=1000,
            timeline_anchor_ms=250,
        ),
    )


def test_recorder_reducer_covers_capture_lifecycle(tmp_path: Path) -> None:
    attempt = _attempt(tmp_path)
    starting = reduce_recorder(Idle(), StartRequested(attempt))
    assert starting == RecorderTransition(
        Starting(attempt),
        (_effect("start_capture", attempt.attempt_id), _effect("publish")),
    )

    recording = reduce_recorder(starting.state, Started(attempt.attempt_id))
    assert recording == RecorderTransition(Recording(attempt), (_effect("publish"),))

    stopping = reduce_recorder(recording.state, StopRequested())
    assert stopping == RecorderTransition(
        Stopping(attempt),
        (_effect("stop_capture", attempt.attempt_id), _effect("publish")),
    )

    finalizing = reduce_recorder(
        stopping.state,
        CaptureCompleted(attempt.attempt_id, tmp_path / "capture.wav", 875),
    )
    assert finalizing == RecorderTransition(
        Finalizing(attempt, tmp_path / "capture.wav", 875),
        (
            _effect("dispose_capture", attempt.attempt_id),
            _effect("persist", attempt.attempt_id),
            _effect("publish"),
        ),
    )


def test_recorder_reducer_covers_persistence_and_analysis_lifecycle(tmp_path: Path) -> None:
    attempt = _attempt(tmp_path)
    capture_path = tmp_path / "capture.wav"
    media = FinalizedMedia(
        path=tmp_path / "take.wav",
        filename="take.wav",
        format="wav",
        duration_ms=875,
        ownership="unpublished_media",
    )
    finalizing = Finalizing(attempt, capture_path, 875)

    persisted = reduce_recorder(finalizing, PersistenceCompleted(attempt.attempt_id, media))
    assert persisted.state == Analyzing(attempt, media)
    assert persisted.effects == (
        _effect("analyze", attempt.attempt_id),
        _effect("publish"),
    )

    analyzed = reduce_recorder(persisted.state, AnalysisCompleted(attempt.attempt_id))
    assert analyzed.state == Idle()
    assert analyzed.effects == (
        _effect("store_take", attempt.attempt_id),
        _effect("publish"),
    )

    stale_id = RecordingAttemptId(99)
    assert _persistence_transition(finalizing, PersistenceCompleted(stale_id, media)).state == finalizing
    assert _analysis_transition(persisted.state, AnalysisCompleted(stale_id)).state == persisted.state


@pytest.mark.parametrize(
    ("state_factory", "expected_effects"),
    [
        (Starting, ("cancel_capture", "dispose_capture", "publish")),
        (Recording, ("cancel_capture", "dispose_capture", "publish")),
        (Stopping, ("cancel_capture", "dispose_capture", "publish")),
        (
            lambda attempt: Finalizing(attempt, attempt.capture.output_path, 800),
            ("cleanup_unpublished", "publish"),
        ),
        (
            lambda attempt: Analyzing(
                attempt,
                FinalizedMedia(
                    path=attempt.capture.output_path,
                    filename=attempt.capture.output_filename,
                    format="wav",
                    duration_ms=800,
                    ownership="unpublished_media",
                ),
            ),
            ("cleanup_unpublished", "publish"),
        ),
    ],
)
def test_recorder_cancel_effects_are_phase_specific(
    tmp_path: Path,
    state_factory: object,
    expected_effects: tuple[str, ...],
) -> None:
    attempt = _attempt(tmp_path)
    state = state_factory(attempt)  # type: ignore[operator]

    transition = reduce_recorder(state, CancelRequested("source_replaced"))

    assert transition.state == Idle()
    assert tuple(effect.type for effect in transition.effects) == expected_effects
    if transition.effects[0].type == "cancel_capture":
        assert transition.effects[0].reason == "source_replaced"


def test_terminal_helper_matches_phase_and_preserves_identity(tmp_path: Path) -> None:
    attempt = _attempt(tmp_path)
    active = Starting(attempt)
    stale_id = RecordingAttemptId(99)

    assert _matches(active, attempt.attempt_id) is True
    assert _matches(active, stale_id) is False
    assert _matches(Idle(), attempt.attempt_id) is False
    assert _terminal_effects(active, attempt.attempt_id, "user") == (
        RecorderEffect("cancel_capture", attempt.attempt_id, "user"),
        RecorderEffect("dispose_capture", attempt.attempt_id),
    )
    finalizing = Finalizing(attempt, tmp_path / "capture.wav", 800)
    assert _terminal_effects(finalizing, attempt.attempt_id) == (
        RecorderEffect("cleanup_unpublished", attempt.attempt_id),
    )
    assert _cancel_transition(finalizing, CancelRequested("user")) == RecorderTransition(
        Idle(),
        (
            RecorderEffect("cleanup_unpublished", attempt.attempt_id),
            RecorderEffect("publish"),
        ),
    )
    assert _terminal_effects(Idle(), attempt.attempt_id) == ()


@pytest.mark.parametrize("state_factory", [Recording, Stopping])
def test_recorder_cancel_from_active_phase_is_terminal_and_disposes(
    tmp_path: Path,
    state_factory: object,
) -> None:
    attempt = _attempt(tmp_path)
    transition = reduce_recorder(state_factory(attempt), CancelRequested("user"))  # type: ignore[operator]
    assert transition.state == Idle()
    assert [effect.type for effect in transition.effects] == ["cancel_capture", "dispose_capture", "publish"]


def test_recorder_rejects_stale_and_duplicate_terminal_facts(tmp_path: Path) -> None:
    attempt = _attempt(tmp_path)
    state = Stopping(attempt)
    stale = reduce_recorder(
        state,
        CaptureCompleted(RecordingAttemptId(99), tmp_path / "stale.wav", 100),
    )
    assert stale.state == state
    assert stale.effects == ()

    failed = reduce_recorder(state, RecorderFailure(attempt.attempt_id, "device lost"))
    assert failed.state == Failed(attempt.attempt_id, attempt.target, "device lost")
    duplicate = reduce_recorder(
        failed.state,
        CaptureCompleted(attempt.attempt_id, tmp_path / "late.wav", 100),
    )
    assert duplicate.state == failed.state
    assert duplicate.effects == ()


@pytest.mark.parametrize("state_factory", [Idle, Starting, Recording, Stopping, Finalizing, Analyzing, Failed])
def test_recorder_rejects_facts_that_do_not_apply_to_the_current_phase(
    tmp_path: Path,
    state_factory: object,
) -> None:
    attempt = _attempt(tmp_path)
    media = FinalizedMedia(
        path=tmp_path / "take.wav",
        filename="take.wav",
        format="wav",
        duration_ms=800,
        ownership="unpublished_media",
    )
    if state_factory is Idle:
        state = Idle()
    elif state_factory is Finalizing:
        state = Finalizing(attempt, tmp_path / "capture.wav", 800)
    elif state_factory is Analyzing:
        state = Analyzing(attempt, media)
    elif state_factory is Failed:
        state = Failed(attempt.attempt_id, attempt.target, "failed")
    else:
        state = state_factory(attempt)  # type: ignore[operator]

    stale = RecordingAttemptId(99)
    facts = (
        Started(stale),
        CaptureCompleted(stale, tmp_path / "stale.wav", 100),
        PersistenceCompleted(stale, media),
        AnalysisCompleted(stale),
        RecorderFailure(stale, "late"),
    )
    for fact in facts:
        assert reduce_recorder(state, fact) == RecorderTransition(state)
    if not isinstance(state, Recording):
        assert reduce_recorder(state, StopRequested()) == RecorderTransition(state)


def test_failure_cleanup_depends_on_phase_and_retains_target(tmp_path: Path) -> None:
    attempt = _attempt(tmp_path)
    media = FinalizedMedia(
        path=tmp_path / "take.wav",
        filename="take.wav",
        format="wav",
        duration_ms=800,
        ownership="unpublished_media",
    )
    cases = (
        (Starting(attempt), ("cancel_capture", "dispose_capture", "publish")),
        (Finalizing(attempt, tmp_path / "capture.wav", 800), ("cleanup_unpublished", "publish")),
        (Analyzing(attempt, media), ("cleanup_unpublished", "publish")),
    )
    for state, effect_types in cases:
        transition = reduce_recorder(state, RecorderFailure(attempt.attempt_id, "device lost"))
        assert transition.state == Failed(attempt.attempt_id, attempt.target, "device lost")
        assert tuple(effect.type for effect in transition.effects) == effect_types
        for effect in transition.effects[:-1]:
            assert effect.attempt_id == attempt.attempt_id


def test_recorder_validator_rejects_invalid_finalized_media(tmp_path: Path) -> None:
    attempt = _attempt(tmp_path)
    state = Analyzing(
        attempt,
        FinalizedMedia(
            path=tmp_path / "take.wav",
            filename="take.wav",
            format="wav",
            duration_ms=0,
            ownership="published_media",
        ),
    )
    assert [violation.invariant_id for violation in validate_recorder_state(state)] == ["R-04"]


@pytest.mark.parametrize(
    "media",
    [
        FinalizedMedia(Path("take.wav"), "take.wav", "wav", 0, "published_media"),
        FinalizedMedia(Path("take.wav"), "", "wav", 1, "published_media"),
        FinalizedMedia(Path("take.wav"), "take.wav", "", 1, "published_media"),
        FinalizedMedia(Path("other.wav"), "take.wav", "wav", 1, "published_media"),
    ],
)
def test_recorder_validator_checks_every_finalized_media_field(tmp_path: Path, media: FinalizedMedia) -> None:
    assert validate_recorder_state(Analyzing(_attempt(tmp_path), media)) == (
        RecorderViolation("R-04", "finalized learner media is incomplete"),
    )


@pytest.mark.parametrize(
    ("duration_ms", "anchor_ms"),
    [(0, 0), (-1, 0), (1, -1)],
)
def test_recorder_validator_rejects_invalid_capture_coordinates(
    tmp_path: Path,
    duration_ms: int,
    anchor_ms: int,
) -> None:
    attempt = _attempt(tmp_path)
    invalid = RecordingAttempt(
        attempt.attempt_id,
        attempt.target,
        CaptureSpec(
            output_filename="take.wav",
            output_path=tmp_path / "take.wav",
            target_duration_ms=duration_ms,
            timeline_anchor_ms=anchor_ms,
        ),
    )
    assert validate_recorder_state(Starting(invalid)) == (
        RecorderViolation("R-01", "recording attempt has invalid capture coordinates"),
    )


def test_recorder_validator_accepts_valid_idle_active_and_media_states(tmp_path: Path) -> None:
    attempt = _attempt(tmp_path)
    media = FinalizedMedia(
        path=tmp_path / "take.wav",
        filename="take.wav",
        format="wav",
        duration_ms=1,
        ownership="published_media",
    )
    assert validate_recorder_state(Idle()) == ()
    assert validate_recorder_state(Starting(attempt)) == ()
    assert validate_recorder_state(Analyzing(attempt, media)) == ()
    boundary_attempt = RecordingAttempt(
        attempt.attempt_id,
        attempt.target,
        CaptureSpec("take.wav", tmp_path / "take.wav", 1, 0),
    )
    assert validate_recorder_state(Starting(boundary_attempt)) == ()
