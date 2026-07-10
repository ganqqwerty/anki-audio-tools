"""E2E tests for enabling selected auto-advance after paused repeat playback."""

from __future__ import annotations

from e2e.editor_chorusing_playback_helpers import (
    _click_pause,
    _click_play,
    _click_play_from_split_menu,
    _configure_play_auto_advance,
    _configure_play_repeat,
)
from e2e.editor_region_loop_helpers import (
    _force_audio_boundary,
    _force_repeat_wrap,
    _open_tone_editor,
    _set_repeat,
    _shift_drag_region,
    _state,
)


def test_play_split_auto_advance_after_paused_selected_repeat(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_auto_advance_after_pause.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.3, 0.8)
        selected = _state(
            editor,
            lambda state: state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600
            and state["chorusingMarkersMs"] == [0, 500, 1000, 1500],
        )
        _set_repeat(editor, True)
        _click_play(editor)
        _click_pause(editor)

        paused = _state(
            editor,
            lambda state: state["playbackState"] == "paused"
            and state["repeatEnabled"] is True
            and state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600,
        )
        _configure_play_auto_advance(editor, pause_seconds=0.0, repeat_count=2)
        _click_play_from_split_menu(editor)

        resumed = _state(
            editor,
            lambda state: state["playbackState"] == "playing"
            and state["repeatEnabled"] is True
            and state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600,
        )
        first_repeat = _force_repeat_wrap(editor, 600)
        auto_advanced = _force_repeat_wrap(editor, 500)

        assert selected["chorusingRepeatPassesCompleted"] == 0
        assert paused["playbackState"] == "paused"
        assert resumed["playbackStartMs"] == 600
        assert first_repeat["chorusingRepeatPassesCompleted"] == 1
        assert first_repeat["selectionStartMs"] == 600
        assert auto_advanced["chorusingRepeatPassesCompleted"] == 0
        assert auto_advanced["selectionStartMs"] == 500
        assert auto_advanced["selectionEndMs"] == 1600
    finally:
        editor.set_note(None)
        parent.close()


def test_play_split_auto_advance_after_split_repeat_pause(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_auto_advance_after_split_repeat_pause.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.3, 0.8)
        selected = _state(
            editor,
            lambda state: state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600
            and state["chorusingMarkersMs"] == [0, 500, 1000, 1500],
        )
        _configure_play_repeat(editor, pause_seconds=0.0)
        _click_play_from_split_menu(editor)

        repeat_before_pause = _force_repeat_wrap(editor, 600)
        _click_pause(editor)
        paused = _state(
            editor,
            lambda state: state["playbackState"] == "paused"
            and state["repeatEnabled"] is True
            and state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600,
        )

        _configure_play_auto_advance(editor, pause_seconds=0.0, repeat_count=2)
        _click_play_from_split_menu(editor)

        resumed = _state(
            editor,
            lambda state: state["playbackState"] == "playing"
            and state["repeatEnabled"] is True
            and state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600,
        )
        first_repeat_with_auto_advance = _force_repeat_wrap(editor, 600)
        auto_advanced = _force_repeat_wrap(editor, 500)

        assert selected["chorusingRepeatPassesCompleted"] == 0
        assert repeat_before_pause["chorusingRepeatPassesCompleted"] == 0
        assert paused["playbackState"] == "paused"
        assert resumed["playbackStartMs"] == 600
        assert first_repeat_with_auto_advance["chorusingRepeatPassesCompleted"] == 1
        assert first_repeat_with_auto_advance["selectionStartMs"] == 600
        assert auto_advanced["chorusingRepeatPassesCompleted"] == 0
        assert auto_advanced["selectionStartMs"] == 500
        assert auto_advanced["selectionEndMs"] == 1600
    finally:
        editor.set_note(None)
        parent.close()


def test_play_split_auto_advance_after_pausing_during_repeat_wait(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_auto_advance_after_repeat_wait_pause.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.3, 0.8)
        _state(
            editor,
            lambda state: state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600
            and state["chorusingMarkersMs"] == [0, 500, 1000, 1500],
        )
        _configure_play_repeat(editor, pause_seconds=5.0)
        _click_play_from_split_menu(editor)
        _force_audio_boundary(editor)

        waiting = _state(
            editor,
            lambda state: state["playbackState"] == "playing"
            and state["progressClockMode"] == "stopped"
            and state["repeatPauseWaiting"] is True
            and state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600,
        )
        _click_pause(editor)
        paused = _state(
            editor,
            lambda state: state["playbackState"] == "paused"
            and state["repeatEnabled"] is True
            and state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600,
        )

        _configure_play_auto_advance(editor, pause_seconds=5.0, repeat_count=1)
        _click_play_from_split_menu(editor)
        resumed = _state(
            editor,
            lambda state: state["playbackState"] == "playing"
            and state["repeatEnabled"] is True
            and state["repeatPauseWaiting"] is False
            and state["selectionStartMs"] == 600
            and state["selectionEndMs"] == 1600,
        )
        auto_advanced = _force_repeat_wrap(editor, 500)

        assert waiting["repeatPauseWaiting"] is True
        assert paused["playbackState"] == "paused"
        assert resumed["playbackStartMs"] == 600
        assert auto_advanced["chorusingRepeatPassesCompleted"] == 0
        assert auto_advanced["selectionStartMs"] == 500
        assert auto_advanced["selectionEndMs"] == 1600
    finally:
        editor.set_note(None)
        parent.close()
