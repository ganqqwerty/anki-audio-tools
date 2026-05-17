"""E2E tests for selected region playback and loop behavior."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_state_js,
    _install_html_audio_test_driver,
    _wait_for_html_playback,
    _wait_for_visualizer_track,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
    _wait_for_generated_mp3,
)
from e2e.editor_playback_helpers import (
    PLAYBACK_INTERVAL_TOLERANCE_MS,
    _record_fake_playback,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_js_condition,
)


def _open_tone_editor(anki_mw, ffmpeg_config, filename: str, duration_s: float, **config_overrides):
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / filename
    generate_tone(ffmpeg_config, source, duration_s=duration_s)
    note = _basic_audio_note(anki_mw, source.name)
    overrides = {"repeat_playback_by_default": False, **config_overrides}
    _configure_ffmpeg(anki_mw, ffmpeg_config, **overrides)
    editor, parent = _open_editor(anki_mw, note)
    track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
    _install_html_audio_test_driver(editor)
    return media_dir, source, note, editor, parent, track


def _plot_pointer_script(ord_: int, start_ratio: float, end_ratio: float, *, shift: bool, move: bool) -> str:
    return f"""
    (() => {{
      const ord = {ord_};
      const startRatio = {start_ratio};
      const endRatio = {end_ratio};
      const svg = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${{ord}}"] .aqe-visualizer-svg`);
      const rect = svg.getBoundingClientRect();
      const plot = {{ width: 620, left: 44, right: 10 }};
      const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
      const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
      const xFor = (ratio) => plotLeft + plotWidth * ratio;
      const EventCtor = window.PointerEvent || window.MouseEvent;
      svg.dispatchEvent(new EventCtor("pointerdown", {{
        bubbles: true,
        clientX: xFor(startRatio),
        clientY: rect.top + 20,
        shiftKey: {str(shift).lower()},
      }}));
      if ({str(move).lower()}) {{
        window.dispatchEvent(new EventCtor("pointermove", {{
          bubbles: true,
          clientX: xFor(endRatio),
          clientY: rect.top + 20,
          shiftKey: {str(shift).lower()},
        }}));
      }}
      window.dispatchEvent(new EventCtor("pointerup", {{
        bubbles: true,
        clientX: xFor(endRatio),
        clientY: rect.top + 20,
        shiftKey: {str(shift).lower()},
      }}));
    }})()
    """


def _plot_pointer_event_script(ord_: int, ratio: float, event_type: str, *, shift: bool) -> str:
    target = "svg" if event_type == "pointerdown" else "window"
    return f"""
    (() => {{
      const ord = {ord_};
      const ratio = {ratio};
      const svg = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${{ord}}"] .aqe-visualizer-svg`);
      const rect = svg.getBoundingClientRect();
      const plot = {{ width: 620, left: 44, right: 10 }};
      const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
      const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
      const x = plotLeft + plotWidth * ratio;
      const EventCtor = window.PointerEvent || window.MouseEvent;
      {target}.dispatchEvent(new EventCtor("{event_type}", {{
        bubbles: true,
        clientX: x,
        clientY: rect.top + 20,
        shiftKey: {str(shift).lower()},
      }}));
    }})()
    """


def _shift_pointer_down(editor, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_event_script(ord_, ratio, "pointerdown", shift=True))


def _shift_pointer_move(editor, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_event_script(ord_, ratio, "pointermove", shift=True))


def _shift_pointer_up(editor, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_event_script(ord_, ratio, "pointerup", shift=True))


def _shift_pointer_cancel(editor, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_event_script(ord_, ratio, "pointercancel", shift=True))


def _shift_drag_region(editor, start_ratio: float, end_ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_script(ord_, start_ratio, end_ratio, shift=True, move=True))


def _shift_click_region(editor, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_script(ord_, ratio, ratio, shift=True, move=False))


def _normal_drag(editor, start_ratio: float, end_ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_script(ord_, start_ratio, end_ratio, shift=False, move=True))


def _set_repeat(editor, enabled: bool, ord_: int = 0) -> None:
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const toggle = document.querySelector('[data-testid="aqe-repeat-{ord_}"]');
          if (!toggle) return null;
          const requested = {str(enabled).lower()};
          const current = toggle.getAttribute("aria-pressed") === "true";
          if (current !== requested) toggle.click();
          return toggle.getAttribute("aria-pressed") === "true";
        }})()
        """,
        lambda value: value is enabled,
        timeout=5.0,
    )


def _state(editor, predicate=lambda state: True, ord_: int = 0, timeout: float = 5.0):
    return wait_for_js_condition(
        editor.web,
        _graph_state_js(ord_),
        lambda state: state is not None and predicate(state),
        timeout=timeout,
    )


def _force_audio_boundary(editor, ord_: int = 0) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          const state = window.__aqeGraphStateForTest && window.__aqeGraphStateForTest({ord_});
          const audio = document.querySelector('[data-testid="aqe-audio-clock-{ord_}"]');
          if (!state || !audio) return false;
          audio.currentTime = state.playbackEndMs / 1000;
          audio.dispatchEvent(new Event("ended"));
          return true;
        }})()
        """,
    )


def _force_repeat_wrap(editor, expected_start_ms: int, ord_: int = 0):
    _force_audio_boundary(editor, ord_)
    return _state(
        editor,
        lambda state: state["playbackState"] == "playing"
        and abs(state["cursorMs"] - expected_start_ms) <= PLAYBACK_INTERVAL_TOLERANCE_MS
        and abs(state["audioClockCurrentMs"] - expected_start_ms) <= PLAYBACK_INTERVAL_TOLERANCE_MS,
        ord_=ord_,
        timeout=5.0,
    )


def _two_audio_field_note(anki_mw, audio_filenames: tuple[str, str]):
    models = anki_mw.col.models
    notetype = models.new("AQE E2E Region Two Audio Fields")
    for name in ("One", "Two"):
        models.add_field(notetype, models.new_field(name))
    template = models.new_template("Card 1")
    template["qfmt"] = "{{One}}"
    template["afmt"] = "{{FrontSide}}<hr>{{Two}}"
    models.add_template(notetype, template)
    models.add(notetype)
    note = anki_mw.col.new_note(notetype)
    for index, filename in enumerate(audio_filenames):
        note.fields[index] = f"Field {index + 1} [sound:{filename}]"
    deck_id = anki_mw.col.decks.id("Default")
    assert deck_id is not None
    anki_mw.col.add_note(note, deck_id)
    return note


def test_region_selection_gestures_create_replace_clamp_and_preserve_normal_cursor(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_selection_basics.wav",
        2.0,
    )
    try:
        _shift_pointer_down(editor, 0.25)
        pointer_down = _state(editor)
        assert pointer_down["selectionActive"] is False
        assert pointer_down["selectionDraftActive"] is False

        _shift_pointer_move(editor, 0.625)
        draft = _state(
            editor,
            lambda state: state["selectionActive"] is False
            and state["selectionDraftActive"] is True
            and state["selectionDraftStartMs"] == 500
            and state["selectionDraftEndMs"] == 1250,
        )
        assert draft["cursorMs"] == pointer_down["cursorMs"]

        _shift_pointer_move(editor, 0.75)
        updated_draft = _state(
            editor,
            lambda state: state["selectionDraftStartMs"] == 500
            and state["selectionDraftEndMs"] == 1500,
        )
        assert updated_draft["selectionActive"] is False

        _shift_pointer_move(editor, 0.625)
        _shift_pointer_up(editor, 0.625)
        committed = _state(
            editor,
            lambda state: state["selectionActive"] is True
            and state["selectionDraftActive"] is False
            and state["selectionStartMs"] == 500
            and state["selectionEndMs"] == 1250,
        )
        assert committed["cursorMs"] == 500

        _shift_drag_region(editor, 0.8, 0.3)
        reversed_selection = _state(
            editor,
            lambda state: state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600
            and state["selectionDraftActive"] is False,
        )
        assert reversed_selection["cursorMs"] == 600

        _shift_pointer_down(editor, 0.7)
        _shift_pointer_move(editor, 0.9)
        cancel_draft = _state(
            editor,
            lambda state: state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600
            and state["selectionDraftActive"] is True
            and state["selectionDraftStartMs"] == 1400
            and state["selectionDraftEndMs"] == 1800,
        )
        assert cancel_draft["selectionActive"] is True
        _shift_pointer_cancel(editor, 0.9)
        canceled = _state(
            editor,
            lambda state: state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600
            and state["selectionDraftActive"] is False,
        )
        assert canceled["selectionActive"] is True

        _normal_drag(editor, 0.9, 0.9)
        clicked = _state(editor, lambda state: 1750 <= state["cursorMs"] <= 1850)
        assert clicked["selectionStartMs"] == 600
        assert clicked["selectionEndMs"] == 1600

        _normal_drag(editor, 0.1, 0.4)
        dragged = _state(editor, lambda state: 750 <= state["cursorMs"] <= 850)
        assert dragged["selectionStartMs"] == 600
        assert dragged["selectionEndMs"] == 1600

        _shift_drag_region(editor, -0.25, 1.25)
        clamped = _state(
            editor,
            lambda state: state["selectionStartMs"] == 0 and state["selectionEndMs"] == 2000,
        )
        assert clamped["playbackRegionMode"] == "selection"

        run_js(editor.web, _plot_pointer_script(0, 0.4, 0.402, shift=True, move=True))
        cleared = _state(editor, lambda state: state["selectionActive"] is False)
        assert cleared["playbackRegionMode"] == "full"
    finally:
        editor.set_note(None)
        parent.close()


@pytest.mark.parametrize(
    ("label", "start_ratio", "end_ratio", "expected_start", "expected_end"),
    [
        ("middle", 0.25, 0.625, 500, 1250),
        ("full-explicit", 0.0, 1.0, 0, 2000),
        ("near-start", 0.0, 0.125, 0, 250),
        ("near-end", 0.875, 1.0, 1750, 2000),
    ],
)
def test_selected_one_shot_playback_respects_region_boundaries(
    anki_mw,
    ffmpeg_config,
    label: str,
    start_ratio: float,
    end_ratio: float,
    expected_start: int,
    expected_end: int,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        f"editor_region_one_shot_{label}.wav",
        2.0,
    )
    try:
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

            _normal_drag(editor, 0.1, 0.1)
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
                and state["selectionActive"] is False
                and state["playbackRegionMode"] == "full"
                and state["playbackState"] == "stopped",
                timeout=10.0,
            )

        assert playback.attempts == []
        assert stopped_for_processing["repeatEnabled"] is True
        assert redrawn["sourceFilename"] == generated_name
    finally:
        editor.set_note(None)
        parent.close()


def test_graph_default_auto_analysis_supports_region_selection(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_graph_default_region_selection.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        repeat_playback_by_default=False,
        show_graph_by_default=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        auto_track = _wait_for_visualizer_track(
            editor,
            lambda state: state["sourceFilename"] == source.name,
            timeout=10.0,
        )
        _shift_drag_region(editor, 0.2, 0.55)
        selected = _state(
            editor,
            lambda state: state["selectionActive"] is True
            and state["selectionStartMs"] == 400
            and state["selectionEndMs"] == 1100,
        )

        assert auto_track["active"] is True
        assert selected["playbackRegionMode"] == "selection"
        assert selected["repeatEnabled"] is False
    finally:
        editor.set_note(None)
        parent.close()


def test_graph_default_repeat_can_be_turned_off_for_selected_region_playback(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_graph_default_repeat_off.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        repeat_playback_by_default=True,
        show_graph_by_default=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _wait_for_visualizer_track(
            editor,
            lambda state: state["sourceFilename"] == source.name,
            timeout=10.0,
        )
        _install_html_audio_test_driver(editor)
        initial = _state(editor, lambda state: state["repeatEnabled"] is True)
        _shift_drag_region(editor, 0.25, 0.65)
        _set_repeat(editor, False)
        repeat_off = _state(
            editor,
            lambda state: state["repeatEnabled"] is False
            and state["selectionStartMs"] == 500
            and state["selectionEndMs"] == 1300,
        )

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            playing = _wait_for_html_playback(
                editor,
                lambda state: state["playbackStartMs"] == 500
                and state["playbackEndMs"] == 1300
                and state["repeatEnabled"] is False,
            )
            _force_audio_boundary(editor)
            finished = _state(
                editor,
                lambda state: state["playbackState"] == "stopped"
                and state["cursorMs"] == 500
                and state["repeatEnabled"] is False,
                timeout=5.0,
            )

        assert playback.attempts == []
        assert initial["repeatEnabled"] is True
        assert repeat_off["playbackRegionMode"] == "selection"
        assert playing["playButtonLabel"] == "Pause"
        assert finished["playButtonLabel"] == "Play"
    finally:
        editor.set_note(None)
        parent.close()


def test_two_audio_fields_keep_region_state_scoped_and_single_active_playback(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    first = media_dir / "editor_region_field_one.wav"
    second = media_dir / "editor_region_field_two.wav"
    generate_tone(ffmpeg_config, first, duration_s=2.0)
    generate_tone(ffmpeg_config, second, duration_s=1.0)
    note = _two_audio_field_note(anki_mw, (first.name, second.name))
    _configure_ffmpeg(anki_mw, ffmpeg_config, repeat_playback_by_default=False)

    editor, parent = _open_editor(anki_mw, note)
    try:
        first_track = _click_graph_and_wait(editor, lambda state: state["sourceFilename"] == first.name, ord_=0)
        second_track = _click_graph_and_wait(editor, lambda state: state["sourceFilename"] == second.name, ord_=1)
        _install_html_audio_test_driver(editor, ord_=0)
        _install_html_audio_test_driver(editor, ord_=1)
        _shift_drag_region(editor, 0.2, 0.6, ord_=0)
        _set_repeat(editor, True, ord_=0)
        _shift_drag_region(editor, 0.3, 0.5, ord_=1)

        with _record_fake_playback(
            media_dir,
            {
                first.name: round(first_track["durationMs"]),
                second.name: round(second_track["durationMs"]),
            },
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play", 0), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["selectionStartMs"] == 400, ord_=0)
            click_selector(editor.web, _button_selector("aqe:play", 1), timeout=5.0)
            second_playing = _wait_for_html_playback(
                editor,
                lambda state: state["selectionStartMs"] == 300,
                ord_=1,
            )
            first_stopped = _state(
                editor,
                lambda state: state["playbackState"] == "stopped"
                and state["selectionStartMs"] == 400
                and state["repeatEnabled"] is True,
                ord_=0,
            )

        active_field = wait_for_js_condition(
            editor.web,
            "window.__aqeActiveField",
            lambda value: value == 1,
            timeout=5.0,
        )
        assert playback.attempts == []
        assert active_field == 1
        assert first_stopped["sourceFilename"] == first.name
        assert second_playing["sourceFilename"] == second.name
        assert second_playing["repeatEnabled"] is False
    finally:
        editor.set_note(None)
        parent.close()


def test_note_switching_stops_looping_playback_and_clears_stale_selection(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    first = media_dir / "editor_region_note_a.wav"
    second = media_dir / "editor_region_note_b.wav"
    generate_tone(ffmpeg_config, first, duration_s=2.0)
    generate_tone(ffmpeg_config, second, duration_s=1.0)
    note_a = _basic_audio_note(anki_mw, first.name)
    note_b = _basic_audio_note(anki_mw, second.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, repeat_playback_by_default=False)

    editor, parent = _open_editor(anki_mw, note_a)
    try:
        first_track = _click_graph_and_wait(editor, lambda state: state["sourceFilename"] == first.name)
        _install_html_audio_test_driver(editor)
        _shift_drag_region(editor, 0.25, 0.65)
        _set_repeat(editor, True)
        with _record_fake_playback(
            media_dir,
            {first.name: round(first_track["durationMs"]), second.name: 1000},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 600)
            editor.set_note(note_b, hide=False, focusTo=0)
            reset_state = _state(
                editor,
                lambda state: state["playbackState"] == "stopped"
                and state["selectionActive"] is False
                and state["repeatEnabled"] is False,
            )
            second_track = _click_graph_and_wait(editor, lambda state: state["sourceFilename"] == second.name)
            second_state = _state(
                editor,
                lambda state: state["sourceFilename"] == second.name
                and state["selectionActive"] is False,
            )

        assert playback.attempts == []
        assert reset_state["hasTrack"] is False
        assert second_track["sourceFilename"] == second.name
        assert second_state["selectionActive"] is False
        assert second_track["audioClockSrc"].endswith(second.name)
    finally:
        editor.set_note(None)
        parent.close()


def test_repeat_default_config_initializes_editor_controls_and_selected_loop(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_repeat_default.wav",
        2.0,
        repeat_playback_by_default=True,
    )
    try:
        checked = _state(editor, lambda state: state["repeatEnabled"] is True)
        _shift_drag_region(editor, 0.25, 0.65)
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 500)
            looped = _force_repeat_wrap(editor, 500)

        assert playback.attempts == []
        assert checked["repeatEnabled"] is True
        assert looped["playbackState"] == "playing"
    finally:
        editor.set_note(None)
        parent.close()

    _configure_ffmpeg(anki_mw, ffmpeg_config, repeat_playback_by_default=False)
    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda state: state["sourceFilename"] == source.name)
        unchecked = _state(editor, lambda state: state["repeatEnabled"] is False)
        assert unchecked["repeatEnabled"] is False
    finally:
        editor.set_note(None)
        parent.close()
