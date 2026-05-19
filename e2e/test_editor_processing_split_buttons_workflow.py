"""E2E tests for editor processing split-button controls."""

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
    _three_audio_field_note,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)


def _split_menu_selector(command: str, ord_: int = 0) -> str:
    slug = command.removeprefix("aqe:")
    return f'[data-testid="aqe-split-{ord_}-{slug}-menu"]'


def _split_popover_state_js(command: str, ord_: int = 0) -> str:
    slug = command.removeprefix("aqe:")
    return f"""
    (() => {{
      const popover = document.querySelector('[data-testid="aqe-split-{ord_}-{slug}-popover"]');
      const slider = document.querySelector('[data-testid="aqe-split-{ord_}-{slug}-slider"]');
      const anchor = document.querySelector('[data-testid="aqe-split-{ord_}-{slug}-menu"]')?.closest('.aqe-split-button');
      if (!popover || !slider || !anchor) return null;
      const popoverRect = popover.getBoundingClientRect();
      const anchorRect = anchor.getBoundingClientRect();
      return {{
        text: popover.textContent,
        sliderValue: slider.value,
        bottom: popoverRect.bottom,
        left: popoverRect.left,
        right: popoverRect.right,
        top: popoverRect.top,
        buttonBottom: anchorRect.bottom,
        viewportHeight: window.innerHeight,
        viewportWidth: window.innerWidth,
        centerDelta: Math.abs(
          popoverRect.left + popoverRect.width / 2 - (anchorRect.left + anchorRect.width / 2)
        )
      }};
    }})()
    """


def _split_value_state_js(command: str, ord_: int = 0) -> str:
    slug = command.removeprefix("aqe:")
    return f"""
    (() => {{
      const input = document.querySelector('[data-testid="aqe-split-{ord_}-{slug}-value"]');
      const slider = document.querySelector('[data-testid="aqe-split-{ord_}-{slug}-slider"]');
      return input && slider ? {{
        inputMax: input.max,
        inputMin: input.min,
        inputStep: input.step,
        inputValue: input.value,
        sliderValue: slider.value,
      }} : null;
    }})()
    """


def _set_split_value_input_js(command: str, value: str, ord_: int = 0) -> str:
    slug = command.removeprefix("aqe:")
    return f"""
    (() => {{
      const input = document.querySelector('[data-testid="aqe-split-{ord_}-{slug}-value"]');
      if (!input) return false;
      input.value = {json.dumps(value)};
      input.dispatchEvent(new Event("input", {{ bubbles: true }}));
      return true;
    }})()
    """


def _set_split_slider_js(command: str, value: str, ord_: int = 0) -> str:
    slug = command.removeprefix("aqe:")
    return f"""
    (() => {{
      const slider = document.querySelector('[data-testid="aqe-split-{ord_}-{slug}-slider"]');
      if (!slider) return false;
      slider.value = {json.dumps(value)};
      slider.dispatchEvent(new Event("input", {{ bubbles: true }}));
      return true;
    }})()
    """


def test_settings_trim_step_controls_editor_button_behavior(anki_mw, ffmpeg_config) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms
    from anki_audio_quick_editor.editor_integration import _SESSIONS

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_settings_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, manual_trim_small_ms=500)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        generated_name = _click_and_wait_for_new_file(
            editor, note, media_dir, "aqe:trim-left", source.name
        )

        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.state is not None
                and session.state.left_trim_ms == 500
            ),
            timeout=5.0,
            message="Editor did not use the configured trim step",
        )
        assert probe_duration_ms(media_dir / generated_name, ffmpeg_config) < probe_duration_ms(
            source, ffmpeg_config
        ) - 350
    finally:
        editor.set_note(None)
        parent.close()


def test_trim_split_button_uses_settings_default_and_closes_on_outside_click(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_split_default_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, manual_trim_small_ms=500)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:trim-left"), timeout=5.0)
        popover = wait_for_js_condition(
            editor.web,
            _split_popover_state_js("aqe:trim-left"),
            lambda value: value is not None
            and value["sliderValue"] == "500"
            and value["left"] >= 0
            and value["top"] >= 0
            and value["right"] <= value["viewportWidth"]
            and value["bottom"] <= value["viewportHeight"],
            timeout=5.0,
        )

        run_js(editor.web, "document.body.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }))")
        wait_for_js_condition(
            editor.web,
            "document.querySelector('[data-testid=\"aqe-split-0-trim-left-popover\"]') === null",
            timeout=5.0,
        )

        assert "500 ms" in popover["text"]
        assert popover["left"] >= 0
        assert popover["top"] >= 0
        assert popover["right"] <= popover["viewportWidth"]
        assert popover["bottom"] <= popover["viewportHeight"]
    finally:
        editor.set_note(None)
        parent.close()


def test_trim_split_button_local_value_repeats_without_changing_settings(
    anki_mw,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.editor_integration import _SESSIONS

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_split_repeat_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, manual_trim_small_ms=500)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:trim-left"), timeout=5.0)
        click_selector(
            editor.web,
            '[data-testid="aqe-split-0-trim-left-preset-200"]',
            timeout=5.0,
        )

        first_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:trim-left",
            source.name,
        )
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        second_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:trim-left",
            first_name,
        )

        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.state is not None
                and session.state.left_trim_ms == 400
            ),
            timeout=5.0,
            message="Trim split button did not reuse the field-local 200 ms value",
        )
        config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID)
        assert config["manual_trim_small_ms"] == 500
        assert _sound_filename(note.fields[0]) == second_name
    finally:
        editor.set_note(None)
        parent.close()


def test_trim_split_button_value_is_isolated_across_audio_fields(
    anki_mw,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms

    media_dir = Path(anki_mw.col.media.dir())
    sources = (
        media_dir / "editor_split_multi_one.wav",
        media_dir / "editor_split_multi_two.wav",
        media_dir / "editor_split_multi_three.wav",
    )
    for source in sources:
        generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _three_audio_field_note(anki_mw, tuple(source.name for source in sources))
    _configure_ffmpeg(anki_mw, ffmpeg_config, manual_trim_small_ms=100)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left", 0), timeout=10.0)
        wait_for_selector(editor.web, _button_selector("aqe:trim-left", 1), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:trim-left", 0), timeout=5.0)
        click_selector(
            editor.web,
            '[data-testid="aqe-split-0-trim-left-preset-200"]',
            timeout=5.0,
        )

        first_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:trim-left",
            sources[0].name,
            field_index=0,
        )
        second_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:trim-left",
            sources[1].name,
            field_index=1,
        )

        first_delta = probe_duration_ms(sources[0], ffmpeg_config) - probe_duration_ms(
            media_dir / first_name,
            ffmpeg_config,
        )
        second_delta = probe_duration_ms(sources[1], ffmpeg_config) - probe_duration_ms(
            media_dir / second_name,
            ffmpeg_config,
        )
        assert 140 <= first_delta <= 320
        assert 40 <= second_delta <= 180
        assert _sound_filename(note.fields[2]) == sources[2].name
    finally:
        editor.set_note(None)
        parent.close()


def test_split_tooltip_value_inputs_sync_with_sliders_and_apply_local_values(
    anki_mw,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.editor_integration import _SESSIONS

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_split_tooltip_input_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, manual_trim_small_ms=100, volume_step_db=3, speed_step=0.05)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:trim-left"), timeout=5.0)
        trim_state = wait_for_js_condition(
            editor.web,
            _split_value_state_js("aqe:trim-left"),
            lambda value: value is not None and value["inputValue"] == "100" and value["sliderValue"] == "100",
            timeout=5.0,
        )
        assert trim_state["inputMin"] == "50"
        assert trim_state["inputMax"] == "10000"
        assert trim_state["inputStep"] == "50"

        wait_for_js_condition(
            editor.web,
            _set_split_slider_js("aqe:trim-left", "250"),
            lambda value: value is True,
            timeout=5.0,
        )
        wait_for_js_condition(
            editor.web,
            _split_value_state_js("aqe:trim-left"),
            lambda value: value is not None and value["inputValue"] == "250",
            timeout=5.0,
        )
        wait_for_js_condition(
            editor.web,
            _set_split_value_input_js("aqe:trim-left", "350"),
            lambda value: value is True,
            timeout=5.0,
        )
        wait_for_js_condition(
            editor.web,
            _split_value_state_js("aqe:trim-left"),
            lambda value: value is not None and value["sliderValue"] == "350",
            timeout=5.0,
        )
        trim_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:trim-left",
            source.name,
        )
        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.state is not None
                and session.state.left_trim_ms == 350
            ),
            timeout=5.0,
            message="Trim tooltip input did not apply the local 350 ms value",
        )

        wait_for_selector(editor.web, _button_selector("aqe:volume-up"), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:volume-up"), timeout=5.0)
        wait_for_js_condition(
            editor.web,
            _set_split_value_input_js("aqe:volume-up", "6.5"),
            lambda value: value is True,
            timeout=5.0,
        )
        wait_for_js_condition(
            editor.web,
            _split_value_state_js("aqe:volume-up"),
            lambda value: value is not None and value["sliderValue"] == "6.5",
            timeout=5.0,
        )
        volume_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:volume-up",
            trim_name,
        )
        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.state is not None
                and session.state.volume_db == 6.5
            ),
            timeout=5.0,
            message="Volume tooltip input did not apply the local 6.5 dB value",
        )

        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:faster"), timeout=5.0)
        wait_for_js_condition(
            editor.web,
            _set_split_value_input_js("aqe:faster", "1.12"),
            lambda value: value is True,
            timeout=5.0,
        )
        wait_for_js_condition(
            editor.web,
            _split_value_state_js("aqe:faster"),
            lambda value: value is not None and value["sliderValue"] == "0.12",
            timeout=5.0,
        )
        faster_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:faster",
            volume_name,
        )
        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.state is not None
                and session.state.speed == 1.12
            ),
            timeout=5.0,
            message="Faster tooltip input did not apply the local x1.12 value",
        )

        wait_for_selector(editor.web, _button_selector("aqe:slower"), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:slower"), timeout=5.0)
        wait_for_js_condition(
            editor.web,
            _set_split_slider_js("aqe:slower", "0.08"),
            lambda value: value is True,
            timeout=5.0,
        )
        wait_for_js_condition(
            editor.web,
            _split_value_state_js("aqe:slower"),
            lambda value: value is not None and value["inputValue"] == "0.92",
            timeout=5.0,
        )
        wait_for_js_condition(
            editor.web,
            _set_split_value_input_js("aqe:slower", "0.88"),
            lambda value: value is True,
            timeout=5.0,
        )
        wait_for_js_condition(
            editor.web,
            _split_value_state_js("aqe:slower"),
            lambda value: value is not None and value["sliderValue"] == "0.12",
            timeout=5.0,
        )
        _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:slower",
            faster_name,
        )
        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.state is not None
                and session.state.speed == 1.0
            ),
            timeout=5.0,
            message="Slower tooltip input did not apply the local x0.88 value",
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_volume_and_speed_split_buttons_apply_local_values_without_changing_settings(
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
            '[data-testid="aqe-split-0-volume-up-preset-6"]',
            timeout=5.0,
        )
        volume_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:volume-up",
            source.name,
        )
        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.state is not None
                and session.state.volume_db == 6
            ),
            timeout=5.0,
            message="Volume split button did not apply the local 6 dB value",
        )

        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:faster"), timeout=5.0)
        click_selector(
            editor.web,
            '[data-testid="aqe-split-0-faster-preset-0.1"]',
            timeout=5.0,
        )
        speed_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:faster",
            volume_name,
        )
        wait_for_condition(
            lambda: (
                (session := _SESSIONS.get(editor)) is not None
                and session.state is not None
                and session.state.speed == 1.1
            ),
            timeout=5.0,
            message="Speed split button did not apply the local x1.10 value",
        )

        config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID)
        assert config["volume_step_db"] == 3
        assert config["speed_step"] == 0.05
        assert probe_duration_ms(media_dir / speed_name, ffmpeg_config) < probe_duration_ms(
            media_dir / volume_name,
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
