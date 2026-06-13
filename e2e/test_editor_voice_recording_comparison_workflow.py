"""E2E tests for learner voice recording and pitch comparison."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from e2e.conftest import import_runtime_addon_module, runtime_addon_import_path
from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _drag_learner_pitch_to_ratio,
    _graph_state_js,
    _install_html_audio_test_driver,
    _wait_for_html_playback,
)
from e2e.editor_note_helpers import (
    DEFAULT_VISIBLE_EDITOR_BUTTONS,
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
)
from e2e.editor_region_loop_helpers import _shift_drag_region
from e2e.editor_playback_helpers import _record_fake_playback
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


def _inject_ready_learner_overlay(
    editor,
    *,
    start_cursor_ms: int,
    learner_duration_ms: int = 1600,
    timeout: float = 5.0,
) -> dict[str, Any]:
    run_js(
        editor.web,
        f"""
        (() => {{
          window.__aqeSetLearnerRecordingState?.({{
            fieldOrd: 0,
            generation: 1,
            startCursorMs: {start_cursor_ms},
            status: "ready",
            targetDurationMs: window.__aqeGraphStateForTest?.(0)?.targetDurationMs || 0,
          }});
          window.__aqeSetLearnerVisualizer?.(0, {{
            analyzerName: "praat",
            durationMs: {learner_duration_ms},
            pitchMaxHz: 500,
            pitchMinHz: 80,
            points: [
              [0, 130, 1, true],
              [600, 210, 0.2, true],
              [{learner_duration_ms}, 260, 0.1, true],
            ],
            sourceFilename: "target__aqe_voice.wav",
          }});
          return true;
        }})()
        """,
    )
    return wait_for_js_condition(
        editor.web,
        _graph_state_js(),
        lambda value: value is not None
        and value["learnerRecordingStatus"] == "ready"
        and value["learnerStartCursorMs"] == start_cursor_ms
        and value["learnerPitchPaths"] > 0
        and value["learnerAlignmentOffsetMs"] == 0,
        timeout=timeout,
    )


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
            wait_for_js_condition(
                editor.web,
                f"""
                (() => {{
                  const state = window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest(0) : null;
                  const play = document.querySelector({play_yours_selector!r});
                  return state && play ? {{
                    ...state,
                    playYoursLabel: play.querySelector('.aqe-button-label')?.textContent || play.textContent || "",
                  }} : null;
                }})()
                """,
                lambda value: value is not None
                and value["learnerPlaybackStatus"] == "playing"
                and "Pause" in value["playYoursLabel"],
                timeout=5.0,
            )
            click_selector(editor.web, play_yours_selector, timeout=5.0)
            wait_for_condition(
                lambda: playback.toggle_count == 1,
                timeout=5.0,
                message="Play yours did not toggle learner playback pause",
            )
            wait_for_js_condition(
                editor.web,
                f"""
                (() => {{
                  const state = window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest(0) : null;
                  const play = document.querySelector({play_yours_selector!r});
                  return state && play ? {{
                    ...state,
                    playYoursLabel: play.querySelector('.aqe-button-label')?.textContent || play.textContent || "",
                  }} : null;
                }})()
                """,
                lambda value: value is not None
                and value["learnerPlaybackStatus"] == "paused"
                and "Play" in value["playYoursLabel"],
                timeout=5.0,
            )

        assert playback.current is not None
        assert playback.current.path == fake_recorder.output_path

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
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_voice_recording_learner_drag_preserves_zoomed_viewport(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_voice_recording_zoom_drag.wav"
    generate_tone(ffmpeg_config, source, duration_s=4.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        visible_editor_buttons=[*DEFAULT_VISIBLE_EDITOR_BUTTONS, "aqe:record-voice"],
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name and value["pitchPaths"] > 0,
            timeout=15.0,
        )
        wait_for_js_condition(
            editor.web,
            f"""
            (() => {{
              const state = window.__aqeGraphStateForTest?.(0);
              if (!state) return null;
              window.__aqeSetCursorForTest?.(0, state.durationMs / 2, false);
              document.querySelector('[data-testid="aqe-zoom-in-0"]')?.click();
              return window.__aqeGraphStateForTest?.(0) || null;
            }})()
            """,
            lambda value: value is not None
            and value["viewportStartMs"] > 0
            and value["viewportEndMs"] < value["durationMs"],
            timeout=5.0,
        )
        zoomed = _inject_ready_learner_overlay(editor, start_cursor_ms=900)

        _drag_learner_pitch_to_ratio(editor, 0.6, 0.45)

        dragged = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None
            and value["learnerAlignmentOffsetMs"] < 0
            and value["viewportStartMs"] == zoomed["viewportStartMs"]
            and value["viewportEndMs"] == zoomed["viewportEndMs"],
            timeout=5.0,
        )
        assert dragged["learnerPitchPaths"] > 0
        assert dragged["targetDurationMs"] == track["durationMs"]
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_voice_recording_learner_drag_preserves_selection_region(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_voice_recording_selection_drag.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        visible_editor_buttons=[*DEFAULT_VISIBLE_EDITOR_BUTTONS, "aqe:record-voice"],
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name and value["pitchPaths"] > 0,
            timeout=15.0,
        )
        _inject_ready_learner_overlay(editor, start_cursor_ms=300, learner_duration_ms=1900)
        _shift_drag_region(editor, 0.25, 0.75)
        selected = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None
            and value["selectionActive"] is True
            and value["selectionStartMs"] is not None
            and value["selectionEndMs"] is not None
            and value["selectionEndMs"] > value["selectionStartMs"],
            timeout=5.0,
        )

        _drag_learner_pitch_to_ratio(editor, 0.55, 0.4)

        dragged = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None
            and value["learnerAlignmentOffsetMs"] < 0
            and value["selectionActive"] is True
            and value["selectionStartMs"] == selected["selectionStartMs"]
            and value["selectionEndMs"] == selected["selectionEndMs"]
            and value["cursorMs"] == selected["cursorMs"],
            timeout=5.0,
        )
        assert dragged["playbackRegionMode"] == "selection"
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_voice_recording_learner_drag_does_not_interrupt_target_playback(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_voice_recording_playback_drag.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.5)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        visible_editor_buttons=[*DEFAULT_VISIBLE_EDITOR_BUTTONS, "aqe:record-voice"],
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name and value["pitchPaths"] > 0,
            timeout=15.0,
        )
        _install_html_audio_test_driver(editor)
        _inject_ready_learner_overlay(editor, start_cursor_ms=500, learner_duration_ms=1700)

        click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
        playing = _wait_for_html_playback(
            editor,
            lambda value: value["playbackStartMs"] == 0 and value["playbackEndMs"] == 2500,
            timeout=5.0,
        )
        moving = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None and value["audioClockCurrentMs"] > 0,
            timeout=5.0,
        )

        _drag_learner_pitch_to_ratio(editor, 0.65, 0.45)

        dragged = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None
            and value["learnerAlignmentOffsetMs"] < 0
            and value["playbackState"] == "playing"
            and value["playbackEngine"] == "html"
            and value["playbackStartMs"] == playing["playbackStartMs"]
            and value["audioClockCurrentMs"] > moving["audioClockCurrentMs"],
            timeout=5.0,
        )
        assert dragged["progressMs"] >= dragged["cursorMs"]
    finally:
        editor.set_note(None)
        parent.close()
