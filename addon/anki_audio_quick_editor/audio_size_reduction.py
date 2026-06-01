"""Source-aware audio size reduction planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .errors import AudioAlreadyCompactError

SIZE_REDUCTION_MODES = frozenset({"gentle", "normal", "aggressive"})
DEFAULT_SIZE_REDUCTION_MODE = "normal"
MIN_SIZE_REDUCTION_BITRATE_KBPS = 16
MAX_SIZE_REDUCTION_BITRATE_KBPS = 320
SIZE_REDUCTION_SAMPLE_RATES_HZ = (8000, 11025, 12000, 16000, 22050, 24000, 32000, 44100, 48000)
MIN_SIZE_REDUCTION_CHANNELS = 1
MAX_SIZE_REDUCTION_CHANNELS = 2


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


@dataclass(frozen=True)
class SizeReductionEncoderParams:
    """User-visible encoder caps used by the size reduction planner."""

    bitrate_kbps: int
    sample_rate_hz: int
    channels: int


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
DEFAULT_SIZE_REDUCTION_ENCODER_PARAMS = SizeReductionEncoderParams(
    bitrate_kbps=SIZE_REDUCTION_PROFILES[DEFAULT_SIZE_REDUCTION_MODE].max_bitrate_kbps,
    sample_rate_hz=SIZE_REDUCTION_PROFILES[DEFAULT_SIZE_REDUCTION_MODE].max_sample_rate_hz,
    channels=SIZE_REDUCTION_PROFILES[DEFAULT_SIZE_REDUCTION_MODE].max_channels,
)


def normalize_size_reduction_mode(value: object) -> str:
    """Return a supported size reduction mode, defaulting to normal."""
    text = str(value).strip().lower()
    return text if text in SIZE_REDUCTION_MODES else DEFAULT_SIZE_REDUCTION_MODE


def size_reduction_encoder_params_for_mode(mode: object) -> SizeReductionEncoderParams:
    """Return the visible advanced-parameter defaults for a mode."""
    profile = SIZE_REDUCTION_PROFILES[normalize_size_reduction_mode(mode)]
    return SizeReductionEncoderParams(
        bitrate_kbps=profile.max_bitrate_kbps,
        sample_rate_hz=profile.max_sample_rate_hz,
        channels=profile.max_channels,
    )


def normalize_size_reduction_bitrate_kbps(
    value: object,
    fallback: int = DEFAULT_SIZE_REDUCTION_ENCODER_PARAMS.bitrate_kbps,
) -> int:
    """Return a supported MP3 bitrate cap in kbps."""
    parsed = _int_or_none(value)
    if parsed is None:
        parsed = fallback
    return max(MIN_SIZE_REDUCTION_BITRATE_KBPS, min(MAX_SIZE_REDUCTION_BITRATE_KBPS, parsed))


def normalize_size_reduction_sample_rate_hz(
    value: object,
    fallback: int = DEFAULT_SIZE_REDUCTION_ENCODER_PARAMS.sample_rate_hz,
) -> int:
    """Return the nearest MP3-compatible sample-rate cap."""
    parsed = _int_or_none(value)
    if parsed is None:
        parsed = fallback
    return min(
        SIZE_REDUCTION_SAMPLE_RATES_HZ,
        key=lambda candidate: (abs(candidate - parsed), candidate),
    )


def normalize_size_reduction_channels(
    value: object,
    fallback: int = DEFAULT_SIZE_REDUCTION_ENCODER_PARAMS.channels,
) -> int:
    """Return a supported channel cap."""
    parsed = _int_or_none(value)
    if parsed is None:
        parsed = fallback
    return max(MIN_SIZE_REDUCTION_CHANNELS, min(MAX_SIZE_REDUCTION_CHANNELS, parsed))


def size_reduction_plan_from_metadata(
    metadata: AudioSizeMetadata,
    mode: object,
    *,
    bitrate_kbps: object | None = None,
    sample_rate_hz: object | None = None,
    channels: object | None = None,
) -> AudioSizeReductionPlan:
    """Return encoder arguments that reduce source size without increasing known params."""
    normalized_mode = normalize_size_reduction_mode(mode)
    profile = SIZE_REDUCTION_PROFILES[normalized_mode]
    default_params = size_reduction_encoder_params_for_mode(normalized_mode)
    encoder_params = SizeReductionEncoderParams(
        bitrate_kbps=normalize_size_reduction_bitrate_kbps(
            bitrate_kbps,
            default_params.bitrate_kbps,
        ),
        sample_rate_hz=normalize_size_reduction_sample_rate_hz(
            sample_rate_hz,
            default_params.sample_rate_hz,
        ),
        channels=normalize_size_reduction_channels(channels, default_params.channels),
    )
    source_bitrate_kbps = _source_bitrate_kbps(metadata)
    target_bitrate_kbps = _target_bitrate_kbps(
        source_bitrate_kbps,
        profile,
        encoder_params.bitrate_kbps,
        preserve_profile_curve=encoder_params.bitrate_kbps == default_params.bitrate_kbps,
    )
    target_sample_rate_hz = _capped_value(metadata.sample_rate, encoder_params.sample_rate_hz)
    target_channels = _capped_value(metadata.channels, encoder_params.channels)

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
    bitrate_cap_kbps: int,
    *,
    preserve_profile_curve: bool,
) -> int | None:
    if source_bitrate_kbps is None:
        return bitrate_cap_kbps
    target = bitrate_cap_kbps
    if preserve_profile_curve:
        target = min(
            bitrate_cap_kbps,
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


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None
