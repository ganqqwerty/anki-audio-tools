"""Tests for batch denoise operation routing."""

from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.audio_operation_params import AudioOperationParameters
from anki_audio_quick_editor.audio_operations import OP_DENOISE
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operations import (
    BatchNoteSnapshot,
    BatchRunRequest,
    process_note_batch_operation,
)


def test_process_note_batch_operation_uses_dpdfnet_parameter_for_denoise(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    note = BatchNoteSnapshot(10, "Basic", {"Audio": "[sound:clip.mp3]"})
    configs: list[AudioProcessingConfig] = []

    def fake_render_dpdfnet_audio(source_path, config, output_path=None, on_command=None):
        del source_path, on_command
        assert output_path is not None
        configs.append(config)
        output_path.write_bytes(b"denoised")

    monkeypatch.setattr(
        "anki_audio_quick_editor.batch_operations.render_dpdfnet_audio",
        fake_render_dpdfnet_audio,
    )

    result = process_note_batch_operation(
        note,
        request=BatchRunRequest(
            operation=OP_DENOISE,
            source_field="Audio",
            parameters=AudioOperationParameters(
                denoise_algorithm="dpdfnet",
                dpdfnet_attn_limit_db=18.0,
            ),
        ),
        media_dir=tmp_path,
        config=AudioProcessingConfig(denoise_algorithm="standard", dpdfnet_attn_limit_db=12.0),
        media_writer=lambda name, data: name,
    )

    assert result.written
    assert configs[0].denoise_algorithm == "dpdfnet"
    assert configs[0].dpdfnet_attn_limit_db == 18.0
