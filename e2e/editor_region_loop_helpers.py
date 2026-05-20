"""Shared helpers for selected-region editor e2e workflows."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_state_js,
    _install_html_audio_test_driver,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.editor_playback_helpers import (
    PLAYBACK_INTERVAL_TOLERANCE_MS,
)
from e2e.helpers import (
    generate_tone,
    run_js,
    wait_for_js_condition,
)


def _open_tone_editor(anki_mw, ffmpeg_config, filename: str, duration_s: float, **config_overrides):
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / filename
    generate_tone(ffmpeg_config, source, duration_s=duration_s)
    note = _basic_audio_note(anki_mw, source.name)
    overrides = {"repeat_playback_by_default": False, **config_overrides}
    _configure_ffmpeg(anki_mw, ffmpeg_config, **overrides)
    editor, parent = _open_editor(anki_mw, note)
    track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
    _install_html_audio_test_driver(editor)
    return media_dir, source, note, editor, parent, track


def _plot_pointer_script(ord_: int, start_ratio: float, end_ratio: float, *, shift: bool, move: bool) -> str:
    return f"""
    (() => {{
      const ord = {ord_};
      const startRatio = {start_ratio};
      const endRatio = {end_ratio};
      const svg = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${{ord}}"] .aqe-visualizer-svg`);
      const rect = svg.getBoundingClientRect();
      const plot = {{ width: 620, left: 44, right: 10 }};
      const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
      const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
      const xFor = (ratio) => plotLeft + plotWidth * ratio;
      const EventCtor = window.PointerEvent || window.MouseEvent;
      svg.dispatchEvent(new EventCtor("pointerdown", {{
        bubbles: true,
        clientX: xFor(startRatio),
        clientY: rect.top + 20,
        shiftKey: {str(shift).lower()},
      }}));
      if ({str(move).lower()}) {{
        window.dispatchEvent(new EventCtor("pointermove", {{
          bubbles: true,
          clientX: xFor(endRatio),
          clientY: rect.top + 20,
          shiftKey: {str(shift).lower()},
        }}));
      }}
      window.dispatchEvent(new EventCtor("pointerup", {{
        bubbles: true,
        clientX: xFor(endRatio),
        clientY: rect.top + 20,
        shiftKey: {str(shift).lower()},
      }}));
    }})()
    """


def _plot_pointer_event_script(ord_: int, ratio: float, event_type: str, *, shift: bool) -> str:
    target = "svg" if event_type == "pointerdown" else "window"
    return f"""
    (() => {{
      const ord = {ord_};
      const ratio = {ratio};
      const svg = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${{ord}}"] .aqe-visualizer-svg`);
      const rect = svg.getBoundingClientRect();
      const plot = {{ width: 620, left: 44, right: 10 }};
      const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
      const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
      const x = plotLeft + plotWidth * ratio;
      const EventCtor = window.PointerEvent || window.MouseEvent;
      {target}.dispatchEvent(new EventCtor("{event_type}", {{
        bubbles: true,
        clientX: x,
        clientY: rect.top + 20,
        shiftKey: {str(shift).lower()},
      }}));
    }})()
    """


def _shift_pointer_down(editor, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_event_script(ord_, ratio, "pointerdown", shift=True))


def _shift_pointer_move(editor, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_event_script(ord_, ratio, "pointermove", shift=True))


def _shift_pointer_up(editor, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_event_script(ord_, ratio, "pointerup", shift=True))


def _shift_pointer_cancel(editor, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_event_script(ord_, ratio, "pointercancel", shift=True))


def _shift_drag_region(editor, start_ratio: float, end_ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_script(ord_, start_ratio, end_ratio, shift=True, move=True))


def _shift_click_region(editor, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_script(ord_, ratio, ratio, shift=True, move=False))


def _normal_drag(editor, start_ratio: float, end_ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_script(ord_, start_ratio, end_ratio, shift=False, move=True))


def _selection_handle_pointer_event_script(
    ord_: int,
    edge: str,
    ratio: float,
    event_type: str,
) -> str:
    target = "handle" if event_type == "pointerdown" else "window"
    return f"""
    (() => {{
      const ord = {ord_};
      const edge = {edge!r};
      const ratio = {ratio};
      const handle = document.querySelector(`[data-testid="aqe-selection-resize-${{edge}}-${{ord}}"]`);
      const svg = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${{ord}}"] .aqe-visualizer-svg`);
      const rect = svg.getBoundingClientRect();
      const plot = {{ width: 620, left: 44, right: 10 }};
      const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
      const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
      const x = plotLeft + plotWidth * ratio;
      const EventCtor = window.PointerEvent || window.MouseEvent;
      {target}.dispatchEvent(new EventCtor("{event_type}", {{
        bubbles: true,
        clientX: x,
        clientY: rect.top + 20,
      }}));
    }})()
    """


def _resize_handle_down(editor, edge: str, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _selection_handle_pointer_event_script(ord_, edge, ratio, "pointerdown"))


def _resize_handle_move(editor, edge: str, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _selection_handle_pointer_event_script(ord_, edge, ratio, "pointermove"))


def _resize_handle_up(editor, edge: str, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _selection_handle_pointer_event_script(ord_, edge, ratio, "pointerup"))


def _drag_resize_handle(editor, edge: str, start_ratio: float, end_ratio: float, ord_: int = 0) -> None:
    _resize_handle_down(editor, edge, start_ratio, ord_)
    _resize_handle_move(editor, edge, end_ratio, ord_)
    _resize_handle_up(editor, edge, end_ratio, ord_)


def _set_repeat(editor, enabled: bool, ord_: int = 0) -> None:
    wait_for_js_condition(
        editor.web,
        f"""
        (() => {{
          let toggle = document.querySelector('[data-testid="aqe-repeat-{ord_}"]');
          if (!toggle) {{
            const menu = document.querySelector('[data-testid="aqe-split-{ord_}-play-menu"]');
            if (!menu) return null;
            if (menu.getAttribute("aria-expanded") !== "true") menu.click();
            toggle = document.querySelector('[data-testid="aqe-repeat-{ord_}"]');
          }}
          if (!toggle) return null;
          const requested = {str(enabled).lower()};
          const current = toggle.getAttribute("aria-pressed") === "true";
          if (current !== requested) toggle.click();
          return toggle.getAttribute("aria-pressed") === "true";
        }})()
        """,
        lambda value: value is enabled,
        timeout=5.0,
    )


def _state(editor, predicate=lambda state: True, ord_: int = 0, timeout: float = 5.0):
    return wait_for_js_condition(
        editor.web,
        _graph_state_js(ord_),
        lambda state: state is not None and predicate(state),
        timeout=timeout,
    )


def _force_audio_boundary(editor, ord_: int = 0) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          const state = window.__aqeGraphStateForTest && window.__aqeGraphStateForTest({ord_});
          const audio = document.querySelector('[data-testid="aqe-audio-clock-{ord_}"]');
          if (!state || !audio) return false;
          audio.currentTime = state.playbackEndMs / 1000;
          audio.dispatchEvent(new Event("ended"));
          return true;
        }})()
        """,
    )


def _force_repeat_wrap(editor, expected_start_ms: int, ord_: int = 0):
    _force_audio_boundary(editor, ord_)
    return _state(
        editor,
        lambda state: state["playbackState"] == "playing"
        and abs(state["cursorMs"] - expected_start_ms) <= PLAYBACK_INTERVAL_TOLERANCE_MS
        and abs(state["audioClockCurrentMs"] - expected_start_ms) <= PLAYBACK_INTERVAL_TOLERANCE_MS,
        ord_=ord_,
        timeout=5.0,
    )


def _two_audio_field_note(anki_mw, audio_filenames: tuple[str, str]):
    models = anki_mw.col.models
    notetype = models.new("AQE E2E Region Two Audio Fields")
    for name in ("One", "Two"):
        models.add_field(notetype, models.new_field(name))
    template = models.new_template("Card 1")
    template["qfmt"] = "{{One}}"
    template["afmt"] = "{{FrontSide}}<hr>{{Two}}"
    models.add_template(notetype, template)
    models.add(notetype)
    note = anki_mw.col.new_note(notetype)
    for index, filename in enumerate(audio_filenames):
        note.fields[index] = f"Field {index + 1} [sound:{filename}]"
    deck_id = anki_mw.col.decks.id("Default")
    assert deck_id is not None
    anki_mw.col.add_note(note, deck_id)
    return note
