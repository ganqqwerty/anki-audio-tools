from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_output_policy import (
    AudioSourceMetadata,
    codec_args_for_output_policy,
    mime_type_for_output_format,
    probe_audio_metadata,
    resolve_output_policy_from_metadata,
)
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.errors import AudioProcessingError


def metadata(
    *,
    filename: str = "clip.mp3",
    codec_name: str = "mp3",
    sample_rate: int | None = 48000,
    channels: int | None = 2,
    bit_rate: int | None = 128000,
    bits_per_raw_sample: int | None = None,
    sample_fmt: str | None = None,
) -> AudioSourceMetadata:
    return AudioSourceMetadata(
        path=Path(filename),
        visible_format=Path(filename).suffix.lower().lstrip(".") or None,
        codec_name=codec_name,
        sample_rate=sample_rate,
        channels=channels,
        bit_rate=bit_rate,
        bits_per_raw_sample=bits_per_raw_sample,
        sample_fmt=sample_fmt,
    )


def test_source_policy_resolves_supported_mp3_source_characteristics() -> None:
    policy = resolve_output_policy_from_metadata(metadata(), requested_format="source")

    assert policy.output_format == "mp3"
    assert policy.extension == ".mp3"
    assert policy.mime_type == "audio/mpeg"
    assert codec_args_for_output_policy(policy) == (
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "128k",
        "-ar",
        "48000",
        "-ac",
        "2",
    )


def test_source_policy_resolves_m4a_source_to_aac_with_source_bitrate() -> None:
    policy = resolve_output_policy_from_metadata(
        metadata(filename="clip.m4a", codec_name="aac", sample_rate=44100, channels=1, bit_rate=96000),
        requested_format="source",
    )

    assert policy.output_format == "m4a"
    assert codec_args_for_output_policy(policy) == (
        "-codec:a",
        "aac",
        "-b:a",
        "96k",
        "-ar",
        "44100",
        "-ac",
        "1",
    )


def test_source_policy_preserves_lossless_source_format() -> None:
    wav_policy = resolve_output_policy_from_metadata(
        metadata(filename="clip.wav", codec_name="pcm_s24le", bits_per_raw_sample=24, bit_rate=None),
        requested_format="source",
    )
    flac_policy = resolve_output_policy_from_metadata(
        metadata(filename="clip.flac", codec_name="flac", bit_rate=None),
        requested_format="source",
    )

    assert codec_args_for_output_policy(wav_policy) == (
        "-codec:a",
        "pcm_s24le",
        "-ar",
        "48000",
        "-ac",
        "2",
    )
    assert codec_args_for_output_policy(flac_policy) == (
        "-codec:a",
        "flac",
        "-compression_level",
        "5",
        "-ar",
        "48000",
        "-ac",
        "2",
    )


@pytest.mark.parametrize(
    ("filename", "codec_name", "expected_args"),
    [
        ("clip.ogg", "vorbis", ("-codec:a", "libvorbis", "-b:a", "64k")),
        ("clip.oga", "opus", ("-codec:a", "libopus", "-b:a", "64k")),
        ("clip.opus", "opus", ("-codec:a", "libopus", "-b:a", "64k")),
        ("clip.webm", "opus", ("-codec:a", "libopus", "-b:a", "64k")),
        ("clip.aac", "aac", ("-codec:a", "aac", "-b:a", "64k", "-f", "adts")),
    ],
)
def test_source_policy_preserves_common_anki_audio_extensions(
    filename: str,
    codec_name: str,
    expected_args: tuple[str, ...],
) -> None:
    policy = resolve_output_policy_from_metadata(
        metadata(filename=filename, codec_name=codec_name, bit_rate=64000),
        requested_format="source",
    )

    assert policy.extension == Path(filename).suffix.lower()
    assert codec_args_for_output_policy(policy)[: len(expected_args)] == expected_args


def test_source_policy_falls_back_to_mp3_for_unknown_source_extension() -> None:
    policy = resolve_output_policy_from_metadata(
        metadata(filename="clip.weird", codec_name="pcm_s16le", bit_rate=None),
        requested_format="source",
    )

    assert policy.output_format == "mp3"
    assert policy.extension == ".mp3"
    assert codec_args_for_output_policy(policy) == (
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        "-ar",
        "48000",
        "-ac",
        "2",
    )


def test_explicit_concrete_format_overrides_source_extension() -> None:
    policy = resolve_output_policy_from_metadata(
        metadata(filename="clip.ogg", codec_name="opus", bit_rate=96000),
        requested_format="flac",
    )

    assert policy.output_format == "flac"
    assert policy.extension == ".flac"
    assert codec_args_for_output_policy(policy) == (
        "-codec:a",
        "flac",
        "-compression_level",
        "5",
        "-ar",
        "48000",
        "-ac",
        "2",
    )


def test_output_path_extension_can_resolve_source_policy_without_renaming() -> None:
    policy = resolve_output_policy_from_metadata(
        metadata(filename="clip.wav", codec_name="pcm_s16le", bit_rate=None),
        requested_format="source",
        output_path=Path("edited.flac"),
    )

    assert policy.output_format == "flac"
    assert policy.extension == ".flac"


@pytest.mark.parametrize(
    ("output_format", "mime_type"),
    [
        ("mp3", "audio/mpeg"),
        ("m4a", "audio/mp4"),
        ("aac", "audio/aac"),
        ("wav", "audio/wav"),
        ("flac", "audio/flac"),
        ("ogg", "audio/ogg"),
        ("oga", "audio/ogg"),
        ("opus", "audio/ogg"),
        ("webm", "audio/webm"),
    ],
)
def test_mime_type_mapping(output_format: str, mime_type: str) -> None:
    assert mime_type_for_output_format(output_format) == mime_type


def test_probe_audio_metadata_parses_first_audio_stream(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_output_policy.find_ffmpeg", lambda path: Path(path or "/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_output_policy.find_ffprobe", lambda _path: Path("/bin/ffprobe"))

    def fake_run(cmd: list[str], **_kwargs: object) -> SimpleNamespace:
        calls.append(cmd)
        return SimpleNamespace(
            returncode=0,
            stdout=(
                '{"streams":[{"codec_type":"video"},{"codec_type":"audio","codec_name":"aac",'
                '"sample_rate":"44100","channels":1,"bit_rate":"96000","sample_fmt":"fltp"}]}'
            ),
            stderr="",
        )

    monkeypatch.setattr("anki_audio_quick_editor.audio_output_policy.subprocess.run", fake_run)

    source = tmp_path / "clip.m4a"
    result = probe_audio_metadata(source, AudioProcessingConfig(ffmpeg_path="/custom/ffmpeg"))

    assert result == metadata(
        filename=str(source),
        codec_name="aac",
        sample_rate=44100,
        channels=1,
        bit_rate=96000,
        sample_fmt="fltp",
    )
    assert calls == [
        [
            "/bin/ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name,codec_type,sample_rate,channels,bit_rate,bits_per_raw_sample,sample_fmt",
            "-of",
            "json",
            str(source),
        ]
    ]


def test_probe_audio_metadata_raises_for_missing_audio_stream(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_output_policy.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_output_policy.find_ffprobe", lambda _path: Path("/bin/ffprobe"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_output_policy.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout='{"streams":[]}', stderr=""),
    )

    with pytest.raises(AudioProcessingError, match="Could not inspect audio stream metadata."):
        probe_audio_metadata(tmp_path / "clip.wav", AudioProcessingConfig())
