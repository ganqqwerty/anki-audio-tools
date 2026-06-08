"""E2E tests for selected-region one-shot loop playback."""

from __future__ import annotations

import pytest

from e2e.editor_note_helpers import (
    _button_selector,
)
from e2e.editor_playback_helpers import (
    PLAYBACK_INTERVAL_TOLERANCE_MS,
    _assert_interval,
    _record_fake_playback,
)
from e2e.editor_region_loop_helpers import (
    _open_tone_editor,
    _shift_drag_region,
    _state,
)
from e2e.helpers import (
    click_selector,
    run_js,
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


def _force_native_playback(editor, ord_: int = 0) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          const visualizer = document.querySelector('[data-testid=\"aqe-graph-{ord_}\"]');
          if (!visualizer) return false;
          visualizer.__aqeAudioClockAvailable = false;
          visualizer.__aqeAudioClockFallback = true;
          visualizer.dataset.playbackEngine = "";
          return true;
        }})()
        """,
    )
