from __future__ import annotations

from pathlib import Path
from typing import Any

from aqt.sound import av_player

from anki_audio_quick_editor.audio_recording import AudioRecordingError
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.editor_recording import (
    play_learner_recording,
    record_learner_voice,
    stop_learner_recording,
)
from anki_audio_quick_editor.editor_session import (
    LearnerRecordingState,
    clear_learner_recording_state,
)
from anki_audio_quick_editor.error_codes import (
    AQE_MEDIA_REFERENCED_AUDIO_MISSING,
    AQE_RECORDING_FAILED,
)
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
    assert session.learner_recording.status == "recording"
    assert session.learner_recording.graph_settings == {"voiceRange": "high"}
    assert session.learner_recording.media_filename is not None
    assert session.learner_recording.media_filename.startswith("target__aqe_voice_")
    assert editor.note.fields == ["[sound:target.wav]"]
    assert deps.stopped == [True]
    assert deps.busy_calls == []

    stop_learner_recording(editor, deps)

    state = session.learner_recording
    assert recorder.stopped is True
    assert state.status == "ready"
    assert state.recording_duration_ms == 1500
    assert state.media_path == source_path.parent / str(state.media_filename)
    assert state.media_path.read_bytes() == b"RIFFfakeWAVE"
    assert state.prosody_payload is not None
    assert state.prosody_payload["sourceFilename"] == state.media_filename
    assert editor.note.fields == ["[sound:target.wav]"]
    assert deps.busy_calls[-1] == (0, False, "")
    assert any("__aqeSetLearnerVisualizer" in call for call in editor.web.eval_calls)


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

    assert session.learner_recording.status == "failed"
    assert session.learner_recording.failure_message == "microphone unavailable"
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

    assert session.learner_recording.status == "failed"
    assert session.learner_recording.failure_message == "recorder failed"
    assert deps.statuses[-1] == _error_status(AQE_RECORDING_FAILED, "recorder failed")


def test_stop_learner_recording_empty_file_failure_sets_failed_state(
    tmp_path: Path,
) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    recorder = _FakeRecorder(source_path, write_bytes=b"")
    deps = _deps(editor, session, source_path, recorder=recorder)

    record_learner_voice(editor, deps)
    stop_learner_recording(editor, deps)

    assert session.learner_recording.status == "failed"
    assert "empty" in str(session.learner_recording.failure_message)
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

    assert session.learner_recording.status == "failed"
    assert session.learner_recording.failure_message == "analysis failed"
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
    clear_learner_recording_state(session)
    recorder.complete()

    assert session.learner_recording.status == "idle"
    assert analyzed == []
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

    state = session.learner_recording
    assert state.status == "ready"
    assert state.media_path is not None
    assert state.media_path.parent == source_path.parent
    assert state.media_path != temp_result_path
    assert state.media_path.read_bytes() == b"RIFFfakeWAVE"


def test_play_learner_recording_reports_missing_before_ready(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    deps = _deps(editor, session, source_path)

    play_learner_recording(editor, deps)

    assert deps.statuses[-1] == _error_status(
        AQE_MEDIA_REFERENCED_AUDIO_MISSING,
        "The referenced audio file was not found in Anki's media folder.",
    )
    assert deps.stopped == []
    av_player.play_tags.assert_not_called()


def test_play_learner_recording_plays_latest_ready_media(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    learner_path = source_path.parent / "target__aqe_voice_latest.wav"
    learner_path.write_bytes(b"RIFFfakeWAVE")
    session.learner_recording = LearnerRecordingState(
        status="ready",
        field_index=0,
        generation=3,
        source_filename="target.wav",
        target_duration_ms=1000,
        media_filename=learner_path.name,
        media_path=learner_path,
    )
    deps = _deps(editor, session, source_path)

    play_learner_recording(editor, deps)

    assert deps.stopped == [True]
    assert deps.statuses[-1] == ("Playing", "info")
    av_player.play_tags.assert_called_once()
    tag = av_player.play_tags.call_args.args[0][0]
    assert tag.filename == str(learner_path)


def test_play_learner_recording_reports_missing_media_file(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    missing_path = source_path.parent / "missing_learner.wav"
    session.learner_recording = LearnerRecordingState(
        status="ready",
        field_index=0,
        generation=1,
        source_filename="target.wav",
        target_duration_ms=1000,
        media_filename=missing_path.name,
        media_path=missing_path,
    )
    deps = _deps(editor, session, source_path)

    play_learner_recording(editor, deps)

    assert deps.statuses[-1] == _error_status(
        AQE_MEDIA_REFERENCED_AUDIO_MISSING,
        "The referenced audio file was not found in Anki's media folder.",
    )
    assert deps.stopped == []
    av_player.play_tags.assert_not_called()
