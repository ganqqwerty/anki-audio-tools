"""E2E tests for deleting selected inline graph regions."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_state_js,
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
from e2e.helpers import click_selector, generate_tone, run_js, wait_for_js_condition


def _plot_pointer_script(ord_: int, start_ratio: float, end_ratio: float) -> str:
    return f"""
    (() => {{
      const ord = {ord_};
      const svg = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${{ord}}"] .aqe-visualizer-svg`);
      const rect = svg.getBoundingClientRect();
      const plot = {{ width: 620, left: 44, right: 10 }};
      const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
      const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
      const xFor = (ratio) => plotLeft + plotWidth * ratio;
      const EventCtor = window.PointerEvent || window.MouseEvent;
      svg.dispatchEvent(new EventCtor("pointerdown", {{
        bubbles: true,
        clientX: xFor({start_ratio}),
        clientY: rect.top + 20,
        shiftKey: true,
      }}));
      window.dispatchEvent(new EventCtor("pointermove", {{
        bubbles: true,
        clientX: xFor({end_ratio}),
        clientY: rect.top + 20,
        shiftKey: true,
      }}));
      window.dispatchEvent(new EventCtor("pointerup", {{
        bubbles: true,
        clientX: xFor({end_ratio}),
        clientY: rect.top + 20,
        shiftKey: true,
      }}));
    }})()
    """


def _shift_drag_region(editor, start_ratio: float, end_ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_script(ord_, start_ratio, end_ratio))


def test_delete_region_button_cuts_middle_region_and_redraws_graph(
    anki_mw,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import (
        AudioProcessingConfig,
        probe_duration_ms,
    )

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_region_delete_middle.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        assert 1900 <= track["durationMs"] <= 2100

        _shift_drag_region(editor, 0.25, 0.625)
        selected = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None
            and state["selectionActive"] is True
            and state["regionDeleteButtonHidden"] is False
            and state["regionDeleteButtonDisabled"] is False,
            timeout=5.0,
        )
        assert selected["selectionStartMs"] == 500
        assert selected["selectionEndMs"] == 1250

        previous_name = _sound_filename(note.fields[0])
        click_selector(editor.web, _button_selector("aqe:delete-selection"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
        redrawn = _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_name
            and value["selectionActive"] is False
            and value["cursorMs"] == 0,
            timeout=10.0,
        )

        generated_duration = probe_duration_ms(media_dir / generated_name, AudioProcessingConfig.from_config({}))
        assert source.read_bytes() == original_bytes
        assert generated_name.startswith("editor_region_delete_middle__aqe_")
        assert 1050 <= generated_duration <= 1450
        assert redrawn["sourceFilename"] == generated_name
        assert redrawn["playbackState"] == "stopped"
    finally:
        editor.set_note(None)
        parent.close()


def test_delete_rest_button_keeps_selected_middle_region_and_redraws_graph(
    anki_mw,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import (
        AudioProcessingConfig,
        probe_duration_ms,
    )

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_delete_rest_middle.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        assert 1900 <= track["durationMs"] <= 2100

        _shift_drag_region(editor, 0.25, 0.625)
        selected = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None
            and state["selectionActive"] is True
            and state["regionDeleteRestButtonHidden"] is False
            and state["regionDeleteRestButtonDisabled"] is False,
            timeout=5.0,
        )
        assert selected["selectionStartMs"] == 500
        assert selected["selectionEndMs"] == 1250

        previous_name = _sound_filename(note.fields[0])
        click_selector(editor.web, _button_selector("aqe:delete-rest"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
        redrawn = _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_name
            and value["selectionActive"] is False
            and value["cursorMs"] == 0,
            timeout=10.0,
        )

        generated_duration = probe_duration_ms(media_dir / generated_name, AudioProcessingConfig.from_config({}))
        assert source.read_bytes() == original_bytes
        assert generated_name.startswith("editor_delete_rest_middle__aqe_")
        assert 600 <= generated_duration <= 900
        assert redrawn["sourceFilename"] == generated_name
        assert redrawn["playbackState"] == "stopped"
    finally:
        editor.set_note(None)
        parent.close()
