"""Tests for one-note trigger operation execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from anki_audio_quick_editor.audio_operation_params import AudioOperationParameters
from anki_audio_quick_editor.audio_operations import OP_CONVERT, OP_GRAPH
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operation_types import (
    BatchNoteResult,
    BatchNoteSnapshot,
    BatchRunRequest,
)
from anki_audio_quick_editor.trigger_batch_adapter import process_trigger_operation
from anki_audio_quick_editor.trigger_rules import (
    AudioTriggerGraphParameters,
    AudioTriggerRule,
    TriggerNoteTypeRef,
)


def _operation_rule(
    operation: str,
    *,
    target_field: str | None = None,
    parameters: AudioOperationParameters | None = None,
    graph_parameters: AudioTriggerGraphParameters | None = None,
) -> AudioTriggerRule:
    return AudioTriggerRule(
        id="trigger-op",
        name="Trigger op",
        enabled=True,
        event="add",
        note_type=TriggerNoteTypeRef(id=123, name="Basic"),
        source_field="Audio",
        action_type="operation",
        operation=operation,
        preset_id=None,
        target_field=target_field,
        parameters=parameters or AudioOperationParameters(),
        graph_parameters=graph_parameters or AudioTriggerGraphParameters(),
    )


def test_graph_trigger_replaces_target_field(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    writes: list[tuple[str, bytes]] = []
    seen_config: list[AudioProcessingConfig] = []

    def fake_analyze(_source_path: Path, config: AudioProcessingConfig) -> object:
        seen_config.append(config)
        return object()

    monkeypatch.setattr(
        "anki_audio_quick_editor.trigger_batch_adapter.analyze_prosody_cached",
        fake_analyze,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_operation_processing.render_prosody_svg",
        lambda _track: b"<svg></svg>",
    )

    def media_writer(name: str, data: bytes) -> str:
        writes.append((name, data))
        return name

    result = process_trigger_operation(
        BatchNoteSnapshot(
            10,
            "Basic",
            {"Audio": "before [sound:clip.mp3] after", "Graph": "old graph"},
        ),
        rule=_operation_rule(
            OP_GRAPH,
            target_field="Graph",
            graph_parameters=AudioTriggerGraphParameters(
                graph_voice_range="high",
                graph_smoothness="raw",
            ),
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(graph_voice_range="general"),
        media_writer=media_writer,
    )

    assert result.written
    assert result.target_field == "Graph"
    assert result.target_html == f'<img src="{result.written_filename}">'
    assert result.original_target_html == "old graph"
    assert writes == [(result.written_filename, b"<svg></svg>")]
    assert seen_config[0].graph_voice_range == "high"
    assert seen_config[0].graph_smoothness == "raw"


def test_transform_trigger_reuses_batch_operation_request(tmp_path: Path, monkeypatch) -> None:
    captured: list[tuple[BatchRunRequest, Path, AudioProcessingConfig]] = []

    def fake_process_note_batch_operation(
        _note: BatchNoteSnapshot,
        *,
        request: BatchRunRequest,
        media_dir: Path,
        config: AudioProcessingConfig,
        **_kwargs: Any,
    ) -> BatchNoteResult:
        captured.append((request, media_dir, config))
        return BatchNoteResult(
            note_id=10,
            status="written",
            message="replaced audio",
            target_field="Audio",
            target_html="[sound:clip.flac]",
            written_filename="clip.flac",
        )

    monkeypatch.setattr(
        "anki_audio_quick_editor.trigger_batch_adapter.process_note_batch_operation",
        fake_process_note_batch_operation,
    )

    result = process_trigger_operation(
        BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.wav]"}),
        rule=_operation_rule(
            OP_CONVERT,
            parameters=AudioOperationParameters(target_format="flac"),
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(output_format="mp3"),
        media_writer=lambda name, _data: name,
    )

    assert result.written
    request, media_dir, config = captured[0]
    assert request.operation == OP_CONVERT
    assert request.source_field == "Audio"
    assert request.parameters.target_format == "flac"
    assert request.target_field is None
    assert media_dir == tmp_path
    assert config.output_format == "mp3"


def test_graph_trigger_skips_when_target_field_missing(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")

    result = process_trigger_operation(
        BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]"}),
        rule=_operation_rule(OP_GRAPH, target_field="Graph"),
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, _data: name,
    )

    assert result.status == "skipped"
    assert result.message == "missing target field 'Graph'"
