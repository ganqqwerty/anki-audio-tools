"""E2E tests for editor prosody graph rendering and graph state."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from e2e.editor_audio_generation_helpers import _generate_tone_silence_tone
from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_state_js,
    _visualizer_js,
    _wait_for_visualizer_track,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _click_and_wait_for_new_file,
    _configure_ffmpeg,
    _open_editor,
    _three_audio_field_note,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)
from e2e.test_settings_dialog import _open_settings_dialog


def _set_show_graph_by_default_from_settings(anki_mw, enabled: bool) -> None:
    dialog = _open_settings_dialog(anki_mw)
    checkbox_selector = '[data-testid="show-graph-by-default"]'
    save_selector = '[data-testid="settings-save"]'
    current = wait_for_js_condition(
        dialog,
        f"document.querySelector({json.dumps(checkbox_selector)})?.checked",
        lambda value: value in {True, False},
        timeout=5.0,
    )
    if current != enabled:
        click_selector(dialog, checkbox_selector, timeout=5.0)
        wait_for_js_condition(
            dialog,
            f"document.querySelector({json.dumps(checkbox_selector)})?.checked",
            lambda value: value is enabled,
            timeout=5.0,
        )

    with patch.object(
        anki_mw.addonManager,
        "writeConfig",
        wraps=anki_mw.addonManager.writeConfig,
    ) as mock_write:
        click_selector(dialog, save_selector, timeout=5.0)
        wait_for_condition(lambda: mock_write.called, timeout=5.0)

    saved_config = mock_write.call_args.args[1]
    assert saved_config["show_graph_by_default"] is enabled


def test_show_graph_by_default_auto_analyzes_all_audio_fields(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    sources = (
        media_dir / "editor_default_graph_one.wav",
        media_dir / "editor_default_graph_two.wav",
        media_dir / "editor_default_graph_three.wav",
    )
    for index, source in enumerate(sources):
        generate_tone(ffmpeg_config, source, duration_s=0.8 + index * 0.1)
    note = _three_audio_field_note(anki_mw, tuple(source.name for source in sources))
    _configure_ffmpeg(anki_mw, ffmpeg_config, show_graph_by_default=True)

    editor, parent = _open_editor(anki_mw, note)
    try:
        tracks = [
            _wait_for_visualizer_track(
                editor,
                lambda value, expected=source.name: value["sourceFilename"] == expected
                and value["pitchPaths"] > 0
                and value["graphButtonLabel"] == "Redraw",
                timeout=20.0,
                ord_=ord_,
            )
            for ord_, source in enumerate(sources)
        ]

        assert [track["sourceFilename"] for track in tracks] == [source.name for source in sources]
        assert all(track["active"] is True and track["hidden"] is False for track in tracks)
    finally:
        editor.set_note(None)
        parent.close()


def test_show_graph_default_setting_change_applies_to_later_editor_loads(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    enabled_source = media_dir / "editor_default_graph_setting_enabled.wav"
    disabled_source = media_dir / "editor_default_graph_setting_disabled.wav"
    generate_tone(ffmpeg_config, enabled_source, duration_s=0.9)
    generate_tone(ffmpeg_config, disabled_source, duration_s=0.9)
    enabled_note = _basic_audio_note(anki_mw, enabled_source.name)
    disabled_note = _basic_audio_note(anki_mw, disabled_source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, show_graph_by_default=False)

    _set_show_graph_by_default_from_settings(anki_mw, True)
    editor, parent = _open_editor(anki_mw, enabled_note)
    try:
        track = _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == enabled_source.name
            and value["graphButtonLabel"] == "Redraw",
            timeout=15.0,
        )
        assert track["active"] is True
    finally:
        editor.set_note(None)
        parent.close()

    _set_show_graph_by_default_from_settings(anki_mw, False)
    editor, parent = _open_editor(anki_mw, disabled_note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
        quiet_until = time.monotonic() + 1.0
        wait_for_condition(lambda: time.monotonic() >= quiet_until, timeout=2.0)
        state = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None,
            timeout=5.0,
        )

        assert state["active"] is False
        assert state["hidden"] is True
        assert state["sourceFilename"] == ""
        assert state["graphButtonLabel"] == "Graph"
    finally:
        editor.set_note(None)
        parent.close()


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
            editor, note, media_dir, "aqe:trim-left", source.name
        )
        track = _wait_for_visualizer_track(
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
            and value["sourceFilename"] == ""
            and value["graphButtonLabel"] == "Graph",
            timeout=10.0,
        )

        assert reset_state["hidden"] is True
        assert reset_state["sourceFilename"] == ""

        second_track = _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == second_source.name,
        )
        assert second_track["sourceFilename"] == second_source.name
    finally:
        editor.set_note(None)
        parent.close()


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
                    const cursorX = Number(document.querySelector('[data-testid="aqe-cursor-0"]').getAttribute('x1'));
                    const pixelX = renderedViewBoxLeft + cursorX * scale;
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
        "anki_audio_quick_editor.prosody_cache.analyze_prosody",
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
            editor, note, media_dir, "aqe:trim-left", source.name
        )

        assert generated_name != source.name
        assert (media_dir / generated_name).is_file()
    finally:
        editor.set_note(None)
        parent.close()
