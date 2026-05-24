"""E2E tests for editor graph cursor playback behavior."""

from __future__ import annotations

import time
from pathlib import Path

from e2e.conftest import import_runtime_addon_module
from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _drag_cursor_to_ratio,
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
)
from e2e.editor_playback_helpers import (
    PLAYBACK_INTERVAL_TOLERANCE_MS,
    _record_fake_playback,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_js_condition,
)


def test_cursor_drag_updates_session_and_play_uses_html_audio(anki_mw, ffmpeg_config) -> None:
    _SESSIONS = import_runtime_addon_module(".editor_integration")._SESSIONS

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_cursor_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _install_html_audio_test_driver(editor)
        run_js(
            editor.web,
            """
            (() => {
              const svg = document.querySelector('.aqe-visualizer[data-aqe-field-ord="0"] .aqe-visualizer-svg');
              const rect = svg.getBoundingClientRect();
              const EventCtor = window.PointerEvent || window.MouseEvent;
              const x = rect.left + rect.width * 0.65;
              svg.dispatchEvent(new EventCtor('pointerdown', { clientX: x, clientY: rect.top + 20, bubbles: true }));
              window.dispatchEvent(new EventCtor('pointerup', { clientX: x, clientY: rect.top + 20, bubbles: true }));
            })()
            """,
        )
        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.cursor_ms >= 1000
            ),
            timeout=5.0,
            message="Dragging the visualizer cursor did not update the editor session",
        )
        track = _wait_for_visualizer_track(editor, lambda value: value["cursorMs"] >= 1000)

        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            progressed = _wait_for_html_playback(
                editor,
                lambda state: state["progressMs"] > track["cursorMs"] + 120,
            )
            timecoded = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None
                and state["timecodeFlagVisible"]
                and state["timecodeFlagPitch"].endswith(" Hz")
                and state["timecodeFlagCurrent"].endswith("s")
                and state["pitchMarkerVisible"] is False
                and state["pitchMarkerX"] is not None
                and state["pitchMarkerY"] is not None
                and state["progressMs"] >= progressed["progressMs"],
                timeout=5.0,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            paused = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None and state["playbackState"] == "paused",
                timeout=5.0,
            )
            paused_progress = paused["progressMs"]
            pause_deadline = time.monotonic() + 0.35
            wait_for_condition(
                lambda: time.monotonic() >= pause_deadline,
                timeout=1.0,
                message="short playback pause wait failed",
            )
            frozen = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None,
                timeout=2.0,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None and state["progressMs"] > paused_progress + 120,
                timeout=5.0,
            )

        assert playback.attempts == []
        assert progressed["playButtonLabel"] == "Pause"
        assert progressed["audioClockMuted"] is False
        assert timecoded["timecodeFlagTransform"].startswith("translate3d(")
        assert timecoded["pitchMarkerX"] > 0
        assert timecoded["pitchMarkerY"] > 0
        assert abs(frozen["progressMs"] - paused_progress) < 80
        assert playback.toggle_count == 0
    finally:
        editor.set_note(None)
        parent.close()


def test_drag_to_70_percent_play_starts_html_audio_at_cursor(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_drag_70_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _install_html_audio_test_driver(editor)
        _drag_cursor_to_ratio(editor, 0.70)
        dragged = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and 650 <= state["anchorMs"] <= 750,
            timeout=5.0,
        )
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            playing = _wait_for_html_playback(
                editor,
                lambda state: state["progressMs"] >= dragged["anchorMs"],
            )

        assert playback.attempts == []
        assert playing["audioClockCurrentMs"] >= dragged["anchorMs"] - PLAYBACK_INTERVAL_TOLERANCE_MS
        assert playing["audioClockMuted"] is False
        assert dragged["cursorMs"] == dragged["anchorMs"]
    finally:
        editor.set_note(None)
        parent.close()


def test_play_from_zero_uses_original_file_without_segment(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_play_zero_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _install_html_audio_test_driver(editor)
        with _record_fake_playback(media_dir, {source.name: round(track["durationMs"])}) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            playing = _wait_for_html_playback(
                editor,
                lambda state: state["audioClockCurrentMs"] < 400,
            )

        assert playback.attempts == []
        assert playing["anchorMs"] == 0
        assert playing["audioClockMuted"] is False
    finally:
        editor.set_note(None)
        parent.close()


def test_play_without_graph_shown_uses_pause_button_until_native_playback_ends(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_no_graph_native_playback_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None
            and state["hidden"] is True
            and state["hasTrack"] is False
            and state["playButtonLabel"] == "Play",
            timeout=5.0,
        )
        with _record_fake_playback(media_dir, {source.name: 1000}) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            playing = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None
                and state["hidden"] is True
                and state["playbackState"] == "playing"
                and state["playButtonLabel"] == "Pause",
                timeout=5.0,
            )
            run_js(editor.web, "pycmd('aqe:play-ended')")
            wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None
                and state["playbackState"] == "stopped"
                and state["playButtonLabel"] == "Play",
                timeout=5.0,
            )

        assert playback.attempts
        assert playback.attempts[0].filename == source.name
        assert playback.attempts[0].start_ms == 0
        assert playing["playbackEngine"] == "native"
    finally:
        editor.set_note(None)
        parent.close()


def test_drag_to_70_percent_plays_html_audio_70_to_100_without_native_seek(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_drag_70_delayed_seek_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _install_html_audio_test_driver(editor)
        _drag_cursor_to_ratio(editor, 0.70)
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and 650 <= state["anchorMs"] <= 750,
            timeout=5.0,
        )
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            apply_immediate_seek=False,
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            playing = _wait_for_html_playback(
                editor,
                lambda state: state["audioClockCurrentMs"] >= state["anchorMs"] - PLAYBACK_INTERVAL_TOLERANCE_MS,
            )

        assert playback.attempts == []
        assert playing["anchorMs"] >= round(track["durationMs"] * 0.70) - PLAYBACK_INTERVAL_TOLERANCE_MS
        assert playing["audioClockMuted"] is False
    finally:
        editor.set_note(None)
        parent.close()


def test_pause_drag_then_play_restarts_from_dragged_cursor(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_pause_drag_play_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _install_html_audio_test_driver(editor)
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(
                editor,
                lambda state: state["progressMs"] >= 500,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None and state["playbackState"] == "paused",
                timeout=5.0,
            )
            _drag_cursor_to_ratio(editor, 0.40)
            dragged = wait_for_js_condition(
                editor.web,
                _graph_state_js(),
                lambda state: state is not None
                and state["resumeRequiresRestart"] is True
                and 700 <= state["cursorMs"] <= 900,
                timeout=5.0,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            restarted = _wait_for_html_playback(
                editor,
                lambda state: state["progressMs"] >= dragged["anchorMs"],
            )

        assert playback.attempts == []
        assert restarted["audioClockCurrentMs"] >= dragged["anchorMs"] - PLAYBACK_INTERVAL_TOLERANCE_MS
        assert dragged["anchorMs"] == dragged["cursorMs"]
        assert playback.toggle_count == 0
    finally:
        editor.set_note(None)
        parent.close()
