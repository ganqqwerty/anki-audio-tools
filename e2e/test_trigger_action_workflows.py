"""Real-Anki coverage for edit and preset trigger action paths."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PyQt6.QtTest import QTest

from e2e.conftest import ADDON_NUMERIC_ID, import_runtime_addon_module
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
)
from e2e.helpers import generate_tone, wait_for_condition
from e2e.test_trigger_automation import (
    _add_audio_note_through_add_cards_ui,
    _wait_for_triggered_audio,
)


def test_editor_edit_trigger_converts_once_across_later_text_edits(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "trigger_edit_convert_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.5)
    rule_id = "e2e-edit-convert"
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        audio_trigger_rules=[
            _trigger_rule(
                anki_mw,
                rule_id=rule_id,
                event="edit",
                action_type="operation",
                operation="convert",
                parameters={"target_format": "mp3"},
            )
        ],
        output_format="mp3",
    )
    note = _basic_audio_note(anki_mw, source.name)

    editor, parent = _open_editor(anki_mw, note)
    try:
        editor.note["Back"] = "First text edit"
        editor._save_current_note()
        generated_name = _wait_for_triggered_audio(
            anki_mw,
            int(note.id),
            media_dir,
            previous_name=source.name,
        )
        wait_for_condition(
            lambda: _trigger_state_entry(anki_mw, int(note.id), rule_id).status == "succeeded",
            timeout=10.0,
            message="Edit trigger did not persist its successful completion state",
        )
        first_entry = _trigger_state_entry(anki_mw, int(note.id), rule_id)
        first_token = first_entry.generation_token
        assert first_entry.last_handled_field_filename == generated_name

        editor.set_note(anki_mw.col.get_note(note.id), hide=False, focusTo=1)
        editor.note["Back"] = "Second text edit"
        editor._save_current_note()
        wait_for_condition(
            lambda: anki_mw.col.get_note(note.id)["Back"] == "Second text edit",
            timeout=10.0,
            message="Editor did not persist the second text-only edit",
        )
        QTest.qWait(750)

        persisted = anki_mw.col.get_note(note.id)
        second_entry = _trigger_state_entry(anki_mw, int(note.id), rule_id)
        assert _sound_filename(persisted["Front"]) == generated_name
        assert second_entry.generation_token == first_token
    finally:
        editor.set_note(None)
        parent.close()


@pytest.mark.allow_native_playback("stop")
def test_add_trigger_runs_graph_only_preset_and_replaces_target(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "trigger_add_preset_graph_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.6)
    preset_id = "e2e-graph-preset"
    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        audio_processing_presets=[
            {
                "id": preset_id,
                "name": "E2E Graph",
                "steps": [],
                "graph": {
                    "enabled": True,
                    "parameters": _graph_parameters(),
                },
            }
        ],
        audio_trigger_rules=[
            _trigger_rule(
                anki_mw,
                rule_id="e2e-add-preset-graph",
                event="add",
                action_type="preset",
                preset_id=preset_id,
                target_field="Back",
            )
        ],
    )

    note_id = _add_audio_note_through_add_cards_ui(anki_mw, source.name)
    generated: dict[str, str] = {}

    def graph_written() -> bool:
        note = anki_mw.col.get_note(note_id)
        match = re.fullmatch(r'<img src="([^"]+\.svg)">', note["Back"])
        if match is None:
            return False
        generated["filename"] = match.group(1)
        return (media_dir / match.group(1)).is_file()

    wait_for_condition(
        graph_written,
        timeout=60.0,
        message="Preset trigger did not replace the Graph target field",
    )
    persisted = anki_mw.col.get_note(note_id)
    assert _sound_filename(persisted["Front"]) == source.name
    assert "<svg" in (media_dir / generated["filename"]).read_text(encoding="utf-8")


def _trigger_rule(
    anki_mw,
    *,
    rule_id: str,
    event: str,
    action_type: str,
    operation: str | None = None,
    preset_id: str | None = None,
    target_field: str | None = None,
    parameters: dict[str, object] | None = None,
) -> dict[str, object]:
    notetype = anki_mw.col.models.by_name("Basic")
    assert notetype is not None
    return {
        "id": rule_id,
        "name": rule_id,
        "enabled": True,
        "event": event,
        "note_type": {"id": int(notetype["id"]), "name": "Basic"},
        "source_field": "Front",
        "action_type": action_type,
        "operation": operation,
        "preset_id": preset_id,
        "target_field": target_field,
        "parameters": parameters or {},
    }


def _graph_parameters() -> dict[str, object]:
    return {
        "graph_voice_range": "general",
        "graph_recording_condition": "auto",
        "graph_smoothness": "very_smooth",
        "graph_connect_short_dropouts_ms": 240,
        "graph_voice_lock": "balanced",
    }


def _trigger_state_entry(anki_mw, note_id: int, rule_id: str):
    scheduler = import_runtime_addon_module(".trigger_scheduler")
    state = import_runtime_addon_module(".trigger_state")
    addon_dir = Path(anki_mw.addonManager.addonsFolder(ADDON_NUMERIC_ID))
    state_path = state.collection_state_path(
        addon_dir,
        scheduler._collection_identity(anki_mw.col),
    )
    key = state.TriggerStateKey(note_id=note_id, rule_id=rule_id, source_field="Front")
    entry = state.TriggerStateStore.load(state_path).get(key)
    assert entry is not None
    return entry
