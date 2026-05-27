from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_pause_pipeline_steps import (
    _render_silero_vad_pause_speedup_audio,
    _silero_vad_parameters,
)
from anki_audio_quick_editor.audio_pipeline import (
    SilenceInterval,
    parse_silero_vad_speech_intervals,
    speech_intervals_to_silence_intervals,
)
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


def test_silero_aggressive_pause_parameters_are_tuned_for_shorter_gaps() -> None:
    params = _silero_vad_parameters(AudioProcessingConfig(pause_aggressiveness="aggressive"))

    assert params == {
        "threshold": 0.85,
        "min_silence_seconds": 0.15,
        "min_speech_seconds": 0.04,
    }


def test_parse_silero_vad_speech_intervals_and_inverts_to_pauses() -> None:
    stderr = """
    VadModelConfig(...)
    0.196 -- 0.984
    1.188 -- 3.544
    5.316 -- 5.560
    Saved to out.wav
    """

    speech = parse_silero_vad_speech_intervals(stderr, 6000)

    assert speech == (
        SilenceInterval(196, 984, 788),
        SilenceInterval(1188, 3544, 2356),
        SilenceInterval(5316, 5560, 244),
    )
    assert speech_intervals_to_silence_intervals(speech, 6000) == (
        SilenceInterval(0, 196, 196),
        SilenceInterval(984, 1188, 204),
        SilenceInterval(3544, 5316, 1772),
        SilenceInterval(5560, 6000, 440),
    )


def test_silero_pipeline_uses_timestamps_to_render_from_original_audio(
    monkeypatch,
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "artifacts" / "run"
    run_dir.mkdir(parents=True)
    manifest_path = run_dir / "manifest.json"
    working_original = run_dir / "01_working_original.wav"
    working_original.write_bytes(b"original")
    output = tmp_path / "out.mp3"
    stages: list[dict[str, object]] = []
    attempted_commands: list[dict[str, object]] = []
    artifacts: list[dict[str, object]] = []
    manifest: dict[str, object] = {"stages": stages}

    def write_manifest() -> None:
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    def fake_run_pipeline_stage(
        stage_name: str,
        command: tuple[str, ...],
        *_args: object,
    ) -> subprocess.CompletedProcess[str]:
        stages.append({"name": stage_name, "command": " ".join(command)})
        if stage_name == "prepare_silero_vad_input":
            Path(command[-1]).write_bytes(b"silero input")
            return subprocess.CompletedProcess(command, 0, "", "")
        if stage_name == "silero_vad_analysis":
            Path(command[-1]).write_bytes(b"silero output")
            return subprocess.CompletedProcess(
                command,
                0,
                "",
                "0.100 -- 0.500\n1.200 -- 1.500\nSaved to vad.wav\n",
            )
        if stage_name == "render_final_output":
            output.write_bytes(b"final")
            return subprocess.CompletedProcess(command, 0, "", "")
        raise AssertionError(f"unexpected stage: {stage_name}")

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pause_pipeline_steps._run_pipeline_stage",
        fake_run_pipeline_stage,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pause_pipeline_steps.probe_duration_ms",
        lambda *_args: 1200,
    )

    result = _render_silero_vad_pause_speedup_audio(
        AudioEditState("source.wav", remove_internal_pauses_enabled=True),
        AudioProcessingConfig(internal_pause_threshold_ms=200, internal_pause_target_gap_ms=100),
        Path("/bin/ffmpeg"),
        output,
        None,
        run_dir=run_dir,
        manifest_path=manifest_path,
        manifest=manifest,
        stages=stages,
        attempted_commands=attempted_commands,
        artifacts=artifacts,
        write_manifest=write_manifest,
        working_original=working_original,
        working_duration_ms=1800,
        silero_vad_path=Path("/bin/silero-vad"),
        silero_model_path=Path("/models/silero_vad.onnx"),
    )

    render_stage = next(stage for stage in stages if stage["name"] == "render_final_output")
    render_command = str(render_stage["command"])
    assert "01_working_original.wav" in render_command
    assert "03_silero_vad_output.wav" not in render_command
    assert result.duration_ms == 1200
    assert manifest["silero_vad_input_duration_ms"] == 1800
    assert manifest["silero_vad_speech_intervals"] == [
        {"duration_ms": 400, "end_ms": 500, "start_ms": 100},
        {"duration_ms": 300, "end_ms": 1500, "start_ms": 1200},
    ]
    assert manifest["silence_intervals"] == [
        {"duration_ms": 100, "end_ms": 100, "start_ms": 0},
        {"duration_ms": 700, "end_ms": 1200, "start_ms": 500},
        {"duration_ms": 300, "end_ms": 1800, "start_ms": 1500},
    ]
    assert manifest["timeline"] == [
        {
            "end_ms": 500,
            "kind": "normal",
            "output_duration_ms": 500,
            "speed_factor": 1.0,
            "start_ms": 0,
        },
        {
            "end_ms": 1200,
            "kind": "pause",
            "output_duration_ms": 100,
            "speed_factor": 7.0,
            "start_ms": 500,
        },
        {
            "end_ms": 1500,
            "kind": "normal",
            "output_duration_ms": 300,
            "speed_factor": 1.0,
            "start_ms": 1200,
        },
        {
            "end_ms": 1800,
            "kind": "pause",
            "output_duration_ms": 100,
            "speed_factor": 3.0,
            "start_ms": 1500,
        },
    ]
    assert (run_dir / "04_silero_vad_stderr.txt").is_file()
    assert (run_dir / "04_silero_speech_intervals.json").is_file()
    assert (run_dir / "04_silence_intervals.json").is_file()
    filter_script = (run_dir / "06_filter_complex.ffscript").read_text(encoding="utf-8")
    assert "[src0]atrim=start=0.000:end=0.500,asetpts=PTS-STARTPTS[a0]" in filter_script
    assert (
        "[src1]atrim=start=0.500:end=1.200,asetpts=PTS-STARTPTS,"
        "atempo=2.000,atempo=2.000,atempo=1.750[a1]"
    ) in filter_script
    assert "[src2]atrim=start=1.200:end=1.500,asetpts=PTS-STARTPTS[a2]" in filter_script
    assert (
        "[src3]atrim=start=1.500:end=1.800,asetpts=PTS-STARTPTS,"
        "atempo=2.000,atempo=1.500[a3]"
    ) in filter_script


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
