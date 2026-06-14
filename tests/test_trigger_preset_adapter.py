"""Tests for trigger processing preset execution."""

from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.audio_operation_params import AudioOperationParameters
from anki_audio_quick_editor.audio_processing_preset_runner import (
    ProcessingPresetRunResult,
)
from anki_audio_quick_editor.audio_processing_presets import presets_from_raw
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operation_types import BatchNoteSnapshot
from anki_audio_quick_editor.trigger_preset_adapter import process_trigger_preset
from anki_audio_quick_editor.trigger_rules import (
    AudioTriggerGraphParameters,
    AudioTriggerRule,
    TriggerNoteTypeRef,
)


def _rule(target_field: str | None = None) -> AudioTriggerRule:
    return AudioTriggerRule(
        id="trigger-preset",
        name="Trigger preset",
        enabled=True,
        event="add",
        note_type=TriggerNoteTypeRef(id=123, name="Basic"),
        source_field="Audio",
        action_type="preset",
        operation=None,
        preset_id="clean",
        target_field=target_field,
        parameters=AudioOperationParameters(),
        graph_parameters=AudioTriggerGraphParameters(),
    )


def _preset(*, graph: bool = False):
    return presets_from_raw(
        [
            {
                "id": "clean",
                "name": "Clean",
                "steps": [
                    {
                        "id": "denoise",
                        "operation": "denoise",
                        "parameters": {"denoise_algorithm": "standard"},
                    }
                ],
                "graph": {
                    "enabled": graph,
                    "parameters": {
                        "graph_voice_range": "general",
                        "graph_recording_condition": "auto",
                        "graph_smoothness": "very_smooth",
                        "graph_connect_short_dropouts_ms": 240,
                        "graph_voice_lock": "balanced",
                    },
                },
            }
        ]
    )


def test_preset_trigger_replaces_source_audio(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    staged = tmp_path / "staged"
    staged.mkdir()
    final_audio = staged / "clip__clean.mp3"
    final_audio.write_bytes(b"clean")
    writes: list[tuple[str, bytes]] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_processing_presets.run_processing_preset",
        lambda *_args, **_kwargs: ProcessingPresetRunResult(
            final_audio_path=final_audio,
            final_audio_name="clip__clean.mp3",
            graph_svg=None,
            graph_name=None,
            steps=(),
            changed=True,
        ),
    )

    result = process_trigger_preset(
        BatchNoteSnapshot(10, "Basic", {"Audio": "before [sound:clip.mp3] after"}),
        rule=_rule(),
        presets=_preset(),
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, data: writes.append((name, data)) or name,
    )

    assert result.written
    assert result.field_updates == {"Audio": "before [sound:clip__clean.mp3] after"}
    assert result.original_field_html == {"Audio": "before [sound:clip.mp3] after"}
    assert result.written_filename == "clip__clean.mp3"
    assert writes == [("clip__clean.mp3", b"clean")]
    assert not staged.exists()


def test_preset_trigger_replaces_graph_target_field(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    writes: list[tuple[str, bytes]] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_processing_presets.run_processing_preset",
        lambda *_args, **_kwargs: ProcessingPresetRunResult(
            final_audio_path=None,
            final_audio_name=None,
            graph_svg=b"<svg></svg>",
            graph_name="clip_graph.svg",
            steps=(),
            changed=True,
        ),
    )

    result = process_trigger_preset(
        BatchNoteSnapshot(
            10,
            "Basic",
            {"Audio": "[sound:clip.mp3]", "Graph": "old graph"},
        ),
        rule=_rule(target_field="Graph"),
        presets=_preset(graph=True),
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, data: writes.append((name, data)) or name,
    )

    assert result.written
    assert result.field_updates == {"Graph": '<img src="clip_graph.svg">'}
    assert result.original_field_html == {"Graph": "old graph"}
    assert result.written_filename == "clip_graph.svg"
    assert writes == [("clip_graph.svg", b"<svg></svg>")]


def test_preset_trigger_skips_missing_preset(tmp_path: Path) -> None:
    result = process_trigger_preset(
        BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]"}),
        rule=_rule(),
        presets=(),
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, _data: name,
    )

    assert result.status == "skipped"
    assert result.message == "missing preset 'clean'"
