"""E2E coverage for post-edit real media repeat playback."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from e2e.editor_audio_generation_helpers import _generate_high_bitrate_mp3
from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_state_js,
    _set_full_time_viewport,
    _wait_for_visualizer_track,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
    _wait_for_generated_mp3,
    _wait_for_status_flow,
)
from e2e.editor_region_loop_helpers import _set_repeat, _shift_drag_region
from e2e.helpers import click_selector, wait_for_js_condition, wait_for_selector
from e2e.test_editor_real_media_repeat_workflow import (
    MEDIA_FIXTURE_DIR,
    _install_real_audio_probe,
    _open_real_media_editor,
    _real_audio_probe_js,
    _stop_real_audio_playback,
    _trusted_click_selector,
    _wait_for_real_audio_ready,
    _wait_for_real_html_playback,
)

POST_EDIT_REPEAT_CASES = [
    ("aqe:delete-rest", "Kept only selection 500-1250 ms."),
    ("aqe:delete-selection", "Deleted selection 500-1250 ms."),
    ("aqe:slower", "Decreased speed to x1.5."),
    ("aqe:faster", "Increased speed to x1.5."),
    ("aqe:volume-up", "Increased volume by 15 dB."),
]


@pytest.mark.parametrize(
    ("command", "expected_status"),
    POST_EDIT_REPEAT_CASES,
    ids=["delete-rest", "delete-selection", "slower", "faster", "volume-up"],
)
def test_real_repeat_post_edit_operation_keeps_generated_audio_local(
    anki_mw,
    ffmpeg_config,
    command: str,
    expected_status: str,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / f"editor_real_repeat_{command.removeprefix('aqe:')}_source.mp3"
    _generate_high_bitrate_mp3(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, repeat_playback_by_default=False)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name,
            timeout=30.0,
        )
        _set_full_time_viewport(editor)
        _wait_for_real_audio_ready(editor)
        _install_real_audio_probe(editor)
        _set_repeat(editor, True)

        _trusted_click_selector(editor, _button_selector("aqe:play"))
        initial_playback = _wait_for_real_html_playback(editor)
        initial_play_calls = initial_playback["playCalls"]
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
        click_selector(editor.web, _button_selector(command), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == expected_status,
            timeout=10.0,
        )
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_name
            and value["durationMs"] > 0,
            timeout=20.0,
        )
        _wait_for_real_audio_ready(editor)

        playing_generated = wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None
            and value["state"]["sourceFilename"] == generated_name
            and generated_name in value["src"]
            and value["state"]["repeatEnabled"] is True
            and value["state"]["playbackState"] == "playing"
            and value["state"]["playbackEngine"] == "html"
            and value["state"]["progressClockMode"] == "audio"
            and value["paused"] is False
            and value["currentTimeMs"] >= 120,
            timeout=12.0,
        )
        repeated_generated = wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None
            and value["state"]["sourceFilename"] == generated_name
            and generated_name in value["src"]
            and value["state"]["repeatEnabled"] is True
            and value["state"]["playbackState"] == "playing"
            and value["state"]["playbackEngine"] == "html"
            and value["state"]["progressClockMode"] == "audio"
            and value["paused"] is False
            and value["playCalls"] >= initial_play_calls + 2,
            timeout=12.0,
        )
        assert playing_generated["backendPlaybackRequests"] == []
        assert playing_generated["nativePlaybackRequests"] == []
        assert repeated_generated["backendPlaybackRequests"] == []
        assert repeated_generated["nativePlaybackRequests"] == []
        assert playing_generated["errorCode"] is None
        assert repeated_generated["errorCode"] is None
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()


def test_real_repeat_speed_sequence_keeps_each_generated_audio_playing(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_real_repeat_speed_sequence_source.mp3"
    _generate_high_bitrate_mp3(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, repeat_playback_by_default=False)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name,
            timeout=30.0,
        )
        _set_full_time_viewport(editor)
        _wait_for_real_audio_ready(editor)
        _install_real_audio_probe(editor)
        _set_repeat(editor, True)
        _trusted_click_selector(editor, _button_selector("aqe:play"))
        initial = _wait_for_real_html_playback(editor)

        previous_name = source.name
        minimum_play_calls = initial["playCalls"]
        sequence = [
            ("aqe:slower", "Decreased speed to x1.5."),
            ("aqe:faster", "Increased speed to x1.5."),
            ("aqe:slower", "Decreased speed to x1.5."),
        ]
        for command, expected_status in sequence:
            click_selector(editor.web, _button_selector(command), timeout=5.0)
            generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
            _wait_for_status_flow(
                editor,
                lambda status, expected=expected_status: status["text"] == expected,
                timeout=10.0,
            )
            _wait_for_visualizer_track(
                editor,
                lambda value, expected=generated_name: value["sourceFilename"] == expected
                and value["durationMs"] > 0,
                timeout=20.0,
            )
            _wait_for_real_audio_ready(editor)
            minimum_play_calls += 1
            playing = _wait_for_generated_real_repeat_playback(
                editor,
                generated_name,
                minimum_play_calls,
            )
            assert playing["backendPlaybackRequests"] == []
            assert playing["nativePlaybackRequests"] == []
            assert playing["errorCode"] is None
            previous_name = generated_name
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()


def test_real_repeat_speed_sequence_without_intermediate_playback_waits(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir, source, note, editor, parent, _track = _open_real_media_editor(
        anki_mw,
        ffmpeg_config,
        MEDIA_FIXTURE_DIR / "forvo_Vertrag.ogg",
    )
    try:
        _install_real_audio_probe(editor)
        _set_repeat(editor, True)
        _trusted_click_selector(editor, _button_selector("aqe:play"))
        initial = _wait_for_real_html_playback(editor)

        previous_name = source.name
        for command, expected_status in [
            ("aqe:slower", "Decreased speed to x1.5."),
            ("aqe:faster", "Increased speed to x1.5."),
            ("aqe:slower", "Decreased speed to x1.5."),
        ]:
            click_selector(editor.web, _button_selector(command), timeout=5.0)
            generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
            _wait_for_status_flow(
                editor,
                lambda status, expected=expected_status: status["text"] == expected,
                timeout=10.0,
            )
            previous_name = generated_name

        final = _wait_for_generated_real_repeat_playback(
            editor,
            previous_name,
            initial["playCalls"] + 3,
        )
        assert final["backendPlaybackRequests"] == []
        assert final["nativePlaybackRequests"] == []
        assert final["errorCode"] is None
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()


def test_real_hidden_repeat_speed_sequence_uses_generated_html_audio(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "forvo_Vertrag.ogg"
    shutil.copy2(MEDIA_FIXTURE_DIR / "forvo_Vertrag.ogg", source)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, repeat_playback_by_default=False)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:play"), timeout=10.0)
        _wait_for_real_audio_ready(editor)
        _install_real_audio_probe(editor)
        _set_repeat(editor, True)
        _trusted_click_selector(editor, _button_selector("aqe:play"))
        initial = _wait_for_real_html_playback(editor)

        previous_name = source.name
        for command, expected_status in [
            ("aqe:slower", "Decreased speed to x1.5."),
            ("aqe:faster", "Increased speed to x1.5."),
            ("aqe:slower", "Decreased speed to x1.5."),
        ]:
            click_selector(editor.web, _button_selector(command), timeout=5.0)
            generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
            _wait_for_status_flow(
                editor,
                lambda status, expected=expected_status: status["text"] == expected,
                timeout=10.0,
            )
            previous_name = generated_name

        final = _wait_for_generated_real_repeat_playback(
            editor,
            previous_name,
            initial["playCalls"] + 3,
        )
        assert final["state"]["hasTrack"] is False
        assert final["backendPlaybackRequests"] == []
        assert final["nativePlaybackRequests"] == []
        assert final["errorCode"] is None
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()


def test_real_hidden_repeat_rapid_speed_sequence_uses_last_generated_html_audio(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "forvo_Vertrag.ogg"
    shutil.copy2(MEDIA_FIXTURE_DIR / "forvo_Vertrag.ogg", source)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, repeat_playback_by_default=False)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:play"), timeout=10.0)
        _wait_for_real_audio_ready(editor)
        _install_real_audio_probe(editor)
        _set_repeat(editor, True)
        _trusted_click_selector(editor, _button_selector("aqe:play"))
        initial = _wait_for_real_html_playback(editor)

        previous_name = source.name
        for command in ("aqe:slower", "aqe:faster", "aqe:slower"):
            click_selector(editor.web, _button_selector(command), timeout=5.0)
            previous_name = _wait_for_generated_mp3(note, media_dir, previous_name)

        final = _wait_for_generated_real_repeat_playback(
            editor,
            previous_name,
            initial["playCalls"] + 3,
        )
        assert final["state"]["hasTrack"] is False
        assert final["backendPlaybackRequests"] == []
        assert final["nativePlaybackRequests"] == []
        assert final["errorCode"] is None
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()


def _wait_for_generated_real_repeat_playback(editor, generated_name: str, minimum_play_calls: int):
    return wait_for_js_condition(
        editor.web,
        _real_audio_probe_js(),
        lambda value: value is not None
        and value["state"]["sourceFilename"] == generated_name
        and generated_name in value["src"]
        and value["state"]["repeatEnabled"] is True
        and value["state"]["playbackState"] == "playing"
        and value["state"]["playbackEngine"] == "html"
        and value["state"]["progressClockMode"] == "audio"
        and value["paused"] is False
        and value["currentTimeMs"] >= 120
        and value["playCalls"] >= minimum_play_calls,
        timeout=12.0,
    )
