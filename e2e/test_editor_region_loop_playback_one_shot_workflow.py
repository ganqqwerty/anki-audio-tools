"""E2E tests for selected-region one-shot loop playback."""

from __future__ import annotations

from pathlib import Path

import pytest

from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _set_full_time_viewport,
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
    _open_tone_editor,
    _shift_drag_region,
    _state,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_js_condition,
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
def test_selected_one_shot_playback_warns_without_temporary_segment_when_browser_audio_rejects(
    anki_mw,
    ffmpeg_config,
    extension: str,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor_without_fake_audio(
        anki_mw,
        ffmpeg_config,
        f"editor_region_html_reject_one_shot.{extension}",
        2.0,
    )
    try:
        expected_start = round(track["durationMs"] * 0.25)
        expected_end = round(track["durationMs"] * 0.625)
        _shift_drag_region(editor, 0.25, 0.625)
        _force_html_audio_play_rejection(editor)

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
            max_attempt_count=0,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            failed = _state(
                editor,
                lambda state: state["playbackState"] == "stopped"
                and state["playbackEngine"] == "html",
                timeout=6.0,
            )
            wait_for_js_condition(
                editor.web,
                "document.querySelector('[data-testid=\"aqe-status-0\"]')?.textContent || ''",
                lambda text: text == "Browser audio is unavailable.",
                timeout=5.0,
            )

        assert playback.attempts == []
        assert failed["selectionStartMs"] == expected_start
        assert failed["selectionEndMs"] == expected_end
        assert failed["playbackRegionMode"] == "selection"
    finally:
        editor.set_note(None)
        parent.close()


def _open_tone_editor_without_fake_audio(anki_mw, ffmpeg_config, filename: str, duration_s: float):
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / filename
    generate_tone(ffmpeg_config, source, duration_s=duration_s)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, repeat_playback_by_default=False)
    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
    except Exception:
        editor.set_note(None)
        parent.close()
        raise
    _set_full_time_viewport(editor)
    return media_dir, source, note, editor, parent, track


def _force_html_audio_play_rejection(editor, ord_: int = 0) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          const visualizer = document.querySelector('[data-testid=\"aqe-graph-{ord_}\"]');
          const audio = document.querySelector('[data-testid=\"aqe-audio-clock-{ord_}\"]');
          if (!visualizer || !audio) return false;
          Object.defineProperty(audio, "duration", {{
            configurable: true,
            value: Number(visualizer.dataset.durationMs || "0") / 1000,
          }});
          Object.defineProperty(audio, "readyState", {{ configurable: true, value: 1 }});
          audio.pause = () => undefined;
          audio.play = () => Promise.reject(new Error("blocked-one-shot"));
          visualizer.__aqeAudioClockAvailable = true;
          visualizer.__aqeAudioClockFallback = false;
          window.__aqeSetFieldStateForTest?.({ord_}, {{ playback: {{ engine: "" }} }});
          audio.dispatchEvent(new Event("loadedmetadata"));
          return true;
        }})()
        """,
    )
