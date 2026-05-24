"""E2E tests for visualizer cursor, silence, and failure edge cases."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from e2e.conftest import runtime_addon_import_path
from e2e.editor_audio_generation_helpers import _generate_tone_silence_tone
from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_state_js,
    _visualizer_js,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _click_and_wait_for_new_file,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_js_condition,
)


def test_redraw_button_resets_cursor_and_reanalyzes_current_clip(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_redraw_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        run_js(editor.web, "window.__aqeSetCursorForTest(0, 1500, false)")
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and state["cursorMs"] == 1500,
            timeout=5.0,
        )
        track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name and value["cursorMs"] == 0,
            timeout=10.0,
        )

        assert track["graphButtonLabel"] == "Redraw"
    finally:
        editor.set_note(None)
        parent.close()


def test_cursor_normalization_matches_pointer_position_at_multiple_widths(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_cursor_width_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        for width in (640, 1000, 1400):
            parent.resize(width, 900)
            resize_deadline = time.monotonic() + 0.1
            wait_for_condition(
                lambda deadline=resize_deadline: time.monotonic() >= deadline,
                timeout=1.0,
            )
            error = wait_for_js_condition(
                editor.web,
                """
                (() => {
                  const ord = 0;
                  const svg = document.querySelector('.aqe-visualizer[data-aqe-field-ord="0"] .aqe-visualizer-svg');
                  if (!svg || !window.__aqeSetCursorByClientXForTest) return 999;
                  const rect = svg.getBoundingClientRect();
                  const viewBoxWidth = 620;
                  const viewBoxHeight = 150;
                  const plotLeft = 44;
                  const plotWidth = 566;
                  const scale = Math.min(rect.width / viewBoxWidth, rect.height / viewBoxHeight);
                  const renderedViewBoxLeft = rect.left + (rect.width - viewBoxWidth * scale) / 2;
                  const renderedPlotLeft = renderedViewBoxLeft + plotLeft * scale;
                  const renderedPlotWidth = plotWidth * scale;
                  return Math.max(...[0.25, 0.5, 0.75].map((ratio) => {
                    const targetX = renderedPlotLeft + renderedPlotWidth * ratio;
                    const result = window.__aqeSetCursorByClientXForTest(ord, targetX, false);
                    if (!result || !result.bounds) return 999;
                    const pixelX = renderedViewBoxLeft + result.cursorX * scale;
                    return Math.abs(pixelX - targetX);
                  }));
                })()
                """,
                lambda value: isinstance(value, (int, float)) and value < 4,
                timeout=5.0,
            )
            assert error < 4
    finally:
        editor.set_note(None)
        parent.close()


def test_visualizer_splits_internal_silence_into_separate_pitch_paths(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_visualizer_tone_silence_tone.wav"
    _generate_tone_silence_tone(ffmpeg_config, source)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name and value["pitchPaths"] >= 2,
        )

        assert track["pitchPaths"] >= 2
        assert track["intensity"].startswith("M ")
    finally:
        editor.set_note(None)
        parent.close()


def test_silence_visualizer_renders_pitch_gaps_without_crashing(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_silence_source.wav"

    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=16000:cl=mono:d=0.7",
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)

        assert track["intensity"].startswith("M ")
        assert track["pitchPaths"] == 0
    finally:
        editor.set_note(None)
        parent.close()


def test_visualizer_failure_is_non_mutating_and_edit_buttons_still_work(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_visualizer_failure_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.2)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    monkeypatch.setattr(
        runtime_addon_import_path(".prosody_cache", "analyze_prosody"),
        lambda *_args: (_ for _ in ()).throw(RuntimeError("visualizer exploded")),
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        click_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
        wait_for_js_condition(
            editor.web,
            _visualizer_js(),
            lambda value: value is not None
            and value["statusKind"] == "error"
            and "visualizer exploded" in value["status"],
            timeout=10.0,
        )
        generated_name = _click_and_wait_for_new_file(
            editor, note, media_dir, "aqe:faster", source.name
        )

        assert generated_name != source.name
        assert (media_dir / generated_name).is_file()
    finally:
        editor.set_note(None)
        parent.close()
