"""Source-aware audio size reduction planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .errors import AudioAlreadyCompactError

SIZE_REDUCTION_MODES = frozenset({"gentle", "normal", "aggressive"})
DEFAULT_SIZE_REDUCTION_MODE = "normal"


@dataclass(frozen=True)
class SizeReductionProfile:
    """Loss budget for one size reduction mode."""

    max_bitrate_kbps: int
    min_bitrate_kbps: int
    bitrate_multiplier: float
    max_sample_rate_hz: int
    max_channels: int


@dataclass(frozen=True)
class AudioSizeReductionPlan:
    """Concrete FFmpeg encoder arguments for a source-aware MP3 render."""

    codec_args: tuple[str, ...]
    target_bitrate_kbps: int | None
    target_sample_rate_hz: int | None
    target_channels: int | None


class AudioSizeMetadata(Protocol):
    """Metadata fields needed to decide safe size reduction parameters."""

    @property
    def sample_rate(self) -> int | None:
        return None

    @property
    def channels(self) -> int | None:
        return None

    @property
    def bit_rate(self) -> int | None:
        return None


SIZE_REDUCTION_PROFILES: dict[str, SizeReductionProfile] = {
    "gentle": SizeReductionProfile(
        max_bitrate_kbps=96,
        min_bitrate_kbps=48,
        bitrate_multiplier=0.80,
        max_sample_rate_hz=44100,
        max_channels=2,
    ),
    "normal": SizeReductionProfile(
        max_bitrate_kbps=64,
        min_bitrate_kbps=40,
        bitrate_multiplier=0.65,
        max_sample_rate_hz=32000,
        max_channels=1,
    ),
    "aggressive": SizeReductionProfile(
        max_bitrate_kbps=40,
        min_bitrate_kbps=24,
        bitrate_multiplier=0.50,
        max_sample_rate_hz=22050,
        max_channels=1,
    ),
}


def normalize_size_reduction_mode(value: object) -> str:
    """Return a supported size reduction mode, defaulting to normal."""
    text = str(value).strip().lower()
    return text if text in SIZE_REDUCTION_MODES else DEFAULT_SIZE_REDUCTION_MODE


def size_reduction_plan_from_metadata(
    metadata: AudioSizeMetadata,
    mode: object,
) -> AudioSizeReductionPlan:
    """Return encoder arguments that reduce source size without increasing known params."""
    normalized_mode = normalize_size_reduction_mode(mode)
    profile = SIZE_REDUCTION_PROFILES[normalized_mode]
    source_bitrate_kbps = _source_bitrate_kbps(metadata)
    target_bitrate_kbps = _target_bitrate_kbps(source_bitrate_kbps, profile)
    target_sample_rate_hz = _capped_value(metadata.sample_rate, profile.max_sample_rate_hz)
    target_channels = _capped_value(metadata.channels, profile.max_channels)

    has_known_degradation = (
        _is_reduced(source_bitrate_kbps, target_bitrate_kbps)
        or _is_reduced(metadata.sample_rate, target_sample_rate_hz)
        or _is_reduced(metadata.channels, target_channels)
    )
    if not has_known_degradation:
        raise AudioAlreadyCompactError(
            f"Audio is already compact for {normalized_mode} size reduction."
        )

    return AudioSizeReductionPlan(
        codec_args=_codec_args(target_bitrate_kbps, target_sample_rate_hz, target_channels),
        target_bitrate_kbps=target_bitrate_kbps,
        target_sample_rate_hz=target_sample_rate_hz,
        target_channels=target_channels,
    )


def _source_bitrate_kbps(metadata: AudioSizeMetadata) -> int | None:
    if metadata.bit_rate is None or metadata.bit_rate <= 0:
        return None
    return max(1, round(metadata.bit_rate / 1000))


def _target_bitrate_kbps(
    source_bitrate_kbps: int | None,
    profile: SizeReductionProfile,
) -> int | None:
    if source_bitrate_kbps is None:
        return profile.max_bitrate_kbps
    target = min(
        profile.max_bitrate_kbps,
        max(profile.min_bitrate_kbps, round(source_bitrate_kbps * profile.bitrate_multiplier)),
    )
    return min(source_bitrate_kbps, target)


def _capped_value(source_value: int | None, max_value: int) -> int | None:
    if source_value is None or source_value <= 0:
        return None
    return min(source_value, max_value)


def _is_reduced(source_value: int | None, target_value: int | None) -> bool:
    return source_value is not None and target_value is not None and target_value < source_value


def _codec_args(
    target_bitrate_kbps: int | None,
    target_sample_rate_hz: int | None,
    target_channels: int | None,
) -> tuple[str, ...]:
    args: list[str] = ["-codec:a", "libmp3lame"]
    if target_bitrate_kbps is not None:
        args.extend(("-b:a", f"{target_bitrate_kbps}k"))
    else:
        args.extend(("-q:a", "6"))
    if target_sample_rate_hz is not None:
        args.extend(("-ar", str(target_sample_rate_hz)))
    if target_channels is not None:
        args.extend(("-ac", str(target_channels)))
    return tuple(args)
