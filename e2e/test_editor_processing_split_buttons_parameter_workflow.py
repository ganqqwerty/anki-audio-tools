"""E2E tests for non-trim editor split-button parameters."""

from __future__ import annotations

import json
from pathlib import Path

from e2e.editor_audio_generation_helpers import _fake_deep_filter_executable
from e2e.editor_note_helpers import (
    ADDON_NUMERIC_ID,
    _artifact_dirs_for_source,
    _artifact_root,
    _basic_audio_note,
    _button_selector,
    _cleanup_artifact_dirs,
    _click_and_wait_for_new_file,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_selector,
)
from e2e.test_editor_processing_split_buttons_workflow import _split_menu_selector


def test_grouped_volume_and_speed_split_buttons_apply_local_values_without_changing_settings(
    anki_mw,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms
    from anki_audio_quick_editor.editor_integration import _SESSIONS

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_split_volume_speed_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, volume_step_db=3, speed_step=0.05)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:volume-up"), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:volume-up"), timeout=5.0)
        click_selector(
            editor.web,
            '[data-testid="aqe-split-0-volume-preset-6"]',
            timeout=5.0,
        )
        volume_down_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:volume-down",
            source.name,
        )
        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.state is not None
                and session.state.volume_db == -6
            ),
            timeout=5.0,
            message="Grouped volume menu did not apply the local 6 dB value to Volume -",
        )
        volume_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:volume-up",
            volume_down_name,
        )
        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.state is not None
                and session.state.volume_db == 0
            ),
            timeout=5.0,
            message="Grouped volume menu did not apply the local 6 dB value to Volume +",
        )

        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:faster"), timeout=5.0)
        click_selector(
            editor.web,
            '[data-testid="aqe-split-0-speed-preset-0.1"]',
            timeout=5.0,
        )
        slower_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:slower",
            volume_name,
        )
        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.state is not None
                and session.state.speed == 0.9
            ),
            timeout=5.0,
            message="Grouped speed menu did not apply the local x0.90 value to Slower",
        )
        speed_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:faster",
            slower_name,
        )

        config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID)
        assert config["volume_step_db"] == 3
        assert config["speed_step"] == 0.05
        assert probe_duration_ms(media_dir / slower_name, ffmpeg_config) > probe_duration_ms(
            media_dir / volume_name,
            ffmpeg_config,
        )
        assert probe_duration_ms(media_dir / speed_name, ffmpeg_config) < probe_duration_ms(
            media_dir / slower_name,
            ffmpeg_config,
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_pause_split_button_applies_local_aggressiveness_without_changing_settings(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_split_pause_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    fake_deep_filter, _deep_filter_log = _fake_deep_filter_executable(tmp_path)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        deep_filter_path=str(fake_deep_filter),
        internal_pause_silence_threshold_db=-45,
        internal_pause_threshold_ms=300,
        internal_pause_target_gap_ms=100,
        pause_aggressiveness="normal",
    )
    artifact_root = _artifact_root(anki_mw)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:remove-pauses"), timeout=10.0)
        before_artifacts = _artifact_dirs_for_source(artifact_root, source)
        click_selector(editor.web, _split_menu_selector("aqe:remove-pauses"), timeout=5.0)
        click_selector(
            editor.web,
            '[data-testid="aqe-split-0-remove-pauses-preset-aggressive"]',
            timeout=5.0,
        )
        generated_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:remove-pauses",
            source.name,
        )
        wait_for_condition(
            lambda: len(_artifact_dirs_for_source(artifact_root, source) - before_artifacts) == 1,
            timeout=5.0,
            message="Pause split button did not produce a new artifact manifest",
        )
        new_artifact = next(iter(_artifact_dirs_for_source(artifact_root, source) - before_artifacts))
        manifest = json.loads((new_artifact / "manifest.json").read_text(encoding="utf-8"))

        config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID)
        assert manifest["config"]["internal_pause_silence_threshold_db"] == -50
        assert manifest["config"]["internal_pause_threshold_ms"] == 180
        assert manifest["config"]["internal_pause_target_gap_ms"] == 60
        assert config["pause_aggressiveness"] == "normal"
        assert config["internal_pause_silence_threshold_db"] == -45
        assert config["internal_pause_threshold_ms"] == 300
        assert config["internal_pause_target_gap_ms"] == 100
        assert _sound_filename(note.fields[0]) == generated_name
    finally:
        editor.set_note(None)
        parent.close()
        _cleanup_artifact_dirs(artifact_root, source)
