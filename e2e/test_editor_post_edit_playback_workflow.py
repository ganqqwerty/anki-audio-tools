"""E2E coverage for playback after editor audio edits."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_graph_helpers import _click_graph_and_wait
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _wait_for_generated_mp3,
)
from e2e.editor_playback_helpers import _record_fake_playback
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_selector,
)


def test_standard_edit_plays_new_generated_audio(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_post_edit_playback_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        with _record_fake_playback(media_dir, {source.name: 1000}, ffmpeg_config=ffmpeg_config) as playback:
            click_selector(editor.web, _button_selector("aqe:faster"), timeout=5.0)
            generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
            wait_for_condition(
                lambda: any(attempt.filename == generated_name for attempt in playback.attempts),
                timeout=5.0,
                message="Post-edit playback did not start for the generated audio",
            )

        assert playback.attempts[-1].filename == generated_name
        assert playback.attempts[-1].filename != source.name
    finally:
        editor.set_note(None)
        parent.close()


def test_post_edit_playback_waits_for_frontend_ready_event(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_post_edit_playback_retry_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        _delay_post_edit_playback_ready_event(editor, delay_ms=1500)

        with _record_fake_playback(media_dir, {source.name: 1000}, ffmpeg_config=ffmpeg_config) as playback:
            click_selector(editor.web, _button_selector("aqe:faster"), timeout=5.0)
            generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
            wait_for_condition(
                lambda: any(attempt.filename == generated_name for attempt in playback.attempts),
                timeout=6.0,
                message="Post-edit playback did not wait for the frontend ready event",
            )

        assert playback.attempts[-1].filename == generated_name
    finally:
        editor.set_note(None)
        parent.close()


def test_undo_post_edit_playback_ignores_stale_graph_redraw_marker(anki_mw, ffmpeg_config, caplog) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_post_edit_playback_undo_stale_graph.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _install_post_edit_ready_probe_with_stale_graph_marker(editor, source.name)

        wait_for_condition(
            lambda: any("post-edit playback ready dispatched" in record.message for record in caplog.records),
            timeout=5.0,
            message="Post-edit ready notification was blocked by a stale graph redraw marker",
        )
    finally:
        editor.set_note(None)
        parent.close()


def _delay_post_edit_playback_ready_event(editor, delay_ms: int) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          const originalPycmd = window.pycmd;
          const delayMs = {delay_ms};
          window.__aqeDelayedPostEditPlaybackReadyForTest = false;
          window.pycmd = (command) => {{
            const payload = window.__aqePendingCommandPayload;
            if (
              command === "aqe:command-payload"
              && payload?.command === "aqe:post-edit-playback-ready"
              && !window.__aqeDelayedPostEditPlaybackReadyForTest
            ) {{
              window.__aqeDelayedPostEditPlaybackReadyForTest = true;
              window.__aqePendingCommandPayload = null;
              setTimeout(() => {{
                window.__aqePendingCommandPayload = payload;
                originalPycmd(command);
              }}, delayMs);
              return;
            }}
            originalPycmd(command);
          }};
          return true;
        }})()
        """,
    )


def _install_post_edit_ready_probe_with_stale_graph_marker(editor, source_name: str) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          window.__AQE_EDITOR_CONFIG__.pendingPostEditPlayback = {{
            fieldOrd: 0,
            generation: 99,
            requireGraphRedraw: true,
            sourceFilename: {source_name!r},
          }};
          window.__aqePendingCommandPayload = null;
          window.__aqePendingGraphRedrawField = 0;
          window.__aqePendingGraphRedrawSource = "stale-redraw-source.mp3";
          window.__aqeSetBusy(0, false);
          return true;
        }})()
        """,
    )
