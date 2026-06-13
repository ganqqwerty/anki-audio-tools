"""Tests for Browser batch processing preset operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from anki_audio_quick_editor.audio_operations import OP_PRESET
from anki_audio_quick_editor.audio_processing_preset_runner import (
    ProcessingPresetRunResult,
)
from anki_audio_quick_editor.audio_processing_presets import presets_from_raw
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operations import (
    BatchNoteSnapshot,
    BatchRunRequest,
    process_note_batch_operation,
)


def test_process_note_batch_operation_writes_preset_audio_and_graph_atomically(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    staged_dir = tmp_path / "staged"
    staged_dir.mkdir()
    final_audio = staged_dir / "clip__preset.mp3"
    final_audio.write_bytes(b"preset audio")
    preset = presets_from_raw(
        [
            {
                "id": "clean_graph",
                "name": "Clean + graph",
                "steps": [
                    {
                        "id": "denoise",
                        "operation": "denoise",
                        "parameters": {"denoise_algorithm": "standard"},
                    }
                ],
                "graph": {
                    "enabled": True,
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
    )[0]
    note = BatchNoteSnapshot(
        10,
        "Basic",
        {
            "Audio": "before [sound:clip.mp3] after",
            "Processed": "",
            "Graph": "old",
        },
    )
    writes: list[tuple[str, bytes]] = []

    def fake_run_processing_preset(*_args, **_kwargs) -> ProcessingPresetRunResult:
        return ProcessingPresetRunResult(
            final_audio_path=final_audio,
            final_audio_name="clip__preset.mp3",
            graph_svg=b"<svg></svg>",
            graph_name="clip__preset_viz.svg",
            steps=(),
            changed=True,
        )

    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_processing_presets.run_processing_preset",
        fake_run_processing_preset,
    )

    def media_writer(name: str, data: bytes) -> str:
        writes.append((name, data))
        return name

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(
            operation=OP_PRESET,
            source_field="Audio",
            preset_id="clean_graph",
            preset=preset,
            audio_target_field="Processed",
            graph_target_field="Graph",
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=media_writer,
    )

    assert result.written
    assert result.message == "ran preset Clean + graph"
    assert result.field_updates == {
        "Processed": "before [sound:clip__preset.mp3] after",
        "Graph": 'old<br><img src="clip__preset_viz.svg">',
    }
    assert result.original_field_html == {"Processed": "", "Graph": "old"}
    assert writes == [
        ("clip__preset.mp3", b"preset audio"),
        ("clip__preset_viz.svg", b"<svg></svg>"),
    ]
    assert not staged_dir.exists()


def test_process_note_batch_operation_skips_preset_before_render_when_target_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    preset = presets_from_raw(
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
                    "enabled": False,
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
    )[0]
    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_processing_presets.run_processing_preset",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("preset should not run")),
    )

    result = process_note_batch_operation(
        BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]"}),
        request=BatchRunRequest(
            operation=OP_PRESET,
            source_field="Audio",
            preset_id="clean",
            preset=preset,
            audio_target_field="Processed",
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, _data: name,
    )

    assert result.status == "skipped"
    assert result.message == "missing target field 'Processed'"


def test_process_note_batch_operation_reports_coded_preset_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    preset = presets_from_raw(
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
                    "enabled": False,
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
    )[0]
    captured: list[tuple[tuple[object, ...], dict[str, Any]]] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_processing_presets.run_processing_preset",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(PermissionError("denied")),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_processing_presets.capture_exception",
        lambda *args, **kwargs: captured.append((args, kwargs)),
    )

    result = process_note_batch_operation(
        BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]", "Processed": ""}),
        request=BatchRunRequest(
            operation=OP_PRESET,
            source_field="Audio",
            preset_id="clean",
            preset=preset,
            audio_target_field="Processed",
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, _data: name,
    )

    assert result.status == "failed"
    assert "AQE-AUDIO-001" in result.message
    assert "denied" in result.message
    assert captured
    assert captured[0][0][0] == "browser.batch.note_preset"
    assert captured[0][1]["operation"] == "browser.batch.preset"
    assert captured[0][1]["context"]["preset_id"] == "clean"
