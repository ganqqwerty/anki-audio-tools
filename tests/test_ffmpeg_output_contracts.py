from __future__ import annotations

from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_output_policy import (
    codec_args_for_output_policy,
    resolve_output_policy_from_metadata,
)
from anki_audio_quick_editor.errors import AudioProcessingError
from anki_audio_quick_editor.ffmpeg_output_contracts import (
    validate_final_ffmpeg_output,
    validate_intermediate_ffmpeg_output,
)

from .test_audio_output_policy import metadata


@pytest.mark.parametrize(
    ("filename", "codec_args"),
    [
        ("clip.mp3", ("-codec:a", "libmp3lame", "-q:a", "4")),
        ("clip.wav", ("-codec:a", "pcm_s16le")),
        ("clip.wav", ("-codec:a", "pcm_s24le")),
        ("clip.flac", ("-codec:a", "flac", "-compression_level", "5")),
        ("clip.m4a", ("-codec:a", "aac", "-b:a", "192k")),
        ("clip.aac", ("-codec:a", "aac", "-b:a", "192k", "-f", "adts")),
        ("clip.ogg", ("-codec:a", "libvorbis", "-b:a", "128k")),
        ("clip.oga", ("-codec:a", "libopus", "-b:a", "128k")),
        ("clip.opus", ("-codec:a", "libopus", "-b:a", "128k")),
        ("clip.webm", ("-codec:a", "libopus", "-b:a", "128k")),
    ],
)
def test_final_ffmpeg_output_contract_accepts_matching_container_and_codec(
    filename: str,
    codec_args: tuple[str, ...],
) -> None:
    validate_final_ffmpeg_output(Path(filename), codec_args)


@pytest.mark.parametrize(
    ("filename", "codec_args"),
    [
        ("clip.mp3", ("-codec:a", "pcm_s16le")),
        ("clip.wav", ("-codec:a", "libmp3lame", "-q:a", "4")),
        ("clip.flac", ("-codec:a", "aac", "-b:a", "192k")),
        ("clip.m4a", ("-codec:a", "aac", "-b:a", "192k", "-f", "adts")),
        ("clip.aac", ("-codec:a", "aac", "-b:a", "192k")),
    ],
)
def test_final_ffmpeg_output_contract_rejects_mismatched_container_and_codec(
    filename: str,
    codec_args: tuple[str, ...],
) -> None:
    with pytest.raises(AudioProcessingError, match="does not match ffmpeg audio codec"):
        validate_final_ffmpeg_output(Path(filename), codec_args)


def test_final_ffmpeg_output_contract_rejects_missing_codec_arg() -> None:
    with pytest.raises(AudioProcessingError, match="missing an explicit audio codec"):
        validate_final_ffmpeg_output(Path("clip.mp3"), ("-b:a", "128k"))


def test_final_ffmpeg_output_contract_rejects_unknown_extension() -> None:
    with pytest.raises(AudioProcessingError, match="unsupported final audio extension"):
        validate_final_ffmpeg_output(Path("clip.weird"), ("-codec:a", "libmp3lame"))


def test_intermediate_ffmpeg_output_contract_accepts_wav_pcm() -> None:
    validate_intermediate_ffmpeg_output(Path("working.wav"), ("-codec:a", "pcm_s16le"))


def test_intermediate_ffmpeg_output_contract_accepts_raw_pcm_muxer() -> None:
    validate_intermediate_ffmpeg_output(Path("input.s16le"), ("-codec:a", "pcm_s16le"), muxer="s16le")


@pytest.mark.parametrize(
    ("filename", "codec_args", "muxer", "message"),
    [
        ("working.mp3", ("-codec:a", "pcm_s16le"), None, "WAV output"),
        ("working.wav", ("-codec:a", "libmp3lame"), None, "PCM codec"),
        ("input.wav", ("-codec:a", "pcm_s16le"), "s16le", "raw PCM output"),
        ("input.s16le", ("-codec:a", "libmp3lame"), "s16le", "PCM codec"),
    ],
)
def test_intermediate_ffmpeg_output_contract_rejects_mismatched_stage_outputs(
    filename: str,
    codec_args: tuple[str, ...],
    muxer: str | None,
    message: str,
) -> None:
    with pytest.raises(AudioProcessingError, match=message):
        validate_intermediate_ffmpeg_output(Path(filename), codec_args, muxer=muxer)


@pytest.mark.parametrize(
    ("filename", "codec_name", "requested_format"),
    [
        ("clip.mp3", "mp3", "source"),
        ("clip.m4a", "aac", "source"),
        ("clip.aac", "aac", "source"),
        ("clip.wav", "pcm_s16le", "source"),
        ("clip.flac", "flac", "source"),
        ("clip.ogg", "vorbis", "source"),
        ("clip.oga", "opus", "source"),
        ("clip.opus", "opus", "source"),
        ("clip.webm", "opus", "source"),
        ("clip.mp3", "mp3", "mp3"),
        ("clip.mp3", "mp3", "m4a"),
        ("clip.mp3", "mp3", "wav"),
        ("clip.mp3", "mp3", "flac"),
    ],
)
def test_resolved_output_policy_respects_final_ffmpeg_contract(
    filename: str,
    codec_name: str,
    requested_format: str,
) -> None:
    policy = resolve_output_policy_from_metadata(
        metadata(filename=filename, codec_name=codec_name),
        requested_format=requested_format,
    )

    validate_final_ffmpeg_output(Path(f"output{policy.extension}"), codec_args_for_output_policy(policy))
