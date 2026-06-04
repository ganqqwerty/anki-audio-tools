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


def test_selected_repeat_resume_finishes_current_pass_then_loops_from_selection_start(
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
            resumed = _wait_for_html_playback(
                editor,
                lambda state: state["progressMs"] >= paused["cursorMs"]
                and state["playbackStartMs"] > state["selectionStartMs"] + PLAYBACK_INTERVAL_TOLERANCE_MS,
            )
            looped = _force_repeat_wrap(editor, 500)

        assert playback.attempts == []
        assert resumed["playbackEndMs"] == 1300
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

        assert playback.attempts == []
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

        assert playback.attempts == []
        assert looped["hidden"] is True
        assert looped["hasTrack"] is False
        assert looped["playbackStartMs"] == 0
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

        assert playback.attempts == []
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
          visualizer.dataset.durationMs = String({duration_ms});
          visualizer.dataset.targetDurationMs = String({duration_ms});
          visualizer.dataset.playbackEndMs = String({duration_ms});
          visualizer.dataset.playbackRegionMode = "full";
          visualizer.dataset.playbackResetCursorMs = "0";
          visualizer.hidden = true;
          return window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest({ord_}) : null;
        }})()
        """,
        lambda state: state is not None
        and state["hidden"] is True
        and state["durationMs"] == duration_ms
        and state["targetDurationMs"] == duration_ms,
        timeout=5.0,
    )
