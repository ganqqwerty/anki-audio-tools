"""E2E tests for Browser audio export workflows."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from e2e.conftest import import_runtime_addon_module
from e2e.helpers import generate_tone, run_js, wait_for_condition, wait_for_js_condition


def test_browser_audio_export_zip_leaves_note_fields_unchanged(
    anki_mw,
    ffmpeg_config,
    tmp_path: Path,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "browser_export_zip_source.mp3"
    generate_tone(ffmpeg_config, source, duration_s=0.4)
    note = _add_audio_note(anki_mw, source.name)
    original_html = note["Front"]
    output = tmp_path / "cards.zip"

    dialog = _run_export_dialog(anki_mw, int(note.id), output, mode="zip")

    wait_for_condition(
        lambda: output.is_file(),
        timeout=10.0,
        message=f"zip export was not written; log={dialog._log_lines!r}",
    )
    assert _front_field(anki_mw, int(note.id)) == original_html
    with zipfile.ZipFile(output) as archive:
        assert archive.namelist() == [
            f"0001__note-{int(note.id)}__Front__001__{source.name}"
        ]


def test_browser_audio_export_combined_mp3_leaves_note_fields_unchanged(
    anki_mw,
    ffmpeg_config,
    tmp_path: Path,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "browser_export_mp3_source.mp3"
    generate_tone(ffmpeg_config, source, duration_s=0.4)
    note = _add_audio_note(anki_mw, source.name)
    original_html = note["Front"]
    output = tmp_path / "cards.mp3"

    dialog = _run_export_dialog(
        anki_mw,
        int(note.id),
        output,
        mode="combined_mp3",
        silence_seconds=0.2,
    )

    wait_for_condition(
        lambda: output.is_file() and output.stat().st_size > 0,
        timeout=15.0,
        message=f"mp3 export was not written; log={dialog._log_lines!r}",
    )
    assert _front_field(anki_mw, int(note.id)) == original_html


def _add_audio_note(anki_mw, filename: str):
    notetype = anki_mw.col.models.by_name("Basic")
    assert notetype is not None
    note = anki_mw.col.new_note(notetype)
    note["Front"] = f"[sound:{filename}]"
    note["Back"] = "Back"
    deck_id = anki_mw.col.decks.id("Default")
    assert deck_id is not None
    anki_mw.col.add_note(note, deck_id)
    return note


def _front_field(anki_mw, note_id: int) -> str:
    return anki_mw.col.get_note(note_id)["Front"]


def _run_export_dialog(
    anki_mw,
    note_id: int,
    output: Path,
    *,
    mode: str,
    silence_seconds: float = 1.0,
):
    batch_operations = import_runtime_addon_module(".batch_operations")
    export_dialog_module = import_runtime_addon_module(".browser_audio_export_dialog")
    note = anki_mw.col.get_note(note_id)
    field_group = batch_operations.FieldGroup("Basic", ("Front", "Back"))
    snapshot = batch_operations.BatchNoteSnapshot(
        note_id,
        "Basic",
        {"Front": note["Front"], "Back": note["Back"]},
    )
    dialog = export_dialog_module.AudioExportDialog(
        anki_mw,
        [note_id],
        (field_group,),
        (snapshot,),
    )
    dialog._dialog.show()
    try:
        wait_for_js_condition(
            dialog._webview,
            "Boolean(document.querySelector('[data-testid=\"audio-export-controls\"]'))",
            lambda value: value is True,
            timeout=10.0,
        )
        request = {
            "mode": mode,
            "destination_path": str(output),
            "field_selections": [{"notetype_name": "Basic", "fields": ["Front"]}],
            "silence_between_clips_seconds": silence_seconds,
        }
        command = "bridge:" + json.dumps(
            {"command": "audio-export.start", "payload": request}
        )
        run_js(dialog._webview, f"pycmd({command!r});")
        wait_for_condition(
            lambda: dialog._finished is True,
            timeout=20.0,
            message=f"audio export dialog did not finish; log={dialog._log_lines!r}",
        )
        return dialog
    finally:
        if dialog._running:
            dialog.cancel_event.set()
        dialog._dialog.close()
