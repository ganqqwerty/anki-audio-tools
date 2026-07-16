"""E2E tests for Browser batch operations through the real Browser UI."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest
from tests.media_oracles import db_ratio, decode_mono_f32, probe_audio, rms

from e2e.browser_workflow_helpers import (
    click_batch_start,
    close_browser,
    open_batch_dialog,
    open_batch_dialog_for_notes,
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
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js_condition,
)


@pytest.mark.parametrize("operation", ["faster", "slower", "volume_up", "volume_down"])
def test_browser_batch_simple_transforms_change_decoded_audio_semantics(
    anki_mw,
    ffmpeg_config,
    operation: str,
) -> None:
    browser_dialog = import_runtime_addon_module(".browser_dialog")
    processor = import_runtime_addon_module(".audio_processor")
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / f"browser_batch_{operation}_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.2)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    ffmpeg = processor.find_ffmpeg(ffmpeg_config.ffmpeg_path)
    ffprobe = processor.find_ffprobe(ffmpeg)
    source_probe = probe_audio(ffprobe, source)
    source_rms = rms(decode_mono_f32(ffmpeg, source))

    browser, opened_context, action_label = open_batch_dialog(
        anki_mw,
        note,
        browser_dialog.BatchOperationsDialog,
    )
    try:
        with opened_context as opened:
            trigger_cards_menu_action(browser, action_label)
            wait_for_opened_dialog(opened)
            dialog = opened[0]
            wait_for_batch_dialog_ready(dialog)
            select_batch_operation(dialog, operation)
            click_batch_start(dialog)
            wait_for_dialog_finished(dialog, timeout=30.0)

        generated_name = _wait_for_front_audio_replacement(
            anki_mw,
            note_id=int(note.id),
            previous_name=source.name,
        )
        generated_path = media_dir / generated_name
        generated_probe = probe_audio(ffprobe, generated_path)
        generated_rms = rms(decode_mono_f32(ffmpeg, generated_path))

        if operation == "faster":
            assert generated_probe.duration_s < source_probe.duration_s * 0.9
        elif operation == "slower":
            assert generated_probe.duration_s > source_probe.duration_s * 1.1
        elif operation == "volume_up":
            assert db_ratio(source_rms, generated_rms) >= 2.5
        else:
            assert db_ratio(source_rms, generated_rms) <= -2.5
        assert source.read_bytes() == original_bytes
    finally:
        close_browser(browser)


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
    dialog._dialog.hide()
    dialog._dialog.close()
    close_browser(browser)


def test_browser_batch_multi_note_partial_failure_keeps_missing_media_unchanged(
    anki_mw,
    ffmpeg_config,
) -> None:
    browser_dialog = import_runtime_addon_module(".browser_dialog")
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "browser_batch_partial_valid.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.8)
    valid_note = _basic_audio_note(anki_mw, source.name)
    missing_name = "browser_batch_intentionally_missing.wav"
    missing_note = _basic_audio_note(anki_mw, missing_name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    browser, opened_context, action_label = open_batch_dialog_for_notes(
        anki_mw,
        (valid_note, missing_note),
        browser_dialog.BatchOperationsDialog,
    )
    try:
        with opened_context as opened:
            trigger_cards_menu_action(browser, action_label)
            wait_for_opened_dialog(opened)
            dialog = opened[0]
            wait_for_batch_dialog_ready(dialog)
            select_batch_operation(dialog, "faster")
            click_batch_start(dialog)
            wait_for_dialog_finished(dialog, timeout=30.0)

        generated_name = _wait_for_front_audio_replacement(
            anki_mw,
            note_id=int(valid_note.id),
            previous_name=source.name,
        )
        assert (media_dir / generated_name).is_file()
        assert _sound_filename(anki_mw.col.get_note(missing_note.id)["Front"]) == missing_name
        wait_for_js_condition(
            dialog._webview,
            "document.querySelector('[data-testid=\"batch-progress-status\"]')?.dataset.failures",
            lambda failures: failures == "1",
            timeout=5.0,
        )
    finally:
        close_browser(browser)


def test_browser_batch_multi_field_note_changes_only_selected_source_field(
    anki_mw,
    ffmpeg_config,
) -> None:
    browser_dialog = import_runtime_addon_module(".browser_dialog")
    media_dir = Path(anki_mw.col.media.dir())
    front_source = media_dir / "browser_batch_multifield_front.wav"
    back_source = media_dir / "browser_batch_multifield_back.wav"
    generate_tone(ffmpeg_config, front_source, duration_s=0.8)
    generate_tone(ffmpeg_config, back_source, duration_s=0.8)
    note = _basic_audio_note(anki_mw, front_source.name)
    note["Back"] = f"[sound:{back_source.name}]"
    anki_mw.col.update_note(note)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    browser, opened_context, action_label = open_batch_dialog(
        anki_mw,
        note,
        browser_dialog.BatchOperationsDialog,
    )
    try:
        with opened_context as opened:
            trigger_cards_menu_action(browser, action_label)
            wait_for_opened_dialog(opened)
            dialog = opened[0]
            wait_for_batch_dialog_ready(dialog)
            select_batch_operation(dialog, "faster")
            click_batch_start(dialog)
            wait_for_dialog_finished(dialog, timeout=30.0)

        persisted = anki_mw.col.get_note(note.id)
        assert _sound_filename(persisted["Front"]) != front_source.name
        assert _sound_filename(persisted["Back"]) == back_source.name
        assert back_source.is_file()
    finally:
        close_browser(browser)


def test_browser_batch_cancel_stops_before_the_next_selected_note(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    browser_dialog = import_runtime_addon_module(".browser_dialog")
    batch_runner = import_runtime_addon_module(".browser_batch_runner")
    media_dir = Path(anki_mw.col.media.dir())
    notes = []
    originals: dict[int, str] = {}
    for index in range(2):
        source = media_dir / f"browser_batch_cancel_{index}.wav"
        generate_tone(ffmpeg_config, source, duration_s=0.8)
        note = _basic_audio_note(anki_mw, source.name)
        notes.append(note)
        originals[int(note.id)] = source.name
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    started = threading.Event()
    release = threading.Event()
    processed_ids: list[int] = []
    original_process_note = batch_runner.process_note

    def delayed_first_note(col, note_id, *args, **kwargs):
        processed_ids.append(int(note_id))
        if len(processed_ids) == 1:
            started.set()
            assert release.wait(10.0), "batch cancellation sentinel was not released"
        return original_process_note(col, note_id, *args, **kwargs)

    monkeypatch.setattr(batch_runner, "process_note", delayed_first_note)
    browser, opened_context, action_label = open_batch_dialog_for_notes(
        anki_mw,
        tuple(notes),
        browser_dialog.BatchOperationsDialog,
    )
    try:
        with opened_context as opened:
            trigger_cards_menu_action(browser, action_label)
            wait_for_opened_dialog(opened)
            dialog = opened[0]
            wait_for_batch_dialog_ready(dialog)
            select_batch_operation(dialog, "faster")
            click_batch_start(dialog)
            wait_for_condition(
                started.is_set,
                timeout=10.0,
                message="batch worker did not reach the deterministic barrier",
            )
            click_selector(dialog._webview, '[data-testid="batch-cancel"]', timeout=5.0)
            assert dialog.cancel_event.is_set()
            release.set()
            wait_for_dialog_finished(dialog, timeout=30.0)

        assert len(processed_ids) == 1
        changed = [
            note_id
            for note_id, original in originals.items()
            if _sound_filename(anki_mw.col.get_note(note_id)["Front"]) != original
        ]
        assert changed == processed_ids
        assert any("cancel" in line.lower() for line in dialog._log_lines)
    finally:
        release.set()
        close_browser(browser)


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
