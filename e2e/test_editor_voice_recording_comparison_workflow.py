"""E2E tests for learner voice recording and pitch comparison."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from e2e.editor_graph_helpers import _click_graph_and_wait, _graph_state_js
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
)
from e2e.editor_playback_helpers import _record_fake_playback
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js_condition,
)


class _FakeRecorderFactory:
    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path
        self.output_path: Path | None = None
        self.generation: int | None = None

    def __call__(self, output_path: Path, _mw, _parent):
        self.output_path = output_path
        return self

    def start(self, generation: int, *, on_started, on_failed) -> None:
        if not callable(on_failed):
            raise AssertionError("fake recorder expected an on_failed callback")
        self.generation = generation
        on_started(generation)

    def stop(self, *, on_completed, on_failed) -> None:
        if not callable(on_failed):
            raise AssertionError("fake recorder expected an on_failed callback")
        from anki_audio_quick_editor.audio_recording import RecordingResult

        if self.output_path is None or self.generation is None:
            raise AssertionError("fake recorder stopped before it was started")
        self.output_path.write_bytes(self.fixture_path.read_bytes())
        on_completed(RecordingResult(path=self.output_path, generation=self.generation))


def test_editor_voice_recording_comparison_workflow(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_voice_recording_target.wav"
    learner_fixture = media_dir / "editor_voice_recording_fake_learner.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    generate_tone(ffmpeg_config, learner_fixture, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    fake_recorder = _FakeRecorderFactory(learner_fixture)

    editor, parent = _open_editor(anki_mw, note)
    try:
        target = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name
            and value["pitchPaths"] > 0
            and value["recordButtonDisabled"] is False
            and value["playRecordingButtonDisabled"] is True,
            timeout=15.0,
        )
        assert target["learnerPitchPaths"] == 0

        with patch(
            "anki_audio_quick_editor.editor_dependencies._native_recorder_factory",
            fake_recorder,
        ):
            click_selector(editor.web, _button_selector("aqe:record-voice"), timeout=5.0)
            learner = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda value: value is not None
                and value["recordingStatus"] == "ready"
                and value["learnerPitchPaths"] > 0
                and value["learnerIntensityPaths"] == 0
                and value["playRecordingButtonDisabled"] is False,
                timeout=20.0,
            )

        assert learner["recordingStatusText"]
        assert _sound_filename(note.fields[0]) == source.name
        assert fake_recorder.output_path is not None
        assert fake_recorder.output_path.parent == media_dir
        assert fake_recorder.output_path.name.startswith("editor_voice_recording_target__aqe_voice_")
        assert fake_recorder.output_path.is_file()

        with _record_fake_playback(
            media_dir,
            {fake_recorder.output_path.name: learner["durationMs"]},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play-recording"), timeout=5.0)
            wait_for_condition(
                lambda: len(playback.attempts) == 1,
                timeout=5.0,
                message="Play yours did not route to native learner playback",
            )

        assert playback.current is not None
        assert playback.current.path == fake_recorder.output_path
    finally:
        editor.set_note(None)
        parent.close()
