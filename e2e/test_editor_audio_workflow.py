"""E2E tests for the real inline editor audio workflow."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from unittest.mock import patch

from PyQt6.QtWidgets import QWidget

from e2e.helpers import (
    click_selector,
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)

ADDON_NUMERIC_ID = "1000000002"


def _basic_audio_note(anki_mw, audio_filename: str):
    notetype = anki_mw.col.models.by_name("Basic")
    assert notetype is not None
    note = anki_mw.col.new_note(notetype)
    note["Front"] = f"Prompt [sound:{audio_filename}]"
    note["Back"] = "Back"
    deck_id = anki_mw.col.decks.id("Default")
    assert deck_id is not None
    anki_mw.col.add_note(note, deck_id)
    return note


def _sound_filename(field_html: str) -> str:
    match = re.search(r"\[sound:([^\]]+)\]", field_html)
    assert match is not None
    return match.group(1)


def _configure_ffmpeg(anki_mw, ffmpeg_config, **overrides: Any) -> None:
    config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
    config.update({"ffmpeg_path": ffmpeg_config.ffmpeg_path, **overrides})
    anki_mw.addonManager.writeConfig(ADDON_NUMERIC_ID, config)


def _button_selector(command: str) -> str:
    return f'.aqe-controls[data-aqe-field-ord="0"] [data-aqe-command="{command}"]'


def _open_editor(anki_mw, note):
    from aqt.editor import Editor, EditorMode

    parent = QWidget()
    container = QWidget(parent)
    parent.show()
    editor = Editor(anki_mw, container, parent, editor_mode=EditorMode.BROWSER)
    editor.set_note(note, hide=False, focusTo=0)
    return editor, parent


def _wait_for_generated_mp3(note, media_dir: Path, previous_name: str) -> str:
    wait_for_condition(
        lambda: (
            (filename := _sound_filename(note.fields[0])) != previous_name
            and "__aqe_" in filename
            and filename.endswith(".mp3")
            and (media_dir / filename).is_file()
        ),
        timeout=10.0,
        message="Editor did not replace the field with a newly generated MP3",
    )
    return _sound_filename(note.fields[0])


def _click_and_wait_for_new_file(editor, note, media_dir: Path, command: str, previous_name: str) -> str:
    click_selector(editor.web, _button_selector(command), timeout=5.0)
    return _wait_for_generated_mp3(note, media_dir, previous_name)


def _processing_status_js() -> str:
    return """
    (() => {
      const status = document.querySelector('.aqe-controls[data-aqe-field-ord="0"] .aqe-status');
      return status ? { text: status.textContent, title: status.title } : null;
    })()
    """


def _visualizer_js() -> str:
    return """
    (() => {
      const visualizer = document.querySelector('.aqe-visualizer[data-aqe-field-ord="0"]');
      if (!visualizer) return null;
      const labels = Array.from(visualizer.querySelectorAll('.aqe-hz-label')).map((node) => node.textContent);
      return {
        durationMs: Number(visualizer.dataset.durationMs || "0"),
        sourceFilename: visualizer.dataset.sourceFilename || "",
        analyzerName: visualizer.dataset.analyzerName || "",
        cursorMs: Number(visualizer.dataset.cursorMs || "0"),
        intensity: visualizer.querySelector('.aqe-intensity')?.getAttribute('d') || "",
        pitchPaths: visualizer.querySelectorAll('.aqe-pitch-path').length,
        labels,
        cursorX: visualizer.querySelector('.aqe-cursor')?.getAttribute('x1') || "",
        status: visualizer.querySelector('.aqe-visualizer-status')?.textContent || "",
        statusKind: visualizer.querySelector('.aqe-visualizer-status')?.dataset.kind || "",
      };
    })()
    """


def _wait_for_visualizer_track(editor, predicate=lambda track: True, timeout: float = 10.0):
    return wait_for_js_condition(
        editor.web,
        _visualizer_js(),
        lambda track: track is not None and track["durationMs"] > 0 and predicate(track),
        timeout=timeout,
    )


def test_each_processing_button_updates_field_to_new_real_audio(anki_mw, ffmpeg_config) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_each_button_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        assert wait_for_js_condition(
            editor.web,
            "Array.from(document.querySelectorAll('[data-aqe-command]')).map((node) => node.dataset.aqeCommand)",
            lambda commands: "aqe:save" not in commands and "aqe:cancel" not in commands,
            timeout=5.0,
        )

        previous_name = source.name
        generated_names: list[str] = []
        for command in (
            "aqe:trim-left",
            "aqe:untrim-left",
            "aqe:trim-right",
            "aqe:untrim-right",
            "aqe:slower",
            "aqe:faster",
            "aqe:trim-silence",
            "aqe:remove-pauses",
        ):
            wait_for_selector(editor.web, _button_selector(command), timeout=5.0)
            previous_name = _click_and_wait_for_new_file(editor, note, media_dir, command, previous_name)
            generated_names.append(previous_name)
            _wait_for_visualizer_track(
                editor,
                lambda track, expected=previous_name: track["sourceFilename"] == expected,
            )

        assert len(generated_names) == len(set(generated_names))
        assert source.read_bytes() == original_bytes
        assert probe_duration_ms(media_dir / generated_names[0], ffmpeg_config) < probe_duration_ms(
            source, ffmpeg_config
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_visualizer_renders_pitch_intensity_labels_and_cursor(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_visualizer_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, '.aqe-visualizer[data-aqe-field-ord="0"]', timeout=10.0)
        track = _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == source.name and value["pitchPaths"] > 0,
        )

        assert track["intensity"].startswith("M ")
        assert len(track["labels"]) == 2
        assert all(label.endswith(" Hz") for label in track["labels"])
        assert track["cursorX"]
    finally:
        editor.set_note(None)
        parent.close()


def test_cursor_drag_updates_session_and_play_uses_seek(anki_mw, ffmpeg_config) -> None:
    from aqt.sound import av_player

    from anki_audio_quick_editor.editor_integration import _SESSIONS

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_cursor_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    seek_calls: list[float] = []
    try:
        _wait_for_visualizer_track(editor, lambda value: value["sourceFilename"] == source.name)
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

        with (
            patch.object(av_player, "stop_and_clear_queue", lambda: None),
            patch.object(av_player, "play_tags", lambda _tags: None),
            patch.object(av_player, "seek_relative", lambda seconds: seek_calls.append(seconds)),
        ):
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            wait_for_condition(
                lambda: bool(seek_calls),
                timeout=5.0,
                message="Playback did not attempt to seek from the selected cursor",
            )

        assert seek_calls[0] >= track["cursorMs"] / 1000 - 0.05
    finally:
        editor.set_note(None)
        parent.close()


def test_silence_visualizer_renders_pitch_gaps_without_crashing(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_silence_source.wav"
    import subprocess

    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=16000:cl=mono:d=0.7",
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _wait_for_visualizer_track(editor, lambda value: value["sourceFilename"] == source.name)

        assert track["intensity"].startswith("M ")
        assert track["pitchPaths"] == 0
    finally:
        editor.set_note(None)
        parent.close()


def test_visualizer_failure_is_non_mutating_and_edit_buttons_still_work(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_visualizer_failure_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.2)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration.analyze_prosody",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("visualizer exploded")),
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_js_condition(
            editor.web,
            _visualizer_js(),
            lambda value: value is not None
            and value["statusKind"] == "error"
            and "visualizer exploded" in value["status"],
            timeout=10.0,
        )
        generated_name = _click_and_wait_for_new_file(
            editor, note, media_dir, "aqe:trim-left", source.name
        )

        assert generated_name != source.name
        assert (media_dir / generated_name).is_file()
    finally:
        editor.set_note(None)
        parent.close()


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
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_undo_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:trim-left"), timeout=10.0)
        first_name = _click_and_wait_for_new_file(editor, note, media_dir, "aqe:trim-left", source.name)
        second_name = _click_and_wait_for_new_file(editor, note, media_dir, "aqe:faster", first_name)

        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == first_name,
            timeout=5.0,
            message="Undo did not restore the previous generated audio reference",
        )

        assert second_name != first_name
        assert (media_dir / second_name).is_file()
        assert (media_dir / first_name).is_file()
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
