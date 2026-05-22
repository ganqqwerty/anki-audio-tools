"""E2E tests for editor prosody visualizer rendering behavior."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QApplication

from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_state_js,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _click_and_wait_for_new_file,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.helpers import (
    generate_tone,
    wait_for_js_condition,
    wait_for_selector,
)


def test_visualizer_renders_pitch_intensity_labels_and_cursor(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_visualizer_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
        initial = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None,
            timeout=5.0,
        )
        assert initial["active"] is False
        assert initial["hidden"] is True
        assert initial["graphButtonLabel"] == "Graph"

        track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name and value["pitchPaths"] > 0,
        )

        assert track["intensity"].startswith("M ")
        assert len(track["labels"]) == 2
        assert all(label.endswith(" Hz") for label in track["labels"])
        assert track["cursorX"]
        assert track["graphButtonLabel"] == "Redraw"
        assert any(label.endswith("ms") for label in track["xAxisLabels"])

        flag_geometry = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const svg = document.querySelector('.aqe-visualizer-svg');
              const notch = document.querySelector('.aqe-cursor-flag-notch');
              if (!svg || !notch) return null;
              const svgRect = svg.getBoundingClientRect();
              const notchRect = notch.getBoundingClientRect();
              const scale = Math.min(svgRect.width / 620, svgRect.height / 150) || 1;
              return {
                notchBottom: notchRect.bottom,
                plotTop: svgRect.top + 10 * scale,
              };
            })()
            """,
            lambda value: value is not None and abs(value["notchBottom"] - value["plotTop"]) <= 2,
            timeout=5.0,
        )
        assert abs(flag_geometry["notchBottom"] - flag_geometry["plotTop"]) <= 2
    finally:
        editor.set_note(None)
        parent.close()

def test_editor_controls_and_graph_are_dark_mode_aware(anki_mw, ffmpeg_config) -> None:
    from aqt.theme import Theme

    previous_theme = anki_mw.pm.theme()
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_dark_mode_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    try:
        anki_mw.set_theme(Theme.DARK)
        editor, parent = _open_editor(anki_mw, note)
        try:
            wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
            initial = wait_for_js_condition(
                editor.web,
                """
                (() => {
                  const buttons = Array.from(document.querySelectorAll('.aqe-button'));
                  return {
                    bodyNight: document.body.classList.contains('nightMode'),
                    htmlNight: document.documentElement.classList.contains('night-mode'),
                    bsTheme: document.documentElement.dataset.bsTheme || "",
                    iconsPerButton: buttons.map((button) => button.querySelectorAll('.aqe-button-icon svg').length),
                    iconStrokeValues: Array.from(document.querySelectorAll('.aqe-button .aqe-button-icon svg'))
                      .map((node) => node.getAttribute('stroke') || getComputedStyle(node).stroke || ''),
                    graphButtonState: document.querySelector('[data-testid="aqe-button-0-graph"]')?.dataset.aqeButtonState || "",
                    playButtonState: document.querySelector('[data-testid="aqe-button-0-play"]')?.dataset.aqeButtonState || "",
                  };
                })()
                """,
                lambda value: value is not None
                and value["htmlNight"] is True
                and value["bodyNight"] is True
                and value["bsTheme"] == "dark"
                and value["iconsPerButton"]
                and all(count >= 1 for count in value["iconsPerButton"])
                and all(stroke == "currentColor" for stroke in value["iconStrokeValues"])
                and value["graphButtonState"] == "graph"
                and value["playButtonState"] == "play",
                timeout=10.0,
            )
            assert initial["bodyNight"] is True

            track = _click_graph_and_wait(
                editor,
                lambda value: value["sourceFilename"] == source.name and value["pitchPaths"] > 0,
            )
            assert track["graphButtonLabel"] == "Redraw"
            assert track["graphButtonState"] == "redraw"

            graph_visibility = wait_for_js_condition(
                editor.web,
                """
                (() => {
                  const svg = document.querySelector('.aqe-visualizer-svg');
                  const pitch = document.querySelector('.aqe-pitch-path');
                  const intensity = document.querySelector('.aqe-intensity');
                  if (!svg || !pitch || !intensity) return null;
                  const pitchStyle = getComputedStyle(pitch);
                  const intensityStyle = getComputedStyle(intensity);
                  return {
                    color: getComputedStyle(svg).color,
                    intensityFill: intensityStyle.fill,
                    intensityPath: intensity.getAttribute('d') || "",
                    pitchStroke: pitchStyle.stroke,
                  };
                })()
                """,
                lambda value: value is not None
                and value["intensityPath"].startswith("M ")
                and value["pitchStroke"] not in ("", "none")
                and value["intensityFill"] not in ("", "none"),
                timeout=5.0,
            )
            assert graph_visibility["pitchStroke"] != "none"
        finally:
            editor.set_note(None)
            parent.close()
    finally:
        anki_mw.set_theme(previous_theme)
        QApplication.processEvents()


def test_visualizer_uses_second_axis_for_long_clip(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_visualizer_long_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=14.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)

        assert track["durationMs"] >= 13_500
        assert any(label.endswith("s") for label in track["xAxisLabels"])
        assert not any(label.endswith("ms") for label in track["xAxisLabels"])
    finally:
        editor.set_note(None)
        parent.close()


def test_graph_redraw_resets_after_audio_edit_when_active(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_graph_redraw_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        generated_name = _click_and_wait_for_new_file(
            editor, note, media_dir, "aqe:faster", source.name
        )
        track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == generated_name and value["cursorMs"] == 0,
            timeout=10.0,
        )

        assert track["graphButtonLabel"] == "Redraw"
        assert track["progressMs"] == 0
    finally:
        editor.set_note(None)
        parent.close()


def test_graph_hides_when_browser_editor_switches_to_another_note(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    first_source = media_dir / "editor_switch_note_one.wav"
    second_source = media_dir / "editor_switch_note_two.wav"
    generate_tone(ffmpeg_config, first_source, duration_s=1.0)
    generate_tone(ffmpeg_config, second_source, duration_s=1.0)
    first_note = _basic_audio_note(anki_mw, first_source.name)
    second_note = _basic_audio_note(anki_mw, second_source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, first_note)
    try:
        first_track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == first_source.name,
        )
        assert first_track["hidden"] is False

        editor.set_note(second_note, hide=False, focusTo=0)
        wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
        reset_state = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None
            and value["hidden"] is True
            and value["active"] is False
            and value["hasTrack"] is False
            and value["graphButtonLabel"] == "Graph",
            timeout=10.0,
        )

        assert reset_state["hidden"] is True
        assert reset_state["hasTrack"] is False

        second_track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == second_source.name,
        )
        assert second_track["sourceFilename"] == second_source.name
    finally:
        editor.set_note(None)
        parent.close()
