"""E2E coverage for post-edit real media repeat playback."""

from __future__ import annotations

from pathlib import Path

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
from e2e.helpers import click_selector, wait_for_js_condition
from e2e.test_editor_real_media_repeat_workflow import (
    _install_real_audio_probe,
    _real_audio_probe_js,
    _stop_real_audio_playback,
    _trusted_click_selector,
    _wait_for_real_audio_ready,
    _wait_for_real_html_playback,
)


def test_real_repeat_delete_rest_restarts_generated_audio_after_edit(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_real_repeat_delete_rest_source.mp3"
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
        _wait_for_real_html_playback(editor)
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
        click_selector(editor.web, _button_selector("aqe:delete-rest"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Kept only selection 500-1250 ms.",
            timeout=10.0,
        )
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_name
            and value["selectionActive"] is True
            and value["selectionStartMs"] == 0
            and abs(value["selectionEndMs"] - value["durationMs"]) <= 1,
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
            timeout=10.0,
        )
        assert playing_generated["nativePlaybackRequests"] == []
        assert playing_generated["errorCode"] is None
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()
