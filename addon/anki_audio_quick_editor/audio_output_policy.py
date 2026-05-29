"""Source-aware final audio output policy for FFmpeg renders."""

from __future__ import annotations

import json
import subprocess  # nosec B404
from dataclasses import dataclass
from pathlib import Path

from .audio_external import _external_command_run_kwargs, _render_external_error_message
from .audio_formats import (
    normalize_output_format,
    validate_target_format,
    visible_extension,
)
from .audio_state import AudioProcessingConfig
from .audio_tools import find_ffmpeg, find_ffprobe
from .errors import AudioProcessingError
from .permission_guidance import launch_error_message

FFMPEG_AUDIO_CODEC_ARG = "-codec:a"
DEFAULT_MP3_CODEC_ARGS = (FFMPEG_AUDIO_CODEC_ARG, "libmp3lame", "-q:a", "4")
PRESERVABLE_SOURCE_FORMATS = frozenset(
    {"mp3", "m4a", "aac", "wav", "flac", "ogg", "oga", "opus", "webm"}
)


@dataclass(frozen=True)
class AudioSourceMetadata:
    """Relevant source stream characteristics used for final output encoding."""

    path: Path
    visible_format: str | None
    codec_name: str | None
    sample_rate: int | None
    channels: int | None
    bit_rate: int | None
    bits_per_raw_sample: int | None
    sample_fmt: str | None


@dataclass(frozen=True)
class AudioOutputPolicy:
    """Concrete final output details after resolving a persisted format policy."""

    output_format: str
    extension: str
    mime_type: str
    codec_args: tuple[str, ...]


def probe_audio_metadata(source_path: Path, config: AudioProcessingConfig) -> AudioSourceMetadata:
    """Inspect the first audio stream characteristics with ffprobe."""
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    ffprobe_path = find_ffprobe(ffmpeg_path)
    cmd = [
        str(ffprobe_path),
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=codec_name,codec_type,sample_rate,channels,bit_rate,bits_per_raw_sample,sample_fmt",
        "-of",
        "json",
        str(source_path),
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            **_external_command_run_kwargs(),
        )  # nosec B603
    except OSError as exc:
        raise AudioProcessingError(launch_error_message("Could not start ffprobe.", exc)) from exc
    if result.returncode != 0:
        raise AudioProcessingError(
            _render_external_error_message(result, "Could not inspect audio stream metadata.")
        )
    try:
        streams = json.loads(result.stdout).get("streams", [])
    except (TypeError, json.JSONDecodeError) as exc:
        raise AudioProcessingError("Could not parse audio stream metadata.") from exc
    stream = _first_audio_stream(streams)
    if stream is None:
        raise AudioProcessingError("Could not inspect audio stream metadata.")
    return AudioSourceMetadata(
        path=source_path,
        visible_format=visible_extension(source_path),
        codec_name=_string_or_none(stream.get("codec_name")),
        sample_rate=_int_or_none(stream.get("sample_rate")),
        channels=_int_or_none(stream.get("channels")),
        bit_rate=_int_or_none(stream.get("bit_rate")),
        bits_per_raw_sample=_int_or_none(stream.get("bits_per_raw_sample")),
        sample_fmt=_string_or_none(stream.get("sample_fmt")),
    )


def resolve_output_policy(
    source_path: Path,
    config: AudioProcessingConfig,
    *,
    requested_format: object | None = None,
    output_path: Path | None = None,
) -> AudioOutputPolicy:
    """Resolve runtime config and source metadata into concrete FFmpeg output args."""
    metadata = probe_audio_metadata(source_path, config)
    return resolve_output_policy_from_metadata(
        metadata,
        requested_format=config.output_format if requested_format is None else requested_format,
        output_path=output_path,
    )


def resolve_output_policy_from_metadata(
    metadata: AudioSourceMetadata,
    *,
    requested_format: object,
    output_path: Path | None = None,
) -> AudioOutputPolicy:
    """Resolve a persisted output policy or explicit target into concrete encoder args."""
    output_format = _resolve_output_format(metadata, requested_format, output_path)
    return AudioOutputPolicy(
        output_format=output_format,
        extension=f".{output_format}",
        mime_type=mime_type_for_output_format(output_format),
        codec_args=_codec_args(output_format, metadata),
    )


def codec_args_for_output_policy(policy: AudioOutputPolicy) -> tuple[str, ...]:
    """Return FFmpeg codec/muxer arguments for a resolved final output policy."""
    return policy.codec_args


def mime_type_for_output_format(output_format: str) -> str:
    """Return the generated artifact MIME type for a concrete audio output format."""
    return {
        "mp3": "audio/mpeg",
        "m4a": "audio/mp4",
        "aac": "audio/aac",
        "wav": "audio/wav",
        "flac": "audio/flac",
        "ogg": "audio/ogg",
        "oga": "audio/ogg",
        "opus": "audio/ogg",
        "webm": "audio/webm",
    }.get(output_format, "audio/mpeg")


def synthetic_audio_metadata(
    source_path: Path,
    *,
    output_path: Path,
    codec_name: str | None,
    sample_rate: int | None,
    channels: int | None,
    bit_rate: int | None = None,
    bits_per_raw_sample: int | None = None,
    sample_fmt: str | None = None,
) -> AudioSourceMetadata:
    """Return metadata for model-generated intermediates with known characteristics."""
    return AudioSourceMetadata(
        path=source_path,
        visible_format=visible_extension(output_path),
        codec_name=codec_name,
        sample_rate=sample_rate,
        channels=channels,
        bit_rate=bit_rate,
        bits_per_raw_sample=bits_per_raw_sample,
        sample_fmt=sample_fmt,
    )


def _resolve_output_format(
    metadata: AudioSourceMetadata,
    requested_format: object,
    output_path: Path | None,
) -> str:
    requested = normalize_output_format(requested_format)
    if requested != "source":
        return validate_target_format(requested)
    output_path_format = visible_extension(output_path) if output_path is not None else None
    if output_path_format in PRESERVABLE_SOURCE_FORMATS:
        return output_path_format
    if metadata.visible_format in PRESERVABLE_SOURCE_FORMATS:
        return metadata.visible_format
    return "mp3"


def _codec_args(output_format: str, metadata: AudioSourceMetadata) -> tuple[str, ...]:
    sample_args = _sample_args(metadata)
    if output_format == "mp3":
        return (*_mp3_args(metadata), *sample_args)
    if output_format in {"m4a", "aac"}:
        muxer_args = ("-f", "adts") if output_format == "aac" else ()
        return (FFMPEG_AUDIO_CODEC_ARG, "aac", "-b:a", _bitrate(metadata, "192k"), *muxer_args, *sample_args)
    if output_format == "wav":
        return (FFMPEG_AUDIO_CODEC_ARG, _wav_codec(metadata), *sample_args)
    if output_format == "flac":
        return (FFMPEG_AUDIO_CODEC_ARG, "flac", "-compression_level", "5", *sample_args)
    if output_format == "ogg":
        codec = "libopus" if metadata.codec_name == "opus" else "libvorbis"
        return (FFMPEG_AUDIO_CODEC_ARG, codec, "-b:a", _bitrate(metadata, "128k"), *sample_args)
    if output_format in {"oga", "opus", "webm"}:
        return (FFMPEG_AUDIO_CODEC_ARG, "libopus", "-b:a", _bitrate(metadata, "128k"), *sample_args)
    return (*DEFAULT_MP3_CODEC_ARGS, *sample_args)


def _mp3_args(metadata: AudioSourceMetadata) -> tuple[str, ...]:
    if metadata.bit_rate is None:
        return DEFAULT_MP3_CODEC_ARGS
    return (FFMPEG_AUDIO_CODEC_ARG, "libmp3lame", "-b:a", _bitrate(metadata, "128k"))


def _sample_args(metadata: AudioSourceMetadata) -> tuple[str, ...]:
    args: list[str] = []
    if metadata.sample_rate is not None and metadata.sample_rate > 0:
        args.extend(("-ar", str(metadata.sample_rate)))
    if metadata.channels is not None and metadata.channels > 0:
        args.extend(("-ac", str(metadata.channels)))
    return tuple(args)


def _wav_codec(metadata: AudioSourceMetadata) -> str:
    if (metadata.bits_per_raw_sample or 0) >= 24 or metadata.sample_fmt in {"s32", "s32p", "s24"}:
        return "pcm_s24le"
    return "pcm_s16le"


def _bitrate(metadata: AudioSourceMetadata, fallback: str) -> str:
    if metadata.bit_rate is None or metadata.bit_rate <= 0:
        return fallback
    return f"{max(1, round(metadata.bit_rate / 1000))}k"


def _first_audio_stream(streams: object) -> dict[str, object] | None:
    if not isinstance(streams, list):
        return None
    for stream in streams:
        if isinstance(stream, dict) and stream.get("codec_type") in {None, "audio"}:
            return stream
    return None


def _int_or_none(value: object) -> int | None:
    if value is None or value == "N/A":
        return None
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _string_or_none(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip().lower()
    return value or None
