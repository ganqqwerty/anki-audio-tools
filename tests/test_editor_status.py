"""Tests for user-facing editor status summaries."""

from __future__ import annotations

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_actions import (
    CMD_DENOISE_STANDARD,
    CMD_DPDFNET,
    CMD_FASTER,
    CMD_PITCH_HUM,
    CMD_REMOVE_PAUSES,
    CMD_RNNOISE,
    CMD_SLOWER,
    CMD_VOICE_ONLY,
    CMD_VOLUME_DOWN,
    CMD_VOLUME_UP,
    EditorCommandOverrides,
    EditorCommandPayload,
)
from anki_audio_quick_editor.editor_session import RegionDeleteRequest, UndoEntry
from anki_audio_quick_editor.editor_status import (
    command_status_summary,
    original_audio_status_summary,
    redo_status_message,
    region_operation_status_summary,
    restored_status_summary,
    undo_status_message,
)


def test_original_audio_status_summary() -> None:
    assert original_audio_status_summary() == "Original audio."


def test_processing_status_summaries_include_operation_parameters() -> None:
    config = AudioProcessingConfig(
        denoise_algorithm="standard",
        dpdfnet_attn_limit_db=12,
        output_format="mp3",
        pause_aggressiveness="normal",
        pitch_hum_mode="direct",
        speed_step=0.05,
        volume_step_db=3,
    )

    assert command_status_summary(CMD_VOLUME_UP, config) == "Increased volume by 3 dB."
    assert command_status_summary(CMD_VOLUME_DOWN, config) == "Decreased volume by 3 dB."
    assert command_status_summary(CMD_FASTER, config) == "Increased speed to x1.05."
    assert command_status_summary(CMD_SLOWER, config) == "Decreased speed to x0.95."
    assert command_status_summary(CMD_REMOVE_PAUSES, config) == "Shortened pauses with Normal level."
    assert command_status_summary(
        EditorCommandPayload(
            command="aqe:convert",
            overrides=EditorCommandOverrides(target_format="flac"),
        ),
        config,
    ) == "Converted audio to FLAC."
    assert command_status_summary(CMD_DENOISE_STANDARD, config) == "Cleaned audio with Standard."
    assert command_status_summary(CMD_RNNOISE, config) == "Cleaned audio with RNNoise."
    assert command_status_summary(CMD_VOICE_ONLY, config) == "Cleaned audio with Voice Only."
    assert command_status_summary(
        EditorCommandPayload(
            command=CMD_DPDFNET,
            overrides=EditorCommandOverrides(dpdfnet_attn_limit_db=18),
        ),
        config,
    ) == "Cleaned audio with DPDFNet at Aggressive aggressiveness."
    assert command_status_summary(
        EditorCommandPayload(
            command=CMD_PITCH_HUM,
            overrides=EditorCommandOverrides(pitch_hum_mode="pitch_tier"),
        ),
        config,
    ) == "Rendered pitch hum with PitchTier mode."


def test_region_operation_status_summaries_include_selected_range() -> None:
    delete_selection = RegionDeleteRequest(
        field_index=0,
        source_filename="clip.wav",
        selection_start_ms=500,
        selection_end_ms=1250,
        cursor_ms=0,
        duration_ms=2000,
        trigger="button",
        playback_active=False,
        operation="delete-selection",
    )
    delete_rest = RegionDeleteRequest(
        field_index=0,
        source_filename="clip.wav",
        selection_start_ms=500,
        selection_end_ms=1250,
        cursor_ms=0,
        duration_ms=2000,
        trigger="button",
        playback_active=False,
        operation="delete-rest",
    )

    assert region_operation_status_summary(delete_selection) == "Deleted selection 500-1250 ms."
    assert region_operation_status_summary(delete_rest) == "Kept only selection 500-1250 ms."


def test_undo_and_redo_status_messages_use_stored_summaries() -> None:
    entry = UndoEntry(
        state=AudioEditState("clip.wav", speed=1.1),
        filename="clip__aqe_1.mp3",
        status_summary="Increased speed to x1.10.",
    )

    assert restored_status_summary(entry) == "Increased speed to x1.10."
    assert undo_status_message(entry) == "Undid: Increased speed to x1.10."
    assert redo_status_message(entry) == "Redid: Increased speed to x1.10."


def test_restored_status_summary_falls_back_to_original_audio_or_filename() -> None:
    original_entry = UndoEntry(state=AudioEditState("clip.wav"), filename="clip.wav")
    generated_entry = UndoEntry(
        state=AudioEditState("clip.wav", volume_db=3),
        filename="clip__aqe_1.mp3",
    )

    assert restored_status_summary(original_entry) == "Original audio."
    assert restored_status_summary(generated_entry) == "clip__aqe_1.mp3"
