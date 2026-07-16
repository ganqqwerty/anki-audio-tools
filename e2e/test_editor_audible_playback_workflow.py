"""Real-WebView playback assertions backed by independently captured PCM."""

from __future__ import annotations

import pytest

from e2e.audible_audio_capture import (
    AUDIBLE_FIXTURE_DIR,
    AUDIBLE_MANIFEST,
    AUDIBLE_SOURCE_NAME,
    analyze_audible_capture,
    audible_capture_status,
    enable_audible_worklet,
    finish_audible_capture,
    install_audible_capture,
)
from e2e.editor_note_helpers import ADDON_NUMERIC_ID, _button_selector, _sound_filename
from e2e.editor_region_loop_helpers import _normal_drag, _set_repeat, _shift_drag_region
from e2e.helpers import click_selector, wait_for_condition, wait_for_js_condition
from e2e.test_editor_convert_workflow import _wait_for_generated_audio
from e2e.test_editor_real_media_repeat_workflow import (
    _install_real_audio_probe,
    _open_real_media_editor,
    _real_audio_probe_js,
    _stop_real_audio_playback,
    _trusted_click_selector,
    _wait_for_real_audio_ready,
    _wait_for_real_html_playback,
)

FIXTURE_DIR = AUDIBLE_FIXTURE_DIR
SOURCE_NAME = AUDIBLE_SOURCE_NAME
MANIFEST = AUDIBLE_MANIFEST

pytestmark = [pytest.mark.shared_desktop, pytest.mark.trusted_input]


def test_audible_wav_playback_emits_the_requested_source_prefix(
    anki_mw,
    ffmpeg_config,
) -> None:
    """Prove that real browser playback emits addressable, non-silent PCM."""
    enable_audible_worklet(anki_mw)
    _media_dir, _source, _note, editor, parent, _track = _open_real_media_editor(
        anki_mw,
        ffmpeg_config,
        FIXTURE_DIR / SOURCE_NAME,
    )
    try:
        _wait_for_real_audio_ready(editor)
        _install_real_audio_probe(editor)
        install_audible_capture(editor, max_duration_ms=1200)

        _trusted_click_selector(editor, _button_selector("aqe:play"))
        _wait_for_real_html_playback(editor)
        wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None and value["currentTimeMs"] >= 600,
            timeout=5.0,
        )
        _stop_real_audio_playback(editor)
        capture = finish_audible_capture(editor)

        assert capture["totalFrames"] >= capture["sampleRate"] * 0.45, capture
        verdict = analyze_audible_capture(
            capture,
            contract=[{
                "kind": "segment",
                "source": SOURCE_NAME,
                "startMs": 0,
                "endMs": 600,
                "startPositionToleranceMs": 55,
                "endPositionToleranceMs": 140,
            }],
            manifest_path=MANIFEST,
            source_file_name=SOURCE_NAME,
            options={"durationToleranceMs": 140, "maxLeadingSilenceMs": 250},
        )
        assert verdict["pass"], verdict
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()


@pytest.mark.parametrize("source_name", [SOURCE_NAME, "addressable-timecode.mp3", "addressable-timecode.ogg"])
def test_audible_selected_playback_emits_only_the_selected_region(
    anki_mw,
    ffmpeg_config,
    source_name: str,
) -> None:
    """Detect wrong-prefix seeks and sound escaping a selected boundary."""
    enable_audible_worklet(anki_mw)
    _media_dir, _source, _note, editor, parent, _track = _open_real_media_editor(
        anki_mw,
        ffmpeg_config,
        FIXTURE_DIR / source_name,
    )
    try:
        _shift_drag_region(editor, 0.2, 0.3)
        _install_real_audio_probe(editor)
        install_audible_capture(editor, max_duration_ms=1800)

        _trusted_click_selector(editor, '[data-testid="aqe-selection-toolbar-play-0"]')
        _wait_for_real_html_playback(editor)
        wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None
            and value["playCalls"] == 1
            and value["state"]["playbackState"] == "stopped",
            timeout=5.0,
        )
        capture = finish_audible_capture(editor)
        verdict = analyze_audible_capture(
            capture,
            contract=[{
                "kind": "segment",
                "source": source_name,
                "startMs": 2000,
                "endMs": 3000,
                "startPositionToleranceMs": 70,
                "endPositionToleranceMs": 90,
            }],
            manifest_path=MANIFEST,
            source_file_name=source_name,
            options={"durationToleranceMs": 100, "maxLeadingSilenceMs": 250},
        )
        assert verdict["pass"], verdict
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()


def test_audible_selected_repeat_has_bounded_passes_gap_and_terminal_silence(
    anki_mw,
    ffmpeg_config,
) -> None:
    """Prove repeat restarts correctly and Repeat-off cannot leave a live timer."""
    enable_audible_worklet(anki_mw)
    _media_dir, _source, _note, editor, parent, _track = _open_real_media_editor(
        anki_mw,
        ffmpeg_config,
        FIXTURE_DIR / SOURCE_NAME,
        config_overrides={"repeat_pause_seconds": 0.2},
    )
    try:
        _shift_drag_region(editor, 0.4, 0.5)
        _set_repeat(editor, True)
        _install_real_audio_probe(editor)
        install_audible_capture(editor, max_duration_ms=3400)

        _trusted_click_selector(editor, '[data-testid="aqe-selection-toolbar-play-0"]')
        _wait_for_real_html_playback(editor)
        wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None
            and value["playCalls"] == 2
            and value["currentTimeMs"] >= 4300,
            timeout=6.0,
        )
        _set_repeat(editor, False)
        wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None
            and value["playCalls"] == 2
            and value["state"]["playbackState"] == "stopped",
            timeout=4.0,
        )
        capture = finish_audible_capture(editor)
        verdict = analyze_audible_capture(
            capture,
            contract=[
                {"kind": "segment", "source": SOURCE_NAME, "startMs": 4000, "endMs": 5000},
                {"kind": "silence", "minMs": 120, "maxMs": 320, "expectedMs": 200},
                {"kind": "segment", "source": SOURCE_NAME, "startMs": 4000, "endMs": 5000},
            ],
            manifest_path=MANIFEST,
            source_file_name=SOURCE_NAME,
            options={
                "durationToleranceMs": 110,
                "maxLeadingSilenceMs": 250,
                "sourcePositionToleranceMs": 70,
            },
        )
        assert verdict["pass"], verdict
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()


def test_audible_unsupported_m4a_recovery_converts_plays_and_preserves_history(
    anki_mw,
    ffmpeg_config,
) -> None:
    """Prove explicit recovery is initially silent, emits the MP3, and remains undoable."""
    source_name = "addressable-timecode.m4a"
    enable_audible_worklet(anki_mw)
    _media_dir, _source, _note, editor, parent, _track = _open_real_media_editor(
        anki_mw,
        ffmpeg_config,
        FIXTURE_DIR / source_name,
        config_overrides={"output_format": "flac"},
        require_browser_audio_ready=False,
    )
    try:
        _install_real_audio_probe(editor)
        wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None
            and value["state"]["htmlAudioReadinessState"] == "failed",
            timeout=10.0,
        )
        install_audible_capture(editor, max_duration_ms=8000)
        _trusted_click_selector(editor, '[data-testid="aqe-split-0-play-menu"]')
        wait_for_js_condition(
            editor.web,
            "window.__aqeAudibleCapture?.status() || null",
            lambda value: value is not None and value["totalFrames"] >= value["sampleRate"] * 0.5,
            timeout=5.0,
        )
        click_selector(editor.web, '[data-testid="aqe-split-0-play-menu"]', timeout=5.0)
        click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
        failure = wait_for_js_condition(
            editor.web,
            """
            (() => {
              const status = document.querySelector('[data-testid="aqe-status-0"]');
              const action = document.querySelector('[data-testid="aqe-convert-to-mp3-0"]');
              return {
                actionVisible: action instanceof HTMLButtonElement,
                statusText: status?.textContent || '',
              };
            })()
            """,
            lambda value: value["actionVisible"] is True
            and "AQE-PLAYBACK-002" in value["statusText"],
            timeout=5.0,
        )
        assert "AQE-MEDIA-002" not in failure["statusText"]
        assert _sound_filename(_note.fields[0]) == source_name
        failed_capture = finish_audible_capture(editor)
        failed_verdict = analyze_audible_capture(
            failed_capture,
            contract=[{"kind": "silence", "minMs": 450, "maxMs": 6000}],
            manifest_path=MANIFEST,
            source_file_name=source_name,
        )
        assert failed_verdict["pass"], failed_verdict["diagnosis"]

        click_selector(editor.web, '[data-testid="aqe-convert-to-mp3-0"]', timeout=5.0)
        generated_name = _wait_for_generated_audio(
            _note,
            _media_dir,
            source_name,
            suffix=".mp3",
            timeout=30.0,
        )
        _wait_for_real_html_playback(editor)
        install_audible_capture(editor, max_duration_ms=2000)
        wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None
            and value["currentTimeMs"] >= 700
            and value["state"]["sourceFilename"] == generated_name,
            timeout=8.0,
        )
        capture = finish_audible_capture(editor)
        _stop_real_audio_playback(editor)
        verdict = analyze_audible_capture(
            capture,
            contract=[
                {
                    "kind": "segment",
                    "source": source_name,
                    "startMs": 0,
                    "endMs": 700,
                    "startPositionToleranceMs": 120,
                    "endPositionToleranceMs": 170,
                },
            ],
            manifest_path=MANIFEST,
            source_file_name=source_name,
            options={"durationToleranceMs": 180, "sourcePositionToleranceMs": 80},
        )
        assert audible_capture_status(editor)["error"] is None
        assert verdict["pass"], verdict["diagnosis"]
        assert anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID)["output_format"] == "flac"

        _trusted_click_selector(editor, _button_selector("aqe:undo"))
        wait_for_condition(
            lambda: _sound_filename(_note.fields[0]) == source_name,
            timeout=10.0,
            message="Undo did not restore the unsupported M4A reference",
        )
        _trusted_click_selector(editor, _button_selector("aqe:play"))
        wait_for_js_condition(
            editor.web,
            "Boolean(document.querySelector('[data-testid=\"aqe-convert-to-mp3-0\"]'))",
            lambda visible: visible is True,
            timeout=8.0,
        )

        _trusted_click_selector(editor, _button_selector("aqe:redo"))
        wait_for_condition(
            lambda: _sound_filename(_note.fields[0]) == generated_name,
            timeout=10.0,
            message="Redo did not restore the recovered MP3 reference",
        )
        _wait_for_real_html_playback(editor)
        _stop_real_audio_playback(editor)
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()


def test_audible_pause_reposition_resume_emits_silence_then_new_cursor(
    anki_mw,
    ffmpeg_config,
) -> None:
    """Prove paused reposition emits nothing and resume does not use stale audio."""
    enable_audible_worklet(anki_mw)
    _media_dir, _source, _note, editor, parent, _track = _open_real_media_editor(
        anki_mw,
        ffmpeg_config,
        FIXTURE_DIR / SOURCE_NAME,
    )
    try:
        _shift_drag_region(editor, 0.2, 0.5)
        _install_real_audio_probe(editor)
        install_audible_capture(editor, max_duration_ms=2200)
        selector = '[data-testid="aqe-selection-toolbar-play-0"]'

        _trusted_click_selector(editor, selector)
        _wait_for_real_html_playback(editor)
        wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None and value["currentTimeMs"] >= 2500,
            timeout=5.0,
        )
        _trusted_click_selector(editor, selector)
        wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None and value["state"]["playbackState"] == "paused",
            timeout=5.0,
        )
        _normal_drag(editor, 0.4, 0.4)
        paused = audible_capture_status(editor)
        wait_for_js_condition(
            editor.web,
            "window.__aqeAudibleCapture?.status() || null",
            lambda value: value is not None
            and value["totalFrames"] >= paused["totalFrames"] + value["sampleRate"] * 0.2,
            timeout=3.0,
        )

        _trusted_click_selector(editor, selector)
        wait_for_js_condition(
            editor.web,
            _real_audio_probe_js(),
            lambda value: value is not None
            and value["playCalls"] == 2
            and value["currentTimeMs"] >= 4400,
            timeout=5.0,
        )
        _stop_real_audio_playback(editor)
        capture = finish_audible_capture(editor)
        verdict = analyze_audible_capture(
            capture,
            contract=[
                {
                    "kind": "segment", "source": SOURCE_NAME,
                    "startMs": 2000, "endMs": 2500,
                    "startPositionToleranceMs": 80, "endPositionToleranceMs": 160,
                },
                {"kind": "silence", "minMs": 150, "maxMs": 800},
                {
                    "kind": "segment", "source": SOURCE_NAME,
                    "startMs": 4000, "endMs": 4400,
                    "startPositionToleranceMs": 90, "endPositionToleranceMs": 160,
                },
            ],
            manifest_path=MANIFEST,
            source_file_name=SOURCE_NAME,
            options={"durationToleranceMs": 170, "sourcePositionToleranceMs": 80},
        )
        assert verdict["pass"], verdict
    finally:
        _stop_real_audio_playback(editor)
        editor.set_note(None)
        parent.close()
