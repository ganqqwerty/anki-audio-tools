"""E2E tests for inline graph-area control mirrors."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_graph_helpers import _click_graph_and_wait
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
)
from e2e.helpers import generate_tone, wait_for_js_condition, wait_for_selector


def test_graph_area_settings_redraw_active_graph(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_graph_area_settings.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.9)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        graph_connect_short_dropouts_ms=0,
        graph_voice_range="general",
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(
            editor,
            lambda value: value["sourceFilename"] == source.name and value["pitchPaths"] > 0,
            timeout=10.0,
        )

        wait_for_js_condition(
            editor.web,
            """
            (() => {
              const select = document.querySelector('[data-testid="aqe-graph-voice-range-0"]');
              if (!select) return false;
              select.value = "child";
              select.dispatchEvent(new Event("change", { bubbles: true }));
              return true;
            })()
            """,
            lambda value: value is True,
            timeout=5.0,
        )
        wait_for_js_condition(
            editor.web,
            """
            (() => {
              const state = window.__aqeSplitButtonStates?.[0];
              const graph = window.__aqeGraphStateForTest?.(0);
              return {
                busy: document.body.dataset.aqeBusy === "true",
                graph,
                voiceRange: state?.graphVoiceRange || "",
              };
            })()
            """,
            lambda value: value is not None
            and value["busy"] is False
            and value["voiceRange"] == "child"
            and value["graph"] is not None
            and value["graph"]["hasTrack"] is True
            and value["graph"]["sourceFilename"] == source.name,
            timeout=10.0,
        )

        wait_for_js_condition(
            editor.web,
            """
            (() => {
              const input = document.querySelector('[data-testid="aqe-graph-connect-dropouts-0"]');
              if (!input) return false;
              input.value = "90";
              input.dispatchEvent(new Event("input", { bubbles: true }));
              return true;
            })()
            """,
            lambda value: value is True,
            timeout=5.0,
        )
        wait_for_js_condition(
            editor.web,
            """
            (() => {
              const state = window.__aqeSplitButtonStates?.[0];
              const graph = window.__aqeGraphStateForTest?.(0);
              return {
                busy: document.body.dataset.aqeBusy === "true",
                connectDropouts: state?.graphConnectShortDropoutsMs,
                graph,
              };
            })()
            """,
            lambda value: value is not None
            and value["busy"] is False
            and value["connectDropouts"] == 90
            and value["graph"] is not None
            and value["graph"]["hasTrack"] is True
            and value["graph"]["sourceFilename"] == source.name,
            timeout=10.0,
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_graph_area_action_rail_stays_play_only_with_recording_configured(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_graph_area_record_visibility.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.8)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:analyze"), timeout=10.0)
        assert wait_for_js_condition(
            editor.web,
            """
            (() => {
              const rail = document.querySelector('[data-testid="aqe-graph-action-rail-0"]');
              return {
                graphRecord: document.querySelector('[data-testid="aqe-graph-record-0"]') !== null,
                graphPlayRecording: document.querySelector('[data-testid="aqe-graph-play-recording-0"]') !== null,
                railButtons: rail ? rail.querySelectorAll('.aqe-button').length : 0,
              };
            })()
            """,
            lambda value: value is not None
            and value["graphRecord"] is False
            and value["graphPlayRecording"] is False
            and value["railButtons"] == 1,
            timeout=5.0,
        )
    finally:
        editor.set_note(None)
        parent.close()

    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        visible_editor_buttons=["aqe:play", "aqe:analyze", "aqe:record-voice"],
    )
    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:record-voice"), timeout=10.0)
        assert wait_for_js_condition(
            editor.web,
            """
            (() => {
              const rail = document.querySelector('[data-testid="aqe-graph-action-rail-0"]');
              return {
                graphRecord: document.querySelector('[data-testid="aqe-graph-record-0"]') !== null,
                graphPlayRecording: document.querySelector('[data-testid="aqe-graph-play-recording-0"]') !== null,
                railButtons: rail ? rail.querySelectorAll('.aqe-button').length : 0,
              };
            })()
            """,
            lambda value: value is not None
            and value["graphRecord"] is False
            and value["graphPlayRecording"] is False
            and value["railButtons"] == 1,
            timeout=5.0,
        )
    finally:
        editor.set_note(None)
        parent.close()
