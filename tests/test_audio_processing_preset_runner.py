"""Tests for shared processing preset execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from anki_audio_quick_editor.audio_processing_preset_runner import (
    ProcessingPresetRunnerAdapters,
    run_processing_preset,
)
from anki_audio_quick_editor.audio_processing_presets import presets_from_raw
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig


def _graph(enabled: bool = False) -> dict[str, object]:
    return {
        "enabled": enabled,
        "parameters": {
            "graph_voice_range": "general",
            "graph_recording_condition": "auto",
            "graph_smoothness": "very_smooth",
            "graph_connect_short_dropouts_ms": 240,
            "graph_voice_lock": "balanced",
        },
    }


class FakeAdapters:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.calls: list[tuple[str, str, str]] = []
        self.paths: list[Path] = []

    def make_audio_output_filename(
        self,
        source_filename: str,
        *,
        output_format: str | None = None,
    ) -> str:
        stem = Path(source_filename).stem
        suffix = output_format if output_format and output_format != "source" else "mp3"
        return f"{stem}.preset.{suffix}"

    def make_graph_output_filename(self, source_filename: str) -> str:
        return f"{Path(source_filename).stem}.svg"

    def temp_output_path(self, desired_name: str) -> Path:
        directory = self.tmp_path / f"tmp-{len(self.paths)}"
        directory.mkdir()
        path = directory / desired_name
        self.paths.append(path)
        return path

    def render_audio(
        self,
        source_path: Path,
        state: AudioEditState,
        _config: AudioProcessingConfig,
        output_path: Path,
        _artifact_root: Path | None,
    ) -> None:
        self.calls.append(("audio", source_path.name, state.source_file))
        output_path.write_bytes(b"audio")

    def render_converted_audio(
        self,
        source_path: Path,
        _config: AudioProcessingConfig,
        target_format: str,
        output_path: Path,
    ) -> None:
        self.calls.append(("convert", source_path.name, target_format))
        output_path.write_bytes(b"converted")

    def render_denoise_audio(
        self,
        source_path: Path,
        config: AudioProcessingConfig,
        output_path: Path,
    ) -> None:
        self.calls.append(("denoise", source_path.name, config.denoise_algorithm))
        output_path.write_bytes(b"denoised")

    def render_size_reduced_audio(
        self,
        source_path: Path,
        config: AudioProcessingConfig,
        output_path: Path,
    ) -> None:
        self.calls.append(("reduce_size", source_path.name, config.size_reduction_mode))
        output_path.write_bytes(b"smaller")

    def analyze_prosody(self, source_path: Path, config: AudioProcessingConfig) -> dict[str, Any]:
        self.calls.append(("graph", source_path.name, config.graph_voice_range))
        return {"source": source_path.name}

    def render_graph_svg(self, track: object) -> bytes:
        return f"<svg>{track}</svg>".encode()

    def as_adapters(self) -> ProcessingPresetRunnerAdapters:
        return ProcessingPresetRunnerAdapters(
            make_audio_output_filename=self.make_audio_output_filename,
            make_graph_output_filename=self.make_graph_output_filename,
            temp_output_path=self.temp_output_path,
            render_audio=self.render_audio,
            render_converted_audio=self.render_converted_audio,
            render_size_reduced_audio=self.render_size_reduced_audio,
            render_denoise_audio=self.render_denoise_audio,
            analyze_prosody=self.analyze_prosody,
            render_graph_svg=self.render_graph_svg,
        )


def _preset(raw: dict[str, object]):
    return presets_from_raw([raw])[0]


def test_run_processing_preset_executes_steps_in_order_and_keeps_final_output(
    tmp_path: Path,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"source")
    adapters = FakeAdapters(tmp_path)
    preset = _preset(
        {
            "id": "clean",
            "name": "Clean",
            "steps": [
                {"id": "denoise", "operation": "denoise", "parameters": {"denoise_algorithm": "rnnoise"}},
                {"id": "faster", "operation": "faster", "parameters": {"speed_step": 1.25}},
            ],
            "graph": _graph(False),
        }
    )

    result = run_processing_preset(
        preset,
        source_path=source,
        source_filename="clip.mp3",
        config=AudioProcessingConfig(),
        adapters=adapters.as_adapters(),
    )

    assert [call[0] for call in adapters.calls] == ["denoise", "audio"]
    assert result.final_audio_path is not None
    assert result.final_audio_path.exists()
    assert result.final_audio_name == "clip.preset.mp3"
    assert [path.name for path in adapters.paths] == ["clip.preset.mp3", "clip.preset.mp3"]
    assert result.graph_svg is None
    assert [step.status for step in result.steps] == ["rendered", "rendered"]
    assert adapters.paths[0].parent.exists() is False
    assert adapters.paths[1].parent.exists() is True


def test_run_processing_preset_skips_same_format_convert_and_reports_noop(
    tmp_path: Path,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"source")
    adapters = FakeAdapters(tmp_path)
    preset = _preset(
        {
            "id": "convert",
            "name": "Convert",
            "steps": [
                {"id": "convert", "operation": "convert", "parameters": {"target_format": "mp3"}},
            ],
            "graph": _graph(False),
        }
    )

    result = run_processing_preset(
        preset,
        source_path=source,
        source_filename="clip.mp3",
        config=AudioProcessingConfig(),
        adapters=adapters.as_adapters(),
    )

    assert adapters.calls == []
    assert result.changed is False
    assert result.final_audio_path is None
    assert result.steps[0].status == "skipped"


def test_run_processing_preset_size_reduction_outputs_mp3(tmp_path: Path) -> None:
    source = tmp_path / "clip.wav"
    source.write_bytes(b"source")
    adapters = FakeAdapters(tmp_path)
    preset = _preset(
        {
            "id": "smaller",
            "name": "Smaller",
            "steps": [
                {
                    "id": "reduce",
                    "operation": "reduce_size",
                    "parameters": {"size_reduction_mode": "aggressive"},
                },
            ],
            "graph": _graph(False),
        }
    )

    result = run_processing_preset(
        preset,
        source_path=source,
        source_filename="clip.wav",
        config=AudioProcessingConfig(size_reduction_mode="normal"),
        adapters=adapters.as_adapters(),
    )

    assert adapters.calls == [("reduce_size", "clip.wav", "aggressive")]
    assert result.final_audio_name == "clip.preset.mp3"
    assert result.final_audio_path is not None
    assert result.final_audio_path.read_bytes() == b"smaller"
    assert result.steps[0].message == "rendered clip.preset.mp3"


def test_run_processing_preset_graph_uses_final_audio(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"source")
    adapters = FakeAdapters(tmp_path)
    preset = _preset(
        {
            "id": "graph",
            "name": "Graph",
            "steps": [
                {"id": "convert", "operation": "convert", "parameters": {"target_format": "wav"}},
            ],
            "graph": _graph(True),
        }
    )

    result = run_processing_preset(
        preset,
        source_path=source,
        source_filename="clip.mp3",
        config=AudioProcessingConfig(graph_voice_range="high"),
        adapters=adapters.as_adapters(),
    )

    assert [call[0] for call in adapters.calls] == ["convert", "graph"]
    assert adapters.calls[-1] == ("graph", "clip.preset.wav", "general")
    assert result.graph_svg is not None
    assert result.graph_name == "clip.preset.svg"
    assert result.changed is True


def test_run_processing_preset_can_defer_graph_rendering(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"source")
    adapters = FakeAdapters(tmp_path)
    preset = _preset(
        {
            "id": "graph",
            "name": "Graph",
            "steps": [],
            "graph": _graph(True),
        }
    )

    result = run_processing_preset(
        preset,
        source_path=source,
        source_filename="clip.mp3",
        config=AudioProcessingConfig(graph_voice_range="high"),
        adapters=adapters.as_adapters(),
        render_graph=False,
    )

    assert adapters.calls == []
    assert result.graph_svg is None
    assert result.graph_name is None
    assert result.changed is False


def test_run_processing_preset_cleans_outputs_when_later_step_fails(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"source")
    adapters = FakeAdapters(tmp_path)

    def fail_render_audio(
        _source_path: Path,
        _state: AudioEditState,
        _config: AudioProcessingConfig,
        _output_path: Path,
        _artifact_root: Path | None,
    ) -> None:
        raise RuntimeError("render failed")

    preset = _preset(
        {
            "id": "fail",
            "name": "Fail",
            "steps": [
                {"id": "denoise", "operation": "denoise", "parameters": {}},
                {"id": "faster", "operation": "faster", "parameters": {}},
            ],
            "graph": _graph(False),
        }
    )
    adapter_bundle = adapters.as_adapters()
    adapter_bundle = ProcessingPresetRunnerAdapters(
        **{
            **adapter_bundle.__dict__,
            "render_audio": fail_render_audio,
        }
    )

    with pytest.raises(RuntimeError, match="render failed"):
        run_processing_preset(
            preset,
            source_path=source,
            source_filename="clip.mp3",
            config=AudioProcessingConfig(),
            adapters=adapter_bundle,
        )

    assert all(path.parent.exists() is False for path in adapters.paths)
