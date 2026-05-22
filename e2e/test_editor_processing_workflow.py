"""E2E tests for editor audio edit controls and processing state."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from e2e.editor_audio_generation_helpers import _fake_deep_filter_executable
from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_state_js,
    _wait_for_visualizer_track,
)
from e2e.editor_note_helpers import (
    _artifact_root,
    _basic_audio_note,
    _button_selector,
    _cleanup_artifact_dirs,
    _click_and_wait_for_new_file,
    _configure_ffmpeg,
    _open_editor,
    _processing_status_js,
    _sound_filename,
    _wait_for_generated_mp3,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
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


def test_each_processing_button_updates_field_to_new_real_audio(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
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
        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        assert wait_for_js_condition(
            editor.web,
            "Array.from(document.querySelectorAll('[data-aqe-command]')).map((node) => node.dataset.aqeCommand)",
            lambda commands: all(
                hidden_command not in commands
                for hidden_command in (
                    "aqe:save",
                    "aqe:cancel",
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
            lambda state: (
                state["labels"]
                == [
                    "Play",
                    "Options",
                    "Graph",
                    "Options",
                    "Folder",
                    "Share",
                    "Options",
                    "Convert",
                    "Options",
                    "Shorten Pauses",
                    "Options",
                    "Denoise",
                    "Options",
                    "Pitch Hum",
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
                and all(stroke == "currentColor" for stroke in state["iconStrokeValues"])
            ),
            timeout=5.0,
        )

        previous_name = source.name
        generated_names: list[str] = []
        for command in (
            "aqe:slower",
            "aqe:faster",
            "aqe:volume-down",
            "aqe:volume-up",
            "aqe:remove-pauses",
            "aqe:pitch-hum",
        ):
            wait_for_selector(editor.web, _button_selector(command), timeout=5.0)
            previous_name = _click_and_wait_for_new_file(editor, note, media_dir, command, previous_name)
            generated_names.append(previous_name)

        assert len(generated_names) == len(set(generated_names))
        assert source.read_bytes() == original_bytes
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
        wait_for_selector(hidden_editor.web, _button_selector("aqe:faster"), timeout=10.0)
        click_selector(hidden_editor.web, _button_selector("aqe:faster"), timeout=5.0)
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
        wait_for_selector(shown_editor.web, _button_selector("aqe:faster"), timeout=10.0)
        click_selector(shown_editor.web, _button_selector("aqe:faster"), timeout=5.0)
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
        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
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
        for command in ("aqe:faster", "aqe:volume-up", "aqe:slower", "aqe:volume-down"):
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
        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)

        first_generated = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:faster",
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
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == first_generated,
            timeout=10.0,
        )
        third_generated = _click_and_wait_for_new_file(
            editor,
            note,
            media_dir,
            "aqe:volume-up",
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
