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
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
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
        on_completed(recording_result(path=self.output_path, generation=self.generation, duration_ms=1600))


def _has_ready_learner_overlay(value: dict[str, Any] | None) -> bool:
    if value is None:
        return False
    if value["learnerRecordingStatus"] != "ready":
        return False
    if value["learnerStartCursorMs"] != 900:
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
    revealed: list[Path] = []
    uploaded: list[tuple[Path, str]] = []
    monkeypatch.setattr(
        runtime_addon_import_path(".editor_dependencies", "_native_recorder_factory"),
        fake_recorder,
    )
    monkeypatch.setattr(
        runtime_addon_import_path(".editor_settings_actions", "reveal_file"),
        lambda path: revealed.append(path),
    )
    monkeypatch.setattr(
        runtime_addon_import_path(".file_sharing", "upload_file"),
        lambda path, share_target: uploaded.append((path, share_target))
        or f"https://example.test/{share_target}/{path.name}",
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
        share_yours_selector = _button_selector("aqe:share-recording")
        show_yours_selector = _button_selector("aqe:show-recording-file")
        wait_for_js_condition(
            editor.web,
            f"""
            (() => {{
              const record = document.querySelector({record_selector!r});
              const play = document.querySelector({play_yours_selector!r});
              const share = document.querySelector({share_yours_selector!r});
              const show = document.querySelector({show_yours_selector!r});
              const panel = document.querySelector('[data-testid="aqe-recording-toolbar-panel-0"]');
              if (!record || !play || !share || !show || !panel) return null;
              const style = getComputedStyle(panel);
              return {{
                ariaLabel: panel.getAttribute("aria-label"),
                borderRadius: style.borderRadius,
                borderTopWidth: style.borderTopWidth,
                container: panel.getAttribute("data-aqe-toolbar-button-container"),
                groupCount: document.querySelectorAll('.aqe-recording-group').length,
                label: panel.querySelector(".aqe-toolbar-panel-label")?.textContent || "",
                recordIconOnly: record.classList.contains('aqe-icon-only'),
                playIconOnly: play.classList.contains('aqe-icon-only'),
                shareDisabled: share.disabled,
                showDisabled: show.disabled,
                recordDisabled: record.disabled,
                playDisabled: play.disabled,
                role: panel.getAttribute("role"),
              }};
            }})()
            """,
            lambda value: value is not None
            and value["ariaLabel"] == "Record / Play yours"
            and value["borderRadius"] == "9px"
            and value["borderTopWidth"] == "0px"
            and value["container"] == "true"
            and value["groupCount"] == 1
            and value["label"] == "Record / Play yours"
            and value["recordIconOnly"] is True
            and value["playIconOnly"] is True
            and value["recordDisabled"] is False
            and value["playDisabled"] is True
            and value["shareDisabled"] is True
            and value["showDisabled"] is True
            and value["role"] == "group",
            timeout=5.0,
        )

        run_js(
            editor.web,
            """
            (() => {
              if (typeof window.__aqeSetCursorForTest !== "function") return false;
              const visualizer = document.querySelector('[data-testid="aqe-graph-0"]');
              if (!visualizer) return false;
              visualizer.hidden = false;
              visualizer.dataset.graphActive = "true";
              window.__aqeSetCursorForTest(0, 900, false);
              return true;
            })()
            """,
        )
        wait_for_js_condition(
            editor.web,
            """
            (() => {
              const scrollbar = document.querySelector('[data-testid="aqe-time-scrollbar-0"]');
              const scroller = document.querySelector('[data-testid="aqe-time-scrollbar-scroll-0"]');
              const state = window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest(0) : null;
              return scrollbar && scroller && state ? {
                hidden: scrollbar.hidden,
                clientWidth: scroller.clientWidth,
                durationMs: state.durationMs,
                scrollLeft: scroller.scrollLeft,
                scrollWidth: scroller.scrollWidth,
                viewportEndMs: state.viewportEndMs,
                viewportStartMs: state.viewportStartMs,
              } : null;
            })()
            """,
            lambda value: value is not None
            and value["hidden"] is True
            and value["durationMs"] == target["durationMs"]
            and value["viewportStartMs"] == 0
            and value["viewportEndMs"] >= value["durationMs"],
            timeout=5.0,
        )
        click_selector(editor.web, record_selector, timeout=5.0)
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None
            and value["learnerRecordingStatus"] == "recording"
            and value["learnerStartCursorMs"] == 900
            and value["learnerPitchPaths"] == 0,
            timeout=5.0,
        )
        wait_for_js_condition(
            editor.web,
            """
            (() => {
              const scrollbar = document.querySelector('[data-testid="aqe-time-scrollbar-0"]');
              const scroller = document.querySelector('[data-testid="aqe-time-scrollbar-scroll-0"]');
              const state = window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest(0) : null;
              return scrollbar && scroller && state ? {
                clientWidth: scroller.clientWidth,
                cursorMs: state.cursorMs,
                durationMs: state.durationMs,
                hidden: scrollbar.hidden,
                learnerDurationMs: state.learnerDurationMs,
                learnerRecordingStatus: state.learnerRecordingStatus,
                scrollLeft: scroller.scrollLeft,
                scrollWidth: scroller.scrollWidth,
                targetDurationMs: state.targetDurationMs,
                viewportEndMs: state.viewportEndMs,
                viewportStartMs: state.viewportStartMs,
              } : null;
            })()
            """,
            lambda value: value is not None
            and value["learnerRecordingStatus"] == "recording"
            and value["learnerDurationMs"] > value["targetDurationMs"]
            and value["cursorMs"] > value["targetDurationMs"]
            and value["durationMs"] > value["targetDurationMs"]
            and value["hidden"] is False
            and value["scrollWidth"] > value["clientWidth"]
            and value["scrollLeft"] > 0
            and value["viewportStartMs"] > 0
            and value["viewportEndMs"] >= value["cursorMs"],
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
        assert learner["learnerStartCursorMs"] == 900

        learner_driver = _install_learner_audio_test_driver(
            editor,
            fake_recorder.output_path.name,
        )
        assert learner_driver["src"] == fake_recorder.output_path.name

        click_selector(editor.web, play_yours_selector, timeout=5.0)
        wait_for_js_condition(
            editor.web,
            _learner_playback_state_js(play_yours_selector),
            lambda value: value is not None
            and value["learnerPlaybackStatus"] == "playing"
            and value["playCalls"] == 1
            and value["pauseCalls"] == 0
            and "Pause" in value["playYoursLabel"],
            timeout=5.0,
        )
        click_selector(editor.web, play_yours_selector, timeout=5.0)
        wait_for_js_condition(
            editor.web,
            _learner_playback_state_js(play_yours_selector),
            lambda value: value is not None
            and value["learnerPlaybackStatus"] == "paused"
            and value["playCalls"] == 1
            and value["pauseCalls"] == 1
            and "Play" in value["playYoursLabel"],
            timeout=5.0,
        )
        click_selector(editor.web, play_yours_selector, timeout=5.0)
        wait_for_js_condition(
            editor.web,
            _learner_playback_state_js(play_yours_selector),
            lambda value: value is not None
            and value["learnerPlaybackStatus"] == "playing"
            and value["playCalls"] == 2
            and value["pauseCalls"] == 1
            and "Pause" in value["playYoursLabel"],
            timeout=5.0,
        )

        click_selector(editor.web, show_yours_selector, timeout=5.0)
        wait_for_condition(
            lambda: revealed == [fake_recorder.output_path],
            timeout=5.0,
            message="Show yours did not reveal the learner recording file",
        )
        click_selector(editor.web, share_yours_selector, timeout=5.0)
        wait_for_condition(
            lambda: uploaded == [(fake_recorder.output_path, "litterbox")],
            timeout=5.0,
            message="Share yours did not upload the learner recording file",
        )
        wait_for_js_condition(
            editor.web,
            "document.querySelector('[data-testid=\"aqe-status-0\"]')?.textContent || ''",
            lambda value: value.startswith("Copied Litterbox link for"),
            timeout=5.0,
        )
    finally:
        editor.set_note(None)
        parent.close()


def _install_learner_audio_test_driver(editor: Any, expected_filename: str) -> dict[str, Any]:
    return wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const audio = document.querySelector('[data-testid="aqe-audio-clock-0"]');
          if (!audio) return null;
          window.__aqeLearnerAudioTestDriver = {{ playCalls: 0, pauseCalls: 0 }};
          audio.play = () => {{
            window.__aqeLearnerAudioTestDriver.playCalls += 1;
            return Promise.resolve();
          }};
          audio.pause = () => {{
            window.__aqeLearnerAudioTestDriver.pauseCalls += 1;
          }};
          return {{
            src: audio.getAttribute("src") || "",
            expected: {expected_filename!r},
          }};
        }})()
        """,
        lambda value: value is not None and value["src"] == expected_filename,
        timeout=5.0,
    )


def _learner_playback_state_js(play_yours_selector: str) -> str:
    return f"""
    (() => {{
      const state = window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest(0) : null;
      const play = document.querySelector({play_yours_selector!r});
      const audio = document.querySelector('[data-testid="aqe-audio-clock-0"]');
      const driver = window.__aqeLearnerAudioTestDriver || {{ playCalls: 0, pauseCalls: 0 }};
      return state && play && audio ? {{
        ...state,
        learnerAudioSrc: audio.getAttribute("src") || "",
        pauseCalls: driver.pauseCalls,
        playCalls: driver.playCalls,
        playYoursLabel: play.querySelector('.aqe-button-label')?.textContent || play.textContent || "",
      }} : null;
    }})()
    """
