"""E2E tests for DeepFilter-backed pause shortening."""

from __future__ import annotations

import json
from pathlib import Path

from e2e.conftest import import_runtime_addon_module
from e2e.editor_audio_generation_helpers import (
    _fake_deep_filter_executable,
    _generate_noisy_pause_and_clean_analysis,
)
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


def test_shorten_pauses_uses_deep_filter_analysis_and_retains_artifacts(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    probe_duration_ms = import_runtime_addon_module(".audio_processor").probe_duration_ms

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_shorten_pause_source.wav"
    cleaned_analysis = tmp_path / "editor_shorten_pause_cleaned.wav"
    _generate_noisy_pause_and_clean_analysis(ffmpeg_config, source, cleaned_analysis)
    original_bytes = source.read_bytes()
    fake_deep_filter, deep_filter_log = _fake_deep_filter_executable(
        tmp_path,
        cleaned_source=cleaned_analysis,
    )
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        deep_filter_path=str(fake_deep_filter),
        deep_filter_post_filter=True,
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
            "02_analysis_input_48k_mono.wav",
            "03_deep_filter_output/clean.wav",
            "04_silencedetect_stderr.txt",
            "04_silence_intervals.json",
            "05_timeline.json",
            "06_filter_complex.ffscript",
            "07_final_output.mp3",
            "manifest.json",
        ):
            assert (run_dir / relative_path).is_file()

        stage_by_name = {stage["name"]: stage for stage in manifest["stages"]}
        assert "03_deep_filter_output/clean.wav" in " ".join(stage_by_name["detect_silence"]["argv"])
        assert "01_working_original.wav" in " ".join(stage_by_name["render_final_output"]["argv"])
        assert "06_filter_complex.ffscript" in " ".join(stage_by_name["render_final_output"]["argv"])
        assert manifest["silence_intervals"]
        pause_segments = [segment for segment in manifest["timeline"] if segment["kind"] == "pause"]
        assert len(pause_segments) == 1
        assert pause_segments[0]["speed_factor"] >= 7.0

        filter_script = (run_dir / "06_filter_complex.ffscript").read_text(encoding="utf-8")
        assert "atempo=" in filter_script
        deep_filter_args = json.loads(deep_filter_log.read_text(encoding="utf-8"))
        assert Path(deep_filter_args[-1]).name == "02_analysis_input_48k_mono.wav"
    finally:
        editor.set_note(None)
        parent.close()
        _cleanup_artifact_dirs(artifact_root, source)


def test_shorten_pauses_failure_leaves_note_unchanged_and_records_manifest(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    support = import_runtime_addon_module(".support")
    clear_latest_pause_pipeline_support_incident = (
        support.clear_latest_pause_pipeline_support_incident
    )
    latest_pause_pipeline_support_incident = support.latest_pause_pipeline_support_incident

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_shorten_pause_failure_source.wav"
    cleaned_analysis = tmp_path / "editor_shorten_pause_failure_cleaned.wav"
    _generate_noisy_pause_and_clean_analysis(ffmpeg_config, source, cleaned_analysis)
    original_field = f"Prompt [sound:{source.name}]"
    fake_deep_filter, deep_filter_log = _fake_deep_filter_executable(tmp_path, fail=True)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        deep_filter_path=str(fake_deep_filter),
        deep_filter_post_filter=True,
    )
    artifact_root = _artifact_root(anki_mw)
    before_artifacts = _artifact_dirs_for_source(artifact_root, source)
    clear_latest_pause_pipeline_support_incident()

    editor, parent = _open_editor(anki_mw, note)
    try:
        click_selector(editor.web, _button_selector("aqe:remove-pauses"), timeout=10.0)
        status = wait_for_js_condition(
            editor.web,
            _processing_status_js(),
            lambda value: value is not None
            and value["kind"] == "error"
            and "fake deep-filter failed" in value["text"],
            timeout=10.0,
        )

        assert status["title"] == ""
        assert note.fields[0] == original_field
        assert _sound_filename(note.fields[0]) == source.name
        assert json.loads(deep_filter_log.read_text(encoding="utf-8"))[-1].endswith(
            "02_analysis_input_48k_mono.wav"
        )

        incident = latest_pause_pipeline_support_incident()
        assert incident is not None
        assert incident["manifest_path"].endswith("manifest.json")
        assert Path(incident["manifest_path"]).is_file()
        assert Path(incident["artifact_dir"]).is_dir()
        assert "fake deep-filter failed" in incident["user_message"]

        new_artifacts = _artifact_dirs_for_source(artifact_root, source) - before_artifacts
        assert len(new_artifacts) == 1
        manifest = json.loads((next(iter(new_artifacts)) / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["errors"]
        assert not list(media_dir.glob("editor_shorten_pause_failure_source__aqe_*.mp3"))
    finally:
        editor.set_note(None)
        parent.close()
        _cleanup_artifact_dirs(artifact_root, source)
