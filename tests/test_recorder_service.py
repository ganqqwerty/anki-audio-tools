from __future__ import annotations

from pathlib import Path

import pytest

from anki_audio_quick_editor.recorder.model import (
    Analyzing,
    BackendMediaGeneration,
    CaptureSpec,
    Failed,
    FinalizedMedia,
    Idle,
    RecorderTarget,
    Recording,
    RecordingAttemptId,
    Starting,
    Stopping,
)
from anki_audio_quick_editor.recorder.service import (
    RecorderInvariantError,
    RecorderService,
    RecorderServiceBusyError,
)


class FakeController:
    def __init__(self) -> None:
        self.cancelled: list[str] = []
        self.disposed = 0
        self.stopped = 0
        self.on_completed = None
        self.on_failed = None

    def stop(self, *, on_completed, on_failed) -> None:
        self.stopped += 1
        self.on_completed = on_completed
        self.on_failed = on_failed

    def cancel(self, reason: str) -> None:
        self.cancelled.append(reason)

    def dispose(self) -> None:
        self.disposed += 1


def _target(owner: int) -> RecorderTarget:
    return RecorderTarget(
        editor_session_id=owner,
        note_id=10 + owner,
        field_index=0,
        source_filename="source.wav",
        backend_media_generation=BackendMediaGeneration(1),
    )


def _capture(tmp_path: Path) -> CaptureSpec:
    return CaptureSpec(
        output_filename="take.wav",
        output_path=tmp_path / "take.wav",
        target_duration_ms=1000,
        timeline_anchor_ms=0,
    )


def test_application_service_serializes_native_handle_ownership(tmp_path: Path) -> None:
    service = RecorderService()
    first = FakeController()
    service.begin(_target(1), _capture(tmp_path), first)

    with pytest.raises(RecorderServiceBusyError):
        service.begin(_target(2), _capture(tmp_path), FakeController())

    assert service.cancel_if_owner(2, "editor_closed") is False
    assert first.cancelled == []
    assert service.cancel_if_owner(1, "editor_closed") is True
    assert first.cancelled == ["editor_closed"]
    assert first.disposed == 1
    assert service.active_attempt is None


def test_service_allocates_monotonic_attempt_ids_and_rejects_busy_without_adopting_handle(tmp_path: Path) -> None:
    service = RecorderService()
    first = FakeController()
    attempt_one = service.begin(_target(1), _capture(tmp_path), first)
    rejected = FakeController()

    with pytest.raises(RecorderServiceBusyError) as error:
        service.begin(_target(2), _capture(tmp_path), rejected)

    assert str(error.value) == "Another editor already owns the microphone."
    assert rejected.cancelled == []
    assert rejected.disposed == 0
    assert service.state == Starting(attempt_one)
    assert service.cancel_if_owner(1, "retry") is True
    attempt_two = service.begin(_target(2), _capture(tmp_path), FakeController())
    assert attempt_two.attempt_id == RecordingAttemptId(2)


def test_begin_rejects_each_inconsistent_busy_resource_shape(tmp_path: Path) -> None:
    service = RecorderService()
    orphaned = FakeController()
    service._controller = orphaned  # type: ignore[attr-defined]
    with pytest.raises(RecorderServiceBusyError):
        service.begin(_target(1), _capture(tmp_path), FakeController())

    service._controller = None  # type: ignore[attr-defined]
    attempt = service.begin(_target(1), _capture(tmp_path), FakeController())
    service._controller = None  # type: ignore[attr-defined]
    assert service.state == Starting(attempt)
    with pytest.raises(RecorderServiceBusyError):
        service.begin(_target(2), _capture(tmp_path), FakeController())


def test_service_suppresses_late_and_duplicate_capture_completion(tmp_path: Path) -> None:
    service = RecorderService()
    controller = FakeController()
    attempt = service.begin(_target(1), _capture(tmp_path), controller)
    assert service.mark_started(attempt.attempt_id)
    assert service.request_stop(1) == attempt
    assert service.stop_requested(
        attempt.attempt_id,
        on_completed=lambda _result: None,
        on_failed=lambda _error: None,
    )
    assert controller.stopped == 1
    assert service.accept_capture(attempt.attempt_id, tmp_path / "capture.wav", 800)
    assert controller.disposed == 1

    assert not service.accept_capture(attempt.attempt_id, tmp_path / "late.wav", 900)
    service.cancel_if_owner(1, "source_replaced")
    assert not service.mark_started(attempt.attempt_id)


def test_service_rejects_stop_commands_unless_owner_attempt_state_and_handle_match(tmp_path: Path) -> None:
    service = RecorderService()
    controller = FakeController()
    attempt = service.begin(_target(1), _capture(tmp_path), controller)
    callbacks = {"on_completed": lambda _result: None, "on_failed": lambda _error: None}

    idle_service = RecorderService()
    assert idle_service.request_stop(1) is None
    assert service.request_stop(2) is None
    assert service.request_stop(1) is None
    assert service.stop_requested(attempt.attempt_id, **callbacks) is False
    assert service.mark_started(attempt.attempt_id) is True
    assert service.stop_requested(attempt.attempt_id, **callbacks) is False
    assert service.request_stop(1) == attempt
    assert service.stop_requested(RecordingAttemptId(99), **callbacks) is False
    owned = service._controller  # type: ignore[attr-defined]
    service._controller = None  # type: ignore[attr-defined]
    assert service.stop_requested(attempt.attempt_id, **callbacks) is False
    service._controller = owned  # type: ignore[attr-defined]
    assert service.stop_requested(attempt.attempt_id, **callbacks) is True
    assert controller.stopped == 1
    assert controller.on_completed is callbacks["on_completed"]
    assert controller.on_failed is callbacks["on_failed"]


def test_service_rejects_stale_capture_persistence_and_analysis_callbacks(tmp_path: Path) -> None:
    service = RecorderService()
    controller = FakeController()
    attempt = service.begin(_target(1), _capture(tmp_path), controller)
    stale = RecordingAttemptId(99)
    media = FinalizedMedia(
        path=tmp_path / "take.wav",
        filename="take.wav",
        format="wav",
        duration_ms=800,
        ownership="unpublished_media",
    )

    assert service.accept_capture(stale, tmp_path / "capture.wav", 800) is False
    assert service.mark_analyzing(stale, media) is False
    assert service.finish_analysis(stale, media, {}) is None
    assert service.state == Starting(attempt)
    assert controller.disposed == 0


def test_capture_completion_preserves_path_duration_and_terminal_identity(tmp_path: Path) -> None:
    service = RecorderService()
    controller = FakeController()
    attempt = service.begin(_target(1), _capture(tmp_path), controller)
    service.mark_started(attempt.attempt_id)
    service.request_stop(1)
    capture_path = tmp_path / "capture.wav"

    assert service.accept_capture(attempt.attempt_id, capture_path, 812) is True
    assert service.state.capture_path == capture_path  # type: ignore[union-attr]
    assert service.state.duration_ms == 812  # type: ignore[union-attr]
    assert attempt.attempt_id in service._capture_terminal_attempts  # type: ignore[attr-defined]


def test_finalized_take_is_separate_from_idle_recorder_state(tmp_path: Path) -> None:
    service = RecorderService()
    attempt = service.begin(_target(1), _capture(tmp_path), FakeController())
    service.mark_started(attempt.attempt_id)
    service.request_stop(1)
    service.accept_capture(attempt.attempt_id, tmp_path / "capture.wav", 800)
    media = FinalizedMedia(
        path=tmp_path / "take.wav",
        filename="take.wav",
        format="wav",
        duration_ms=800,
        ownership="unpublished_media",
    )
    assert service.mark_analyzing(attempt.attempt_id, media)
    take = service.finish_analysis(attempt.attempt_id, media, {"points": []})

    assert take is not None
    assert service.active_attempt is None
    assert service.current_take(1) == take
    assert service.is_busy is False
    assert take.take_id == 1
    assert take.attempt_id == attempt.attempt_id
    assert take.origin == attempt.target
    assert take.finalized_media == FinalizedMedia(
        path=tmp_path / "take.wav",
        filename="take.wav",
        format="wav",
        duration_ms=800,
        ownership="published_media",
    )
    assert take.timeline_anchor_ms == 0
    assert take.target_duration_ms == 1000
    assert take.analysis_payload == {"points": []}
    assert service.finish_analysis(attempt.attempt_id, media, {}) is None


def test_service_allocates_monotonic_take_ids(tmp_path: Path) -> None:
    service = RecorderService()
    take_ids = []
    for owner in (1, 2):
        attempt = service.begin(_target(owner), _capture(tmp_path), FakeController())
        service.mark_started(attempt.attempt_id)
        service.request_stop(owner)
        service.accept_capture(attempt.attempt_id, tmp_path / f"capture-{owner}.wav", 800)
        media = FinalizedMedia(
            path=tmp_path / f"take-{owner}.wav",
            filename=f"take-{owner}.wav",
            format="wav",
            duration_ms=800,
            ownership="unpublished_media",
        )
        service.mark_analyzing(attempt.attempt_id, media)
        take = service.finish_analysis(attempt.attempt_id, media, {})
        assert take is not None
        take_ids.append(take.take_id)
    assert take_ids == [1, 2]


def test_service_failure_cancels_exact_handle_and_rejects_stale_failure(tmp_path: Path) -> None:
    service = RecorderService()
    controller = FakeController()
    attempt = service.begin(_target(1), _capture(tmp_path), controller)

    assert service.fail(RecordingAttemptId(99), "late") is False
    assert controller.cancelled == []
    assert service.fail(attempt.attempt_id, "device lost") is True
    assert controller.cancelled == ["dispose"]
    assert controller.disposed == 1
    assert service.state == Failed(attempt.attempt_id, attempt.target, "device lost")
    assert service.active_attempt is None
    assert service.fail(attempt.attempt_id, "duplicate") is False


@pytest.mark.parametrize("phase", ["starting", "recording", "stopping"])
def test_owner_cancellation_cleans_handle_from_every_handle_owning_phase(
    tmp_path: Path,
    phase: str,
) -> None:
    service = RecorderService()
    controller = FakeController()
    attempt = service.begin(_target(1), _capture(tmp_path), controller)
    if phase in {"recording", "stopping"}:
        assert service.mark_started(attempt.attempt_id)
    if phase == "stopping":
        assert service.request_stop(1) == attempt

    assert service.cancel_if_owner(1, "source_replaced") is True
    assert controller.cancelled == ["source_replaced"]
    assert controller.disposed == 1
    assert service.state == Idle()
    assert service.cancel_if_owner(1, "duplicate") is False


def test_take_clear_discard_and_dispose_are_owner_scoped(tmp_path: Path) -> None:
    service = RecorderService()
    attempt = service.begin(_target(1), _capture(tmp_path), FakeController())
    service.mark_started(attempt.attempt_id)
    service.request_stop(1)
    service.accept_capture(attempt.attempt_id, tmp_path / "capture.wav", 800)
    media = FinalizedMedia(
        path=tmp_path / "take.wav",
        filename="take.wav",
        format="wav",
        duration_ms=800,
        ownership="unpublished_media",
    )
    service.mark_analyzing(attempt.attempt_id, media)
    service.finish_analysis(attempt.attempt_id, media, {})
    assert service.current_take(1) is not None

    service.clear_owner(2, "other_editor_closed")
    assert service.current_take(1) is not None
    service.clear_owner(1, "editor_closed")
    assert service.current_take(1) is None
    service.discard_take(999)

    active_controller = FakeController()
    service.begin(_target(1), _capture(tmp_path), active_controller)
    service.clear_owner(1, "editor_closed")
    assert active_controller.cancelled == ["editor_closed"]
    assert active_controller.disposed == 1

    active_controller = FakeController()
    service.begin(_target(1), _capture(tmp_path), active_controller)
    service.dispose("addon_unload")
    assert active_controller.cancelled == ["addon_unload"]
    assert active_controller.disposed == 1
    assert service.state == Idle()


def test_dispose_cleans_an_orphaned_controller_and_resets_state(tmp_path: Path) -> None:
    service = RecorderService()
    controller = FakeController()
    service._controller = controller  # type: ignore[attr-defined]

    service.dispose("addon_unload")

    assert controller.cancelled == ["addon_unload"]
    assert controller.disposed == 1
    assert service.state == Idle()


def test_resource_validator_detects_handle_state_mismatch(tmp_path: Path) -> None:
    service = RecorderService()
    assert service.validate_resources() == ()
    service._controller = FakeController()  # type: ignore[attr-defined]
    assert [violation.invariant_id for violation in service.validate_resources()] == ["R-01"]


def test_resource_validator_detects_missing_handle_for_each_owning_state(tmp_path: Path) -> None:
    service = RecorderService()
    attempt = service.begin(_target(1), _capture(tmp_path), FakeController())
    for state in (Starting(attempt), Recording(attempt), Stopping(attempt)):
        service.state = state
        service._controller = None  # type: ignore[attr-defined]
        violations = service.validate_resources()
        assert [(item.invariant_id, item.message) for item in violations] == [
            ("R-01", "native recorder handle does not match recorder state")
        ]


def test_assert_valid_cancels_owned_handle_and_fails_closed(tmp_path: Path) -> None:
    service = RecorderService()
    controller = FakeController()
    attempt = service.begin(_target(1), _capture(tmp_path), controller)
    service.state = Analyzing(
        attempt,
        FinalizedMedia(tmp_path / "take.wav", "take.wav", "wav", 0, "unpublished_media"),
    )

    with pytest.raises(RecorderInvariantError, match="R-04.*R-01"):
        service._assert_valid()  # type: ignore[attr-defined]

    assert controller.cancelled == ["dispose"]
    assert controller.disposed == 1
    assert service.state == Idle()
