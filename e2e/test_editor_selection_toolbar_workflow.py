"""E2E tests for the selected-region floating toolbar."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_state_js,
    _install_html_audio_test_driver,
    _wait_for_html_playback,
    _wait_for_visualizer_track,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
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
      const plot = {{ width: 620, height: 150, left: 44, right: 10 }};
      const scale = Math.min(rect.width / plot.width, rect.height / plot.height) || 1;
      const plotLeft = rect.left + plot.left * scale;
      const plotWidth = (plot.width - plot.left - plot.right) * scale;
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


def _toolbar_selector(kind: str, ord_: int = 0) -> str:
    return f'[data-testid="aqe-selection-toolbar-{kind}-{ord_}"]'


def _dispatch_toolbar_event(editor, kind: str, event_name: str, ord_: int = 0) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          const button = document.querySelector({_toolbar_selector(kind, ord_)!r});
          if (!button) return false;
          button.dispatchEvent(new MouseEvent({event_name!r}, {{ bubbles: true }}));
          return true;
        }})()
        """,
    )


def _wait_for_toolbar(editor, predicate=lambda state: True, timeout: float = 5.0):
    return wait_for_js_condition(
        editor.web,
        _graph_state_js(),
        lambda state: state is not None
        and state["selectionToolbarHidden"] is False
        and predicate(state),
        timeout=timeout,
    )


def _toolbar_alignment_state(editor, ord_: int = 0):
    return wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          const visualizer = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="{ord_}"]`);
          const svg = visualizer?.querySelector(".aqe-visualizer-svg");
          const toolbar = visualizer?.querySelector(".aqe-selection-toolbar");
          const selectionEnd = visualizer?.querySelector(".aqe-selection-end");
          if (!svg || !toolbar || !selectionEnd) return null;
          const rect = svg.getBoundingClientRect();
          const toolbarRect = toolbar.getBoundingClientRect();
          const scale = Math.min(rect.width / 620, rect.height / 150) || 1;
          const selectionEndClientX = rect.left + Number(selectionEnd.getAttribute("x1") || "0") * scale;
          return {{
            rightDeltaPx: toolbarRect.right - selectionEndClientX,
            selectionEndClientX,
            toolbarRight: toolbarRect.right,
          }};
        }})()
        """,
        lambda state: state is not None,
        timeout=5.0,
    )


def test_selection_toolbar_appears_collapses_and_expands(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_toolbar_expand_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _shift_drag_region(editor, 0.25, 0.625)
        visible = _wait_for_toolbar(
            editor,
            lambda state: state["selectionToolbarCollapsed"] is False
            and state["selectionToolbarDotHidden"] is True
            and state["selectionToolbarDeleteRegionHidden"] is False
            and state["selectionToolbarDeleteRestHidden"] is False,
        )
        assert visible["selectionStartMs"] == 500
        assert visible["selectionEndMs"] == 1250
        alignment = _toolbar_alignment_state(editor)
        assert alignment is not None
        assert 0 <= alignment["rightDeltaPx"] <= 12

        click_selector(editor.web, _toolbar_selector("collapse"), timeout=5.0)
        collapsed = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None
            and state["selectionToolbarCollapsed"] is True
            and state["selectionToolbarHidden"] is True
            and state["selectionToolbarDotHidden"] is False,
            timeout=5.0,
        )
        assert collapsed["selectionActive"] is True

        _shift_drag_region(editor, 0.3, 0.7)
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None
            and state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1400
            and state["selectionToolbarCollapsed"] is True
            and state["selectionToolbarHidden"] is True
            and state["selectionToolbarDotHidden"] is False,
            timeout=5.0,
        )

        previous_name = _sound_filename(note.fields[0])
        click_selector(editor.web, '[data-testid="aqe-button-0-volume-up"]', timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_name,
            timeout=10.0,
        )
        _shift_drag_region(editor, 0.25, 0.5)
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None
            and state["selectionToolbarCollapsed"] is True
            and state["selectionToolbarHidden"] is True
            and state["selectionToolbarDotHidden"] is False,
            timeout=5.0,
        )

        _dispatch_toolbar_event(editor, "dot", "click")
        expanded = _wait_for_toolbar(
            editor,
            lambda state: state["selectionToolbarCollapsed"] is False
            and state["selectionToolbarDotHidden"] is True,
        )
        assert expanded["selectionActive"] is True

        _shift_drag_region(editor, 0.2, 0.4)
        _wait_for_toolbar(
            editor,
            lambda state: state["selectionToolbarCollapsed"] is False
            and state["selectionToolbarDotHidden"] is True,
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_selection_toolbar_delete_hover_previews_clear_and_switch(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_toolbar_preview_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _shift_drag_region(editor, 0.2, 0.6)
        _wait_for_toolbar(editor)

        _dispatch_toolbar_event(editor, "delete-region", "mouseenter")
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and state["selectionToolbarPreview"] == "region",
            timeout=5.0,
        )

        _dispatch_toolbar_event(editor, "delete-region", "mouseleave")
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and state["selectionToolbarPreview"] == "none",
            timeout=5.0,
        )

        _dispatch_toolbar_event(editor, "delete-rest", "mouseenter")
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and state["selectionToolbarPreview"] == "rest",
            timeout=5.0,
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_selection_toolbar_play_pause_uses_selected_html_audio(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_toolbar_play_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _install_html_audio_test_driver(editor)
        _shift_drag_region(editor, 0.25, 0.625)
        _wait_for_toolbar(editor)

        click_selector(editor.web, _toolbar_selector("play"), timeout=5.0)
        playing = _wait_for_html_playback(
            editor,
            lambda state: state["playbackRegionMode"] == "selection"
            and 450 <= state["playbackStartMs"] <= 550
            and 1200 <= state["playbackEndMs"] <= 1300
            and state["selectionToolbarPlayState"] == "pause"
            and state["selectionToolbarPlayAriaLabel"] == "Pause selection",
        )
        assert playing["selectionActive"] is True

        click_selector(editor.web, _toolbar_selector("play"), timeout=5.0)
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None
            and state["playbackState"] == "paused"
            and state["selectionToolbarPlayState"] == "play",
            timeout=5.0,
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_selection_toolbar_delete_rest_keeps_selected_audio(anki_mw, ffmpeg_config) -> None:
    from anki_audio_quick_editor.audio_processor import (
        AudioProcessingConfig,
        probe_duration_ms,
    )

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_toolbar_delete_rest_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _shift_drag_region(editor, 0.25, 0.625)
        _wait_for_toolbar(
            editor,
            lambda state: state["selectionToolbarDeleteRestHidden"] is False
            and state["selectionToolbarDeleteRestDisabled"] is False,
        )

        previous_name = _sound_filename(note.fields[0])
        click_selector(editor.web, _toolbar_selector("delete-rest"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
        redrawn = _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_name
            and value["selectionActive"] is True
            and value["selectionToolbarHidden"] is True,
            timeout=10.0,
        )

        generated_duration = probe_duration_ms(media_dir / generated_name, AudioProcessingConfig.from_config({}))
        assert source.read_bytes() == original_bytes
        assert generated_name.startswith("editor_toolbar_delete_rest_source__aqe_")
        assert 600 <= generated_duration <= 900
        assert redrawn["playbackState"] == "stopped"

        _shift_drag_region(editor, 0.1, 0.8)
        _wait_for_toolbar(
            editor,
            lambda state: state["selectionToolbarCollapsed"] is False
            and state["selectionToolbarDotHidden"] is True,
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_selection_toolbar_hides_for_whole_clip_selection(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_toolbar_whole_clip_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _shift_drag_region(editor, 0.0, 1.0)
        whole_clip = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None
            and state["selectionActive"] is True
            and state["selectionToolbarHidden"] is True
            and state["regionDeleteButtonHidden"] is True
            and state["regionDeleteRestButtonHidden"] is True,
            timeout=5.0,
        )
        assert whole_clip["selectionStartMs"] == 0
        assert abs(whole_clip["selectionEndMs"] - whole_clip["durationMs"]) <= 1
    finally:
        editor.set_note(None)
        parent.close()
