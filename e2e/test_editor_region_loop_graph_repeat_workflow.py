"""E2E tests for selected-region graph loop playback behavior."""

from __future__ import annotations

import json
from pathlib import Path

from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _install_html_audio_test_driver,
    _wait_for_html_playback,
    _wait_for_visualizer_track,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.editor_playback_helpers import (
    _assert_no_playback_leaks,
    _record_fake_playback,
)
from e2e.editor_region_loop_helpers import (
    _drag_resize_handle,
    _force_audio_boundary,
    _force_repeat_wrap,
    _open_tone_editor,
    _set_repeat,
    _shift_drag_region,
    _state,
    _two_audio_field_note,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js_condition,
)


def _force_html_audio_play_rejection(editor, expected_source: str, ord_: int = 0) -> None:
    expected_source_json = json.dumps(expected_source)
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const visualizer = document.querySelector('[data-testid="aqe-graph-{ord_}"]');
          const audio = document.querySelector('[data-testid="aqe-audio-clock-{ord_}"]');
          if (!visualizer || !audio) return null;
          if ((audio.getAttribute("src") || "") !== {expected_source_json}) return null;
          try {{
            Object.defineProperty(audio, "duration", {{
              configurable: true,
              value: Number(visualizer.dataset.durationMs || "0") / 1000,
            }});
            Object.defineProperty(audio, "readyState", {{ configurable: true, value: 1 }});
          }} catch (_error) {{
          }}
          audio.pause = () => undefined;
          audio.play = () => Promise.reject(new Error("blocked-aac"));
          visualizer.__aqeAudioClockAvailable = true;
          visualizer.__aqeAudioClockFallback = false;
          audio.dispatchEvent(new Event("loadedmetadata"));
          return {{
            ready: Boolean(visualizer.__aqeAudioClockAvailable),
            src: audio.getAttribute("src") || "",
          }};
        }})()
        """,
        lambda value: isinstance(value, dict)
        and value.get("ready") is True
        and value.get("src") == expected_source,
        timeout=5.0,
    )


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

        _assert_no_playback_leaks(playback)
        assert initial["repeatEnabled"] is True
        assert repeat_off["playbackRegionMode"] == "selection"
        assert playing["playButtonLabel"] == "Pause"
        assert finished["playButtonLabel"] == "Play"
    finally:
        editor.set_note(None)
        parent.close()


def test_aac_full_repeat_falls_back_to_native_when_browser_audio_rejects_after_graph(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_aac_full_repeat_browser_reject.aac"
    generate_tone(ffmpeg_config, source, duration_s=1.2)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        repeat_playback_by_default=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(
            editor,
            lambda state: state["sourceFilename"] == source.name,
            timeout=10.0,
        )
        _force_html_audio_play_rejection(editor, source.name)
        _state(
            editor,
            lambda state: state["repeatEnabled"] is True
            and state["playbackEngine"] == "html",
        )

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
            max_attempt_count=1,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            playing = _state(
                editor,
                lambda state: state["playbackState"] == "playing"
                and state["playbackEngine"] == "native",
                timeout=6.0,
            )
            wait_for_condition(
                lambda: len(playback.attempts) == 1,
                timeout=5.0,
                message="AAC full-repeat browser playback failure did not fall back to native playback",
            )

        _assert_no_playback_leaks(playback, expected_attempt_count=1)
        assert playback.attempts[0].filename == source.name
        assert playing["selectionStartMs"] == 0
        assert playing["selectionEndMs"] == round(track["durationMs"])
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
        first_track = _click_graph_and_wait(
            editor,
            lambda state: state["sourceFilename"] == first.name,
            ord_=0,
        )
        second_track = _click_graph_and_wait(
            editor,
            lambda state: state["sourceFilename"] == second.name,
            ord_=1,
        )
        _install_html_audio_test_driver(editor, ord_=0)
        _install_html_audio_test_driver(editor, ord_=1)
        _shift_drag_region(editor, 0.2, 0.6, ord_=0)
        _drag_resize_handle(editor, "end", 0.6, 0.75, ord_=0)
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
            _wait_for_html_playback(
                editor,
                lambda state: state["selectionStartMs"] == 400
                and state["selectionEndMs"] == 1500
                and state["playbackEndMs"] == 1500,
                ord_=0,
            )
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
                and state["selectionEndMs"] == 1500
                and state["repeatEnabled"] is True,
                ord_=0,
            )

        active_field = wait_for_js_condition(
            editor.web,
            "window.__aqeActiveField",
            lambda value: value == 1,
            timeout=5.0,
        )
        _assert_no_playback_leaks(playback)
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
        first_track = _click_graph_and_wait(
            editor,
            lambda state: state["sourceFilename"] == first.name,
        )
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
            second_track = _click_graph_and_wait(
                editor,
                lambda state: state["sourceFilename"] == second.name,
            )
            second_state = _state(
                editor,
                lambda state: state["sourceFilename"] == second.name
                and state["selectionActive"] is True
                and state["selectionStartMs"] == 0
                and state["selectionEndMs"] == 1000,
            )

        _assert_no_playback_leaks(playback)
        assert reset_state["hasTrack"] is False
        assert second_track["sourceFilename"] == second.name
        assert second_state["playbackRegionMode"] == "selection"
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

        _assert_no_playback_leaks(playback)
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
