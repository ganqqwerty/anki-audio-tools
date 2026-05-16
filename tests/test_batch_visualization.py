"""Tests for import-safe batch visualization core behavior."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_visualization import (
    BatchNoteSnapshot,
    append_image_reference,
    field_groups_for_notes,
    process_note_visualization,
    unique_note_ids,
)
from anki_audio_quick_editor.prosody_types import ProsodyPoint, ProsodyTrack


def test_unique_note_ids_preserves_first_seen_order() -> None:
    assert unique_note_ids([3, 2, 3, 1, 2]) == [3, 2, 1]


def test_field_groups_preserve_fields_by_note_type() -> None:
    groups = field_groups_for_notes(
        [
            BatchNoteSnapshot(1, "Basic", {"Front": "", "Audio": ""}),
            BatchNoteSnapshot(2, "Basic", {"Back": "", "Audio": ""}),
            BatchNoteSnapshot(3, "Cloze", {"Text": "", "Audio": ""}),
        ]
    )

    assert groups[0].notetype_name == "Basic"
    assert groups[0].fields == ("Front", "Audio", "Back")
    assert groups[1].notetype_name == "Cloze"
    assert groups[1].fields == ("Text", "Audio")


def test_append_image_reference_uses_new_line_media_tag() -> None:
    assert append_image_reference("existing", "viz.svg") == 'existing<br><img src="viz.svg">'
    assert append_image_reference("", "viz.svg") == '<img src="viz.svg">'


def test_process_note_visualization_appends_generated_media(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]", "Image": "old"})
    track = ProsodyTrack(
        duration_ms=100,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True), ProsodyPoint(100, 230.0, -19.0, 0.6, True)),
        pitch_min_hz=220.0,
        pitch_max_hz=230.0,
        source_filename="clip.mp3",
        analyzer_name="test",
    )
    writes: list[tuple[str, bytes]] = []

    monkeypatch.setattr("anki_audio_quick_editor.batch_visualization.analyze_prosody_cached", lambda *_args: track)

    def media_writer(name: str, data: bytes) -> str:
        writes.append((name, data))
        return name

    result = process_note_visualization(
        note,
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=media_writer,
        now_provider=lambda: datetime(2026, 5, 16, 1, 2, 3, 456000),
    )

    assert result.written
    assert result.audio_filename == "clip.mp3"
    assert result.image_filename == "clip__aqe_viz_20260516_010203_456000.svg"
    assert result.target_html == 'old<br><img src="clip__aqe_viz_20260516_010203_456000.svg">'
    assert writes[0][0] == result.image_filename
    assert writes[0][1].startswith(b"<svg ")


def test_process_note_visualization_skips_expected_missing_inputs(tmp_path: Path) -> None:
    writer = lambda name, data: name
    config = AudioProcessingConfig()

    missing_source = process_note_visualization(
        BatchNoteSnapshot(1, "Basic", {"Image": ""}),
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=config,
        media_writer=writer,
    )
    empty_source = process_note_visualization(
        BatchNoteSnapshot(2, "Basic", {"Audio": "", "Image": ""}),
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=config,
        media_writer=writer,
    )
    unsupported = process_note_visualization(
        BatchNoteSnapshot(3, "Basic", {"Audio": "[sound:movie.mp4]", "Image": ""}),
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=config,
        media_writer=writer,
    )

    assert missing_source.status == "skipped"
    assert empty_source.status == "skipped"
    assert unsupported.status == "skipped"


def test_process_note_visualization_counts_missing_media_as_failure(tmp_path: Path) -> None:
    result = process_note_visualization(
        BatchNoteSnapshot(1, "Basic", {"Audio": "[sound:missing.mp3]", "Image": ""}),
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, data: name,
    )

    assert result.failure
    assert "media file not found" in result.message
