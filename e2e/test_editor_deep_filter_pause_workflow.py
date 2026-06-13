"""E2E tests for DPDFNet-backed pause detection preprocessing."""

from __future__ import annotations

import json
from pathlib import Path

from e2e.conftest import import_runtime_addon_module
from e2e.editor_audio_generation_helpers import _generate_tone_silence_tone
from e2e.editor_note_helpers import (
    _artifact_dirs_for_source,
    _artifact_root,
    _basic_audio_note,
    _button_selector,
    _cleanup_artifact_dirs,
    _configure_ffmpeg,
    _open_editor,
    _processing_status_js,
    _sound_filename,
    _wait_for_generated_mp3,
)
from e2e.helpers import click_selector, wait_for_js_condition


def test_shorten_pauses_uses_dpdfnet_analysis_and_retains_artifacts(
    anki_mw,
    ffmpeg_config,
) -> None:
    probe_duration_ms = import_runtime_addon_module(".audio_processor").probe_duration_ms
    runtime_platform = import_runtime_addon_module(".runtime_platform")

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_shorten_pause_source.wav"
    _generate_tone_silence_tone(ffmpeg_config, source)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        pause_silencedetect_preprocess_denoise=True,
        show_ffmpeg_commands=True,
    )
    artifact_root = _artifact_root(anki_mw)
    before_artifacts = _artifact_dirs_for_source(artifact_root, source)

    editor, parent = _open_editor(anki_mw, note)
    try:
        click_selector(editor.web, _button_selector("aqe:remove-pauses"), timeout=10.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
        generated_path = media_dir / generated_name

        source_duration_ms = probe_duration_ms(source, ffmpeg_config)
        generated_duration_ms = probe_duration_ms(generated_path, ffmpeg_config)
        assert source.read_bytes() == original_bytes
        assert 650 <= generated_duration_ms <= 1050
        assert generated_duration_ms < source_duration_ms - 350

        new_artifacts = sorted(
            _artifact_dirs_for_source(artifact_root, source) - before_artifacts,
            key=lambda path: path.stat().st_mtime_ns,
        )
        assert len(new_artifacts) == 1
        run_dir = new_artifacts[0]
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))

        for relative_path in (
            "01_working_original.wav",
            "02_denoised_analysis.wav",
            "04_detection_stderr.txt",
            "04_detected_pause_intervals.json",
            "04_removed_intervals.json",
            "05_timeline.json",
            "06_filter_complex.ffscript",
            "07_final_output.wav",
            "manifest.json",
        ):
            assert (run_dir / relative_path).is_file()

        stage_by_name = {stage["name"]: stage for stage in manifest["stages"]}
        assert "02_denoised_analysis.wav" in " ".join(stage_by_name["detect_silence"]["argv"])
        assert "01_working_original.wav" in " ".join(stage_by_name["render_final_output"]["argv"])
        assert "06_filter_complex.ffscript" in " ".join(stage_by_name["render_final_output"]["argv"])
        assert "01_working_original.wav" in " ".join(
            stage_by_name["preprocess_pause_analysis_denoise"]["argv"]
        )
        platform_key = runtime_platform.current_platform_key()
        assert platform_key is not None
        dpdfnet_path = Path(manifest["dpdfnet_path"])
        assert dpdfnet_path.is_file()
        assert dpdfnet_path.name == runtime_platform.tool_executable_name(
            "dpdfnet",
            platform_key,
        )
        assert manifest["silence_intervals"]
        assert manifest["pause_preprocessing"]["enabled"] is True
        assert manifest["pause_preprocessing"]["implementation"] == "dpdfnet"
        assert manifest["pause_detection_parameters"]["algorithm"] == "silencedetect"
        assert manifest["pause_detection_parameters"]["preprocess_denoise"] is True
        assert not [segment for segment in manifest["timeline"] if segment["kind"] == "pause"]
        assert all(segment["speed_factor"] == 1.0 for segment in manifest["timeline"])

        filter_script = (run_dir / "06_filter_complex.ffscript").read_text(encoding="utf-8")
        assert "atempo=" not in filter_script
    finally:
        editor.set_note(None)
        parent.close()
        _cleanup_artifact_dirs(artifact_root, source)


def test_shorten_pauses_invalid_source_leaves_note_unchanged(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_shorten_pause_failure_source.wav"
    source.write_bytes(b"not an audio file")
    original_field = f"Prompt [sound:{source.name}]"
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        pause_silencedetect_preprocess_denoise=True,
    )
    artifact_root = _artifact_root(anki_mw)
    before_artifacts = _artifact_dirs_for_source(artifact_root, source)

    editor, parent = _open_editor(anki_mw, note)
    try:
        click_selector(editor.web, _button_selector("aqe:remove-pauses"), timeout=10.0)
        status = wait_for_js_condition(
            editor.web,
            _processing_status_js(),
            lambda value: value is not None
            and value["kind"] == "error"
            and "Invalid data" in value["text"],
            timeout=10.0,
        )

        assert status["title"] == ""
        assert note.fields[0] == original_field
        assert _sound_filename(note.fields[0]) == source.name
        assert _artifact_dirs_for_source(artifact_root, source) == before_artifacts
        assert not list(media_dir.glob("editor_shorten_pause_failure_source__aqe_*"))
    finally:
        editor.set_note(None)
        parent.close()
        _cleanup_artifact_dirs(artifact_root, source)
