"""Shared Anki editor setup helpers for editor E2E tests."""

from __future__ import annotations

import re
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import QWidget

from e2e.helpers import click_selector, wait_for_condition

ADDON_NUMERIC_ID = "1000000002"

DEFAULT_VISIBLE_EDITOR_BUTTONS = (
    "aqe:play",
    "aqe:analyze",
    "aqe:show-file",
    "aqe:convert",
    "aqe:trim-left",
    "aqe:trim-right",
    "aqe:remove-pauses",
    "aqe:denoise-standard",
    "aqe:pitch-hum",
    "aqe:slower",
    "aqe:faster",
    "aqe:volume-down",
    "aqe:volume-up",
    "aqe:undo",
    "aqe:redo",
    "aqe:settings",
)


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


def _three_audio_field_note(anki_mw, audio_filenames: tuple[str, str, str]):
    models = anki_mw.col.models
    notetype = models.new("AQE E2E Three Audio Fields")
    for name in ("One", "Two", "Three"):
        models.add_field(notetype, models.new_field(name))
    template = models.new_template("Card 1")
    template["qfmt"] = "{{One}}"
    template["afmt"] = "{{FrontSide}}<hr>{{Two}} {{Three}}"
    models.add_template(notetype, template)
    models.add(notetype)
    note = anki_mw.col.new_note(notetype)
    for index, filename in enumerate(audio_filenames):
        note.fields[index] = f"Field {index + 1} [sound:{filename}]"
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
    config.update(asdict(ffmpeg_config))
    config.update(
        {
            "ffmpeg_path": ffmpeg_config.ffmpeg_path,
            "repeat_playback_by_default": False,
            "repeat_pause_seconds": 0.0,
            "show_graph_by_default": False,
            "visible_editor_buttons": list(DEFAULT_VISIBLE_EDITOR_BUTTONS),
            **overrides,
        }
    )
    anki_mw.addonManager.writeConfig(ADDON_NUMERIC_ID, config)


def _artifact_root(anki_mw) -> Path:
    return Path(anki_mw.addonManager.addonsFolder(ADDON_NUMERIC_ID)) / "aqe_artifacts"


def _artifact_dirs_for_source(artifact_root: Path, source: Path) -> set[Path]:
    if not artifact_root.exists():
        return set()
    return set(artifact_root.glob(f"{source.stem}__*"))


def _cleanup_artifact_dirs(artifact_root: Path, source: Path) -> None:
    for run_dir in _artifact_dirs_for_source(artifact_root, source):
        shutil.rmtree(run_dir, ignore_errors=True)


def _button_selector(command: str, ord_: int = 0) -> str:
    return f'.aqe-controls[data-aqe-field-ord="{ord_}"] [data-aqe-command="{command}"]'


def _open_editor(anki_mw, note):
    from aqt.editor import Editor, EditorMode

    parent = QWidget()
    container = QWidget(parent)
    parent.resize(1400, 900)
    parent.show()
    editor = Editor(anki_mw, container, parent, editor_mode=EditorMode.BROWSER)
    editor.set_note(note, hide=False, focusTo=0)
    return editor, parent


def _wait_for_generated_mp3(note, media_dir: Path, previous_name: str, field_index: int = 0) -> str:
    wait_for_condition(
        lambda: (
            (filename := _sound_filename(note.fields[field_index])) != previous_name
            and "__aqe_" in filename
            and filename.endswith(".mp3")
            and (media_dir / filename).is_file()
        ),
        timeout=10.0,
        message="Editor did not replace the field with a newly generated MP3",
    )
    return _sound_filename(note.fields[field_index])


def _click_and_wait_for_new_file(
    editor,
    note,
    media_dir: Path,
    command: str,
    previous_name: str,
    field_index: int = 0,
) -> str:
    click_selector(editor.web, _button_selector(command, field_index), timeout=5.0)
    return _wait_for_generated_mp3(note, media_dir, previous_name, field_index)


def _processing_status_js() -> str:
    return """
    (() => {
      const status = document.querySelector('.aqe-controls[data-aqe-field-ord="0"] .aqe-status');
      return status ? { text: status.textContent, title: status.title, kind: status.dataset.kind || "" } : null;
    })()
    """
