"""E2E tests for learner drag edge cases in the editor graph."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _dispatch_learner_drag_sequence,
    _inject_ready_learner_overlay,
    _learner_drag_state_js,
)
from e2e.editor_note_helpers import (
    DEFAULT_VISIBLE_EDITOR_BUTTONS,
    _basic_audio_note,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.helpers import generate_tone, wait_for_js_condition


def _open_editor_with_learner_overlay(anki_mw, ffmpeg_config, *, source_name: str, duration_s: float):
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / source_name
    generate_tone(ffmpeg_config, source, duration_s=duration_s)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        visible_editor_buttons=[*DEFAULT_VISIBLE_EDITOR_BUTTONS, "aqe:record-voice"],
    )
    editor, parent = _open_editor(anki_mw, note)
    _click_graph_and_wait(
        editor,
        lambda value: value["sourceFilename"] == source.name and value["pitchPaths"] > 0,
        timeout=15.0,
    )
    _inject_ready_learner_overlay(editor, start_cursor_ms=500, learner_duration_ms=1700)
    return editor, parent


def test_editor_voice_recording_learner_drag_blur_restores_start_offset(
    anki_mw,
    ffmpeg_config,
) -> None:
    editor, parent = _open_editor_with_learner_overlay(
        anki_mw,
        ffmpeg_config,
        source_name="editor_voice_recording_drag_blur.wav",
        duration_s=2.0,
    )
    try:
        _dispatch_learner_drag_sequence(editor, start_ratio=0.5, end_ratio=0.6)
        baseline = wait_for_js_condition(
            editor.web,
            _learner_drag_state_js(),
            lambda value: value is not None and value["learnerAlignmentOffsetMs"] > 0,
            timeout=5.0,
        )

        _dispatch_learner_drag_sequence(editor, start_ratio=0.6, move_ratio=0.2, end_event="blur")

        restored = wait_for_js_condition(
            editor.web,
            _learner_drag_state_js(),
            lambda value: value is not None
            and value["learnerAlignmentOffsetMs"] == baseline["learnerAlignmentOffsetMs"]
            and value["learnerAlignmentDragging"] is False,
            timeout=5.0,
        )
        assert restored["learnerPitchPaths"] > 0
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_voice_recording_learner_drag_pointercancel_restores_start_offset(
    anki_mw,
    ffmpeg_config,
) -> None:
    editor, parent = _open_editor_with_learner_overlay(
        anki_mw,
        ffmpeg_config,
        source_name="editor_voice_recording_drag_pointercancel.wav",
        duration_s=2.0,
    )
    try:
        _dispatch_learner_drag_sequence(editor, start_ratio=0.5, end_ratio=0.6)
        baseline = wait_for_js_condition(
            editor.web,
            _learner_drag_state_js(),
            lambda value: value is not None and value["learnerAlignmentOffsetMs"] > 0,
            timeout=5.0,
        )

        _dispatch_learner_drag_sequence(editor, start_ratio=0.6, move_ratio=0.85, end_event="pointercancel")

        restored = wait_for_js_condition(
            editor.web,
            _learner_drag_state_js(),
            lambda value: value is not None
            and value["learnerAlignmentOffsetMs"] == baseline["learnerAlignmentOffsetMs"]
            and value["learnerAlignmentDragging"] is False,
            timeout=5.0,
        )
        assert restored["cursorMs"] == 0
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_voice_recording_learner_drag_capture_loss_restores_start_offset(
    anki_mw,
    ffmpeg_config,
) -> None:
    editor, parent = _open_editor_with_learner_overlay(
        anki_mw,
        ffmpeg_config,
        source_name="editor_voice_recording_drag_capture_loss.wav",
        duration_s=2.0,
    )
    try:
        _dispatch_learner_drag_sequence(editor, start_ratio=0.5, end_ratio=0.6)
        baseline = wait_for_js_condition(
            editor.web,
            _learner_drag_state_js(),
            lambda value: value is not None and value["learnerAlignmentOffsetMs"] > 0,
            timeout=5.0,
        )

        _dispatch_learner_drag_sequence(
            editor,
            start_ratio=0.6,
            move_ratio=0.9,
            end_event="lostpointercapture",
            end_ratio=0.9,
        )

        restored = wait_for_js_condition(
            editor.web,
            _learner_drag_state_js(),
            lambda value: value is not None
            and value["learnerAlignmentOffsetMs"] == baseline["learnerAlignmentOffsetMs"]
            and value["learnerAlignmentDragging"] is False,
            timeout=5.0,
        )
        assert restored["learnerDurationMs"] > restored["targetDurationMs"]
    finally:
        editor.set_note(None)
        parent.close()


def test_editor_voice_recording_learner_drag_clamps_at_graph_bounds(
    anki_mw,
    ffmpeg_config,
) -> None:
    editor, parent = _open_editor_with_learner_overlay(
        anki_mw,
        ffmpeg_config,
        source_name="editor_voice_recording_drag_bounds.wav",
        duration_s=2.0,
    )
    try:
        initial = wait_for_js_condition(
            editor.web,
            _learner_drag_state_js(),
            lambda value: value is not None and value["viewportEndMs"] > value["viewportStartMs"],
            timeout=5.0,
        )
        viewport_span = initial["viewportEndMs"] - initial["viewportStartMs"]

        _dispatch_learner_drag_sequence(editor, start_ratio=0.5, end_ratio=-0.2)
        left = wait_for_js_condition(
            editor.web,
            _learner_drag_state_js(),
            lambda value: value is not None
            and value["learnerAlignmentDragging"] is False
            and abs(value["learnerAlignmentOffsetMs"] + (viewport_span / 2)) <= 2,
            timeout=5.0,
        )

        _dispatch_learner_drag_sequence(editor, start_ratio=0.0, end_ratio=1.3)
        right = wait_for_js_condition(
            editor.web,
            _learner_drag_state_js(),
            lambda value: value is not None
            and value["learnerAlignmentDragging"] is False
            and abs(value["learnerAlignmentOffsetMs"] - (viewport_span / 2)) <= 2,
            timeout=5.0,
        )

        assert left["learnerPitchPaths"] > 0
        assert right["learnerPitchPaths"] > 0
    finally:
        editor.set_note(None)
        parent.close()
