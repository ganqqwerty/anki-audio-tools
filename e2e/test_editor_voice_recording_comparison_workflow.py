"""E2E tests for learner voice recording and pitch comparison."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from e2e.conftest import import_runtime_addon_module, runtime_addon_import_path
from e2e.editor_graph_helpers import _click_graph_and_wait, _graph_state_js
from e2e.editor_note_helpers import (
    DEFAULT_VISIBLE_EDITOR_BUTTONS,
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
        self.started = False
        self.stopped = False

    def __call__(self, output_path: Path, _mw: Any, _parent: Any) -> "_FakeRecorderFactory":
        self.output_path = output_path
        return self

    def start(self, generation: int, *, on_started: Any, on_failed: Any) -> None:
        if not callable(on_failed):
            raise AssertionError("fake recorder expected an on_failed callback")
        self.generation = generation
        self.started = True
        on_started(generation)

    def stop(self, *, on_completed: Any, on_failed: Any) -> None:
        if not callable(on_failed):
            raise AssertionError("fake recorder expected an on_failed callback")
        if self.output_path is None or self.generation is None:
            raise AssertionError("fake recorder stopped before it was started")
        recording_result = import_runtime_addon_module(".audio_recording").RecordingResult
        self.stopped = True
        self.output_path.write_bytes(self.fixture_path.read_bytes())
        on_completed(recording_result(path=self.output_path, generation=self.generation))


def _has_ready_learner_overlay(value: dict[str, Any] | None) -> bool:
    if value is None:
        return False
    if value["learnerRecordingStatus"] != "ready":
        return False
    if value["learnerPitchPaths"] <= 0:
        return False
    if value["learnerIntensityPaths"] != 0:
        return False
    if value["learnerDurationMs"] <= value["targetDurationMs"]:
        return False
    return value["durationMs"] == value["learnerDurationMs"]


def test_editor_voice_recording_comparison_workflow(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_voice_recording_target.wav"
    learner_fixture = media_dir / "editor_voice_recording_fake_learner.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    generate_tone(ffmpeg_config, learner_fixture, duration_s=1.6)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        voice_recording_countdown_seconds=0,
        visible_editor_buttons=[
            *DEFAULT_VISIBLE_EDITOR_BUTTONS,
            "aqe:record-voice",
            "aqe:play-recording",
        ],
    )
    fake_recorder = _FakeRecorderFactory(learner_fixture)
    monkeypatch.setattr(
        runtime_addon_import_path(".editor_dependencies", "_native_recorder_factory"),
        fake_recorder,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        target = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name
            and value["pitchPaths"] > 0,
            timeout=15.0,
        )
        assert target["durationMs"] > 0
        assert wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None
            and value["targetDurationMs"] == value["durationMs"]
            and value["learnerPitchPaths"] == 0,
            timeout=5.0,
        )

        record_selector = _button_selector("aqe:record-voice")
        play_yours_selector = _button_selector("aqe:play-recording")
        wait_for_js_condition(
            editor.web,
            f"""
            (() => {{
              const record = document.querySelector({record_selector!r});
              const play = document.querySelector({play_yours_selector!r});
              return record && play ? {{
                groupCount: document.querySelectorAll('.aqe-recording-group').length,
                recordIconOnly: record.classList.contains('aqe-icon-only'),
                playIconOnly: play.classList.contains('aqe-icon-only'),
                recordDisabled: record.disabled,
                playDisabled: play.disabled,
              }} : null;
            }})()
            """,
            lambda value: value is not None
            and value["groupCount"] == 1
            and value["recordIconOnly"] is True
            and value["playIconOnly"] is True
            and value["recordDisabled"] is False
            and value["playDisabled"] is True,
            timeout=5.0,
        )

        click_selector(editor.web, record_selector, timeout=5.0)
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None
            and value["learnerRecordingStatus"] == "recording"
            and value["learnerPitchPaths"] == 0,
            timeout=5.0,
        )
        click_selector(editor.web, record_selector, timeout=5.0)
        learner = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            _has_ready_learner_overlay,
            timeout=20.0,
        )

        assert _sound_filename(note.fields[0]) == source.name
        assert fake_recorder.started is True
        assert fake_recorder.stopped is True
        assert fake_recorder.output_path is not None
        assert fake_recorder.output_path.parent == media_dir
        assert fake_recorder.output_path.name.startswith("editor_voice_recording_target__aqe_voice_")
        assert fake_recorder.output_path.is_file()

        with _record_fake_playback(
            media_dir,
            {fake_recorder.output_path.name: learner["learnerDurationMs"]},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, play_yours_selector, timeout=5.0)
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
