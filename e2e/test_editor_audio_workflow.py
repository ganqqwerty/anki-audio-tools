"""E2E tests for the real inline editor audio workflow."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

from PyQt6.QtWidgets import QWidget

from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)

ADDON_NUMERIC_ID = "1000000002"


def _basic_audio_note(anki_mw, audio_filename: str):
    notetype = anki_mw.col.models.by_name("Basic")
    assert notetype is not None
    note = anki_mw.col.new_note(notetype)
    note["Front"] = f"Prompt [sound:{audio_filename}]"
    note["Back"] = "Back"
    deck_id = anki_mw.col.decks.id("Default")
    assert deck_id is not None
    anki_mw.col.add_note(note, deck_id)
    return note


def _three_audio_field_note(anki_mw, audio_filenames: tuple[str, str, str]):
    models = anki_mw.col.models
    notetype = models.new("AQE E2E Three Audio Fields")
    for name in ("One", "Two", "Three"):
        models.add_field(notetype, models.new_field(name))
    template = models.new_template("Card 1")
    template["qfmt"] = "{{One}}"
    template["afmt"] = "{{FrontSide}}<hr>{{Two}} {{Three}}"
    models.add_template(notetype, template)
    models.add(notetype)
    note = anki_mw.col.new_note(notetype)
    for index, filename in enumerate(audio_filenames):
        note.fields[index] = f"Field {index + 1} [sound:{filename}]"
    deck_id = anki_mw.col.decks.id("Default")
    assert deck_id is not None
    anki_mw.col.add_note(note, deck_id)
    return note


def _sound_filename(field_html: str) -> str:
    match = re.search(r"\[sound:([^\]]+)\]", field_html)
    assert match is not None
    return match.group(1)


def _configure_ffmpeg(anki_mw, ffmpeg_config, **overrides: Any) -> None:
    config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
    config.update({"ffmpeg_path": ffmpeg_config.ffmpeg_path, **overrides})
    anki_mw.addonManager.writeConfig(ADDON_NUMERIC_ID, config)


def _button_selector(command: str, ord_: int = 0) -> str:
    return f'.aqe-controls[data-aqe-field-ord="{ord_}"] [data-aqe-command="{command}"]'


def _open_editor(anki_mw, note):
    from aqt.editor import Editor, EditorMode

    parent = QWidget()
    container = QWidget(parent)
    parent.resize(1400, 900)
    parent.show()
    editor = Editor(anki_mw, container, parent, editor_mode=EditorMode.BROWSER)
    editor.set_note(note, hide=False, focusTo=0)
    return editor, parent


def _wait_for_generated_mp3(note, media_dir: Path, previous_name: str, field_index: int = 0) -> str:
    wait_for_condition(
        lambda: (
            (filename := _sound_filename(note.fields[field_index])) != previous_name
            and "__aqe_" in filename
            and filename.endswith(".mp3")
            and (media_dir / filename).is_file()
        ),
        timeout=10.0,
        message="Editor did not replace the field with a newly generated MP3",
    )
    return _sound_filename(note.fields[field_index])


def _click_and_wait_for_new_file(
    editor,
    note,
    media_dir: Path,
    command: str,
    previous_name: str,
    field_index: int = 0,
) -> str:
    click_selector(editor.web, _button_selector(command, field_index), timeout=5.0)
    return _wait_for_generated_mp3(note, media_dir, previous_name, field_index)


def _processing_status_js() -> str:
    return """
    (() => {
      const status = document.querySelector('.aqe-controls[data-aqe-field-ord="0"] .aqe-status');
      return status ? { text: status.textContent, title: status.title } : null;
    })()
    """


def _visualizer_js(ord_: int = 0) -> str:
    return """
    (() => {
      const ord = __ORD__;
      const visualizer = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${ord}"]`);
      if (!visualizer) return null;
      const labels = Array.from(visualizer.querySelectorAll('.aqe-hz-label')).map((node) => node.textContent);
      return {
        active: visualizer.dataset.graphActive === "true",
        busy: visualizer.dataset.graphBusy === "true",
        hidden: visualizer.hidden,
        durationMs: Number(visualizer.dataset.durationMs || "0"),
        sourceFilename: visualizer.dataset.sourceFilename || "",
        analyzerName: visualizer.dataset.analyzerName || "",
        anchorMs: Number(visualizer.dataset.anchorMs || "0"),
        cursorMs: Number(visualizer.dataset.cursorMs || "0"),
        progressMs: Number(visualizer.dataset.progressMs || "0"),
        resumeRequiresRestart: visualizer.dataset.resumeRequiresRestart === "true",
        intensity: visualizer.querySelector('.aqe-intensity')?.getAttribute('d') || "",
        pitchPaths: visualizer.querySelectorAll('.aqe-pitch-path').length,
        xAxisLabels: Array.from(visualizer.querySelectorAll('.aqe-x-label')).map((node) => node.textContent),
        labels,
        cursorX: visualizer.querySelector('.aqe-cursor')?.getAttribute('x1') || "",
        status: visualizer.querySelector('.aqe-visualizer-status')?.textContent || "",
        statusKind: visualizer.querySelector('.aqe-visualizer-status')?.dataset.kind || "",
        graphButtonLabel: document.querySelector(`[data-testid="aqe-button-${ord}-graph"]`)?.textContent || "",
        playButtonLabel: document.querySelector(`[data-testid="aqe-button-${ord}-play"]`)?.textContent || "",
        allButtonsDisabled: Array.from(document.querySelectorAll('.aqe-button')).every((button) => button.disabled),
      };
    })()
    """.replace("__ORD__", json.dumps(ord_))


def _wait_for_visualizer_track(editor, predicate=lambda track: True, timeout: float = 10.0, ord_: int = 0):
    return wait_for_js_condition(
        editor.web,
        _visualizer_js(ord_),
        lambda track: track is not None
        and track["durationMs"] > 0
        and track["allButtonsDisabled"] is False
        and predicate(track),
        timeout=timeout,
    )


def _graph_state_js(ord_: int = 0) -> str:
    return f"window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest({ord_}) : null"


def _click_graph_and_wait(editor, predicate=lambda track: True, ord_: int = 0, timeout: float = 10.0):
    selector = f'[data-testid="aqe-button-{ord_}-graph"]'
    wait_for_selector(editor.web, selector, timeout=5.0)
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const button = document.querySelector({json.dumps(selector)});
          if (!button) return null;
          button.click();
          return window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest({ord_}) : null;
        }})()
        """,
        lambda state: state is not None and state["active"] is True,
        timeout=5.0,
    )
    return _wait_for_visualizer_track(editor, predicate, timeout=timeout, ord_=ord_)


def _drag_cursor_to_ratio(editor, ratio: float, ord_: int = 0) -> None:
    run_js(
        editor.web,
        """
        (() => {
          const ord = __ORD__;
          const ratio = __RATIO__;
          const svg = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${ord}"] .aqe-visualizer-svg`);
          const rect = svg.getBoundingClientRect();
          const plot = { width: 620, left: 44, right: 10 };
          const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
          const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
          const x = plotLeft + plotWidth * ratio;
          const EventCtor = window.PointerEvent || window.MouseEvent;
          svg.dispatchEvent(new EventCtor('pointerdown', { clientX: x, clientY: rect.top + 20, bubbles: true }));
          window.dispatchEvent(new EventCtor('pointerup', { clientX: x, clientY: rect.top + 20, bubbles: true }));
        })()
        """.replace("__ORD__", json.dumps(ord_)).replace("__RATIO__", json.dumps(ratio)),
    )


def test_each_processing_button_updates_field_to_new_real_audio(anki_mw, ffmpeg_config) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_each_button_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        assert wait_for_js_condition(
            editor.web,
            "Array.from(document.querySelectorAll('[data-aqe-command]')).map((node) => node.dataset.aqeCommand)",
            lambda commands: all(
                command not in commands
                for command in (
                    "aqe:save",
                    "aqe:cancel",
                    "aqe:untrim-left",
                    "aqe:untrim-right",
                )
            ),
            timeout=5.0,
        )
        assert wait_for_js_condition(
            editor.web,
            """
            Array.from(document.querySelectorAll('.aqe-button'))
              .map((node) => node.textContent.trim())
            """,
            lambda labels: labels
            == ["Play", "Graph", "-L", "-R", "Trim Silence", "Remove Pauses", "Slower", "Faster", "Undo"],
            timeout=5.0,
        )

        previous_name = source.name
        generated_names: list[str] = []
        for command in (
            "aqe:trim-left",
            "aqe:trim-right",
            "aqe:slower",
            "aqe:faster",
            "aqe:trim-silence",
            "aqe:remove-pauses",
        ):
            wait_for_selector(editor.web, _button_selector(command), timeout=5.0)
            previous_name = _click_and_wait_for_new_file(editor, note, media_dir, command, previous_name)
            generated_names.append(previous_name)

        assert len(generated_names) == len(set(generated_names))
        assert source.read_bytes() == original_bytes
        assert probe_duration_ms(media_dir / generated_names[0], ffmpeg_config) < probe_duration_ms(
            source, ffmpeg_config
        )
        graph_state = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None,
            timeout=5.0,
        )
        assert graph_state["active"] is False
        assert graph_state["hidden"] is True
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
                  const targetX = rect.left + rect.width * 0.73;
                  const result = window.__aqeSetCursorByClientXForTest(ord, targetX, false);
                  if (!result || !result.bounds) return 999;
                  const cursorX = Number(document.querySelector('[data-testid="aqe-cursor-0"]').getAttribute('x1'));
                  const pixelX = result.bounds.left + ((cursorX - 44) / 566) * result.bounds.width;
                  return Math.abs(pixelX - targetX);
                })()
                """,
                lambda value: isinstance(value, (int, float)) and value < 4,
                timeout=5.0,
            )
            assert error < 4
    finally:
        editor.set_note(None)
        parent.close()


def test_cursor_drag_updates_session_and_play_uses_seek(anki_mw, ffmpeg_config) -> None:
    from aqt.sound import av_player

    from anki_audio_quick_editor.editor_integration import _SESSIONS

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_cursor_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    seek_calls: list[float] = []
    toggle_calls: list[str] = []
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        run_js(
            editor.web,
            """
            (() => {
              const svg = document.querySelector('.aqe-visualizer[data-aqe-field-ord="0"] .aqe-visualizer-svg');
              const rect = svg.getBoundingClientRect();
              const EventCtor = window.PointerEvent || window.MouseEvent;
              const x = rect.left + rect.width * 0.65;
              svg.dispatchEvent(new EventCtor('pointerdown', { clientX: x, clientY: rect.top + 20, bubbles: true }));
              window.dispatchEvent(new EventCtor('pointerup', { clientX: x, clientY: rect.top + 20, bubbles: true }));
            })()
            """,
        )
        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.cursor_ms >= 1000
            ),
            timeout=5.0,
            message="Dragging the visualizer cursor did not update the editor session",
        )
        track = _wait_for_visualizer_track(editor, lambda value: value["cursorMs"] >= 1000)

        with (
            patch.object(av_player, "stop_and_clear_queue", lambda: None),
            patch.object(av_player, "play_tags", lambda _tags: None),
            patch.object(av_player, "seek_relative", lambda seconds: seek_calls.append(seconds)),
            patch.object(av_player, "toggle_pause", lambda: toggle_calls.append("toggle")),
        ):
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_condition(
                lambda: bool(seek_calls),
                timeout=5.0,
                message="Playback did not attempt to seek from the selected cursor",
            )
            progressed = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None and state["progressMs"] > track["cursorMs"] + 120,
                timeout=5.0,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            paused = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None and state["playbackState"] == "paused",
                timeout=5.0,
            )
            paused_progress = paused["progressMs"]
            pause_deadline = time.monotonic() + 0.35
            wait_for_condition(
                lambda: time.monotonic() >= pause_deadline,
                timeout=1.0,
                message="short playback pause wait failed",
            )
            frozen = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None,
                timeout=2.0,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None and state["progressMs"] > paused_progress + 120,
                timeout=5.0,
            )

        assert seek_calls[0] >= track["cursorMs"] / 1000 - 0.05
        assert progressed["playButtonLabel"] == "Pause"
        assert abs(frozen["progressMs"] - paused_progress) < 80
        assert len(toggle_calls) >= 2
    finally:
        editor.set_note(None)
        parent.close()


def test_pause_drag_then_play_restarts_from_dragged_cursor(anki_mw, ffmpeg_config) -> None:
    from aqt.sound import av_player

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_pause_drag_play_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    seek_calls: list[float] = []
    play_calls: list[str] = []
    toggle_calls: list[str] = []
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        with (
            patch.object(av_player, "stop_and_clear_queue", lambda: None),
            patch.object(av_player, "play_tags", lambda _tags: play_calls.append("play")),
            patch.object(av_player, "seek_relative", lambda seconds: seek_calls.append(seconds)),
            patch.object(av_player, "toggle_pause", lambda: toggle_calls.append("toggle")),
        ):
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None and state["progressMs"] >= 500,
                timeout=5.0,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None and state["playbackState"] == "paused",
                timeout=5.0,
            )
            _drag_cursor_to_ratio(editor, 0.40)
            dragged = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None
                and state["resumeRequiresRestart"] is True
                and 700 <= state["cursorMs"] <= 900,
                timeout=5.0,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_condition(
                lambda: len(play_calls) >= 2 and bool(seek_calls) and seek_calls[-1] >= 0.75,
                timeout=5.0,
                message="Playback did not restart from the cursor selected while paused",
            )

        assert dragged["anchorMs"] == dragged["cursorMs"]
        assert len(toggle_calls) == 1
    finally:
        editor.set_note(None)
        parent.close()


def test_playback_completion_clears_status_and_returns_cursor_to_anchor(anki_mw, ffmpeg_config) -> None:
    from aqt.sound import av_player

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_playback_finish_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    seek_calls: list[float] = []
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        run_js(editor.web, "window.__aqeSetCursorForTest(0, 300, false)")
        with (
            patch.object(av_player, "stop_and_clear_queue", lambda: None),
            patch.object(av_player, "play_tags", lambda _tags: None),
            patch.object(av_player, "seek_relative", lambda seconds: seek_calls.append(seconds)),
            patch.object(av_player, "toggle_pause", lambda: None),
        ):
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_condition(
                lambda: bool(seek_calls),
                timeout=5.0,
                message="Playback did not seek from the selected anchor before completion",
            )
            finished = wait_for_js_condition(
                editor.web,
                """
                (() => {
                  const state = window.__aqeGraphStateForTest ? window.__aqeGraphStateForTest(0) : null;
                  const status = document.querySelector('.aqe-controls[data-aqe-field-ord="0"] .aqe-status')?.textContent || "";
                  return state ? { ...state, status } : null;
                })()
                """,
                lambda state: state is not None
                and state["playbackState"] == "stopped"
                and state["playButtonLabel"] == "Play"
                and state["status"] == ""
                and state["cursorMs"] == 300,
                timeout=5.0,
            )

        assert finished["anchorMs"] == 300
        assert seek_calls and seek_calls[0] >= 0.25
    finally:
        editor.set_note(None)
        parent.close()


def test_drag_while_playing_restarts_playback_from_released_cursor(anki_mw, ffmpeg_config) -> None:
    from aqt.sound import av_player

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_drag_while_playing_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    seek_calls: list[float] = []
    play_calls: list[str] = []
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        with (
            patch.object(av_player, "stop_and_clear_queue", lambda: None),
            patch.object(av_player, "play_tags", lambda _tags: play_calls.append("play")),
            patch.object(av_player, "seek_relative", lambda seconds: seek_calls.append(seconds)),
            patch.object(av_player, "toggle_pause", lambda: None),
        ):
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None
                and state["playbackState"] == "playing"
                and state["progressMs"] >= 250,
                timeout=5.0,
            )
            _drag_cursor_to_ratio(editor, 0.75)
            restarted = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None
                and state["playbackState"] == "playing"
                and 1400 <= state["anchorMs"] <= 1600,
                timeout=5.0,
            )
            wait_for_condition(
                lambda: len(play_calls) >= 2 and bool(seek_calls) and seek_calls[-1] >= 1.4,
                timeout=5.0,
                message="Dragging while playing did not restart playback from release point",
            )

        assert restarted["playButtonLabel"] == "Pause"
    finally:
        editor.set_note(None)
        parent.close()


def test_silence_visualizer_renders_pitch_gaps_without_crashing(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_silence_source.wav"
    import subprocess

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
        "anki_audio_quick_editor.editor_integration.analyze_prosody",
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


def test_ffmpeg_command_status_respects_settings_flag(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    hidden_source = media_dir / "editor_hidden_command_source.wav"
    shown_source = media_dir / "editor_shown_command_source.wav"
    generate_tone(ffmpeg_config, hidden_source, duration_s=2.0)
    generate_tone(ffmpeg_config, shown_source, duration_s=2.0)

    hidden_note = _basic_audio_note(anki_mw, hidden_source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, show_ffmpeg_commands=False)
    hidden_editor, hidden_parent = _open_editor(anki_mw, hidden_note)
    try:
        wait_for_selector(hidden_editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        click_selector(hidden_editor.web, _button_selector("aqe:trim-left"), timeout=5.0)
        hidden_status = wait_for_js_condition(
            hidden_editor.web,
            _processing_status_js(),
            lambda status: status is not None and status["text"].startswith("Processing with ffmpeg"),
            timeout=5.0,
        )
        assert " -i " not in hidden_status["text"]
        assert hidden_status["title"] == ""
        _wait_for_generated_mp3(hidden_note, media_dir, hidden_source.name)
    finally:
        hidden_editor.set_note(None)
        hidden_parent.close()

    shown_note = _basic_audio_note(anki_mw, shown_source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, show_ffmpeg_commands=True)
    shown_editor, shown_parent = _open_editor(anki_mw, shown_note)
    try:
        wait_for_selector(shown_editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        click_selector(shown_editor.web, _button_selector("aqe:trim-left"), timeout=5.0)
        shown_status = wait_for_js_condition(
            shown_editor.web,
            _processing_status_js(),
            lambda status: status is not None and " -i " in status["text"],
            timeout=5.0,
        )
        assert shown_status["title"].startswith(ffmpeg_config.ffmpeg_path)
        _wait_for_generated_mp3(shown_note, media_dir, shown_source.name)
    finally:
        shown_editor.set_note(None)
        shown_parent.close()


def test_undo_restores_previous_generated_reference(anki_mw, ffmpeg_config) -> None:
    from aqt.sound import av_player

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_undo_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        with (
            patch.object(av_player, "stop_and_clear_queue", lambda: None),
            patch.object(av_player, "play_tags", lambda _tags: None),
            patch.object(av_player, "seek_relative", lambda _seconds: None),
            patch.object(av_player, "toggle_pause", lambda: None),
        ):
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)

        previous_name = source.name
        generated_names: list[str] = []
        for command in ("aqe:trim-left", "aqe:faster", "aqe:trim-right", "aqe:trim-silence"):
            previous_name = _click_and_wait_for_new_file(
                editor, note, media_dir, command, previous_name
            )
            generated_names.append(previous_name)
            _wait_for_visualizer_track(
                editor,
                lambda value, expected=previous_name: value["sourceFilename"] == expected,
                timeout=10.0,
            )

        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == generated_names[-2],
            timeout=5.0,
            message="Undo did not restore the previous generated audio reference",
        )
        restored_track = _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_names[-2],
            timeout=10.0,
        )

        assert len(generated_names) == len(set(generated_names))
        assert restored_track["sourceFilename"] == generated_names[-2]
        assert all((media_dir / name).is_file() for name in generated_names)
    finally:
        editor.set_note(None)
        parent.close()


def test_fast_clicks_are_ignored_while_processing(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_fast_click_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=3.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        selector = _button_selector("aqe:trim-left")
        wait_for_selector(editor.web, selector, timeout=10.0)
        run_js(
            editor.web,
            f"""
            const button = document.querySelector({json.dumps(selector)});
            for (let i = 0; i < 5; i++) button.click();
            """,
        )
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)

        generated_for_source = list(media_dir.glob("editor_fast_click_source__aqe_*.mp3"))
        assert generated_for_source == [media_dir / generated_name]
        assert (media_dir / generated_name).is_file()
    finally:
        editor.set_note(None)
        parent.close()


def test_three_audio_fields_fast_cross_clicks_lock_globally_and_do_not_corrupt_fields(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    sources = (
        media_dir / "editor_three_fields_one.wav",
        media_dir / "editor_three_fields_two.wav",
        media_dir / "editor_three_fields_three.wav",
    )
    for source in sources:
        generate_tone(ffmpeg_config, source, duration_s=3.0)
    note = _three_audio_field_note(anki_mw, tuple(source.name for source in sources))
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left", 0), timeout=10.0)
        wait_for_selector(editor.web, _button_selector("aqe:faster", 1), timeout=10.0)
        wait_for_selector(editor.web, _button_selector("aqe:trim-right", 2), timeout=10.0)
        locked = wait_for_js_condition(
            editor.web,
            """
            (() => {
              document.querySelector('[data-testid="aqe-button-0-trim-left"]').click();
              const lockedAfterFirst = Array.from(document.querySelectorAll('.aqe-button')).every((button) => button.disabled);
              const firstButton = document.querySelector('[data-testid="aqe-button-0-trim-left"]');
              const controls = document.querySelector('[data-testid="aqe-controls-0"]');
              const buttonStyle = getComputedStyle(firstButton);
              const controlsStyle = getComputedStyle(controls);
              document.querySelector('[data-testid="aqe-button-1-faster"]').click();
              document.querySelector('[data-testid="aqe-button-2-trim-right"]').click();
              return {
                lockedAfterFirst,
                cursor: buttonStyle.cursor,
                opacity: Number(buttonStyle.opacity),
                borderStyle: controlsStyle.borderTopStyle
              };
            })()
            """,
            lambda value: value is not None and value["lockedAfterFirst"] is True,
            timeout=5.0,
        )
        generated_name = _wait_for_generated_mp3(note, media_dir, sources[0].name, field_index=0)
        unlocked = wait_for_js_condition(
            editor.web,
            _graph_state_js(0),
            lambda state: state is not None and state["allButtonsDisabled"] is False,
            timeout=5.0,
        )

        assert locked["lockedAfterFirst"] is True
        assert locked["cursor"] == "not-allowed"
        assert locked["opacity"] < 0.7
        assert locked["borderStyle"] == "dashed"
        assert unlocked["allButtonsDisabled"] is False
        assert _sound_filename(note.fields[0]) == generated_name
        assert _sound_filename(note.fields[1]) == sources[1].name
        assert _sound_filename(note.fields[2]) == sources[2].name
        assert list(media_dir.glob("editor_three_fields_one__aqe_*.mp3")) == [media_dir / generated_name]
    finally:
        editor.set_note(None)
        parent.close()


def test_settings_trim_step_controls_editor_button_behavior(anki_mw, ffmpeg_config) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms
    from anki_audio_quick_editor.editor_integration import _SESSIONS

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_settings_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, manual_trim_small_ms=500)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        generated_name = _click_and_wait_for_new_file(
            editor, note, media_dir, "aqe:trim-left", source.name
        )

        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.state is not None
                and session.state.left_trim_ms == 500
            ),
            timeout=5.0,
            message="Editor did not use the configured trim step",
        )
        assert probe_duration_ms(media_dir / generated_name, ffmpeg_config) < probe_duration_ms(
            source, ffmpeg_config
        ) - 350
    finally:
        editor.set_note(None)
        parent.close()
