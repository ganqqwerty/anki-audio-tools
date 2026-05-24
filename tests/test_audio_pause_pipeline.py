from __future__ import annotations

import json
from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_processor import (
    probe_duration_ms,
    render_audio,
)
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.errors import (
    AudioProcessingError,
)
from anki_audio_quick_editor.support import (
    clear_latest_pause_pipeline_support_incident,
    latest_pause_pipeline_support_incident,
)
from tests.audio_fixtures import (
    FFMPEG_AVAILABLE,
    FFMPEG_SKIP_REASON,
    _fake_deep_filter_executable,
    _generate_long_pause_clip,
    _generate_quiet_micro_word_clip,
    _generate_short_pause_clip,
)


def test_render_audio_pause_pipeline_records_launch_error_for_out_of_disk(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_pause_pipeline_support_incident()
    source = tmp_path / "source.mp3"
    source.write_bytes(b"source")
    output = tmp_path / "out.mp3"
    artifact_root = tmp_path / "artifacts"

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda *_args: Path("/bin/deep-filter"),
    )
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)

    def fake_run(*_args, **_kwargs) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="No space left on device"):
        render_audio(
            source,
            AudioEditState("source.mp3", remove_internal_pauses_enabled=True),
            AudioProcessingConfig(),
            output_path=output,
            artifact_root=artifact_root,
        )

    run_dirs = list(artifact_root.iterdir())
    assert len(run_dirs) == 1
    manifest_path = run_dirs[0] / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["stages"][0]["name"] == "render_working_original"
    assert "No space left on device" in manifest["stages"][0]["launch_error"]
    incident = latest_pause_pipeline_support_incident()
    assert incident is not None
    assert incident["manifest_path"] == str(manifest_path)
    assert incident["attempted_commands"][0]["launch_error"].startswith("Could not start working-audio preparation.")


@pytest.mark.skipif(
    not FFMPEG_AVAILABLE,
    reason=FFMPEG_SKIP_REASON,
)
def test_render_audio_remove_pauses_preserves_short_pause(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "short_pause.wav"
    output = tmp_path / "short_pause.mp3"
    artifact_root = tmp_path / "artifacts"
    fake_deep_filter = _fake_deep_filter_executable(tmp_path)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda *_args: fake_deep_filter,
    )
    _generate_short_pause_clip(source)
    source_duration_ms = probe_duration_ms(source, AudioProcessingConfig())

    result = render_audio(
        source,
        AudioEditState("short_pause.wav", remove_internal_pauses_enabled=True),
        AudioProcessingConfig(),
        output_path=output,
        artifact_root=artifact_root,
    )

    assert result.output_path == output
    assert abs((result.duration_ms or 0) - source_duration_ms) <= 25
    assert result.artifact_manifest_path is not None
    manifest = json.loads(result.artifact_manifest_path.read_text(encoding="utf-8"))
    assert manifest["timeline"] == [
        {
            "end_ms": source_duration_ms,
            "kind": "normal",
            "output_duration_ms": source_duration_ms,
            "speed_factor": 1.0,
            "start_ms": 0,
        }
    ]


@pytest.mark.skipif(
    not FFMPEG_AVAILABLE,
    reason=FFMPEG_SKIP_REASON,
)
def test_render_audio_remove_pauses_compresses_obvious_long_pause(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "long_pause.wav"
    output = tmp_path / "long_pause.mp3"
    artifact_root = tmp_path / "artifacts"
    fake_deep_filter = _fake_deep_filter_executable(tmp_path)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda *_args: fake_deep_filter,
    )
    _generate_long_pause_clip(source)
    source_duration_ms = probe_duration_ms(source, AudioProcessingConfig())

    result = render_audio(
        source,
        AudioEditState("long_pause.wav", remove_internal_pauses_enabled=True),
        AudioProcessingConfig(),
        output_path=output,
        artifact_root=artifact_root,
    )

    assert result.output_path == output
    assert result.duration_ms is not None
    assert result.duration_ms <= source_duration_ms - 200
    assert result.artifact_manifest_path is not None
    run_dir = result.artifact_manifest_path.parent
    assert (run_dir / "01_working_original.wav").is_file()
    assert (run_dir / "02_analysis_input_48k_mono.wav").is_file()
    assert (run_dir / "03_deep_filter_output" / "clean.wav").is_file()
    assert (run_dir / "04_silencedetect_stderr.txt").is_file()
    assert (run_dir / "04_silence_intervals.json").is_file()
    assert (run_dir / "05_timeline.json").is_file()
    assert (run_dir / "06_filter_complex.ffscript").is_file()
    assert (run_dir / "07_final_output.mp3").is_file()
    filter_script = (run_dir / "06_filter_complex.ffscript").read_text(encoding="utf-8")
    assert "atempo=" in filter_script
    manifest = json.loads(result.artifact_manifest_path.read_text(encoding="utf-8"))
    assert manifest["operation"] == "deep_filter_pause_speedup"
    assert manifest["source"]["filename"] == "long_pause.wav"
    assert manifest["silence_intervals"]
    assert any(segment["kind"] == "pause" for segment in manifest["timeline"])
    render_stage = next(stage for stage in manifest["stages"] if stage["name"] == "render_final_output")
    assert "01_working_original.wav" in render_stage["command"]
    assert "06_filter_complex.ffscript" in render_stage["command"]


@pytest.mark.skipif(
    not FFMPEG_AVAILABLE,
    reason=FFMPEG_SKIP_REASON,
)
def test_render_audio_remove_pauses_keeps_partial_manifest_on_deep_filter_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_pause_pipeline_support_incident()
    source = tmp_path / "long_pause.wav"
    output = tmp_path / "long_pause.mp3"
    artifact_root = tmp_path / "artifacts"
    fake_deep_filter = _fake_deep_filter_executable(tmp_path, fail=True)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda *_args: fake_deep_filter,
    )
    _generate_long_pause_clip(source)

    with pytest.raises(AudioProcessingError, match="fake deep-filter failed"):
        render_audio(
            source,
            AudioEditState("long_pause.wav", remove_internal_pauses_enabled=True),
            AudioProcessingConfig(),
            output_path=output,
            artifact_root=artifact_root,
        )

    run_dirs = list(artifact_root.iterdir())
    assert len(run_dirs) == 1
    manifest_path = run_dirs[0] / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["errors"] == ["fake deep-filter failed"]
    assert [stage["name"] for stage in manifest["stages"]] == [
        "render_working_original",
        "prepare_deep_filter_input",
        "deep_filter_analysis",
    ]
    assert not output.exists()
    incident = latest_pause_pipeline_support_incident()
    assert incident is not None
    assert incident["manifest_path"] == str(manifest_path)
    assert incident["artifact_dir"] == str(run_dirs[0])


@pytest.mark.skipif(
    not FFMPEG_AVAILABLE,
    reason=FFMPEG_SKIP_REASON,
)
def test_render_audio_remove_pauses_preserves_quiet_micro_word_between_pauses(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "quiet_micro_word.wav"
    output = tmp_path / "quiet_micro_word.mp3"
    fake_deep_filter = _fake_deep_filter_executable(tmp_path)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda *_args: fake_deep_filter,
    )
    _generate_quiet_micro_word_clip(source)
    source_duration_ms = probe_duration_ms(source, AudioProcessingConfig())

    result = render_audio(
        source,
        AudioEditState("quiet_micro_word.wav", remove_internal_pauses_enabled=True),
        AudioProcessingConfig(),
        output_path=output,
        artifact_root=tmp_path / "artifacts",
    )

    assert result.output_path == output
    assert result.duration_ms is not None
    assert result.duration_ms < source_duration_ms
    assert result.duration_ms > 550
    assert result.artifact_manifest_path is not None
    manifest = json.loads(result.artifact_manifest_path.read_text(encoding="utf-8"))
    assert sum(1 for segment in manifest["timeline"] if segment["kind"] == "pause") == 2
