"""E2E tests for editor audio edit controls and processing state."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from e2e.editor_audio_generation_helpers import _fake_deep_filter_executable
from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_state_js,
    _wait_for_visualizer_track,
)
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
    _processing_status_js,
    _sound_filename,
    _three_audio_field_note,
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
      return popover && slider ? {{
        text: popover.textContent,
        sliderValue: slider.value,
        top: popover.getBoundingClientRect().top,
        buttonBottom: anchor.getBoundingClientRect().bottom,
        centerDelta: Math.abs(
          popover.getBoundingClientRect().left + popover.getBoundingClientRect().width / 2
          - (anchor.getBoundingClientRect().left + anchor.getBoundingClientRect().width / 2)
        )
      }} : null;
    }})()
    """


def test_each_processing_button_updates_field_to_new_real_audio(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_each_button_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    original_bytes = source.read_bytes()
    fake_deep_filter, _deep_filter_log = _fake_deep_filter_executable(tmp_path)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, deep_filter_path=str(fake_deep_filter))
    artifact_root = _artifact_root(anki_mw)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        assert wait_for_js_condition(
            editor.web,
            "Array.from(document.querySelectorAll('[data-aqe-command]')).map((node) => node.dataset.aqeCommand)",
            lambda commands: all(
                command not in commands
                for command in (
                    "aqe:save",
                    "aqe:cancel",
                    "aqe:untrim-left",
                    "aqe:untrim-right",
                )
            ),
            timeout=5.0,
        )
        assert wait_for_js_condition(
            editor.web,
            """
            (() => {
              const buttons = Array.from(document.querySelectorAll('.aqe-button'))
                .filter((node) => getComputedStyle(node).display !== 'none' && node.getClientRects().length > 0);
              return {
                labels: buttons.map((node) => (
                  node.querySelector('.aqe-button-label')?.textContent || node.textContent || ''
                ).trim()),
                iconsPerButton: buttons.map((node) => node.querySelectorAll('.aqe-button-icon svg').length),
                iconStrokeValues: buttons.flatMap((button) =>
                  Array.from(button.querySelectorAll('.aqe-button-icon svg'))
                    .map((node) => node.getAttribute('stroke') || getComputedStyle(node).stroke || '')
                ),
              };
            })()
            """,
            lambda state: state["labels"]
            == [
                "Play",
                "Repeat",
                "Graph",
                "Folder",
                "-L",
                "Options",
                "-R",
                "Options",
                "Shorten Pauses",
                "Options",
                "Denoise",
                "Options",
                "Slower",
                "Options",
                "Faster",
                "Options",
                "Volume -",
                "Options",
                "Volume +",
                "Options",
                "Undo",
                "Redo",
                "Settings",
            ]
            and all(count >= 1 for count in state["iconsPerButton"])
            and state["iconStrokeValues"]
            and all(stroke == "currentColor" for stroke in state["iconStrokeValues"]),
            timeout=5.0,
        )

        previous_name = source.name
        generated_names: list[str] = []
        for command in (
            "aqe:trim-left",
            "aqe:trim-right",
            "aqe:slower",
            "aqe:faster",
            "aqe:volume-down",
            "aqe:volume-up",
            "aqe:remove-pauses",
        ):
            wait_for_selector(editor.web, _button_selector(command), timeout=5.0)
            previous_name = _click_and_wait_for_new_file(editor, note, media_dir, command, previous_name)
            generated_names.append(previous_name)

        assert len(generated_names) == len(set(generated_names))
        assert source.read_bytes() == original_bytes
        assert probe_duration_ms(media_dir / generated_names[0], ffmpeg_config) < probe_duration_ms(
            source, ffmpeg_config
        )
        graph_state = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda value: value is not None,
            timeout=5.0,
        )
        assert graph_state["active"] is False
        assert graph_state["hidden"] is True
    finally:
        editor.set_note(None)
        parent.close()
        _cleanup_artifact_dirs(artifact_root, source)


def test_ffmpeg_command_status_respects_settings_flag(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    hidden_source = media_dir / "editor_hidden_command_source.wav"
    shown_source = media_dir / "editor_shown_command_source.wav"
    generate_tone(ffmpeg_config, hidden_source, duration_s=2.0)
    generate_tone(ffmpeg_config, shown_source, duration_s=2.0)

    hidden_note = _basic_audio_note(anki_mw, hidden_source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, show_ffmpeg_commands=False)
    hidden_editor, hidden_parent = _open_editor(anki_mw, hidden_note)
    try:
        wait_for_selector(hidden_editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        click_selector(hidden_editor.web, _button_selector("aqe:trim-left"), timeout=5.0)
        hidden_status = wait_for_js_condition(
            hidden_editor.web,
            _processing_status_js(),
            lambda status: status is not None and status["text"].startswith("Processing with ffmpeg"),
            timeout=5.0,
        )
        assert " -i " not in hidden_status["text"]
        assert hidden_status["title"] == ""
        _wait_for_generated_mp3(hidden_note, media_dir, hidden_source.name)
    finally:
        hidden_editor.set_note(None)
        hidden_parent.close()

    shown_note = _basic_audio_note(anki_mw, shown_source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, show_ffmpeg_commands=True)
    shown_editor, shown_parent = _open_editor(anki_mw, shown_note)
    try:
        wait_for_selector(shown_editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        click_selector(shown_editor.web, _button_selector("aqe:trim-left"), timeout=5.0)
        shown_status = wait_for_js_condition(
            shown_editor.web,
            _processing_status_js(),
            lambda status: status is not None and " -i " in status["text"],
            timeout=5.0,
        )
        assert shown_status["title"].startswith(ffmpeg_config.ffmpeg_path)
        _wait_for_generated_mp3(shown_note, media_dir, shown_source.name)
    finally:
        shown_editor.set_note(None)
        shown_parent.close()


def test_undo_restores_previous_generated_reference(anki_mw, ffmpeg_config) -> None:
    from aqt.sound import av_player

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_undo_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        with (
            patch.object(av_player, "stop_and_clear_queue", lambda: None),
            patch.object(av_player, "play_tags", lambda _tags: None),
            patch.object(av_player, "seek_relative", lambda _seconds: None),
            patch.object(av_player, "toggle_pause", lambda: None),
        ):
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)

        previous_name = source.name
        generated_names: list[str] = []
        for command in ("aqe:trim-left", "aqe:faster", "aqe:trim-right", "aqe:volume-up"):
            previous_name = _click_and_wait_for_new_file(
                editor, note, media_dir, command, previous_name
            )
            generated_names.append(previous_name)
            _wait_for_visualizer_track(
                editor,
                lambda value, expected=previous_name: value["sourceFilename"] == expected,
                timeout=10.0,
            )

        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == generated_names[-2],
            timeout=5.0,
            message="Undo did not restore the previous generated audio reference",
        )
        restored_track = _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_names[-2],
            timeout=10.0,
        )

        assert len(generated_names) == len(set(generated_names))
        assert restored_track["sourceFilename"] == generated_names[-2]
        assert all((media_dir / name).is_file() for name in generated_names)
    finally:
        editor.set_note(None)
        parent.close()


def test_processing_undo_redo_and_new_edit_clears_redo(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_redo_stack_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)

        first_generated = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:trim-left",
            source.name,
        )
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == first_generated,
            timeout=10.0,
        )
        second_generated = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:volume-up",
            first_generated,
        )
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == second_generated,
            timeout=10.0,
        )

        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == first_generated,
            timeout=5.0,
            message="Undo did not restore the previous generated reference",
        )
        click_selector(editor.web, _button_selector("aqe:redo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == second_generated,
            timeout=5.0,
            message="Redo did not restore the undone generated reference",
        )

        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == first_generated,
            timeout=5.0,
            message="Second undo did not restore the previous generated reference",
        )
        third_generated = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:trim-right",
            first_generated,
        )
        assert third_generated not in {first_generated, second_generated}
        wait_for_js_condition(
            editor.web,
            f"""
            (() => {{
              const controls = document.querySelector('.aqe-controls[data-aqe-field-ord="0"]');
              const redo = document.querySelector({_button_selector("aqe:redo")!r});
              return controls?.dataset.aqeSourceFilename === {third_generated!r}
                && redo !== null
                && redo.disabled === false;
            }})()
            """,
            lambda value: value is True,
            timeout=5.0,
        )

        click_selector(editor.web, _button_selector("aqe:redo"), timeout=5.0)
        redo_status = wait_for_js_condition(
            editor.web,
            _processing_status_js(),
            lambda value: value is not None and value["text"] == "Nothing to redo.",
            timeout=5.0,
        )
        assert redo_status["kind"] == "info"
        assert _sound_filename(note.fields[0]) == third_generated
    finally:
        editor.set_note(None)
        parent.close()


def test_fast_clicks_are_ignored_while_processing(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_fast_click_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=3.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        selector = _button_selector("aqe:trim-left")
        wait_for_selector(editor.web, selector, timeout=10.0)
        run_js(
            editor.web,
            f"""
            const button = document.querySelector({json.dumps(selector)});
            for (let i = 0; i < 5; i++) button.click();
            """,
        )
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)

        generated_for_source = list(media_dir.glob("editor_fast_click_source__aqe_*.mp3"))
        assert generated_for_source == [media_dir / generated_name]
        assert (media_dir / generated_name).is_file()
    finally:
        editor.set_note(None)
        parent.close()


def test_three_audio_fields_fast_cross_clicks_lock_globally_and_do_not_corrupt_fields(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    sources = (
        media_dir / "editor_three_fields_one.wav",
        media_dir / "editor_three_fields_two.wav",
        media_dir / "editor_three_fields_three.wav",
    )
    for source in sources:
        generate_tone(ffmpeg_config, source, duration_s=3.0)
    note = _three_audio_field_note(anki_mw, tuple(source.name for source in sources))
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left", 0), timeout=10.0)
        wait_for_selector(editor.web, _button_selector("aqe:faster", 1), timeout=10.0)
        wait_for_selector(editor.web, _button_selector("aqe:trim-right", 2), timeout=10.0)
        locked = wait_for_js_condition(
            editor.web,
            """
            (() => {
              document.querySelector('[data-testid="aqe-button-0-trim-left"]').click();
              const lockedAfterFirst = Array.from(document.querySelectorAll('.aqe-button')).every((button) => button.disabled);
              const firstButton = document.querySelector('[data-testid="aqe-button-0-trim-left"]');
              const controls = document.querySelector('[data-testid="aqe-controls-0"]');
              const buttonStyle = getComputedStyle(firstButton);
              const controlsStyle = getComputedStyle(controls);
              document.querySelector('[data-testid="aqe-button-1-faster"]').click();
              document.querySelector('[data-testid="aqe-button-2-trim-right"]').click();
              return {
                lockedAfterFirst,
                cursor: buttonStyle.cursor,
                opacity: Number(buttonStyle.opacity),
                borderStyle: controlsStyle.borderTopStyle
              };
            })()
            """,
            lambda value: value is not None and value["lockedAfterFirst"] is True,
            timeout=5.0,
        )
        generated_name = _wait_for_generated_mp3(note, media_dir, sources[0].name, field_index=0)
        unlocked = wait_for_js_condition(
            editor.web,
            _graph_state_js(0),
            lambda state: state is not None and state["allButtonsDisabled"] is False,
            timeout=5.0,
        )

        assert locked["lockedAfterFirst"] is True
        assert locked["cursor"] == "not-allowed"
        assert locked["opacity"] < 0.7
        assert locked["borderStyle"] == "dashed"
        assert unlocked["allButtonsDisabled"] is False
        assert _sound_filename(note.fields[0]) == generated_name
        assert _sound_filename(note.fields[1]) == sources[1].name
        assert _sound_filename(note.fields[2]) == sources[2].name
        assert list(media_dir.glob("editor_three_fields_one__aqe_*.mp3")) == [media_dir / generated_name]
    finally:
        editor.set_note(None)
        parent.close()


@pytest.mark.parametrize(
    "command",
    [
        "aqe:trim-left",
        "aqe:faster",
        "aqe:volume-up",
        "aqe:remove-pauses",
        "aqe:rnnoise",
    ],
)
def test_multi_field_processing_undo_redo_survives_graph_default_auto_analysis(
    anki_mw,
    ffmpeg_config,
    tmp_path,
    monkeypatch,
    command: str,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    slug = command.removeprefix("aqe:").replace("-", "_")
    sources = (
        media_dir / f"editor_graph_default_{slug}_one.wav",
        media_dir / f"editor_graph_default_{slug}_two.wav",
        media_dir / f"editor_graph_default_{slug}_three.wav",
    )
    for index, source in enumerate(sources):
        generate_tone(ffmpeg_config, source, duration_s=1.4 + index * 0.1)
    note = _three_audio_field_note(anki_mw, tuple(source.name for source in sources))
    fake_deep_filter, _deep_filter_log = _fake_deep_filter_executable(tmp_path)
    if command == "aqe:rnnoise":
        monkeypatch.setattr(
            "anki_audio_quick_editor.editor_integration.render_rnnoise_audio",
            _fake_special_renderer,
        )
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        deep_filter_path=str(fake_deep_filter),
        deep_filter_post_filter=True,
        show_graph_by_default=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == sources[2].name,
            ord_=2,
            timeout=10.0,
        )
        click_command = command
        if command == "aqe:rnnoise":
            click_selector(editor.web, _split_menu_selector("aqe:denoise-standard"), timeout=5.0)
            click_selector(
                editor.web,
                '[data-testid="aqe-split-0-denoise-standard-preset-rnnoise"]',
                timeout=5.0,
            )
            click_command = "aqe:denoise-standard"
        generated_name = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            click_command,
            sources[0].name,
        )
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == sources[2].name,
            ord_=2,
            timeout=10.0,
        )

        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == sources[0].name,
            timeout=5.0,
            message=f"Undo after {command} failed after graph-default auto-analysis crossed fields",
        )
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == sources[2].name,
            ord_=2,
            timeout=10.0,
        )
        click_selector(editor.web, _button_selector("aqe:redo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == generated_name,
            timeout=5.0,
            message=f"Redo after {command} failed after graph-default auto-analysis crossed fields",
        )

        assert _sound_filename(note.fields[1]) == sources[1].name
        assert _sound_filename(note.fields[2]) == sources[2].name
    finally:
        editor.set_note(None)
        parent.close()


def _fake_special_renderer(source_path: Path, config, output_path: Path, **_kwargs) -> None:
    subprocess.run(
        [
            config.ffmpeg_path,
            "-y",
            "-i",
            str(source_path),
            "-vn",
            "-codec:a",
            "libmp3lame",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


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
            lambda value: value is not None and value["sliderValue"] == "500",
            timeout=5.0,
        )

        run_js(editor.web, "document.body.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }))")
        wait_for_js_condition(
            editor.web,
            "document.querySelector('[data-testid=\"aqe-split-0-trim-left-popover\"]') === null",
            timeout=5.0,
        )

        assert "500 ms" in popover["text"]
        assert popover["top"] >= popover["buttonBottom"]
        assert popover["centerDelta"] < 2
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
