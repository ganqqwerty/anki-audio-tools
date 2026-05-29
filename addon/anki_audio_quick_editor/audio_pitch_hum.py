"""Praat-guided pitch hum resynthesis."""

from __future__ import annotations

import subprocess  # nosec B404
import tempfile
import wave
from collections.abc import Callable, Sequence
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import Any, cast

from .audio_commands import build_audio_encode_command
from .audio_external import _external_command_run_kwargs, probe_duration_ms
from .audio_output_policy import (
    AudioOutputPolicy,
    codec_args_for_output_policy,
    resolve_output_policy_from_metadata,
    synthetic_audio_metadata,
)
from .audio_pitch_hum_frames import (
    PitchHumFrame,
    sanitize_pitch_hum_frames,
)
from .audio_pitch_hum_synthesis import (
    HUM_SAMPLE_RATE,
    _apply_nasal_onsets,
    _nearest_intensity,
    _sound_duration_s,
)
from .audio_pitch_hum_synthesis import (
    _synthesize_pitch_hum_pcm as _synthesize_pitch_hum_pcm_impl,
)
from .audio_pitch_hum_synthesis import (
    _synthesize_pitch_tier_pcm as _synthesize_pitch_tier_pcm_impl,
)
from .audio_state import AudioProcessingConfig
from .audio_tools import find_ffmpeg
from .audio_types import AudioProcessingResult
from .errors import AudioProcessingError
from .permission_guidance import launch_error_message
from .prosody_settings import resolve_analysis_options


# noinspection PyInconsistentReturns
def render_pitch_hum_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render a neutral hum whose voiced regions follow Praat's F0 contour."""
    if not _is_praat_available():
        raise AudioProcessingError("Praat/Parselmouth is required for pitch hum rendering.")

    import parselmouth

    output_policy = _pitch_hum_output_policy(source_path, config, output_path)
    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_pitch_hum_", suffix=output_policy.extension)[1])

    sound = parselmouth.Sound(str(source_path))
    frames = _pitch_hum_frames(sound, config)
    duration_s = _sound_duration_s(sound, frames)
    with tempfile.TemporaryDirectory(prefix="aqe_pitch_hum_") as temp_dir:
        wav_path = Path(temp_dir) / "pitch_hum.wav"
        _write_pitch_hum_wav(wav_path, frames, duration_s)
        return _encode_pitch_hum_wav(
            wav_path,
            config,
            output_path,
            on_command,
            failure_message="Pitch hum rendering failed.",
        )


# noinspection PyInconsistentReturns
def render_pitch_tier_hum_audio(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render Praat Manipulation/PitchTier resynthesis for pitch-focused listening."""
    if not _is_praat_available():
        raise AudioProcessingError("Praat/Parselmouth is required for PitchTier rendering.")

    import parselmouth

    call = import_module("parselmouth.praat").call

    output_policy = _pitch_hum_output_policy(source_path, config, output_path)
    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_pitch_tier_", suffix=output_policy.extension)[1])

    options = resolve_analysis_options(config)
    sound = parselmouth.Sound(str(source_path))
    manipulation = call(
        sound,
        "To Manipulation",
        options.time_step_s,
        options.pitch_floor_hz,
        options.pitch_ceiling_hz,
    )
    pitch_tier = call(manipulation, "Extract pitch tier")
    pitch_tier_sound = call(pitch_tier, "To Sound (sine)", HUM_SAMPLE_RATE)
    frames = _pitch_hum_frames(sound, config)
    duration_s = _sound_duration_s(sound, frames)
    with tempfile.TemporaryDirectory(prefix="aqe_pitch_tier_") as temp_dir:
        wav_path = Path(temp_dir) / "pitch_tier.wav"
        _write_pitch_tier_hum_wav(wav_path, pitch_tier_sound, frames, duration_s)
        return _encode_pitch_hum_wav(
            wav_path,
            config,
            output_path,
            on_command,
            failure_message="PitchTier rendering failed.",
        )


def _encode_pitch_hum_wav(
    wav_path: Path,
    config: AudioProcessingConfig,
    output_path: Path,
    on_command: Callable[[tuple[str, ...]], None] | None,
    *,
    failure_message: str,
) -> AudioProcessingResult:
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    output_policy = _pitch_hum_output_policy(wav_path, config, output_path)
    command = build_audio_encode_command(
        ffmpeg_path,
        wav_path,
        output_path,
        codec_args_for_output_policy(output_policy),
    )
    if on_command:
        on_command(command)
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
            **_external_command_run_kwargs(),
        )  # nosec B603
    except OSError as exc:
        raise AudioProcessingError(launch_error_message("Could not start pitch hum encoding.", exc)) from exc
    if result.returncode != 0:
        raise AudioProcessingError(result.stderr.strip() or failure_message)
    return AudioProcessingResult(
        output_path=output_path,
        command=command,
        duration_ms=probe_duration_ms(output_path, config),
    )


def _pitch_hum_output_policy(
    source_path: Path,
    config: AudioProcessingConfig,
    output_path: Path | None,
) -> AudioOutputPolicy:
    return resolve_output_policy_from_metadata(
        synthetic_audio_metadata(
            source_path,
            output_path=output_path or source_path,
            codec_name="pcm_s16le",
            sample_rate=HUM_SAMPLE_RATE,
            channels=1,
            bits_per_raw_sample=16,
        ),
        requested_format=config.output_format,
        output_path=output_path,
    )


def _is_praat_available() -> bool:
    return find_spec("parselmouth") is not None


def _pitch_hum_frames(sound: Any, config: AudioProcessingConfig) -> list[PitchHumFrame]:
    options = resolve_analysis_options(config)
    to_pitch_ac = getattr(sound, "to_pitch_ac", None)
    if callable(to_pitch_ac):
        pitch = to_pitch_ac(
            time_step=options.time_step_s,
            pitch_floor=options.pitch_floor_hz,
            max_number_of_candidates=options.max_number_of_candidates,
            silence_threshold=options.silence_threshold,
            voicing_threshold=options.voicing_threshold,
            octave_cost=options.octave_cost,
            octave_jump_cost=options.octave_jump_cost,
            voiced_unvoiced_cost=options.voiced_unvoiced_cost,
            pitch_ceiling=options.pitch_ceiling_hz,
        )
    else:
        pitch = sound.to_pitch(
            time_step=options.time_step_s,
            pitch_floor=options.pitch_floor_hz,
            pitch_ceiling=options.pitch_ceiling_hz,
        )
    intensity = sound.to_intensity(
        minimum_pitch=options.pitch_floor_hz,
        time_step=options.time_step_s,
    )
    intensity_times = list(intensity.xs())
    intensity_values = list(intensity.values[0])
    raw_frames = [
        PitchHumFrame(
            time_s=float(time_s),
            pitch_hz=float(frequency) if frequency and frequency > 0 else None,
            intensity_db=_nearest_intensity(time_s, intensity_times, intensity_values),
        )
        for time_s, frequency in zip(pitch.xs(), pitch.selected_array["frequency"], strict=False)
    ]
    return sanitize_pitch_hum_frames(
        raw_frames,
        pitch_floor_hz=options.pitch_floor_hz,
        pitch_ceiling_hz=options.pitch_ceiling_hz,
    )


def _write_pitch_hum_wav(
    output_path: Path,
    frames: Sequence[PitchHumFrame],
    duration_s: float,
    *,
    sample_rate: int = HUM_SAMPLE_RATE,
) -> None:
    samples = _synthesize_pitch_hum_pcm(list(frames), duration_s, sample_rate=sample_rate)
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(samples.tobytes())


def _write_pitch_tier_hum_wav(
    output_path: Path,
    pitch_tier_sound: Any,
    frames: Sequence[PitchHumFrame],
    duration_s: float,
    *,
    sample_rate: int = HUM_SAMPLE_RATE,
) -> None:
    samples = _synthesize_pitch_tier_pcm(
        pitch_tier_sound,
        list(frames),
        duration_s,
        sample_rate=sample_rate,
    )
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(samples.tobytes())


def _synthesize_pitch_hum_pcm(
    frames: list[PitchHumFrame] | tuple[PitchHumFrame, ...],
    duration_s: float,
    *,
    sample_rate: int = HUM_SAMPLE_RATE,
) -> Any:
    from . import audio_pitch_hum_synthesis as synthesis

    synthesis._apply_nasal_onsets = _apply_nasal_onsets
    return cast(Any, _synthesize_pitch_hum_pcm_impl(frames, duration_s, sample_rate=sample_rate))


def _synthesize_pitch_tier_pcm(
    pitch_tier_sound: Any,
    frames: list[PitchHumFrame] | tuple[PitchHumFrame, ...],
    duration_s: float,
    *,
    sample_rate: int = HUM_SAMPLE_RATE,
) -> Any:
    from . import audio_pitch_hum_synthesis as synthesis

    synthesis._apply_nasal_onsets = _apply_nasal_onsets
    return cast(Any, _synthesize_pitch_tier_pcm_impl(
        pitch_tier_sound,
        frames,
        duration_s,
        sample_rate=sample_rate,
    ))
