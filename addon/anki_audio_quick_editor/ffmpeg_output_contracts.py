"""Validation for ffmpeg output container and codec invariants."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .errors import AudioProcessingError

_AUDIO_CODEC_OPTIONS = frozenset({"-codec:a", "-c:a", "-acodec"})
_SUPPORTED_FINAL_EXTENSIONS = frozenset(
    {".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg", ".oga", ".opus", ".webm"}
)
_MP3_CODECS = frozenset({"libmp3lame", "mp3"})
_AAC_CODECS = frozenset({"aac", "libfdk_aac"})
_FLAC_CODECS = frozenset({"flac"})
_VORBIS_CODECS = frozenset({"libvorbis", "vorbis"})
_OPUS_CODECS = frozenset({"libopus", "opus"})
_OGG_CODECS = _VORBIS_CODECS | _OPUS_CODECS
_FINAL_OUTPUT_RULES: dict[str, tuple[frozenset[str], frozenset[str | None]]] = {
    ".mp3": (_MP3_CODECS, frozenset({None, "mp3"})),
    ".m4a": (_AAC_CODECS, frozenset({None, "ipod", "mp4"})),
    ".aac": (_AAC_CODECS, frozenset({"adts"})),
    ".flac": (_FLAC_CODECS, frozenset({None, "flac"})),
    ".ogg": (_OGG_CODECS, frozenset({None, "ogg"})),
    ".oga": (_OPUS_CODECS, frozenset({None, "ogg", "opus"})),
    ".opus": (_OPUS_CODECS, frozenset({None, "ogg", "opus"})),
    ".webm": (_OGG_CODECS, frozenset({None, "webm"})),
}


def validate_final_ffmpeg_output(output_path: Path, codec_args: Sequence[str]) -> None:
    """Raise if a final ffmpeg output path cannot contain the requested codec."""
    suffix = _visible_suffix(output_path)
    if suffix not in _SUPPORTED_FINAL_EXTENSIONS:
        raise AudioProcessingError(
            f"Final ffmpeg output {output_path.name!r} uses unsupported final audio extension {suffix!r}."
        )

    args = tuple(codec_args)
    codec = _audio_codec(args)
    if codec is None:
        raise AudioProcessingError(
            f"Final ffmpeg output {output_path.name!r} is missing an explicit audio codec."
        )

    muxer = _option_value(args, "-f")
    if _final_output_matches(suffix, codec, muxer):
        return

    raise AudioProcessingError(
        f"Final ffmpeg output extension {suffix!r} does not match ffmpeg audio codec {codec!r}."
    )


def validate_intermediate_ffmpeg_output(
    output_path: Path,
    codec_args: Sequence[str],
    *,
    muxer: str | None = None,
) -> None:
    """Raise if an intermediate ffmpeg stage path does not match its stage format."""
    args = tuple(codec_args)
    codec = _audio_codec(args)
    if codec is None:
        raise AudioProcessingError(
            f"Intermediate ffmpeg output {output_path.name!r} is missing an explicit audio codec."
        )

    normalized_muxer = muxer.lower() if muxer is not None else None
    if normalized_muxer == "s16le":
        _validate_raw_pcm_intermediate(output_path, codec)
        return
    if normalized_muxer is not None:
        raise AudioProcessingError(
            f"Intermediate ffmpeg output {output_path.name!r} uses unsupported muxer {muxer!r}."
        )

    _validate_wav_intermediate(output_path, codec)


def _final_output_matches(suffix: str, codec: str, muxer: str | None) -> bool:
    if suffix == ".wav":
        return _is_pcm_codec(codec) and muxer in {None, "wav"}
    rule = _FINAL_OUTPUT_RULES.get(suffix)
    return rule is not None and codec in rule[0] and muxer in rule[1]


def _validate_wav_intermediate(output_path: Path, codec: str) -> None:
    suffix = _visible_suffix(output_path)
    if suffix != ".wav":
        raise AudioProcessingError(
            f"Intermediate ffmpeg WAV output {output_path.name!r} must use a .wav filename."
        )
    if not _is_pcm_codec(codec):
        raise AudioProcessingError(
            f"Intermediate ffmpeg WAV output {output_path.name!r} requires a PCM codec."
        )


def _validate_raw_pcm_intermediate(output_path: Path, codec: str) -> None:
    suffix = _visible_suffix(output_path)
    if suffix != ".s16le":
        raise AudioProcessingError(
            f"Intermediate ffmpeg raw PCM output {output_path.name!r} must use a .s16le filename."
        )
    if codec != "pcm_s16le":
        raise AudioProcessingError(
            f"Intermediate ffmpeg raw PCM output {output_path.name!r} requires a PCM codec."
        )


def _audio_codec(args: tuple[str, ...]) -> str | None:
    for index, value in reversed(tuple(enumerate(args))):
        if value.lower() in _AUDIO_CODEC_OPTIONS and index + 1 < len(args):
            return args[index + 1].lower()
    return None


def _option_value(args: tuple[str, ...], option: str) -> str | None:
    normalized_option = option.lower()
    for index, value in reversed(tuple(enumerate(args))):
        if value.lower() == normalized_option and index + 1 < len(args):
            return args[index + 1].lower()
    return None


def _visible_suffix(path: Path) -> str:
    return path.suffix.lower()


def _is_pcm_codec(codec: str) -> bool:
    return codec.startswith("pcm_")
