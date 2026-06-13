"""E2E tests for Browser batch audio size reduction."""

from __future__ import annotations

from pathlib import Path

from e2e.conftest import import_runtime_addon_module
from e2e.editor_audio_generation_helpers import _generate_high_bitrate_mp3


# noinspection PyUnusedLocal
def test_batch_reduce_size_renders_smaller_mp3_with_real_ffmpeg(
    anki_mw,
    ffmpeg_config,
    tmp_path: Path,
) -> None:
    del anki_mw
    audio_operation_params = import_runtime_addon_module(".audio_operation_params")
    audio_state = import_runtime_addon_module(".audio_state")
    batch_operations = import_runtime_addon_module(".batch_operations")

    source = tmp_path / "batch_size_reduce_source.mp3"
    _generate_high_bitrate_mp3(ffmpeg_config, source)
    original_bytes = source.read_bytes()
    writes: list[tuple[str, bytes]] = []

    def media_writer(name: str, data: bytes) -> str:
        writes.append((name, data))
        (tmp_path / name).write_bytes(data)
        return name

    result = batch_operations.process_note_batch_operation(
        batch_operations.BatchNoteSnapshot(
            1001,
            "Basic",
            {"Front": f"Prompt [sound:{source.name}]", "Back": "Answer"},
        ),
        request=batch_operations.BatchRunRequest(
            operation="reduce_size",
            source_field="Front",
            parameters=audio_operation_params.AudioOperationParameters(
                size_reduction_mode="aggressive"
            ),
        ),
        media_dir=tmp_path,
        config=audio_state.AudioProcessingConfig(
            ffmpeg_path=ffmpeg_config.ffmpeg_path,
            size_reduction_mode="normal",
        ),
        media_writer=media_writer,
    )

    assert result.status == "written"
    assert result.written_filename is not None
    assert result.written_filename.endswith(".mp3")
    assert result.written_filename in (result.target_html or "")
    assert len(writes) == 1
    assert writes[0][0] == result.written_filename
    assert (tmp_path / result.written_filename).stat().st_size < len(original_bytes)
    assert source.read_bytes() == original_bytes
