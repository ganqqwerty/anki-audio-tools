"""Operation-matrix coverage for automatic trigger actions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from anki_audio_quick_editor.audio_operations import TRANSFORM_OPERATIONS
from anki_audio_quick_editor.audio_processing_presets import presets_from_raw
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operation_types import (
    BatchNoteResult,
    BatchNoteSnapshot,
    BatchRunRequest,
)
from anki_audio_quick_editor.trigger_batch_adapter import process_trigger_operation
from anki_audio_quick_editor.trigger_rules import trigger_rules_from_raw
from anki_audio_quick_editor.trigger_scheduler import _matching_jobs
from anki_audio_quick_editor.trigger_state import TriggerStateStore


@pytest.mark.parametrize("operation", TRANSFORM_OPERATIONS)
def test_each_transform_action_routes_through_the_one_note_batch_core(
    operation: str,
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: list[BatchRunRequest] = []

    def fake_process(
        _note: BatchNoteSnapshot,
        *,
        request: BatchRunRequest,
        **_kwargs: Any,
    ) -> BatchNoteResult:
        captured.append(request)
        return BatchNoteResult(10, "skipped", "handled", audio_filename="clip.wav")

    monkeypatch.setattr(
        "anki_audio_quick_editor.trigger_batch_adapter.process_note_batch_operation",
        fake_process,
    )
    rule = trigger_rules_from_raw(
        [
            {
                "id": f"trigger-{operation}",
                "name": operation,
                "enabled": True,
                "event": "edit",
                "note_type": {"id": 123, "name": "Basic"},
                "source_field": "Audio",
                "action_type": "operation",
                "operation": operation,
                "preset_id": None,
                "target_field": None,
                "parameters": {},
            }
        ]
    )[0]

    result = process_trigger_operation(
        BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.wav]"}),
        rule=rule,
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, _data: name,
    )

    assert result.status == "skipped"
    assert [request.operation for request in captured] == [operation]


def test_missing_preset_rule_does_not_block_other_matching_actions(tmp_path: Path) -> None:
    presets = presets_from_raw(
        [
            {
                "id": "available",
                "name": "Available",
                "steps": [
                    {
                        "id": "faster",
                        "operation": "faster",
                        "parameters": {"speed_step": 1.5},
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
    )
    base = {
        "enabled": True,
        "event": "edit",
        "note_type": {"id": 123, "name": "Basic"},
        "source_field": "Audio",
        "target_field": None,
        "parameters": {},
    }
    rules = trigger_rules_from_raw(
        [
            {
                **base,
                "id": "missing-preset",
                "name": "Missing preset",
                "action_type": "preset",
                "operation": None,
                "preset_id": "deleted",
            },
            {
                **base,
                "id": "convert",
                "name": "Convert",
                "action_type": "operation",
                "operation": "convert",
                "preset_id": None,
            },
        ],
        presets=presets,
        allow_missing_presets=True,
    )

    jobs = _matching_jobs(
        rules,
        event="edit",
        note_id=10,
        note_type_id=123,
        note_type_name="Basic",
        fields={"Audio": "[sound:clip.wav]"},
        presets=presets,
        store=TriggerStateStore.load(tmp_path / "state.json"),
        state_path=tmp_path / "state.json",
    )

    assert [job.rule.id for job in jobs] == ["convert"]
