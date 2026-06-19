"""E2E tests for processing preset settings."""

from __future__ import annotations

from pathlib import Path

from e2e.conftest import ADDON_NUMERIC_ID
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _wait_for_generated_mp3,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)
from e2e.settings_dialog_helpers import open_settings_dialog


def test_settings_dialog_constructs_and_saves_processing_preset(anki_mw) -> None:
    config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
    config["audio_processing_presets"] = []
    config["dpdfnet_attn_limit_db"] = 12.0
    anki_mw.addonManager.writeConfig(ADDON_NUMERIC_ID, config)

    dialog = open_settings_dialog(anki_mw)
    try:
        click_selector(dialog, '[data-testid="settings-tab-presets"]', timeout=5.0)
        click_selector(dialog, '[data-testid="preset-add"]', timeout=5.0)
        wait_for_selector(dialog, '[data-testid="preset-name"]', timeout=5.0)
        run_js(
            dialog,
            """
            (() => {
              const input = document.querySelector('[data-testid="preset-name"]');
              if (!input) return false;
              input.value = 'E2E Clean graph';
              input.dispatchEvent(new Event('input', { bubbles: true }));
              return true;
            })()
            """,
        )
        wait_for_js_condition(
            dialog,
            "document.querySelector('[data-testid=\"preset-name\"]')?.value",
            lambda value: value == "E2E Clean graph",
            timeout=5.0,
        )
        click_selector(dialog, '[data-testid="preset-graph-enabled"]', timeout=5.0)
        click_selector(dialog, '[data-testid="settings-save"]', timeout=5.0)
        wait_for_condition(
            lambda: len(
                (anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}).get(
                    "audio_processing_presets",
                    [],
                )
            )
            == 1,
            timeout=5.0,
        )
    finally:
        if dialog.isVisible():
            dialog.close()

    saved = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
    presets = saved["audio_processing_presets"]
    assert presets[0]["name"] == "E2E Clean graph"
    assert presets[0]["steps"][0]["operation"] == "denoise"
    assert presets[0]["steps"][0]["parameters"]["denoise_algorithm"] == "standard"
    assert presets[0]["steps"][0]["parameters"]["dpdfnet_attn_limit_db"] == 12.0
    assert presets[0]["graph"]["enabled"] is True
    assert presets[0]["graph"]["parameters"] == {
        "graph_voice_range": "general",
        "graph_recording_condition": "auto",
        "graph_smoothness": "very_smooth",
        "graph_connect_short_dropouts_ms": 240,
        "graph_voice_lock": "balanced",
    }


def test_editor_runs_processing_preset_against_current_field(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_processing_preset_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.2)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        audio_processing_presets=[
            {
                "id": "faster_preset",
                "name": "Faster preset",
                "steps": [
                    {
                        "id": "faster",
                        "operation": "faster",
                        "parameters": {"speed_step": 1.25},
                    }
                ],
                "graph": {
                    "enabled": False,
                    "parameters": {
                        "graph_voice_range": "general",
                        "graph_recording_condition": "auto",
                        "graph_smoothness": "very_smooth",
                        "graph_connect_short_dropouts_ms": 240,
                        "graph_voice_lock": "balanced",
                    },
                },
            }
        ],
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:preset"), timeout=10.0)
        click_selector(editor.web, _button_selector("aqe:preset"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)

        assert generated_name.startswith("editor_processing_preset_source__aqe_")
        assert generated_name.count("__aqe_") == 1
        assert (media_dir / generated_name).is_file()
    finally:
        editor.set_note(None)
        parent.close()
