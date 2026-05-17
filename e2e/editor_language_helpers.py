"""Language contour helpers for editor graph E2E tests."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

from tests.prosody_language_fixtures import (
    LANGUAGE_CONTOUR_SPECS,
    ContourWindow,
    generate_praat_vowel_fixture,
    median,
    require_praat_and_ffmpeg,
)

from e2e.editor_graph_helpers import _click_graph_and_wait
from e2e.editor_note_helpers import _basic_audio_note, _configure_ffmpeg, _open_editor
from e2e.helpers import wait_for_js_condition


def _generate_language_contour_for_e2e(path: Path, spec_name: str) -> None:
    require_praat_and_ffmpeg()
    generate_praat_vowel_fixture(path, LANGUAGE_CONTOUR_SPECS[spec_name])


def _rendered_pitch_points_js(ord_: int = 0) -> str:
    return """
    (() => {
      const ord = __ORD__;
      const visualizer = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${ord}"]`);
      if (!visualizer) return null;
      const durationMs = Number(visualizer.dataset.durationMs || "0");
      const plot = { width: 620, left: 44, right: 10 };
      const plotWidth = plot.width - plot.left - plot.right;
      const points = [];
      for (const path of visualizer.querySelectorAll(".aqe-pitch-path")) {
        const values = (path.getAttribute("d") || "").match(/-?\\d+(?:\\.\\d+)?/g) || [];
        for (let index = 0; index + 1 < values.length; index += 2) {
          const x = Number(values[index]);
          const y = Number(values[index + 1]);
          const ms = ((x - plot.left) / plotWidth) * durationMs;
          points.push({ ms, y });
        }
      }
      return {
        durationMs,
        paths: visualizer.querySelectorAll(".aqe-pitch-path").length,
        points
      };
    })()
    """.replace("__ORD__", json.dumps(ord_))


def _median_rendered_y(rendered: dict, window: ContourWindow) -> float:
    values = [
        point["y"]
        for point in rendered["points"]
        if window.start_ms <= point["ms"] <= window.end_ms
    ]
    return median(values)


@contextmanager
def _language_contour_editor(anki_mw, ffmpeg_config, spec_name: str):
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / f"editor_{spec_name}.wav"
    _generate_language_contour_for_e2e(source, spec_name)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    editor, parent = _open_editor(anki_mw, note)
    try:
        yield editor, parent, source, LANGUAGE_CONTOUR_SPECS[spec_name]
    finally:
        editor.set_note(None)
        parent.close()


def _rendered_language_contour(editor, source_name: str) -> dict:
    _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source_name)
    return wait_for_js_condition(
        editor.web,
        _rendered_pitch_points_js(),
        lambda value: value is not None and value["paths"] > 0 and bool(value["points"]),
        timeout=5.0,
    )
