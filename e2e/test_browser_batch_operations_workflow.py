"""Decoded-media E2E coverage for the remaining Browser batch operations."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from tests.media_oracles import (
    db_ratio,
    decode_mono_f32,
    difference_rms,
    probe_audio,
    window_rms,
)

from e2e.browser_workflow_helpers import (
    click_batch_start,
    close_browser,
    open_batch_dialog,
    select_batch_operation,
    select_batch_value,
    trigger_cards_menu_action,
    wait_for_batch_dialog_ready,
    wait_for_dialog_finished,
    wait_for_opened_dialog,
)
from e2e.conftest import import_runtime_addon_module
from e2e.editor_audio_generation_helpers import _generate_tone_silence_tone
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _configure_ffmpeg,
    _sound_filename,
)
from e2e.helpers import click_selector, generate_tone, trusted_pointer_to_selector


@contextmanager
def _completed_batch(
    anki_mw,
    note,
    operation: str,
    configure: Callable[[object], None] | None = None,
    *,
    trusted_start: bool = False,
) -> Iterator[object]:
    browser_dialog = import_runtime_addon_module(".browser_dialog")
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
            if configure is not None:
                configure(dialog)
            if trusted_start:
                trusted_pointer_to_selector(
                    dialog._webview,
                    '[data-testid="batch-start"]',
                    click=True,
                )
            else:
                click_batch_start(dialog)
            wait_for_dialog_finished(dialog, timeout=45.0)
            yield dialog
    finally:
        close_browser(browser)


def _runtime_tools(ffmpeg_config) -> tuple[Path, Path]:
    processor = import_runtime_addon_module(".audio_processor")
    ffmpeg = processor.find_ffmpeg(ffmpeg_config.ffmpeg_path)
    return ffmpeg, processor.find_ffprobe(ffmpeg)


def _generated_front_path(anki_mw, note, source_name: str) -> Path:
    generated = _sound_filename(anki_mw.col.get_note(note.id)["Front"])
    assert generated != source_name
    path = Path(anki_mw.col.media.dir()) / generated
    assert path.is_file()
    return path


@pytest.mark.trusted_input
def test_browser_batch_convert_writes_decodable_requested_codec(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "browser_batch_convert_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.8)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    _ffmpeg, ffprobe = _runtime_tools(ffmpeg_config)

    with _completed_batch(
        anki_mw,
        note,
        "convert",
        lambda dialog: select_batch_value(dialog, "batch-output-format", "mp3"),
        trusted_start=True,
    ):
        generated = _generated_front_path(anki_mw, note, source.name)

    assert generated.suffix == ".mp3"
    assert probe_audio(ffprobe, generated).codec == "mp3"


def test_browser_batch_remove_pauses_shortens_decoded_tone_silence_tone(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "browser_batch_remove_pauses_source.wav"
    _generate_tone_silence_tone(ffmpeg_config, source)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        pause_silencedetect_preprocess_denoise=False,
    )
    _ffmpeg, ffprobe = _runtime_tools(ffmpeg_config)
    source_duration = probe_audio(ffprobe, source).duration_s

    with _completed_batch(anki_mw, note, "remove_pauses"):
        generated = _generated_front_path(anki_mw, note, source.name)

    generated_duration = probe_audio(ffprobe, generated).duration_s
    assert 0.7 < generated_duration < source_duration - 0.2


def test_browser_batch_standard_denoise_changes_decoded_noisy_pcm(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "browser_batch_denoise_source.wav"
    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1",
            "-f",
            "lavfi",
            "-i",
            "anoisesrc=color=white:amplitude=0.08:duration=1",
            "-filter_complex",
            "[0:a][1:a]amix=inputs=2:weights='1 0.35'[out]",
            "-map",
            "[out]",
            str(source),
        ],
        check=True,
        capture_output=True,
    )
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    ffmpeg, _ffprobe = _runtime_tools(ffmpeg_config)

    with _completed_batch(
        anki_mw,
        note,
        "denoise",
        lambda dialog: click_selector(
            dialog._webview,
            '[data-testid="batch-denoise-algorithm-standard"]',
            timeout=5.0,
        ),
    ):
        generated = _generated_front_path(anki_mw, note, source.name)

    assert difference_rms(
        decode_mono_f32(ffmpeg, source),
        decode_mono_f32(ffmpeg, generated),
        start_s=0.1,
        end_s=0.9,
    ) > 0.001


def test_browser_batch_graph_appends_real_svg_to_selected_target_field(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "browser_batch_graph_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.8)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    with _completed_batch(
        anki_mw,
        note,
        "graph",
        lambda dialog: select_batch_value(dialog, "batch-target-field", "Back"),
    ):
        persisted = anki_mw.col.get_note(note.id)

    assert _sound_filename(persisted["Front"]) == source.name
    assert ".svg" in persisted["Back"]
    svg_name = persisted["Back"].split('src="', 1)[1].split('"', 1)[0]
    assert (media_dir / svg_name).read_text(encoding="utf-8").lstrip().startswith("<svg")


def test_browser_batch_default_preset_changes_decoded_audio_semantics(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "browser_batch_preset_source.wav"
    speech = Path(__file__).resolve().parent / "fixtures" / "audio" / "forvo_Vertrag.ogg"
    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-i",
            str(speech),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=48000:cl=mono:d=0.45",
            "-i",
            str(speech),
            "-filter_complex",
            "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
            "-map",
            "[out]",
            str(source),
        ],
        check=True,
        capture_output=True,
    )
    note = _basic_audio_note(anki_mw, source.name)
    config_defaults = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "addon"
            / "anki_audio_quick_editor"
            / "config.json"
        ).read_text(encoding="utf-8")
    )
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        audio_processing_presets=config_defaults["audio_processing_presets"],
    )
    ffmpeg, ffprobe = _runtime_tools(ffmpeg_config)
    source_duration = probe_audio(ffprobe, source).duration_s

    with _completed_batch(anki_mw, note, "preset"):
        generated = _generated_front_path(anki_mw, note, source.name)

    generated_duration = probe_audio(ffprobe, generated).duration_s
    assert 0.4 < generated_duration < source_duration - 0.2
    source_rms = window_rms(decode_mono_f32(ffmpeg, source), start_s=0.05, end_s=0.15)
    generated_rms = window_rms(decode_mono_f32(ffmpeg, generated), start_s=0.05, end_s=0.15)
    assert db_ratio(source_rms, generated_rms) >= 10.0
