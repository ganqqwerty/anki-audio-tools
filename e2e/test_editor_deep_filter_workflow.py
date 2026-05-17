"""E2E tests for DeepFilter-backed editor commands."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from e2e.editor_audio_generation_helpers import (
    _fake_deep_filter_executable,
    _generate_noisy_pause_and_clean_analysis,
    _render_direct_deep_filter_reference,
)
from e2e.editor_graph_helpers import _click_graph_and_wait, _wait_for_visualizer_track
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
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js_condition,
)


def test_shorten_pauses_uses_deep_filter_analysis_and_retains_artifacts(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms

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
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

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
        assert "03_deep_filter_output/clean.wav" in " ".join(
            stage_by_name["detect_silence"]["argv"]
        )
        assert "01_working_original.wav" in " ".join(
            stage_by_name["render_final_output"]["argv"]
        )
        assert "06_filter_complex.ffscript" in " ".join(
            stage_by_name["render_final_output"]["argv"]
        )
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
    from anki_audio_quick_editor.support import (
        clear_latest_pause_pipeline_support_incident,
        latest_pause_pipeline_support_incident,
    )

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
        manifest = json.loads(
            (next(iter(new_artifacts)) / "manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["errors"]
        assert not list(media_dir.glob("editor_shorten_pause_failure_source__aqe_*.mp3"))
    finally:
        editor.set_note(None)
        parent.close()
        _cleanup_artifact_dirs(artifact_root, source)


def test_remove_noise_button_runs_deep_filter_and_is_undoable(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_remove_noise_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.2)
    original_bytes = source.read_bytes()
    fake_deep_filter, deep_filter_log = _fake_deep_filter_executable(tmp_path)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        deep_filter_path=str(fake_deep_filter),
        deep_filter_post_filter=True,
        show_ffmpeg_commands=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        click_selector(editor.web, _button_selector("aqe:remove-noise"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)

        generated_path = media_dir / generated_name
        assert generated_path.is_file()
        assert generated_name.endswith(".mp3")
        assert source.read_bytes() == original_bytes
        assert probe_duration_ms(generated_path, ffmpeg_config) > 0
        assert abs(probe_duration_ms(generated_path, ffmpeg_config) - 1200) < 250

        deep_filter_args = json.loads(deep_filter_log.read_text(encoding="utf-8"))
        assert "-D" in deep_filter_args
        assert "--pf" in deep_filter_args
        assert "-o" in deep_filter_args
        output_dir = Path(deep_filter_args[deep_filter_args.index("-o") + 1])
        assert output_dir.name == "deep_filter_output"
        assert Path(deep_filter_args[-1]).name == "input_48k_mono.wav"

        _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_name and value["cursorMs"] == 0,
            timeout=10.0,
        )

        click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == source.name,
            timeout=5.0,
            message="Undo did not restore the original audio reference after noise removal",
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_remove_noise_button_matches_direct_deep_filter_output(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    sample_path = Path(
        "/Users/iuriikatkov/Library/Application Support/Anki2/main2/collection.media/3d8ca69aee6.mp3"
    )
    if not sample_path.is_file():
        pytest.skip(f"Local DeepFilterNet sample is unavailable: {sample_path}")

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / sample_path.name
    shutil.copyfile(sample_path, source)
    direct_output = tmp_path / "3d8ca69aee6_direct_deep_filter.mp3"
    _render_direct_deep_filter_reference(
        ffmpeg_config,
        source,
        direct_output,
        post_filter=True,
    )

    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        deep_filter_path="",
        deep_filter_post_filter=True,
        show_ffmpeg_commands=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        click_selector(editor.web, _button_selector("aqe:remove-noise"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
        generated_path = media_dir / generated_name

        ui_bytes = generated_path.read_bytes()
        direct_bytes = direct_output.read_bytes()
        assert ui_bytes == direct_bytes, (
            "Remove noise button output differs from direct DeepFilterNet output: "
            f"ui={generated_path} ({len(ui_bytes)} bytes), "
            f"direct={direct_output} ({len(direct_bytes)} bytes)"
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_remove_noise_failure_leaves_note_unchanged(
    anki_mw,
    ffmpeg_config,
    tmp_path,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_remove_noise_failure_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.8)
    original_field = f"Prompt [sound:{source.name}]"
    fake_deep_filter, deep_filter_log = _fake_deep_filter_executable(tmp_path, fail=True)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        deep_filter_path=str(fake_deep_filter),
        deep_filter_post_filter=True,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        click_selector(editor.web, _button_selector("aqe:remove-noise"), timeout=10.0)
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
            "input_48k_mono.wav"
        )
        assert not list(media_dir.glob("editor_remove_noise_failure_source__aqe_*.mp3"))
    finally:
        editor.set_note(None)
        parent.close()
