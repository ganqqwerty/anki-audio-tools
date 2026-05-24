"""E2E tests for processing while graph-default analysis is active."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from e2e.conftest import runtime_addon_import_path
from e2e.editor_audio_generation_helpers import _fake_deep_filter_executable
from e2e.editor_graph_helpers import (
    _wait_for_visualizer_track,
)
from e2e.editor_note_helpers import (
    _button_selector,
    _click_and_wait_for_new_file,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
    _three_audio_field_note,
    _wait_for_status_flow,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js_condition,
)


def _split_slug(command: str) -> str:
    if command in {"aqe:volume-up", "aqe:volume-down"}:
        return "volume"
    if command in {"aqe:faster", "aqe:slower"}:
        return "speed"
    return command.removeprefix("aqe:")


def _split_menu_selector(command: str, ord_: int = 0) -> str:
    slug = _split_slug(command)
    return f'[data-testid="aqe-split-{ord_}-{slug}-menu"]'


def _split_popover_state_js(command: str, ord_: int = 0) -> str:
    slug = _split_slug(command)
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


def _click_latest_enabled_button_js(command: str, ord_: int = 0) -> str:
    selector = _button_selector(command, ord_)
    return f"""
    (() => {{
      const nodes = Array.from(document.querySelectorAll({selector!r}));
      const node = nodes.reverse().find((candidate) => (
        candidate instanceof HTMLButtonElement &&
        candidate.disabled !== true &&
        candidate.getAttribute("aria-disabled") !== "true"
      ));
      if (!node) return false;
      node.click();
      return true;
    }})()
    """


def _expected_processing_status(command: str) -> str:
    return {
        "aqe:faster": "Increased speed to x1.05.",
        "aqe:volume-up": "Increased volume by 3 dB.",
        "aqe:remove-pauses": "Shortened pauses with Normal level.",
        "aqe:rnnoise": "Cleaned audio with RNNoise.",
    }[command]

@pytest.mark.parametrize(
    "command",
    [
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
            runtime_addon_import_path(".editor_dependencies", "render_rnnoise_audio"),
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
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == _expected_processing_status(command),
            timeout=10.0,
        )
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == sources[2].name,
            ord_=2,
            timeout=10.0,
        )

        wait_for_js_condition(
            editor.web,
            _click_latest_enabled_button_js("aqe:undo"),
            lambda value: value is True,
            timeout=5.0,
        )
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == sources[0].name,
            timeout=5.0,
            message=f"Undo after {command} failed after graph-default auto-analysis crossed fields",
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Undid: Original audio.",
            timeout=10.0,
        )
        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == sources[2].name,
            ord_=2,
            timeout=10.0,
        )
        wait_for_js_condition(
            editor.web,
            _click_latest_enabled_button_js("aqe:redo"),
            lambda value: value is True,
            timeout=5.0,
        )
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == generated_name,
            timeout=5.0,
            message=f"Redo after {command} failed after graph-default auto-analysis crossed fields",
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == f"Redid: {_expected_processing_status(command)}",
            timeout=10.0,
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
