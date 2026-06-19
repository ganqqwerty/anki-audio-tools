"""E2E tests for Browser batch operations through the real Browser UI."""

from __future__ import annotations

from pathlib import Path

from e2e.browser_workflow_helpers import (
    click_batch_start,
    open_batch_dialog,
    select_batch_operation,
    trigger_cards_menu_action,
    wait_for_batch_dialog_ready,
    wait_for_dialog_finished,
    wait_for_opened_dialog,
)
from e2e.conftest import import_runtime_addon_module
from e2e.editor_audio_generation_helpers import _generate_high_bitrate_mp3
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _configure_ffmpeg,
    _sound_filename,
)
from e2e.helpers import click_selector, wait_for_condition, wait_for_js_condition


def test_browser_batch_reduce_size_renders_smaller_mp3_from_selected_row(
    anki_mw,
    ffmpeg_config,
) -> None:
    browser_dialog = import_runtime_addon_module(".browser_dialog")
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "browser_batch_size_reduce_source.mp3"
    _generate_high_bitrate_mp3(ffmpeg_config, source)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, size_reduction_mode="normal")

    browser, opened_context, action_label = open_batch_dialog(
        anki_mw,
        note,
        browser_dialog.BatchOperationsDialog,
    )

    with opened_context as opened:
        trigger_cards_menu_action(browser, action_label)
        wait_for_opened_dialog(opened)
        dialog = opened[0]
        wait_for_batch_dialog_ready(dialog)
        select_batch_operation(dialog, "reduce_size")
        click_selector(
            dialog._webview,
            '[data-testid="batch-size-reduction-mode-aggressive"]',
            timeout=5.0,
        )
        wait_for_js_condition(
            dialog._webview,
            "document.querySelector('[data-testid=\"batch-size-reduction-mode-aggressive\"]')?.getAttribute('aria-checked')",
            lambda value: value == "true",
            timeout=5.0,
        )
        click_batch_start(dialog)
        wait_for_dialog_finished(dialog, timeout=30.0)

    generated_name = _wait_for_front_audio_replacement(
        anki_mw,
        note_id=int(note.id),
        previous_name=source.name,
    )
    generated_path = media_dir / generated_name

    assert generated_name != source.name
    assert generated_name.endswith(".mp3")
    assert generated_path.is_file()
    assert generated_path.stat().st_size < len(original_bytes)
    assert source.read_bytes() == original_bytes


def _wait_for_front_audio_replacement(
    anki_mw,
    *,
    note_id: int,
    previous_name: str,
) -> str:
    last_front = ""

    def has_replacement() -> bool:
        nonlocal last_front
        last_front = anki_mw.col.get_note(note_id)["Front"]
        return _sound_filename(last_front) != previous_name

    try:
        wait_for_condition(
            has_replacement,
            timeout=30.0,
            message="Browser batch workflow did not persist the generated audio reference",
        )
    except TimeoutError as exc:
        raise TimeoutError(
            "Browser batch workflow did not persist the generated audio reference; "
            f"last persisted Front field was {last_front!r}"
        ) from exc

    return _sound_filename(last_front)
