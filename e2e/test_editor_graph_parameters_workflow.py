"""E2E tests for graph algorithm parameters changing rendered pitch graphs."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from tests.prosody_language_fixtures import PRAAT_SKIP_REASON

from e2e.conftest import import_runtime_addon_module
from e2e.editor_graph_helpers import _click_graph_and_wait
from e2e.editor_language_helpers import _rendered_pitch_points_js
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.helpers import click_selector, wait_for_js_condition, wait_for_selector


@pytest.mark.praat
def test_graph_smoothness_changes_real_praat_rendered_pitch_density(
    anki_mw,
    ffmpeg_config,
) -> None:
    pytest.importorskip("parselmouth", reason=PRAAT_SKIP_REASON)
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_graph_params_praat_smoothness.wav"
    _generate_frequency_tone(ffmpeg_config, source, frequency_hz=440, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, graph_smoothness="raw")

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)

        default_track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name
            and value["analyzerName"] == "praat-parselmouth"
            and value["pitchPaths"] > 0,
        )
        default_points = _rendered_pitch_point_count(editor)

        _set_graph_range_option(editor, "smoothness", 3)
        smooth_track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name
            and value["analyzerName"] == "praat-parselmouth"
            and value["pitchPaths"] > 0,
            timeout=10.0,
        )
        smooth_points = wait_for_js_condition(
            editor.web,
            _rendered_pitch_points_js(),
            lambda value: value is not None and 0 < len(value["points"]) < default_points * 0.7,
            timeout=5.0,
        )

        assert smooth_track["pitchPaths"] == default_track["pitchPaths"]
        assert len(smooth_points["points"]) < default_points
    finally:
        editor.set_note(None)
        parent.close()


def test_graph_smoothness_changes_real_ffmpeg_pcm_rendered_pitch_density(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    prosody_analyzer = import_runtime_addon_module(".prosody_analyzer")

    monkeypatch.setattr(prosody_analyzer, "is_praat_available", lambda: False)
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_graph_params_fallback_smoothness.wav"
    _generate_frequency_tone(ffmpeg_config, source, frequency_hz=220, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, graph_smoothness="raw")

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)

        default_track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name
            and value["analyzerName"] == "ffmpeg-pcm"
            and value["pitchPaths"] > 0,
            timeout=10.0,
        )
        default_points = _rendered_pitch_point_count(editor)

        _set_graph_range_option(editor, "smoothness", 3)
        smooth_track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name
            and value["analyzerName"] == "ffmpeg-pcm"
            and value["pitchPaths"] > 0,
            timeout=10.0,
        )
        smooth_points = wait_for_js_condition(
            editor.web,
            _rendered_pitch_points_js(),
            lambda value: value is not None and 0 < len(value["points"]) < default_points * 0.7,
            timeout=5.0,
        )

        assert smooth_track["pitchPaths"] == default_track["pitchPaths"]
        assert len(smooth_points["points"]) < default_points
    finally:
        editor.set_note(None)
        parent.close()


def _set_graph_range_option(editor, option_slug: str, value: int) -> None:
    click_selector(editor.web, '[data-testid="aqe-split-0-graph-menu"]', timeout=5.0)
    selector = _graph_option_selector(option_slug, value)
    wait_for_selector(editor.web, selector, timeout=5.0)
    click_selector(editor.web, selector, timeout=5.0)
    state_key, expected = _expected_graph_state(option_slug, value)
    wait_for_js_condition(
        editor.web,
        """
        (() => {
          const state = window.__aqeSplitButtonStates?.[0];
          return state ? state[__STATE_KEY__] : null;
        })()
        """.replace("__STATE_KEY__", json.dumps(state_key)),
        lambda result: result == expected,
        timeout=5.0,
    )


def _expected_graph_state(option_slug: str, value: int) -> tuple[str, str | int]:
    if option_slug == "smoothness":
        return "graphSmoothness", ["raw", "balanced", "smooth", "very_smooth"][value]
    raise AssertionError(f"Unsupported graph option {option_slug!r}")


def _graph_option_selector(option_slug: str, value: int) -> str:
    if option_slug == "smoothness":
        option = ["raw", "balanced", "smooth", "very_smooth"][value]
        return f'[data-testid="aqe-split-0-graph-smoothness-{option}"]'
    raise AssertionError(f"Unsupported graph option {option_slug!r}")


def _generate_frequency_tone(
    ffmpeg_config,
    path: Path,
    *,
    frequency_hz: int,
    duration_s: float,
) -> None:
    _run_ffmpeg(
        ffmpeg_config,
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={frequency_hz}:duration={duration_s}",
        str(path),
    )


def _run_ffmpeg(ffmpeg_config, *args: str) -> None:
    subprocess.run(
        [ffmpeg_config.ffmpeg_path, "-y", *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _rendered_pitch_point_count(editor) -> int:
    rendered = wait_for_js_condition(
        editor.web,
        _rendered_pitch_points_js(),
        lambda value: value is not None and value["paths"] > 0 and bool(value["points"]),
        timeout=5.0,
    )
    return len(rendered["points"])
