from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from aqt.sound import av_player

from anki_audio_quick_editor.audio_recording import AudioRecordingError, RecordingResult
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.editor_recording import (
    play_learner_recording,
    record_learner_voice,
)
from anki_audio_quick_editor.editor_runtime import is_busy
from anki_audio_quick_editor.editor_session import (
    EditorSession,
    LearnerRecordingState,
    clear_learner_recording_state,
)
from anki_audio_quick_editor.errors import AudioProcessingError
from anki_audio_quick_editor.prosody_settings import config_with_graph_settings
from anki_audio_quick_editor.prosody_types import ProsodyPoint, build_prosody_track


class _Web:
    def __init__(self) -> None:
        self.eval_calls: list[str] = []

    def eval(self, script: str) -> None:
        self.eval_calls.append(script)


class _ImmediateThread:
    def __init__(self, target: Callable[[], None], daemon: bool = False) -> None:
        del daemon
        self._target = target

    def start(self) -> None:
        self._target()


class _FakeRecorder:
    def __init__(
        self,
        output_path: Path,
        *,
        start_error: AudioRecordingError | None = None,
        stop_error: AudioRecordingError | None = None,
        write_bytes: bytes | None = b"RIFFfakeWAVE",
        complete_on_stop: bool = True,
        result_path: Path | None = None,
    ) -> None:
        self.output_path = output_path
        self.start_error = start_error
        self.stop_error = stop_error
        self.write_bytes = write_bytes
        self.complete_on_stop = complete_on_stop
        self.result_path = result_path
        self.generation: int | None = None
        self._on_completed: Callable[[RecordingResult], None] | None = None

    def start(
        self,
        generation: int,
        *,
        on_started: Callable[[int], None],
        on_failed: Callable[[AudioRecordingError], None],
    ) -> None:
        self.generation = generation
        if self.start_error is not None:
            on_failed(self.start_error)
            return
        on_started(generation)

    def stop(
        self,
        *,
        on_completed: Callable[[RecordingResult], None],
        on_failed: Callable[[AudioRecordingError], None],
    ) -> None:
        if self.stop_error is not None:
            on_failed(self.stop_error)
            return
        self._on_completed = on_completed
        if self.complete_on_stop:
            self.complete()

    def complete(self) -> None:
        if self.generation is None or self._on_completed is None:
            raise AssertionError("fake recorder has not been stopped")
        result_path = self.result_path or self.output_path
        if self.write_bytes is not None:
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_bytes(self.write_bytes)
        self._on_completed(RecordingResult(path=result_path, generation=self.generation))


def _editor_with_target(tmp_path: Path) -> tuple[Any, EditorSession, Path]:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    target_path = media_dir / "target.wav"
    target_path.write_bytes(b"target")

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:target.wav]"])
    editor.web = _Web()
    editor.mw = SimpleNamespace(
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
        taskman=SimpleNamespace(run_on_main=lambda callback: callback()),
    )
    session = EditorSession(
        field_index=0,
        current_filename="target.wav",
        visualized_filename="target.wav",
        visualized_duration_ms=1000,
        visualized_filenames_by_field={0: "target.wav"},
        visualized_durations_by_field={0: 1000},
    )
    return editor, session, target_path


def _deps(
    editor: Any,
    session: EditorSession,
    source_path: Path,
    *,
    recorder: _FakeRecorder | None = None,
    recorder_factory: Callable[[Path, Any, Any], _FakeRecorder] | None = None,
    analyzer: Callable[[Path, AudioProcessingConfig], Any] | None = None,
    schedule_timer: Callable[[int, Callable[[], None]], None] | None = None,
) -> SimpleNamespace:
    statuses: list[tuple[str, str]] = []
    busy_calls: list[tuple[int, bool, str]] = []
    stopped: list[bool] = []
    timers: list[int] = []

    def default_factory(output_path: Path, _mw: Any, _parent: Any) -> _FakeRecorder:
        if recorder is not None:
            recorder.output_path = output_path
            return recorder
        return _FakeRecorder(output_path)

    def default_analyzer(media_path: Path, _config: AudioProcessingConfig) -> Any:
        return build_prosody_track(
            duration_ms=1000,
            points=[ProsodyPoint(time_ms=0, pitch_hz=180.0, intensity_db=-20.0, intensity_norm=0.0, voiced=True)],
            source_filename=media_path.name,
            analyzer_name="fake",
        )

    def default_timer(delay_ms: int, callback: Callable[[], None]) -> None:
        timers.append(delay_ms)
        callback()

    return SimpleNamespace(
        analyze_prosody_cached=analyzer or default_analyzer,
        config=lambda _editor: {},
        current_field_index=lambda _editor: int(editor.currentField),
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        is_busy=is_busy,
        main=lambda _editor, callback: callback(),
        recorder_factory=recorder_factory or default_factory,
        resolve_requested_field_media=lambda _editor, field_index, filename: (
            (filename, source_path) if field_index == editor.currentField and filename == "target.wav" else None
        ),
        schedule_timer=schedule_timer or default_timer,
        session_and_source=lambda _editor: (session, source_path),
        sessions={editor: session},
        set_busy_for_field=lambda _editor, field_index, busy, message="": busy_calls.append(
            (field_index, busy, message)
        ),
        statuses=statuses,
        stopped=stopped,
        stop_session_playback=lambda _session: stopped.append(True),
        threading=SimpleNamespace(Thread=_ImmediateThread),
        timers=timers,
        visualized_duration_for_field=lambda _session, field_index, filename: (
            session.visualized_durations_by_field.get(field_index)
            if session.visualized_filenames_by_field.get(field_index) == filename
            else None
        ),
    )


def test_record_learner_voice_success_persists_media_and_sets_learner_visualizer(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    deps = _deps(editor, session, source_path)

    record_learner_voice(editor, deps, graph_settings={"voiceRange": "high"})

    state = session.learner_recording
    assert state.status == "ready"
    assert state.media_filename is not None
    assert state.media_filename.startswith("target__aqe_voice_")
    assert state.media_filename.endswith(".wav")
    assert state.media_path == source_path.parent / state.media_filename
    assert state.media_path.read_bytes() == b"RIFFfakeWAVE"
    assert state.prosody_payload is not None
    assert state.prosody_payload["sourceFilename"] == state.media_filename
    assert editor.note.fields == ["[sound:target.wav]"]
    assert deps.stopped == [True]
    assert deps.timers == [1000]
    assert any("__aqeSetLearnerVisualizer" in call for call in editor.web.eval_calls)


def test_record_learner_voice_uses_graph_settings_for_analysis_config(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    captured: dict[str, AudioProcessingConfig] = {}

    def analyzer(media_path: Path, config: AudioProcessingConfig) -> Any:
        captured["config"] = config
        return build_prosody_track(
            duration_ms=1000,
            points=[ProsodyPoint(time_ms=0, pitch_hz=180.0, intensity_db=-20.0, intensity_norm=0.0, voiced=True)],
            source_filename=media_path.name,
            analyzer_name="fake",
        )

    deps = _deps(editor, session, source_path, analyzer=analyzer)

    record_learner_voice(editor, deps, graph_settings={"voiceRange": "high"})

    expected = config_with_graph_settings(AudioProcessingConfig(), {"voiceRange": "high"})
    assert captured["config"].graph_voice_range == expected.graph_voice_range


def test_record_learner_voice_start_failure_sets_failed_state(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    recorder = _FakeRecorder(source_path, start_error=AudioRecordingError("microphone unavailable"))
    deps = _deps(editor, session, source_path, recorder=recorder)

    record_learner_voice(editor, deps)

    assert session.learner_recording.status == "failed"
    assert session.learner_recording.failure_message == "microphone unavailable"
    assert deps.timers == []
    assert deps.statuses[-1] == ("microphone unavailable", "error")


def test_record_learner_voice_empty_file_failure_sets_failed_state(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    recorder = _FakeRecorder(source_path, write_bytes=b"")
    deps = _deps(editor, session, source_path, recorder=recorder)

    record_learner_voice(editor, deps)

    assert session.learner_recording.status == "failed"
    assert "empty" in str(session.learner_recording.failure_message)
    assert not any("__aqeSetLearnerVisualizer" in call for call in editor.web.eval_calls)


def test_record_learner_voice_analysis_failure_sets_failed_state(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)

    def analyzer(_media_path: Path, _config: AudioProcessingConfig) -> Any:
        raise AudioProcessingError("analysis failed")

    deps = _deps(editor, session, source_path, analyzer=analyzer)

    record_learner_voice(editor, deps)

    assert session.learner_recording.status == "failed"
    assert session.learner_recording.failure_message == "analysis failed"
    assert not any("__aqeSetLearnerVisualizer" in call for call in editor.web.eval_calls)


def test_record_learner_voice_ignores_stale_completion(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    recorder = _FakeRecorder(source_path, complete_on_stop=False)
    analyzed: list[Path] = []
    deps = _deps(
        editor,
        session,
        source_path,
        recorder=recorder,
        analyzer=lambda media_path, _config: analyzed.append(media_path),
    )

    record_learner_voice(editor, deps)
    clear_learner_recording_state(session)
    recorder.complete()

    assert session.learner_recording.status == "idle"
    assert analyzed == []
    assert not any("__aqeSetLearnerVisualizer" in call for call in editor.web.eval_calls)


def test_record_learner_voice_copies_temp_result_into_generated_media_file(tmp_path: Path) -> None:
    editor, session, source_path = _editor_with_target(tmp_path)
    temp_result_path = tmp_path / "temp" / "capture.wav"
    recorder = _FakeRecorder(source_path, result_path=temp_result_path)
    deps = _deps(editor, session, source_path, recorder=recorder)

    record_learner_voice(editor, deps)

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

    assert deps.statuses[-1] == ("The referenced audio file was not found in Anki's media folder.", "error")
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

    assert deps.statuses[-1] == ("The referenced audio file was not found in Anki's media folder.", "error")
    assert deps.stopped == []
    av_player.play_tags.assert_not_called()
