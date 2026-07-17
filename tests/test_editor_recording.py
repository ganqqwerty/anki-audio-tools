from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from anki_audio_quick_editor.audio_recording import AudioRecordingError, RecordingResult
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.editor_recording import (
    persist_learner_recording,
    record_learner_voice,
    stop_learner_recording,
)
from anki_audio_quick_editor.editor_session import (
    clear_recorder_projection,
)
from anki_audio_quick_editor.error_codes import AQE_RECORDING_FAILED
from anki_audio_quick_editor.errors import AudioProcessingError
from anki_audio_quick_editor.prosody_settings import config_with_graph_settings
from anki_audio_quick_editor.prosody_types import ProsodyPoint, build_prosody_track
from tests.editor_recording_helpers import _deps, _editor_with_target, _FakeRecorder


def _error_status(code: str, message: str) -> tuple[dict[str, str], str]:
    return ({"code": code, "message": message}, "error")


def test_record_and_explicit_stop_persists_media_and_sets_visualizer(
    tmp_path: Path,
) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    recorder = _FakeRecorder(source_path)
    deps = _deps(editor, session, source_path, recorder=recorder)

    record_learner_voice(editor, deps, graph_settings={"voiceRange": "high"})

    assert recorder.started is True
    assert recorder.stopped is False
    assert session.recorder.status == "recording"
    attempt = deps.recorder_service.active_attempt
    assert attempt is not None
    assert attempt.capture.graph_settings == {"voiceRange": "high"}
    assert attempt.capture.output_filename.startswith("target__aqe_voice_")
    assert editor.note.fields == ["[sound:target.wav]"]
    assert deps.busy_calls == []

    stop_learner_recording(editor, deps)

    take = session.learner_take
    assert recorder.stopped is True
    assert session.recorder.status == "idle"
    assert take is not None
    assert take.finalized_media.duration_ms == 1500
    assert take.finalized_media.path == source_path.parent / take.finalized_media.filename
    assert take.finalized_media.path.read_bytes() == b"RIFFfakeWAVE"
    assert take.analysis_payload["sourceFilename"] == take.finalized_media.filename
    assert editor.note.fields == ["[sound:target.wav]"]
    assert deps.busy_calls[-1] == (0, False, "")
    assert any("__aqeSetLearnerVisualizer" in call for call in editor.web.eval_calls)


def test_record_learner_voice_clamps_start_cursor_to_target_duration(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    deps = _deps(editor, session, source_path)

    record_learner_voice(editor, deps, start_cursor_ms=2500)

    assert session.recorder.start_cursor_ms == 1000
    assert any('"startCursorMs": 1000' in call for call in editor.web.eval_calls)


def test_record_learner_voice_uses_graph_settings_for_analysis_config(
    tmp_path: Path,
) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    captured: dict[str, AudioProcessingConfig] = {}

    def analyzer(media_path: Path, config: AudioProcessingConfig) -> Any:
        captured["config"] = config
        return build_prosody_track(
            duration_ms=1000,
            points=[
                ProsodyPoint(
                    time_ms=0,
                    pitch_hz=180.0,
                    intensity_db=-20.0,
                    intensity_norm=0.0,
                    voiced=True,
                )
            ],
            source_filename=media_path.name,
            analyzer_name="fake",
        )

    deps = _deps(editor, session, source_path, analyzer=analyzer)

    record_learner_voice(editor, deps, graph_settings={"voiceRange": "high"})
    stop_learner_recording(editor, deps)

    expected = config_with_graph_settings(AudioProcessingConfig(), {"voiceRange": "high"})
    assert captured["config"].graph_voice_range == expected.graph_voice_range


def test_record_learner_voice_start_failure_sets_failed_state(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    recorder = _FakeRecorder(
        source_path,
        start_error=AudioRecordingError("microphone unavailable"),
    )
    deps = _deps(editor, session, source_path, recorder=recorder)

    record_learner_voice(editor, deps)

    assert session.recorder.status == "failed"
    assert session.recorder.failure_message == "microphone unavailable"
    assert deps.statuses[-1] == _error_status(AQE_RECORDING_FAILED, "microphone unavailable")


def test_stop_learner_recording_failure_sets_failed_state(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    recorder = _FakeRecorder(
        source_path,
        stop_error=AudioRecordingError("recorder failed"),
    )
    deps = _deps(editor, session, source_path, recorder=recorder)

    record_learner_voice(editor, deps)
    stop_learner_recording(editor, deps)

    assert session.recorder.status == "failed"
    assert session.recorder.failure_message == "recorder failed"
    assert deps.statuses[-1] == _error_status(AQE_RECORDING_FAILED, "recorder failed")


def test_stop_learner_recording_empty_file_failure_sets_failed_state(
    tmp_path: Path,
) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    recorder = _FakeRecorder(source_path, write_bytes=b"")
    deps = _deps(editor, session, source_path, recorder=recorder)

    record_learner_voice(editor, deps)
    stop_learner_recording(editor, deps)

    assert session.recorder.status == "failed"
    assert "empty" in str(session.recorder.failure_message)
    assert not any("__aqeSetLearnerVisualizer" in call for call in editor.web.eval_calls)


def test_stop_learner_recording_analysis_failure_sets_failed_state(
    tmp_path: Path,
) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)

    def analyzer(_media_path: Path, _config: AudioProcessingConfig) -> Any:
        raise AudioProcessingError("analysis failed")

    deps = _deps(editor, session, source_path, analyzer=analyzer)

    record_learner_voice(editor, deps)
    stop_learner_recording(editor, deps)

    assert session.recorder.status == "failed"
    assert session.recorder.failure_message == "analysis failed"
    assert not any("__aqeSetLearnerVisualizer" in call for call in editor.web.eval_calls)


def test_stop_learner_recording_ignores_stale_completion(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    recorder = _FakeRecorder(source_path, complete_on_stop=False)
    analyzed: list[Path] = []

    def analyzer(media_path: Path, _config: AudioProcessingConfig) -> Any:
        analyzed.append(media_path)
        return build_prosody_track(
            duration_ms=1000,
            points=[],
            source_filename=media_path.name,
            analyzer_name="fake",
        )

    deps = _deps(editor, session, source_path, recorder=recorder, analyzer=analyzer)

    record_learner_voice(editor, deps)
    stop_learner_recording(editor, deps)
    deps.recorder_service.clear_owner(session.editor_session_id, "replaced")
    clear_recorder_projection(session)
    recorder.complete()

    assert session.recorder.status == "idle"
    assert analyzed == []
    assert not any("__aqeSetLearnerVisualizer" in call for call in editor.web.eval_calls)


def test_late_analysis_cannot_publish_and_cleans_unpublished_media(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    callbacks: list[Any] = []

    class DeferredThread:
        def __init__(self, *, target: Any, daemon: bool) -> None:
            del daemon
            callbacks.append(target)

        def start(self) -> None:
            pass

    deps = _deps(editor, session, source_path)
    deps.threading = type("Threading", (), {"Thread": DeferredThread})

    record_learner_voice(editor, deps)
    stop_learner_recording(editor, deps)
    attempt = deps.recorder_service.active_attempt
    assert attempt is not None
    unpublished_path = attempt.capture.output_path
    assert unpublished_path.is_file()

    deps.recorder_service.clear_owner(session.editor_session_id, "note_changed")
    clear_recorder_projection(session)
    callbacks[0]()

    assert session.learner_take is None
    assert not unpublished_path.exists()
    assert not any("__aqeSetLearnerVisualizer" in call for call in editor.web.eval_calls)


def test_stop_learner_recording_copies_temp_result_into_generated_media_file(
    tmp_path: Path,
) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    temp_result_path = tmp_path / "temp" / "capture.wav"
    recorder = _FakeRecorder(source_path, result_path=temp_result_path)
    deps = _deps(editor, session, source_path, recorder=recorder)

    record_learner_voice(editor, deps)
    stop_learner_recording(editor, deps)

    take = session.learner_take
    assert take is not None
    assert take.finalized_media.path.parent == source_path.parent
    assert take.finalized_media.path != temp_result_path
    assert take.finalized_media.path.read_bytes() == b"RIFFfakeWAVE"


def test_persist_learner_recording_copies_temp_result_without_reading_into_memory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_path = tmp_path / "temp" / "capture.wav"
    source_path.parent.mkdir()
    source_path.write_bytes(b"RIFFfakeWAVE")
    output_path = tmp_path / "media" / "target__aqe_voice.wav"
    copied: list[tuple[Path, Path]] = []

    def copyfile(src: Path, dst: Path) -> None:
        copied.append((src, dst))
        dst.write_bytes(src.read_bytes())

    monkeypatch.setattr("anki_audio_quick_editor.editor_recording.shutil.copyfile", copyfile)

    result = persist_learner_recording(
        RecordingResult(path=source_path, generation=1),
        output_path,
    )

    assert result == output_path
    assert copied == [(source_path, output_path)]
    assert output_path.read_bytes() == b"RIFFfakeWAVE"


def test_ready_learner_recording_state_publishes_media_filename_without_absolute_path(
    tmp_path: Path,
) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    deps = _deps(editor, session, source_path)

    record_learner_voice(editor, deps)
    stop_learner_recording(editor, deps)

    take = session.learner_take
    payload = _last_learner_recording_payload(editor)
    assert take is not None
    assert payload["status"] == "ready"
    assert payload["mediaFilename"] == take.finalized_media.filename
    assert payload["recordingDurationMs"] == 1500
    assert payload["targetDurationMs"] == 1000
    assert payload["attemptId"] == int(take.attempt_id)
    assert payload["schemaVersion"] == 1
    assert "playbackStatus" not in payload
    assert str(source_path.parent) not in json.dumps(payload)


def test_missing_completed_recording_media_publishes_failed_state(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    recorder = _FakeRecorder(source_path, write_bytes=None)
    deps = _deps(editor, session, source_path, recorder=recorder)

    record_learner_voice(editor, deps)
    stop_learner_recording(editor, deps)

    payload = _last_learner_recording_payload(editor)
    assert session.recorder.status == "failed"
    assert payload["status"] == "failed"
    assert payload["failureMessage"]
    assert payload["schemaVersion"] == 1
    assert "playbackStatus" not in payload
    assert str(source_path.parent) not in json.dumps(payload)


def _last_learner_recording_payload(editor: Any) -> dict[str, Any]:
    calls = [
        call
        for call in editor.web.eval_calls
        if "__aqeSetLearnerRecordingState" in call
    ]
    if not calls:
        raise AssertionError("expected learner recording state publication")
    raw_payload = calls[-1].split("__aqeSetLearnerRecordingState(", 1)[1].rsplit(")", 1)[0]
    return json.loads(raw_payload)
