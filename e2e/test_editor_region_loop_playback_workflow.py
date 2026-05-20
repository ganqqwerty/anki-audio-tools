"""E2E tests for selected-region loop playback."""

from __future__ import annotations

import time

import pytest

from e2e.editor_graph_helpers import (
    _wait_for_html_playback,
)
from e2e.editor_note_helpers import (
    _button_selector,
    _sound_filename,
    _wait_for_generated_mp3,
)
from e2e.editor_playback_helpers import (
    PLAYBACK_INTERVAL_TOLERANCE_MS,
    _assert_interval,
    _record_fake_playback,
)
from e2e.editor_region_loop_helpers import (
    _force_audio_boundary,
    _force_repeat_wrap,
    _normal_drag,
    _open_tone_editor,
    _set_repeat,
    _shift_click_region,
    _shift_drag_region,
    _state,
)
from e2e.helpers import (
    click_selector,
    run_js,
    wait_for_condition,
)


@pytest.mark.parametrize(
    ("label", "extension", "start_ratio", "end_ratio"),
    [
        pytest.param("middle", "wav", 0.25, 0.625, id="wav-middle"),
        pytest.param("full-explicit", "wav", 0.0, 1.0, id="wav-full-explicit"),
        pytest.param("near-start", "wav", 0.0, 0.125, id="wav-near-start"),
        pytest.param("near-end", "wav", 0.875, 1.0, id="wav-near-end"),
        pytest.param("middle", "aac", 0.25, 0.625, id="aac-middle"),
        pytest.param("middle", "flac", 0.25, 0.625, id="flac-middle"),
        pytest.param("middle", "m4a", 0.25, 0.625, id="m4a-middle"),
        pytest.param("middle", "mp3", 0.25, 0.625, id="mp3-middle"),
        pytest.param("middle", "oga", 0.25, 0.625, id="oga-middle"),
        pytest.param("middle", "ogg", 0.25, 0.625, id="ogg-middle"),
        pytest.param("middle", "opus", 0.25, 0.625, id="opus-middle"),
        pytest.param("middle", "webm", 0.25, 0.625, id="webm-middle"),
    ],
)
def test_selected_one_shot_playback_respects_region_boundaries(
    anki_mw,
    ffmpeg_config,
    label: str,
    extension: str,
    start_ratio: float,
    end_ratio: float,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        f"editor_region_one_shot_{extension}_{label}.{extension}",
        2.0,
    )
    try:
        expected_start = round(track["durationMs"] * start_ratio)
        expected_end = round(track["durationMs"] * end_ratio)
        _shift_drag_region(editor, start_ratio, end_ratio)
        selected = _state(
            editor,
            lambda state: state["selectionStartMs"] == expected_start
            and state["selectionEndMs"] == expected_end,
        )
        assert selected["playbackRegionMode"] == "selection"

        max_progress = {"value": expected_start}

        def stopped_at_region_start(state) -> bool:
            max_progress["value"] = max(max_progress["value"], state["progressMs"])
            return (
                state["playbackState"] == "stopped"
                and state["playButtonLabel"] == "Play"
                and abs(state["cursorMs"] - expected_start) <= PLAYBACK_INTERVAL_TOLERANCE_MS
            )

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _state(
                editor,
                lambda state: state["playbackState"] == "playing"
                and state["playbackStartMs"] == expected_start
                and state["playbackEndMs"] == expected_end,
            )
            finished = _state(editor, stopped_at_region_start, timeout=6.0)

        assert playback.attempts == []
        assert finished["playbackStartMs"] == expected_start
        assert finished["playbackEndMs"] == expected_end
        assert finished["playbackRegionMode"] == "selection"
        assert max_progress["value"] <= expected_end + PLAYBACK_INTERVAL_TOLERANCE_MS * 3
    finally:
        editor.set_note(None)
        parent.close()


@pytest.mark.parametrize("extension", ["aac", "m4a"])
def test_native_selected_one_shot_playback_renders_only_selected_region(
    anki_mw,
    ffmpeg_config,
    extension: str,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        f"editor_region_native_one_shot.{extension}",
        2.0,
    )
    try:
        expected_start = round(track["durationMs"] * 0.25)
        expected_end = round(track["durationMs"] * 0.625)
        _shift_drag_region(editor, 0.25, 0.625)
        _force_native_playback(editor)

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _state(
                editor,
                lambda state: state["playbackState"] == "playing"
                and state["playbackEngine"] == "native"
                and state["playbackStartMs"] == expected_start
                and state["playbackEndMs"] == expected_end,
                timeout=6.0,
            )
            finished = _state(
                editor,
                lambda state: state["playbackState"] == "stopped"
                and abs(state["cursorMs"] - expected_start) <= PLAYBACK_INTERVAL_TOLERANCE_MS,
                timeout=6.0,
            )

        assert len(playback.attempts) == 1
        _assert_interval(playback.attempts[0], expected_start, expected_end_ms=expected_end)
        assert playback.attempts[0].path.parent.name.startswith("aqe_playback_")
        assert finished["playbackRegionMode"] == "selection"
    finally:
        editor.set_note(None)
        parent.close()


def test_selected_repeat_loops_pauses_resumes_and_can_finish_current_pass(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_repeat_middle.wav",
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
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 500)
            looped = [_force_repeat_wrap(editor, 500) for _ in range(3)]
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            paused = _state(
                editor,
                lambda state: state["playbackState"] == "paused"
                and state["playButtonLabel"] == "Play",
            )
            paused_progress = paused["progressMs"]
            pause_deadline = time.monotonic() + 0.35
            wait_for_condition(
                lambda: time.monotonic() >= pause_deadline,
                timeout=1.0,
                message="short selected repeat pause wait failed",
            )
            frozen = _state(editor)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            resumed = _wait_for_html_playback(
                editor,
                lambda state: 500 <= state["progressMs"] <= 1300,
            )
            _set_repeat(editor, False)
            _force_audio_boundary(editor)
            finished = _state(
                editor,
                lambda state: state["playbackState"] == "stopped"
                and state["cursorMs"] == 500
                and state["repeatEnabled"] is False,
                timeout=5.0,
            )

        assert playback.attempts == []
        assert len(looped) == 3
        assert looped[-1]["playButtonLabel"] == "Pause"
        assert abs(frozen["progressMs"] - paused_progress) < PLAYBACK_INTERVAL_TOLERANCE_MS * 2
        assert 500 <= resumed["progressMs"] <= 1300
        assert finished["playbackEndMs"] == 1300
    finally:
        editor.set_note(None)
        parent.close()


def _force_native_playback(editor, ord_: int = 0) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          const visualizer = document.querySelector('[data-testid="aqe-graph-{ord_}"]');
          if (!visualizer) return false;
          visualizer.__aqeAudioClockAvailable = false;
          visualizer.__aqeAudioClockFallback = true;
          visualizer.dataset.playbackEngine = "";
          return true;
        }})()
        """,
    )


def test_selected_repeat_waits_configured_pause_between_html_loop_passes(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_repeat_pause_middle.wav",
        2.0,
        repeat_pause_seconds=0.2,
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
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 600)
            _force_audio_boundary(editor)
            waiting = _state(
                editor,
                lambda state: state["playbackState"] == "playing"
                and state["progressClockMode"] == "stopped"
                and state["repeatPauseWaiting"] is True
                and state["repeatPauseSeconds"] == 0.2
                and abs(state["cursorMs"] - 500) <= PLAYBACK_INTERVAL_TOLERANCE_MS,
                timeout=2.0,
            )
            restarted = _wait_for_html_playback(
                editor,
                lambda state: state["repeatPauseWaiting"] is False
                and state["repeatPauseSeconds"] == 0.2
                and state["progressMs"] >= 500,
                timeout=5.0,
            )

        assert playback.attempts == []
        assert waiting["playButtonLabel"] == "Pause"
        assert restarted["playButtonLabel"] == "Pause"
    finally:
        editor.set_note(None)
        parent.close()


def test_repeat_playback_interactions_replace_clear_and_clamp_region(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_repeat_interactions.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.55)
        _set_repeat(editor, True)
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 600)

            _shift_drag_region(editor, 0.6, 0.85)
            replaced = _wait_for_html_playback(
                editor,
                lambda state: state["selectionStartMs"] == 1200
                and state["selectionEndMs"] == 1700
                and state["audioClockCurrentMs"] >= 1200 - PLAYBACK_INTERVAL_TOLERANCE_MS,
            )

            _normal_drag(editor, 0.1, 0.2)
            clamped = _wait_for_html_playback(
                editor,
                lambda state: state["selectionStartMs"] == 1200
                and state["cursorMs"] >= 1200 - PLAYBACK_INTERVAL_TOLERANCE_MS,
            )

            _shift_click_region(editor, 0.4)
            cleared = _wait_for_html_playback(
                editor,
                lambda state: state["selectionActive"] is False
                and state["playbackRegionMode"] == "full"
                and state["playbackEndMs"] == 2000,
            )

        assert playback.attempts == []
        assert replaced["playButtonLabel"] == "Pause"
        assert clamped["selectionEndMs"] == 1700
        assert cleared["repeatEnabled"] is True
    finally:
        editor.set_note(None)
        parent.close()


def test_processing_during_selected_repeat_stops_playback_and_redraw_clears_selection(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_repeat_process.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.65)
        _set_repeat(editor, True)
        previous_name = _sound_filename(note.fields[0])
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 650)
            click_selector(editor.web, _button_selector("aqe:volume-up"), timeout=5.0)
            stopped_for_processing = _state(
                editor,
                lambda state: state["playbackState"] == "stopped"
                and state["playButtonLabel"] == "Play"
                and state["allButtonsDisabled"] is True,
            )
            generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
            redrawn = _state(
                editor,
                lambda state: state["sourceFilename"] == generated_name
                and state["durationMs"] > 0
                and state["allButtonsDisabled"] is False
                and state["selectionActive"] is True
                and state["selectionStartMs"] == 0
                and abs(state["selectionEndMs"] - state["durationMs"]) <= 1
                and state["playbackRegionMode"] == "selection"
                and state["playbackState"] == "stopped",
                timeout=10.0,
            )

        assert playback.attempts == []
        assert stopped_for_processing["repeatEnabled"] is True
        assert redrawn["sourceFilename"] == generated_name
    finally:
        editor.set_note(None)
        parent.close()
