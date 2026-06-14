"""E2E tests for resumed playback loop reset behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from e2e.editor_graph_helpers import (
    _install_html_audio_test_driver,
    _wait_for_html_playback,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.editor_playback_helpers import (
    PLAYBACK_INTERVAL_TOLERANCE_MS,
    _assert_no_playback_leaks,
    _record_fake_playback,
)
from e2e.editor_region_loop_helpers import (
    _force_audio_boundary,
    _force_repeat_wrap,
    _open_tone_editor,
    _set_repeat,
    _shift_click_region,
    _shift_drag_region,
    _state,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_js_condition,
)


def test_selected_repeat_play_after_pause_restarts_from_selection_start(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_repeat_resume_loop_selected.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.65)
        _set_repeat(editor, True)

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 800)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            paused = _state(
                editor,
                lambda state: state["playbackState"] == "paused"
                and state["cursorMs"] > state["selectionStartMs"] + PLAYBACK_INTERVAL_TOLERANCE_MS,
            )

            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            restarted = _wait_for_html_playback(
                editor,
                lambda state: state["progressMs"] >= state["selectionStartMs"]
                and state["playbackStartMs"] == state["selectionStartMs"],
            )
            looped = _force_repeat_wrap(editor, 500)

        _assert_no_playback_leaks(playback)
        assert restarted["playbackStartMs"] == 500
        assert restarted["playbackEndMs"] == 1300
        assert paused["cursorMs"] > restarted["playbackStartMs"] + PLAYBACK_INTERVAL_TOLERANCE_MS
        assert looped["playbackStartMs"] == 500
        assert looped["selectionStartMs"] == 500
    finally:
        editor.set_note(None)
        parent.close()


@pytest.mark.parametrize(
    ("label", "select_everything"),
    [
        pytest.param("nothing-selected", False, id="nothing-selected"),
        pytest.param("everything-selected", True, id="everything-selected"),
    ],
)
def test_full_region_repeat_resume_loops_from_beginning(
    anki_mw,
    ffmpeg_config,
    label: str,
    select_everything: bool,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        f"editor_region_repeat_resume_loop_{label}.wav",
        2.0,
    )
    try:
        if select_everything:
            _shift_drag_region(editor, 0.0, 1.0)
        else:
            _shift_click_region(editor, 0.5)
            _state(editor, lambda state: state["selectionActive"] is False)
        _set_repeat(editor, True)

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 800)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            paused = _state(
                editor,
                lambda state: state["playbackState"] == "paused"
                and state["cursorMs"] > PLAYBACK_INTERVAL_TOLERANCE_MS,
            )

            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(
                editor,
                lambda state: state["progressMs"] >= paused["cursorMs"]
                and state["playbackStartMs"] > PLAYBACK_INTERVAL_TOLERANCE_MS,
            )
            looped = _force_repeat_wrap(editor, 0)

        _assert_no_playback_leaks(playback)
        assert looped["playbackStartMs"] == 0
        assert looped["selectionActive"] is select_everything
    finally:
        editor.set_note(None)
        parent.close()


def test_hidden_full_repeat_resume_loops_from_beginning_without_graph(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_hidden_repeat_resume_loop.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, repeat_playback_by_default=False)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _prime_hidden_audio_duration(editor, 2000)
        _install_html_audio_test_driver(editor)
        _set_repeat(editor, True)

        with _record_fake_playback(media_dir, {source.name: 2000}, ffmpeg_config=ffmpeg_config) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(
                editor,
                lambda state: state["hidden"] is True
                and state["hasTrack"] is False
                and state["progressMs"] >= 800,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            paused = _state(
                editor,
                lambda state: state["hidden"] is True
                and state["playbackState"] == "paused"
                and state["cursorMs"] > PLAYBACK_INTERVAL_TOLERANCE_MS,
            )

            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(
                editor,
                lambda state: state["hidden"] is True
                and state["progressMs"] >= paused["cursorMs"]
                and state["playbackStartMs"] > PLAYBACK_INTERVAL_TOLERANCE_MS,
            )
            looped = _force_repeat_wrap(editor, 0)

        _assert_no_playback_leaks(playback)
        assert looped["hidden"] is True
        assert looped["hasTrack"] is False
        assert looped["playbackStartMs"] == 0
    finally:
        editor.set_note(None)
        parent.close()


def test_hidden_default_repeat_ended_replays_browser_audio_with_stale_field_state(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_hidden_default_repeat_stale_state.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.6)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        repeat_playback_by_default=True,
        repeat_pause_seconds=0.0,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        _prime_hidden_audio_duration(editor, 600)
        _install_lagging_html_audio_driver(editor)

        with _record_fake_playback(media_dir, {source.name: 600}, ffmpeg_config=ffmpeg_config) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _state(
                editor,
                lambda state: state["hidden"] is True
                and state["hasTrack"] is False
                and state["repeatEnabled"] is True
                and state["playbackState"] == "playing"
                and state["playbackEngine"] == "html"
                and state["progressClockMode"] == "audio"
                and state["progressMs"] >= 250,
            )
            assert _lagging_audio_play_calls(editor) == 1
            _stale_field_duration_for_test(editor)
            _dispatch_audio_ended(editor)
            wait_for_js_condition(
                editor.web,
                "window.__aqeLaggingAudioPlayCalls ?? 0",
                lambda value: value >= 2,
                timeout=5.0,
            )

        _assert_no_playback_leaks(playback)
    finally:
        editor.set_note(None)
        parent.close()


def test_selected_non_repeat_resume_completion_resets_to_selection_start(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_resume_non_repeat_completion.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.65)

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 800)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            paused = _state(
                editor,
                lambda state: state["playbackState"] == "paused"
                and state["cursorMs"] > state["selectionStartMs"] + PLAYBACK_INTERVAL_TOLERANCE_MS,
            )

            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= paused["cursorMs"])
            _force_audio_boundary(editor)
            finished = _state(
                editor,
                lambda state: state["playbackState"] == "stopped"
                and state["repeatEnabled"] is False
                and abs(state["cursorMs"] - 500) <= PLAYBACK_INTERVAL_TOLERANCE_MS,
            )

        _assert_no_playback_leaks(playback)
        assert finished["playbackRegionMode"] == "selection"
    finally:
        editor.set_note(None)
        parent.close()


def _prime_hidden_audio_duration(editor, duration_ms: int, ord_: int = 0) -> None:
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const visualizer = document.querySelector('[data-testid="aqe-graph-{ord_}"]');
          if (!visualizer) return null;
          visualizer.dataset.targetDurationMs = String({duration_ms});
          visualizer.dataset.playbackResetCursorMs = "0";
          visualizer.hidden = true;
          window.__aqeSetFieldStateForTest?.({ord_}, {{
            graph: {{ active: true, durationMs: {duration_ms} }},
            playback: {{ endMs: {duration_ms}, regionMode: "full" }}
          }});
          return window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest({ord_}) : null;
        }})()
        """,
        lambda state: state is not None
        and state["hidden"] is True
        and state["durationMs"] == duration_ms
        and state["targetDurationMs"] == duration_ms,
        timeout=5.0,
    )


def _install_lagging_html_audio_driver(editor, ord_: int = 0) -> None:
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const visualizer = document.querySelector('[data-testid="aqe-graph-{ord_}"]');
          const audio = document.querySelector('[data-testid="aqe-audio-clock-{ord_}"]');
          if (!visualizer || !audio) return false;
          const durationSeconds = Number(visualizer.dataset.durationMs || "0") / 1000;
          const markReady = () => {{
            try {{
              Object.defineProperty(audio, "readyState", {{ configurable: true, value: 1 }});
              Object.defineProperty(audio, "duration", {{
                configurable: true,
                get: () => durationSeconds,
              }});
            }} catch {{}}
            visualizer.__aqeAudioClockAvailable = true;
            visualizer.__aqeAudioClockFallback = false;
          }};
          window.__aqeLaggingAudioPlayCalls = 0;
          audio.pause = function pause() {{}};
          audio.play = function play() {{
            window.__aqeLaggingAudioPlayCalls += 1;
            return Promise.resolve();
          }};
          markReady();
          audio.dispatchEvent(new Event("loadedmetadata"));
          return true;
        }})()
        """,
        lambda value: value is True,
        timeout=5.0,
    )


def _stale_field_duration_for_test(editor, ord_: int = 0) -> None:
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          if (typeof window.__aqeSetFieldStateForTest !== "function") return false;
          const state = window.__aqeSetFieldStateForTest({ord_}, {{
            graph: {{ durationMs: 0 }}
          }});
          return state !== null;
        }})()
        """,
        lambda value: value is True,
        timeout=5.0,
    )


def _dispatch_audio_ended(editor, ord_: int = 0) -> None:
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const audio = document.querySelector('[data-testid="aqe-audio-clock-{ord_}"]');
          if (!audio) return false;
          audio.dispatchEvent(new Event("ended"));
          return true;
        }})()
        """,
        lambda value: value is True,
        timeout=5.0,
    )


def _lagging_audio_play_calls(editor) -> int:
    return int(
        wait_for_js_condition(
            editor.web,
            "window.__aqeLaggingAudioPlayCalls ?? 0",
            lambda value: value is not None,
            timeout=5.0,
        )
    )
