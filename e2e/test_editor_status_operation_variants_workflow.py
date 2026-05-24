"""E2E status coverage for editor operations with explicit variants."""

from __future__ import annotations

from pathlib import Path

from e2e.conftest import import_runtime_addon_module, runtime_addon_import_path
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
    _wait_for_generated_mp3,
    _wait_for_status_flow,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_selector,
)


def _wait_for_generated_file(
    note,
    media_dir: Path,
    previous_name: str,
    suffix: str,
    field_index: int = 0,
) -> str:
    wait_for_condition(
        lambda: (
            (filename := _sound_filename(note.fields[field_index])) != previous_name
            and "__aqe_" in filename
            and filename.endswith(suffix)
            and (media_dir / filename).is_file()
        ),
        timeout=10.0,
        message=f"Editor did not replace the field with a newly generated {suffix} file",
    )
    return _sound_filename(note.fields[field_index])


def test_convert_status_reports_selected_output_format(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    AudioProcessingConfig = import_runtime_addon_module(".audio_state").AudioProcessingConfig

    captured: list[tuple[str, str, str]] = []
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_convert_status_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, output_format="mp3")

    def fake_render_converted_audio(
        source_path: Path,
        _config: AudioProcessingConfig,
        target_format: str,
        output_path: Path,
        **_kwargs,
    ) -> None:
        captured.append((source_path.name, target_format, output_path.suffix))
        output_path.write_bytes(b"converted")

    monkeypatch.setattr(
        runtime_addon_import_path(".editor_dependencies", "render_converted_audio"),
        fake_render_converted_audio,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:convert"), timeout=10.0)
        click_selector(editor.web, '[data-testid="aqe-split-0-convert-menu"]', timeout=5.0)
        click_selector(editor.web, '[data-testid="aqe-split-0-convert-preset-flac"]', timeout=5.0)
        click_selector(editor.web, _button_selector("aqe:convert"), timeout=5.0)

        generated_name = _wait_for_generated_file(note, media_dir, source.name, ".flac")
        wait_for_condition(
            lambda: captured == [(source.name, "flac", ".flac")],
            timeout=5.0,
            message="Convert did not pass the selected FLAC target to the renderer",
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Converted audio to FLAC.",
            timeout=10.0,
        )

        assert generated_name.endswith(".flac")
    finally:
        editor.set_note(None)
        parent.close()


def test_voice_only_status_reports_selected_cleanup_variant(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    AudioProcessingConfig = import_runtime_addon_module(".audio_state").AudioProcessingConfig

    captured: list[str] = []
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_voice_only_status_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, denoise_algorithm="standard")

    def fake_render_voice_only_audio(
        source_path: Path,
        _config: AudioProcessingConfig,
        output_path: Path,
        **_kwargs,
    ) -> None:
        captured.append(source_path.name)
        output_path.write_bytes(b"voice-only")

    monkeypatch.setattr(
        runtime_addon_import_path(".editor_dependencies", "render_voice_only_audio"),
        fake_render_voice_only_audio,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:denoise-standard"), timeout=10.0)
        click_selector(editor.web, '[data-testid="aqe-split-0-denoise-standard-menu"]', timeout=5.0)
        click_selector(
            editor.web,
            '[data-testid="aqe-split-0-denoise-standard-preset-voice_only"]',
            timeout=5.0,
        )
        click_selector(editor.web, _button_selector("aqe:denoise-standard"), timeout=5.0)

        _wait_for_generated_mp3(note, media_dir, source.name)
        wait_for_condition(
            lambda: captured == [source.name],
            timeout=5.0,
            message="Voice Only did not invoke the selected renderer",
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Cleaned audio with Voice Only.",
            timeout=10.0,
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_pitch_hum_status_reports_selected_pitchtier_mode(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    AudioProcessingConfig = import_runtime_addon_module(".audio_state").AudioProcessingConfig

    captured: list[str] = []
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_pitchtier_status_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, pitch_hum_mode="direct")

    def fake_render_pitch_tier_hum_audio(
        source_path: Path,
        _config: AudioProcessingConfig,
        output_path: Path,
        **_kwargs,
    ) -> None:
        captured.append(source_path.name)
        output_path.write_bytes(b"pitch-tier")

    monkeypatch.setattr(
        runtime_addon_import_path(".editor_dependencies", "render_pitch_tier_hum_audio"),
        fake_render_pitch_tier_hum_audio,
    )
    monkeypatch.setattr(
        runtime_addon_import_path(".editor_dependencies", "render_pitch_hum_audio"),
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("PitchTier selection used direct hum renderer")),
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:pitch-hum"), timeout=10.0)
        click_selector(editor.web, '[data-testid="aqe-split-0-pitch-hum-menu"]', timeout=5.0)
        click_selector(
            editor.web,
            '[data-testid="aqe-split-0-pitch-hum-preset-pitch_tier"]',
            timeout=5.0,
        )
        click_selector(editor.web, _button_selector("aqe:pitch-hum"), timeout=5.0)

        _wait_for_generated_mp3(note, media_dir, source.name)
        wait_for_condition(
            lambda: captured == [source.name],
            timeout=5.0,
            message="Pitch Hum did not invoke the selected PitchTier renderer",
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Rendered pitch hum with PitchTier mode.",
            timeout=10.0,
        )
    finally:
        editor.set_note(None)
        parent.close()
