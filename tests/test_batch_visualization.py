"""Tests for import-safe batch visualization core behavior."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_visualization import (
    BatchNoteSnapshot,
    append_image_reference,
    field_groups_for_notes,
    first_audio_filename,
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


def test_field_groups_sort_note_types_case_insensitively() -> None:
    groups = field_groups_for_notes(
        [
            BatchNoteSnapshot(1, "basic", {"Front": ""}),
            BatchNoteSnapshot(2, "Basic", {"Back": ""}),
        ]
    )

    assert [group.notetype_name for group in groups] == ["basic", "Basic"]


def test_append_image_reference_uses_new_line_media_tag() -> None:
    assert append_image_reference("existing", "viz.svg") == 'existing<br><img src="viz.svg">'
    assert append_image_reference("", "viz.svg") == '<img src="viz.svg">'


def test_append_image_reference_escapes_filename_for_html() -> None:
    assert append_image_reference("existing", 'viz"bad.svg') == 'existing<br><img src="viz&quot;bad.svg">'


def test_first_audio_filename_returns_sanitized_basename() -> None:
    note = BatchNoteSnapshot(10, "Basic", {"Audio": r"[sound:..\nested\clip.mp3]"})

    assert first_audio_filename(note, "Audio") == "clip.mp3"


def test_first_audio_filename_returns_none_for_missing_or_invalid_source() -> None:
    missing = BatchNoteSnapshot(10, "Basic", {"Image": ""})
    unsupported = BatchNoteSnapshot(11, "Basic", {"Audio": "[sound:movie.mp4]"})

    assert first_audio_filename(missing, "Audio") is None
    assert first_audio_filename(unsupported, "Audio") is None


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
    analyzer_calls: list[tuple[Path, AudioProcessingConfig]] = []
    config = AudioProcessingConfig()

    def analyze(source_path: Path, call_config: AudioProcessingConfig) -> ProsodyTrack:
        analyzer_calls.append((source_path, call_config))
        return track

    monkeypatch.setattr("anki_audio_quick_editor.batch_visualization.analyze_prosody_cached", analyze)

    def media_writer(name: str, data: bytes) -> str:
        writes.append((name, data))
        return name

    result = process_note_visualization(
        note,
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=config,
        media_writer=media_writer,
        now_provider=lambda: datetime(2026, 5, 16, 1, 2, 3, 456000),
    )

    assert result.written
    assert result.note_id == 10
    assert result.message == "appended clip__aqe_viz_20260516_010203_456000.svg"
    assert result.target_field == "Image"
    assert result.audio_filename == "clip.mp3"
    assert result.image_filename == "clip__aqe_viz_20260516_010203_456000.svg"
    assert result.target_html == 'old<br><img src="clip__aqe_viz_20260516_010203_456000.svg">'
    assert analyzer_calls == [(source, config)]
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
    missing_target = process_note_visualization(
        BatchNoteSnapshot(4, "Basic", {"Audio": "[sound:clip.mp3]"}),
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=config,
        media_writer=writer,
    )

    assert missing_source.status == "skipped"
    assert missing_source.note_id == 1
    assert missing_source.message == "missing source field 'Audio'"
    assert empty_source.status == "skipped"
    assert empty_source.note_id == 2
    assert empty_source.message == "source field 'Audio' has no supported sound reference"
    assert unsupported.status == "skipped"
    assert unsupported.note_id == 3
    assert unsupported.message == "The first audio reference uses an unsupported format."
    assert missing_target.status == "skipped"
    assert missing_target.note_id == 4
    assert missing_target.message == "missing target field 'Image'"


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
    assert result.note_id == 1
    assert result.audio_filename == "missing.mp3"
    assert result.message == "media file not found: missing.mp3"


def test_process_note_visualization_preserves_failure_payload_when_generation_raises(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]", "Image": "old"})

    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_visualization.analyze_prosody_cached",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    result = process_note_visualization(
        note,
        source_field="Audio",
        target_field="Image",
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, data: name,
    )

    assert result.note_id == 10
    assert result.status == "failed"
    assert result.message == "boom"
    assert result.target_field is None
    assert result.target_html is None
    assert result.audio_filename == "clip.mp3"
    assert result.image_filename is None
