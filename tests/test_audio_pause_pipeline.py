from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_pause_pipeline_steps import (
    _render_pause_removal_audio,
)
from anki_audio_quick_editor.audio_pause_settings import preset_for_pause_detection
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
from anki_audio_quick_editor.errors import AudioProcessingError
from anki_audio_quick_editor.support import (
    clear_latest_pause_pipeline_support_incident,
    latest_pause_pipeline_support_incident,
)
from tests.audio_fixtures import (
    FFMPEG_AVAILABLE,
    FFMPEG_SKIP_REASON,
    _generate_long_pause_clip,
    _generate_short_pause_clip,
)


def test_silero_aggressive_pause_preset_matches_contract() -> None:
    preset = preset_for_pause_detection("silero_vad", "aggressive")

    assert preset.threshold == 0.85
    assert preset.min_silence_seconds == 0.15
    assert preset.min_speech_seconds == 0.04
    assert preset.preprocess_denoise is False


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


def test_silero_pipeline_cuts_pauses_and_renders_from_original_audio(
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
        **_kwargs: object,
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
        "anki_audio_quick_editor.audio_pause_pipeline_stage.run_pipeline_stage",
        fake_run_pipeline_stage,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pause_pipeline_steps.probe_duration_ms",
        lambda *_args: 1200,
    )

    result = _render_pause_removal_audio(
        AudioEditState("source.wav", remove_internal_pauses_enabled=True),
        AudioProcessingConfig(
            pause_detection_algorithm="silero_vad",
            pause_silero_min_silence_seconds=0.2,
            pause_silero_min_speech_seconds=0.1,
        ),
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
        analysis_input=run_dir / "02_analysis_input.wav",
        denoised_analysis=run_dir / "02_denoised_analysis.wav",
        raw_silence_path=run_dir / "04_detection_stderr.txt",
        intervals_path=run_dir / "04_removed_intervals.json",
        timeline_path=run_dir / "05_timeline.json",
        filter_script_path=run_dir / "06_filter_complex.ffscript",
        final_copy_path=run_dir / "07_final_output.mp3",
        dpdfnet_path=None,
        silero_vad_path=Path("/bin/silero-vad"),
        silero_model_path=Path("/models/silero_vad.onnx"),
    )

    render_stage = next(stage for stage in stages if stage["name"] == "render_final_output")
    render_command = str(render_stage["command"])
    assert "01_working_original.wav" in render_command
    assert "03_silero_vad_output.wav" not in render_command
    assert result.duration_ms == 1200
    assert manifest["detected_intervals"] == [
        {"duration_ms": 100, "end_ms": 100, "start_ms": 0},
        {"duration_ms": 700, "end_ms": 1200, "start_ms": 500},
        {"duration_ms": 300, "end_ms": 1800, "start_ms": 1500},
    ]
    assert manifest["removed_intervals"] == [
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
            "end_ms": 1500,
            "kind": "normal",
            "output_duration_ms": 300,
            "speed_factor": 1.0,
            "start_ms": 1200,
        },
    ]
    filter_script = (run_dir / "06_filter_complex.ffscript").read_text(encoding="utf-8")
    assert "atempo=" not in filter_script
    assert "[src0]atrim=start=0.000:end=0.500,asetpts=PTS-STARTPTS[a0]" in filter_script
    assert "[src1]atrim=start=1.200:end=1.500,asetpts=PTS-STARTPTS[a1]" in filter_script


def test_denoise_preprocessing_changes_detection_input_not_render_source(
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
        **_kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        stages.append({"name": stage_name, "command": " ".join(command)})
        if stage_name == "preprocess_pause_analysis_denoise":
            Path(command[-1]).write_bytes(b"denoised")
            return subprocess.CompletedProcess(command, 0, "", "")
        if stage_name == "detect_silence":
            assert "02_denoised_analysis.wav" in " ".join(command)
            return subprocess.CompletedProcess(
                command,
                0,
                "",
                "[silencedetect] silence_start: 0.500\n"
                "[silencedetect] silence_end: 1.200 | silence_duration: 0.700\n",
            )
        if stage_name == "render_final_output":
            output.write_bytes(b"final")
            return subprocess.CompletedProcess(command, 0, "", "")
        raise AssertionError(f"unexpected stage: {stage_name}")

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pause_pipeline_stage.run_pipeline_stage",
        fake_run_pipeline_stage,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pause_pipeline_steps.probe_duration_ms",
        lambda *_args: 800,
    )

    _render_pause_removal_audio(
        AudioEditState("source.wav", remove_internal_pauses_enabled=True),
        AudioProcessingConfig(
            pause_detection_algorithm="silencedetect",
            pause_silencedetect_preprocess_denoise=True,
            pause_silencedetect_min_silence_seconds=0.2,
        ),
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
        analysis_input=run_dir / "02_analysis_input.wav",
        denoised_analysis=run_dir / "02_denoised_analysis.wav",
        raw_silence_path=run_dir / "04_detection_stderr.txt",
        intervals_path=run_dir / "04_removed_intervals.json",
        timeline_path=run_dir / "05_timeline.json",
        filter_script_path=run_dir / "06_filter_complex.ffscript",
        final_copy_path=run_dir / "07_final_output.mp3",
        dpdfnet_path=Path("/bin/dpdfnet"),
        silero_vad_path=None,
        silero_model_path=None,
    )

    render_stage = next(stage for stage in stages if stage["name"] == "render_final_output")
    assert "01_working_original.wav" in str(render_stage["command"])
    assert manifest["pause_preprocessing"] == {
        "enabled": True,
        "implementation": "dpdfnet",
        "analysis_source": str(run_dir / "02_denoised_analysis.wav"),
    }


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
        "anki_audio_quick_editor.audio_processor.find_dpdfnet_bundle",
        lambda: Path("/bin/dpdfnet"),
    )
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)

    def fake_run(*_args: object, **_kwargs: object) -> None:
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
def test_render_audio_remove_pauses_preserves_short_pause(tmp_path: Path) -> None:
    source = tmp_path / "short_pause.wav"
    output = tmp_path / "short_pause.mp3"
    artifact_root = tmp_path / "artifacts"
    _generate_short_pause_clip(source)
    config = AudioProcessingConfig(pause_silencedetect_preprocess_denoise=False)
    source_duration_ms = probe_duration_ms(source, config)

    result = render_audio(
        source,
        AudioEditState("short_pause.wav", remove_internal_pauses_enabled=True),
        config,
        output_path=output,
        artifact_root=artifact_root,
    )

    assert result.output_path == output
    assert abs((result.duration_ms or 0) - source_duration_ms) <= 25
    assert result.artifact_manifest_path is not None
    manifest = json.loads(result.artifact_manifest_path.read_text(encoding="utf-8"))
    assert manifest["removed_intervals"] == []
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
def test_render_audio_remove_pauses_cuts_obvious_long_pause(tmp_path: Path) -> None:
    source = tmp_path / "long_pause.wav"
    output = tmp_path / "long_pause.mp3"
    artifact_root = tmp_path / "artifacts"
    _generate_long_pause_clip(source)
    config = AudioProcessingConfig(pause_silencedetect_preprocess_denoise=False)
    source_duration_ms = probe_duration_ms(source, config)

    result = render_audio(
        source,
        AudioEditState("long_pause.wav", remove_internal_pauses_enabled=True),
        config,
        output_path=output,
        artifact_root=artifact_root,
    )

    assert result.output_path == output
    assert result.duration_ms is not None
    assert result.duration_ms <= source_duration_ms - 200
    assert result.artifact_manifest_path is not None
    run_dir = result.artifact_manifest_path.parent
    assert (run_dir / "01_working_original.wav").is_file()
    assert (run_dir / "04_detection_stderr.txt").is_file()
    assert (run_dir / "04_removed_intervals.json").is_file()
    assert (run_dir / "05_timeline.json").is_file()
    assert (run_dir / "06_filter_complex.ffscript").is_file()
    assert (run_dir / "07_final_output.mp3").is_file()
    filter_script = (run_dir / "06_filter_complex.ffscript").read_text(encoding="utf-8")
    assert "atempo=" not in filter_script
    manifest = json.loads(result.artifact_manifest_path.read_text(encoding="utf-8"))
    assert manifest["operation"] == "silencedetect_pause_removal"
    assert manifest["source"]["filename"] == "long_pause.wav"
    assert manifest["removed_intervals"]
    assert all(segment["kind"] == "normal" for segment in manifest["timeline"])
    render_stage = next(stage for stage in manifest["stages"] if stage["name"] == "render_final_output")
    assert "01_working_original.wav" in render_stage["command"]
    assert "06_filter_complex.ffscript" in render_stage["command"]
