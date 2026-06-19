"""E2E tests for Browser audio export workflows."""

import zipfile
from pathlib import Path

from e2e.browser_workflow_helpers import (
    add_basic_audio_note,
    click_batch_start,
    front_field,
    open_audio_export_dialog,
    trigger_cards_menu_action,
    wait_for_dialog_finished,
)
from e2e.conftest import import_runtime_addon_module
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js_condition,
)


def test_browser_audio_export_zip_leaves_note_fields_unchanged(
    anki_mw,
    ffmpeg_config,
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    sources = (
        media_dir / "browser_export_zip_source_1.mp3",
        media_dir / "browser_export_zip_source_2.mp3",
    )
    for source in sources:
        generate_tone(ffmpeg_config, source, duration_s=0.4)
    note = add_basic_audio_note(anki_mw, tuple(source.name for source in sources))
    original_html = note["Front"]
    output = tmp_path / "cards.zip"

    dialog = _run_export_dialog_from_browser(
        anki_mw,
        note,
        output,
        monkeypatch=monkeypatch,
        mode="zip",
    )

    wait_for_condition(
        lambda: output.is_file(),
        timeout=10.0,
        message=f"zip export was not written; log={dialog._log_lines!r}",
    )
    assert front_field(anki_mw, int(note.id)) == original_html
    with zipfile.ZipFile(output) as archive:
        assert archive.namelist() == [
            f"0001__note-{int(note.id)}__Front__001__{sources[0].name}",
            f"0002__note-{int(note.id)}__Front__002__{sources[1].name}",
        ]


def test_browser_audio_export_combined_mp3_leaves_note_fields_unchanged(
    anki_mw,
    ffmpeg_config,
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    sources = (
        media_dir / "browser_export_mp3_source_1.mp3",
        media_dir / "browser_export_mp3_source_2.mp3",
    )
    for source in sources:
        generate_tone(ffmpeg_config, source, duration_s=0.4)
    note = add_basic_audio_note(anki_mw, tuple(source.name for source in sources))
    original_html = note["Front"]
    output = tmp_path / "cards.mp3"

    dialog = _run_export_dialog_from_browser(
        anki_mw,
        note,
        output,
        monkeypatch=monkeypatch,
        mode="combined_mp3",
        silence_seconds=0.2,
    )

    wait_for_condition(
        lambda: output.is_file() and output.stat().st_size > 0,
        timeout=15.0,
        message=f"mp3 export was not written; log={dialog._log_lines!r}",
    )
    assert front_field(anki_mw, int(note.id)) == original_html


def _run_export_dialog_from_browser(
    anki_mw,
    note,
    output: Path,
    *,
    monkeypatch,
    mode: str,
    silence_seconds: float = 1.0,
):
    export_dialog_module = import_runtime_addon_module(".browser_audio_export_dialog")
    from aqt.qt import QFileDialog

    browser, opened_context, action_label = open_audio_export_dialog(
        anki_mw,
        note,
        export_dialog_module.AudioExportDialog,
    )
    original_get_save_file_name = QFileDialog.getSaveFileName
    QFileDialog.getSaveFileName = lambda *_args, **_kwargs: (str(output), "")
    try:
        with opened_context as opened:
            trigger_cards_menu_action(browser, action_label)
            wait_for_condition(
                lambda: len(opened) == 1,
                timeout=10.0,
                message="Browser audio export dialog did not open after saving the editor",
            )
            dialog = opened[0]
            wait_for_js_condition(
                dialog._webview,
                "Boolean(document.querySelector('[data-testid=\"audio-export-controls\"]'))",
                lambda value: value is True,
                timeout=10.0,
            )
            if mode == "combined_mp3":
                wait_for_js_condition(
                    dialog._webview,
                    """
                    (() => {
                      const radios = Array.from(document.querySelectorAll('input[type="radio"]'));
                      const radio = radios.find((node) => node.value === 'combined_mp3');
                      if (!radio) return false;
                      radio.click();
                      return radio.checked;
                    })()
                    """,
                    lambda value: value is True,
                    timeout=5.0,
                )
                wait_for_js_condition(
                    dialog._webview,
                    f"""
                    (() => {{
                      const input = document.querySelector('[data-testid="audio-export-silence"]');
                      if (!input) return false;
                      input.value = {str(silence_seconds)!r};
                      input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                      input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                      return Number(input.value);
                    }})()
                    """,
                    lambda value: value == silence_seconds,
                    timeout=5.0,
                )
            click_selector(dialog._webview, "button", timeout=5.0)
            wait_for_js_condition(
                dialog._webview,
                "document.querySelector('[data-testid=\"audio-export-destination\"]')?.value",
                lambda value: value == str(output),
                timeout=5.0,
            )
            click_batch_start(dialog)
            wait_for_dialog_finished(dialog, timeout=30.0)
            return dialog
    finally:
        QFileDialog.getSaveFileName = original_get_save_file_name
