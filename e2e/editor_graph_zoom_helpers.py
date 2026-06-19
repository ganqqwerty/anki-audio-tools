"""Shared E2E helpers for inline editor graph zoom workflows."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_graph_helpers import _click_graph_and_wait
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.helpers import generate_tone, wait_for_selector


def _open_zoom_graph_editor(anki_mw, ffmpeg_config, filename: str, duration_s: float = 4.0):
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / filename
    generate_tone(ffmpeg_config, source, duration_s=duration_s)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    editor, parent = _open_editor(anki_mw, note)
    wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
    track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
    return media_dir, source, editor, parent, track
