"""Failure and skip-path tests for batch visualization workflows."""

from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.audio_operations import OP_FASTER, OP_VOLUME_DOWN
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operations import (
    BatchNoteSnapshot,
    BatchRunRequest,
    process_note_batch_operation,
)
from anki_audio_quick_editor.batch_visualization import process_note_visualization
from anki_audio_quick_editor.errors import AudioProcessingError


def test_process_note_batch_operation_requires_exact_non_windows_case(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "Clip.MP3").write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]"})
    monkeypatch.setattr("anki_audio_quick_editor.media_paths.platform.system", lambda: "Darwin")

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(operation=OP_FASTER, source_field="Audio"),
        media_dir=tmp_path,
        config=AudioProcessingConfig(speed_step=0.1),
        media_writer=lambda name, data: name,
    )
    assert not result.written
    assert result.status == "failed"
    assert result.message == "media file not found: clip.mp3"


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


def test_process_note_batch_operation_skips_missing_transform_source_field(tmp_path: Path) -> None:
    result = process_note_batch_operation(
        BatchNoteSnapshot(5, "Basic", {"Image": ""}),
        request=BatchRunRequest(operation=OP_VOLUME_DOWN, source_field="Audio"),
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, data: name,
    )
    assert result.status == "skipped"
    assert result.message == "missing source field 'Audio'"


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


def test_process_note_batch_operation_preserves_failure_payload_when_transform_render_raises(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]"})
    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_operations.render_audio",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AudioProcessingError("boom")),
    )

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(operation=OP_FASTER, source_field="Audio"),
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
    assert result.written_filename is None


def test_process_note_visualization_preserves_failure_payload_when_generation_raises(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]", "Image": "old"})
    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_operations.analyze_prosody_cached",
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
