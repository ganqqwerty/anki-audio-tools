from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig


def test_render_working_original_uses_requested_pcm_codec(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from anki_audio_quick_editor.audio_pause_pipeline import _render_working_original

    captured: dict[str, object] = {}
    stages: list[dict[str, object]] = []
    attempted_commands: list[dict[str, object]] = []
    artifacts: list[dict[str, object]] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pause_pipeline.build_wav_filter_command",
        lambda ffmpeg_path, source_path, filters, output_path, codec_args: captured.update(
            ffmpeg_path=ffmpeg_path,
            source_path=source_path,
            filters=filters,
            output_path=output_path,
            codec_args=codec_args,
        )
        or ("ffmpeg", "-i", str(source_path), str(output_path)),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pause_pipeline.run_pipeline_stage",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pause_pipeline.probe_duration_ms",
        lambda *_args: 1234,
    )

    duration_ms = _render_working_original(
        tmp_path / "source.flac",
        AudioEditState("source.flac", remove_internal_pauses_enabled=True),
        AudioProcessingConfig(),
        Path("/bin/ffmpeg"),
        2000,
        tmp_path / "01_working_original.wav",
        ("-codec:a", "pcm_s24le"),
        stages,
        attempted_commands,
        artifacts,
        None,
    )

    assert captured["codec_args"] == ("-codec:a", "pcm_s24le")
    assert duration_ms == 1234


def test_pause_pipeline_resolves_source_quality_for_final_and_working_audio(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from anki_audio_quick_editor.audio_pause_pipeline import (
        _PauseDetectionRuntime,
        _render_pause_removal_pipeline_audio,
    )

    captured: dict[str, object] = {}
    source = tmp_path / "source.mp3"
    source.write_bytes(b"source")

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pause_pipeline.resolve_output_policy",
        lambda *_args, **_kwargs: SimpleNamespace(
            codec_args=("-codec:a", "libmp3lame", "-b:a", "192k", "-ar", "44100", "-ac", "1"),
            mime_type="audio/mpeg",
        ),
        raising=False,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pause_pipeline._resolve_pause_detection_runtime",
        lambda *_args, **_kwargs: _PauseDetectionRuntime(),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pause_pipeline._render_working_original",
        lambda *_args, **_kwargs: captured.update(working_codec_args=_args[6]) or 1800,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pause_pipeline._render_selected_pause_detection_pipeline",
        lambda _state, _config, _ffmpeg_path, output_path, _on_command, **kwargs: captured.update(
            final_codec_args=kwargs["codec_args"],
            final_output_mime_type=kwargs["output_mime_type"],
        )
        or SimpleNamespace(output_path=output_path, command=("pause",), duration_ms=1500),
    )

    result = _render_pause_removal_pipeline_audio(
        source,
        AudioEditState("source.mp3", remove_internal_pauses_enabled=True),
        AudioProcessingConfig(),
        Path("/bin/ffmpeg"),
        tmp_path / "edited.mp3",
        None,
        artifact_root=tmp_path / "artifacts",
        source_duration_ms=2000,
    )

    assert captured["working_codec_args"] == ("-codec:a", "pcm_s24le")
    assert captured["final_codec_args"] == (
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "192k",
        "-ar",
        "44100",
        "-ac",
        "1",
    )
    assert captured["final_output_mime_type"] == "audio/mpeg"
    assert result.duration_ms == 1500
