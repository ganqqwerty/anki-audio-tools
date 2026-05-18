"""E2E tests for selected region gestures."""

# ruff: noqa: F401
from __future__ import annotations

import time
from pathlib import Path

import pytest

from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_state_js,
    _install_html_audio_test_driver,
    _wait_for_html_playback,
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
from e2e.editor_playback_helpers import (
    PLAYBACK_INTERVAL_TOLERANCE_MS,
    _record_fake_playback,
)
from e2e.editor_region_loop_helpers import (
    _force_audio_boundary,
    _force_repeat_wrap,
    _normal_drag,
    _open_tone_editor,
    _plot_pointer_script,
    _set_repeat,
    _shift_click_region,
    _shift_drag_region,
    _shift_pointer_cancel,
    _shift_pointer_down,
    _shift_pointer_move,
    _shift_pointer_up,
    _state,
    _two_audio_field_note,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_js_condition,
)


def test_region_selection_gestures_create_replace_clamp_and_preserve_normal_cursor(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_selection_basics.wav",
        2.0,
    )
    try:
        _shift_pointer_down(editor, 0.25)
        pointer_down = _state(editor)
        assert pointer_down["selectionActive"] is False
        assert pointer_down["selectionDraftActive"] is False

        _shift_pointer_move(editor, 0.625)
        draft = _state(
            editor,
            lambda state: state["selectionActive"] is False
            and state["selectionDraftActive"] is True
            and state["selectionDraftStartMs"] == 500
            and state["selectionDraftEndMs"] == 1250,
        )
        assert draft["cursorMs"] == pointer_down["cursorMs"]

        _shift_pointer_move(editor, 0.75)
        updated_draft = _state(
            editor,
            lambda state: state["selectionDraftStartMs"] == 500
            and state["selectionDraftEndMs"] == 1500,
        )
        assert updated_draft["selectionActive"] is False

        _shift_pointer_move(editor, 0.625)
        _shift_pointer_up(editor, 0.625)
        committed = _state(
            editor,
            lambda state: state["selectionActive"] is True
            and state["selectionDraftActive"] is False
            and state["selectionStartMs"] == 500
            and state["selectionEndMs"] == 1250,
        )
        assert committed["cursorMs"] == 500

        _shift_drag_region(editor, 0.8, 0.3)
        reversed_selection = _state(
            editor,
            lambda state: state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600
            and state["selectionDraftActive"] is False,
        )
        assert reversed_selection["cursorMs"] == 600

        _shift_pointer_down(editor, 0.7)
        _shift_pointer_move(editor, 0.9)
        cancel_draft = _state(
            editor,
            lambda state: state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600
            and state["selectionDraftActive"] is True
            and state["selectionDraftStartMs"] == 1400
            and state["selectionDraftEndMs"] == 1800,
        )
        assert cancel_draft["selectionActive"] is True
        _shift_pointer_cancel(editor, 0.9)
        canceled = _state(
            editor,
            lambda state: state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600
            and state["selectionDraftActive"] is False,
        )
        assert canceled["selectionActive"] is True

        _normal_drag(editor, 0.9, 0.9)
        clicked = _state(editor, lambda state: 1750 <= state["cursorMs"] <= 1850)
        assert clicked["selectionStartMs"] == 600
        assert clicked["selectionEndMs"] == 1600

        _normal_drag(editor, 0.1, 0.4)
        dragged = _state(editor, lambda state: 750 <= state["cursorMs"] <= 850)
        assert dragged["selectionStartMs"] == 600
        assert dragged["selectionEndMs"] == 1600

        _shift_drag_region(editor, -0.25, 1.25)
        clamped = _state(
            editor,
            lambda state: state["selectionStartMs"] == 0 and state["selectionEndMs"] == 2000,
        )
        assert clamped["playbackRegionMode"] == "selection"

        run_js(editor.web, _plot_pointer_script(0, 0.4, 0.402, shift=True, move=True))
        cleared = _state(editor, lambda state: state["selectionActive"] is False)
        assert cleared["playbackRegionMode"] == "full"
    finally:
        editor.set_note(None)
        parent.close()
