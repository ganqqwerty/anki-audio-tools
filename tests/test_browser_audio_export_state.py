from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.audio_export_types import (
    EXPORT_MODE_COMBINED_MP3,
    AudioExportFieldSelection,
    AudioExportReport,
)
from anki_audio_quick_editor.batch_operation_types import BatchNoteSnapshot, FieldGroup
from anki_audio_quick_editor.browser_audio_export_state import (
    audio_export_finish_payload,
    audio_export_progress_payload,
    build_audio_export_initial_state,
    request_from_audio_export_start_payload,
)

DESTINATION_ERROR = "Choose a destination before starting."


def test_build_audio_export_initial_state_contains_defaults_fields_and_i18n() -> None:
    state = build_audio_export_initial_state(
        note_count=2,
        groups=(FieldGroup("Basic", ("Front", "Back", "Audio")),),
        snapshots=(
            BatchNoteSnapshot(1, "Basic", {"Front": "[sound:front.mp3]", "Back": "text"}),
            BatchNoteSnapshot(2, "Basic", {"Front": "text", "Audio": "[sound:audio.wav]"}),
        ),
    )

    assert state["surface"] == "audio_export"
    assert state["note_count"] == 2
    assert state["field_groups"] == [
        {"notetype_name": "Basic", "fields": ["Front", "Back", "Audio"]}
    ]
    assert state["default_field_selections"] == [
        {"notetype_name": "Basic", "fields": ["Front", "Audio"]}
    ]
    assert state["defaults"] == {
        "mode": "zip",
        "silence_between_clips_seconds": 1.0,
        "normalize_volume": False,
    }
    assert state["locale"] == "en"
    assert state["direction"] == "ltr"
    assert "audio_export.start" in state["messages"]


def test_request_from_audio_export_start_payload_decodes_combined_mp3_request() -> None:
    request = request_from_audio_export_start_payload(
        {
            "mode": "combined_mp3",
            "destination_path": "/tmp/export.mp3",
            "field_selections": [
                {"notetype_name": "Basic", "fields": ["Front", "Audio"]},
                {"notetype_name": "Cloze", "fields": ["Text"]},
            ],
            "silence_between_clips_seconds": 1.5,
            "normalize_volume": True,
        }
    )

    assert request.mode == EXPORT_MODE_COMBINED_MP3
    assert request.destination_path == Path("/tmp/export.mp3")
    assert request.field_selections == (
        AudioExportFieldSelection("Basic", ("Front", "Audio")),
        AudioExportFieldSelection("Cloze", ("Text",)),
    )
    assert request.silence_between_clips_seconds == 1.5
    assert request.normalize_volume is True


def test_request_from_audio_export_start_payload_rejects_invalid_silence() -> None:
    try:
        request_from_audio_export_start_payload(
            {
                "mode": "zip",
                "destination_path": "/tmp/export.zip",
                "field_selections": [{"notetype_name": "Basic", "fields": ["Audio"]}],
                "silence_between_clips_seconds": 10.1,
                "normalize_volume": False,
            }
        )
    except ValueError as exc:
        assert str(exc) == "Silence between clips must be between 0 and 10 seconds."
    else:
        raise AssertionError("expected invalid silence to fail")


def test_request_from_audio_export_start_payload_rejects_blank_destination() -> None:
    for destination_path in ("   ", "."):
        try:
            request_from_audio_export_start_payload(
                {
                    "mode": "zip",
                    "destination_path": destination_path,
                    "field_selections": [{"notetype_name": "Basic", "fields": ["Audio"]}],
                    "silence_between_clips_seconds": 1.0,
                    "normalize_volume": False,
                }
            )
        except ValueError as exc:
            assert str(exc) == DESTINATION_ERROR
        else:
            raise AssertionError(f"expected destination {destination_path!r} to fail")


def test_request_from_audio_export_start_payload_requires_normalize_volume() -> None:
    try:
        request_from_audio_export_start_payload(
            {
                "mode": "zip",
                "destination_path": "/tmp/export.zip",
                "field_selections": [{"notetype_name": "Basic", "fields": ["Audio"]}],
                "silence_between_clips_seconds": 1.0,
            }
        )
    except ValueError as exc:
        assert str(exc) == "Choose an export mode before starting."
    else:
        raise AssertionError("expected missing normalize_volume to fail generated contract decoding")


def test_progress_and_finish_payloads_match_frontend_contract() -> None:
    progress = audio_export_progress_payload(
        processed=1,
        total=3,
        current_audio="clip.mp3",
        failures=0,
        message="Exported 1/3 audio files. Current audio: clip.mp3. Failures: 0.",
    )
    report = AudioExportReport(
        total=3,
        processed=2,
        exported=1,
        skipped=1,
        failures=0,
        output_path="/tmp/export.zip",
    )
    finish = audio_export_finish_payload(report)

    assert progress == {
        "processed": 1,
        "total": 3,
        "current_audio": "clip.mp3",
        "failures": 0,
        "message": "Exported 1/3 audio files. Current audio: clip.mp3. Failures: 0.",
    }
    assert finish == {
        "processed": 2,
        "total": 3,
        "exported": 1,
        "skipped": 1,
        "failures": 0,
        "canceled": False,
        "output_path": "/tmp/export.zip",
        "summary": report.summary,
    }


def test_audio_export_report_summary_uses_messages_when_available() -> None:
    completed = AudioExportReport(
        total=3,
        processed=3,
        exported=2,
        skipped=1,
        failures=0,
        output_path="/tmp/export.zip",
        messages={
            "audio_export.completed": (
                "Done exported={exported} skipped={skipped} "
                "failures={failures} output={output}"
            )
        },
    )
    canceled = AudioExportReport(
        total=5,
        processed=3,
        exported=2,
        skipped=1,
        failures=1,
        canceled=True,
        messages={
            "audio_export.canceled": (
                "Stopped processed={processed}/{total} exported={exported} "
                "skipped={skipped} failures={failures}"
            )
        },
    )

    assert completed.summary == "Done exported=2 skipped=1 failures=0 output=/tmp/export.zip"
    assert canceled.summary == "Stopped processed=3/5 exported=2 skipped=1 failures=1"
