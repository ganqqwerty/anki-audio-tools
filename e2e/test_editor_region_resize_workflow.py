"""E2E tests for resizing selected inline graph regions."""

from __future__ import annotations

import time

from e2e.editor_graph_helpers import (
    _wait_for_html_playback,
)
from e2e.editor_note_helpers import (
    _button_selector,
    _sound_filename,
    _wait_for_generated_mp3,
)
from e2e.editor_playback_helpers import (
    PLAYBACK_INTERVAL_TOLERANCE_MS,
    _record_fake_playback,
)
from e2e.editor_region_loop_helpers import (
    _drag_resize_handle,
    _force_repeat_wrap,
    _normal_drag,
    _open_tone_editor,
    _resize_handle_down,
    _resize_handle_move,
    _resize_handle_up,
    _set_repeat,
    _shift_drag_region,
    _state,
)
from e2e.helpers import (
    click_selector,
    wait_for_condition,
)


def test_resize_handles_update_stopped_selection_and_preserve_graph_gestures(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_resize_stopped.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.625)
        selected = _state(
            editor,
            lambda state: state["selectionStartMs"] == 500
            and state["selectionEndMs"] == 1250
            and state["selectionStartHandleVisible"] is True
            and state["selectionEndHandleVisible"] is True,
        )
        assert selected["playbackRegionMode"] == "selection"

        _drag_resize_handle(editor, "end", 0.625, 0.75)
        resized_end = _state(
            editor,
            lambda state: state["selectionStartMs"] == 500
            and state["selectionEndMs"] == 1500
            and state["playbackEndMs"] == 1500,
        )
        assert resized_end["cursorMs"] == 500

        _drag_resize_handle(editor, "start", 0.25, 0.125)
        resized_start = _state(
            editor,
            lambda state: state["selectionStartMs"] == 250
            and state["selectionEndMs"] == 1500
            and state["cursorMs"] == 250,
        )
        assert resized_start["playbackStartMs"] == 250

        _normal_drag(editor, 0.425, 0.9)
        scrubbed = _state(
            editor,
            lambda state: 1450 <= state["cursorMs"] <= 1550,
        )
        assert scrubbed["selectionStartMs"] == 250
        assert scrubbed["selectionEndMs"] == 1500

        _shift_drag_region(editor, 0.1, 0.3)
        replaced = _state(
            editor,
            lambda state: state["selectionStartMs"] == 200
            and state["selectionEndMs"] == 600
            and state["selectionStartHandleVisible"] is True
            and state["selectionEndHandleVisible"] is True,
        )
        assert replaced["cursorMs"] == 200
    finally:
        editor.set_note(None)
        parent.close()


def test_resize_while_playing_restarts_progress_from_resized_region_start(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_resize_playing.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.65)

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 650)

            _resize_handle_down(editor, "end", 0.65)
            stopped_for_resize = _state(
                editor,
                lambda state: state["playbackState"] == "stopped"
                and state["playButtonLabel"] == "Play",
            )
            assert stopped_for_resize["selectionStartMs"] == 500
            assert stopped_for_resize["selectionEndMs"] == 1300

            _resize_handle_move(editor, "end", 0.85)
            draft = _state(
                editor,
                lambda state: state["selectionDraftActive"] is True
                and state["selectionDraftStartMs"] == 500
                and state["selectionDraftEndMs"] == 1700,
            )

            frozen_progress = draft["progressMs"]
            freeze_deadline = time.monotonic() + 0.25
            wait_for_condition(
                lambda: time.monotonic() >= freeze_deadline,
                timeout=1.0,
                message="short resize progress freeze wait failed",
            )
            frozen = _state(editor)
            assert abs(frozen["progressMs"] - frozen_progress) <= PLAYBACK_INTERVAL_TOLERANCE_MS * 2

            _resize_handle_up(editor, "end", 0.85)
            restarted = _wait_for_html_playback(
                editor,
                lambda state: state["playbackState"] == "playing"
                and state["playButtonLabel"] == "Pause"
                and state["selectionStartMs"] == 500
                and state["selectionEndMs"] == 1700
                and state["playbackStartMs"] == 500
                and state["playbackEndMs"] == 1700
                and state["audioClockCurrentMs"] >= 500 - PLAYBACK_INTERVAL_TOLERANCE_MS,
            )

        assert playback.attempts == []
        assert abs(restarted["cursorMs"] - 500) <= PLAYBACK_INTERVAL_TOLERANCE_MS
    finally:
        editor.set_note(None)
        parent.close()


def test_resize_paused_and_repeat_playback_use_updated_boundaries(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_resize_paused_repeat.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.65)

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 600)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _state(
                editor,
                lambda state: state["playbackState"] == "paused"
                and state["playButtonLabel"] == "Play",
            )

            _drag_resize_handle(editor, "start", 0.25, 0.1)
            resized_start = _state(
                editor,
                lambda state: state["selectionStartMs"] == 200
                and state["selectionEndMs"] == 1300
                and state["playbackState"] == "paused"
                and state["resumeRequiresRestart"] is True
                and state["playButtonLabel"] == "Play",
            )
            assert resized_start["playbackStartMs"] == 200

            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            resumed = _wait_for_html_playback(
                editor,
                lambda state: state["playbackState"] == "playing"
                and state["playbackStartMs"] == 200,
            )
            assert resumed["selectionEndMs"] == 1300

            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _state(editor, lambda state: state["playbackState"] == "paused")
            _set_repeat(editor, True)
            _drag_resize_handle(editor, "end", 0.65, 0.85)
            resized_end = _state(
                editor,
                lambda state: state["selectionStartMs"] == 200
                and state["selectionEndMs"] == 1700
                and state["playbackEndMs"] == 1700,
            )
            assert resized_end["repeatEnabled"] is True

            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(
                editor,
                lambda state: state["playbackState"] == "playing"
                and state["playbackStartMs"] == 200
                and state["playbackEndMs"] == 1700,
            )
            looped = _force_repeat_wrap(editor, 200)

        assert playback.attempts == []
        assert looped["playbackEndMs"] == 1700
        assert looped["repeatEnabled"] is True
    finally:
        editor.set_note(None)
        parent.close()


def test_delete_region_after_resize_uses_resized_range(
    anki_mw,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import (
        probe_duration_ms,
    )

    media_dir, _source, note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_resize_delete.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.625)
        _drag_resize_handle(editor, "end", 0.625, 0.75)
        resized = _state(
            editor,
            lambda state: state["selectionStartMs"] == 500
            and state["selectionEndMs"] == 1500
            and state["regionDeleteButtonHidden"] is False
            and state["regionDeleteButtonDisabled"] is False,
        )
        assert resized["playbackEndMs"] == 1500

        previous_name = _sound_filename(note.fields[0])
        click_selector(editor.web, _button_selector("aqe:delete-selection"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
        generated_duration = probe_duration_ms(media_dir / generated_name, ffmpeg_config)

        assert 850 <= generated_duration <= 1150
    finally:
        editor.set_note(None)
        parent.close()
