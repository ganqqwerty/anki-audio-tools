"""Tests for batch audio conversion behavior."""

from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.audio_operation_params import AudioOperationParameters
from anki_audio_quick_editor.audio_operations import OP_CONVERT, OP_REDUCE_SIZE
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operations import (
    BatchNoteSnapshot,
    BatchRunRequest,
    process_note_batch_operation,
)
from anki_audio_quick_editor.errors import AudioAlreadyCompactError


def test_process_note_batch_operation_converts_audio_to_target_format(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.wav"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "before [sound:clip.wav] after"})
    convert_calls: list[tuple[str, str, str]] = []
    writes: list[tuple[str, bytes]] = []

    def fake_render_converted_audio(
        source_path,
        _config,
        target_format,
        output_path=None,
        on_command=None,
    ):
        del on_command
        assert output_path is not None
        output_path.write_bytes(b"converted")
        convert_calls.append((source_path.name, target_format, output_path.suffix))

    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_operations.render_converted_audio",
        fake_render_converted_audio,
    )

    def media_writer(name: str, data: bytes) -> str:
        writes.append((name, data))
        return name

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(
            operation=OP_CONVERT,
            source_field="Audio",
            parameters=AudioOperationParameters(target_format="flac"),
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(output_format="mp3"),
        media_writer=media_writer,
    )

    assert result.written
    assert result.audio_filename == "clip.wav"
    assert result.target_field == "Audio"
    assert result.written_filename is not None
    assert result.written_filename.endswith(".flac")
    assert "[sound:clip.wav]" not in result.target_html
    assert result.written_filename in result.target_html
    assert convert_calls == [("clip.wav", "flac", ".flac")]
    assert writes[0][0].endswith(".flac")
    assert writes[0][1] == b"converted"


def test_process_note_batch_operation_skips_convert_when_visible_extension_matches(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.MP3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.MP3]"})

    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_operations.render_converted_audio",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not render")),
    )

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(
            operation=OP_CONVERT,
            source_field="Audio",
            parameters=AudioOperationParameters(target_format="mp3"),
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(output_format="flac"),
        media_writer=lambda name, data: name,
    )

    assert result.status == "skipped"
    assert result.message == "already in MP3 format"
    assert result.audio_filename == "clip.MP3"
    assert result.written_filename is None


def test_process_note_batch_operation_reduces_audio_size_to_mp3(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.wav"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "before [sound:clip.wav] after"})
    reduce_calls: list[tuple[str, str, str, str]] = []
    writes: list[tuple[str, bytes]] = []

    def fake_render_size_reduced_audio(
        source_path,
        config,
        output_path=None,
        on_command=None,
        *,
        mode=None,
    ):
        del on_command
        assert output_path is not None
        output_path.write_bytes(b"smaller")
        reduce_calls.append((source_path.name, config.size_reduction_mode, mode, output_path.suffix))

    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_operations.render_size_reduced_audio",
        fake_render_size_reduced_audio,
    )

    def media_writer(name: str, data: bytes) -> str:
        writes.append((name, data))
        return name

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(
            operation=OP_REDUCE_SIZE,
            source_field="Audio",
            parameters=AudioOperationParameters(size_reduction_mode="aggressive"),
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(size_reduction_mode="normal"),
        media_writer=media_writer,
    )

    assert result.written
    assert result.written_filename is not None
    assert result.written_filename.endswith(".mp3")
    assert result.written_filename in result.target_html
    assert reduce_calls == [("clip.wav", "aggressive", "aggressive", ".mp3")]
    assert writes[0][0].endswith(".mp3")
    assert writes[0][1] == b"smaller"


def test_process_note_batch_operation_skips_size_reduction_when_already_compact(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]"})

    def fake_render_size_reduced_audio(*_args, **_kwargs):
        raise AudioAlreadyCompactError("already compact")

    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_operations.render_size_reduced_audio",
        fake_render_size_reduced_audio,
    )

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(
            operation=OP_REDUCE_SIZE,
            source_field="Audio",
            parameters=AudioOperationParameters(size_reduction_mode="normal"),
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(),
        media_writer=lambda name, data: name,
    )

    assert result.status == "skipped"
    assert result.message == "already compact"
    assert result.written_filename is None
