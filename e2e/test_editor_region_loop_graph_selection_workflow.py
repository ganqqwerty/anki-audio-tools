"""E2E tests for selected-region graph defaults (selection behavior)."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_graph_helpers import _wait_for_visualizer_track
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.editor_region_loop_helpers import (
    _drag_resize_handle,
    _normal_drag,
    _open_tone_editor,
    _shift_drag_region,
    _state,
)
from e2e.helpers import (
    generate_tone,
)


def test_graph_render_selects_full_region_and_outside_click_expands_boundaries(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_initial_full_selection.wav",
        2.0,
    )
    try:
        initial = _state(
            editor,
            lambda state: state["selectionActive"] is True
            and state["selectionStartMs"] == 0
            and state["selectionEndMs"] == 2000
            and state["playbackRegionMode"] == "selection"
            and state["regionDeleteButtonHidden"] is True
            and state["regionDeleteButtonDisabled"] is True
            and state["regionDeleteRestButtonHidden"] is True
            and state["regionDeleteRestButtonDisabled"] is True,
        )
        assert initial["playbackStartMs"] == 0
        assert initial["playbackEndMs"] == 2000

        _shift_drag_region(editor, 0.25, 0.625)
        selected = _state(
            editor,
            lambda state: state["selectionStartMs"] == 500
            and state["selectionEndMs"] == 1250,
        )
        assert selected["cursorMs"] == 500

        _normal_drag(editor, 0.75, 0.75)
        expanded_right = _state(
            editor,
            lambda state: state["selectionStartMs"] == 500
            and state["selectionEndMs"] == 1500
            and state["cursorMs"] == 1500,
        )
        assert expanded_right["playbackRegionMode"] == "selection"

        _normal_drag(editor, 0.125, 0.125)
        expanded_left = _state(
            editor,
            lambda state: state["selectionStartMs"] == 250
            and state["selectionEndMs"] == 1500
            and state["cursorMs"] == 250,
        )
        assert expanded_left["playbackStartMs"] == 250
    finally:
        editor.set_note(None)
        parent.close()


def test_graph_default_auto_analysis_supports_region_selection(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_graph_default_region_selection.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        repeat_playback_by_default=False,
        show_graph_by_default=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        auto_track = _wait_for_visualizer_track(
            editor,
            lambda state: state["sourceFilename"] == source.name,
            timeout=10.0,
        )
        _shift_drag_region(editor, 0.2, 0.55)
        selected = _state(
            editor,
            lambda state: state["selectionActive"] is True
            and state["selectionStartMs"] == 400
            and state["selectionEndMs"] == 1100,
        )
        _drag_resize_handle(editor, "end", 0.55, 0.7)
        resized = _state(
            editor,
            lambda state: state["selectionStartMs"] == 400
            and state["selectionEndMs"] == 1400
            and state["selectionEndHandleVisible"] is True,
        )

        assert auto_track["active"] is True
        assert selected["playbackRegionMode"] == "selection"
        assert resized["playbackEndMs"] == 1400
        assert selected["repeatEnabled"] is False
    finally:
        editor.set_note(None)
        parent.close()
