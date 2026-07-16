"""Acoustic E2E coverage for stateful playback interaction chains."""

from __future__ import annotations

import json

import pytest

from e2e.audible_audio_capture import (
    AUDIBLE_FIXTURE_DIR,
    AUDIBLE_MANIFEST,
    AUDIBLE_SOURCE_NAME,
    analyze_audible_capture,
    enable_audible_worklet,
    finish_audible_capture,
    install_audible_capture,
)
from e2e.editor_note_helpers import (
    _button_selector,
    _sound_filename,
    _wait_for_generated_mp3,
)
from e2e.editor_region_loop_helpers import _set_repeat, _shift_drag_region
from e2e.helpers import click_selector, wait_for_js_condition
from e2e.test_editor_real_media_repeat_workflow import (
    _install_real_audio_probe,
    _open_real_media_editor,
    _real_audio_probe_js,
    _stop_real_audio_playback,
    _trusted_click_selector,
    _wait_for_real_html_playback,
)

pytestmark = [pytest.mark.shared_desktop, pytest.mark.trusted_input]


def test_audible_replacing_selection_during_repeat_cancels_the_old_region(
    anki_mw,
    ffmpeg_config,
) -> None:
    """Forbid an old selected pass or timer from surviving region replacement."""
    enable_audible_worklet(anki_mw)
    _media_dir, _source, _note, editor, parent, _track = _open_real_media_editor(
        anki_mw,
        ffmpeg_config,
        AUDIBLE_FIXTURE_DIR / AUDIBLE_SOURCE_NAME,
        config_overrides={"repeat_pause_seconds": 0.15},
    )
    try:
        _shift_drag_region(editor, 0.2, 0.3)
        _set_repeat(editor, True)
        _install_real_audio_probe(editor)
        install_audible_capture(editor, max_duration_ms=3000)
        selector = '[data-testid="aqe-selection-toolbar-play-0"]'
        _trusted_click_selector(editor, selector)
        _wait_for_real_html_playback(editor)
        wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None and value["currentTimeMs"] >= 2500,
            timeout=5.0,
        )

        _shift_drag_region(editor, 0.6, 0.7)
        wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None
            and value["playCalls"] == 2
            and value["currentTimeMs"] >= 6400,
            timeout=5.0,
        )
        _set_repeat(editor, False)
        wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None
            and value["playCalls"] == 2
            and value["state"]["playbackState"] == "stopped",
            timeout=5.0,
        )
        capture = finish_audible_capture(editor)
        verdict = analyze_audible_capture(
            capture,
            contract=[
                {
                    "kind": "segment", "source": AUDIBLE_SOURCE_NAME,
                    "startMs": 2000, "endMs": 2500,
                    "startPositionToleranceMs": 80, "endPositionToleranceMs": 180,
                },
                {
                    "kind": "segment", "source": AUDIBLE_SOURCE_NAME,
                    "startMs": 6000, "endMs": 7000,
                    "startPositionToleranceMs": 90, "endPositionToleranceMs": 130,
                },
            ],
            manifest_path=AUDIBLE_MANIFEST,
            source_file_name=AUDIBLE_SOURCE_NAME,
            options={
                "durationToleranceMs": 190,
                "maxTransitionMs": 250,
                "sourcePositionToleranceMs": 80,
            },
        )
        assert verdict["pass"], json.dumps(verdict["segments"], indent=2)
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()


def test_audible_transform_during_repeat_stops_old_audio_and_autoplays_new_source(
    anki_mw,
    ffmpeg_config,
) -> None:
    """Forbid an old repeat timer or decoded source from surviving a transform."""
    enable_audible_worklet(anki_mw)
    media_dir, _source, note, editor, parent, _track = _open_real_media_editor(
        anki_mw,
        ffmpeg_config,
        AUDIBLE_FIXTURE_DIR / AUDIBLE_SOURCE_NAME,
        config_overrides={"repeat_pause_seconds": 0.15},
    )
    try:
        _shift_drag_region(editor, 0.2, 0.3)
        _set_repeat(editor, True)
        _install_real_audio_probe(editor)
        install_audible_capture(editor, max_duration_ms=5000)
        _trusted_click_selector(editor, '[data-testid="aqe-selection-toolbar-play-0"]')
        _wait_for_real_html_playback(editor)
        wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None and value["currentTimeMs"] >= 2400,
            timeout=5.0,
        )

        previous_name = _sound_filename(note.fields[0])
        click_selector(editor.web, _button_selector("aqe:volume-down"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
        wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None
            and value["state"]["sourceFilename"] == generated_name
            and value["state"]["playbackState"] == "playing"
            and value["currentTimeMs"] >= 350,
            timeout=12.0,
        )
        _set_repeat(editor, False)
        _stop_real_audio_playback(editor)
        capture = finish_audible_capture(editor)
        verdict = analyze_audible_capture(
            capture,
            contract=[
                {
                    "kind": "segment", "source": AUDIBLE_SOURCE_NAME,
                    "startMs": 2000, "endMs": 2400,
                    "minDurationMs": 250, "maxDurationMs": 1100,
                    "startPositionToleranceMs": 80, "endPositionToleranceMs": 700,
                },
                {"kind": "silence", "minMs": 100, "maxMs": 3500},
                {
                    "kind": "segment", "source": AUDIBLE_SOURCE_NAME,
                    "startMs": 0, "endMs": 500,
                    "minDurationMs": 250, "maxDurationMs": 1200,
                    "startPositionToleranceMs": 90, "endPositionToleranceMs": 350,
                },
            ],
            manifest_path=AUDIBLE_MANIFEST,
            source_file_name=AUDIBLE_SOURCE_NAME,
            options={
                "durationToleranceMs": 190,
                "maxTransitionMs": 250,
                "sourcePositionToleranceMs": 80,
            },
            oracle_options={"transitionMaxMs": 40},
        )
        assert verdict["pass"], json.dumps(verdict["segments"], indent=2)
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()
