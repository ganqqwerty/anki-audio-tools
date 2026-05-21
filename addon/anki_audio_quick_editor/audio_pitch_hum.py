"""Praat-guided pitch hum resynthesis."""

from __future__ import annotations

import math
import subprocess  # nosec B404
import tempfile
import wave
from array import array
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from .audio_commands import build_mp3_encode_command
from .audio_external import _external_command_run_kwargs, probe_duration_ms
from .audio_state import AudioProcessingConfig
from .audio_tools import find_ffmpeg
from .audio_types import AudioProcessingResult
from .errors import AudioProcessingError
from .prosody_settings import resolve_analysis_options

HUM_SAMPLE_RATE = 22_050
HUM_BASE_AMPLITUDE = 0.24
HUM_RAMP_MS = 5
NASAL_ONSET_MS = 70
NASAL_FADE_IN_MS = 15
NASAL_DROPOUT_MERGE_MS = 120
_HARMONICS = ((1, 0.72), (2, 0.2), (3, 0.08))
_NASAL_HARMONICS = ((1, 0.88), (2, 0.09), (3, 0.03))


@dataclass(frozen=True)
class PitchHumFrame:
    """One Praat pitch frame used for neutral hum synthesis."""

    time_s: float
    pitch_hz: float | None
    intensity_db: float | None


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

    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_pitch_hum_", suffix=".mp3")[1])

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

    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_pitch_tier_", suffix=".mp3")[1])

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
    command = build_mp3_encode_command(ffmpeg_path, wav_path, output_path)
    if on_command:
        on_command(command)
    result = subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        check=False,
        **_external_command_run_kwargs(),
    )  # nosec B603
    if result.returncode != 0:
        raise AudioProcessingError(result.stderr.strip() or failure_message)
    return AudioProcessingResult(
        output_path=output_path,
        command=command,
        duration_ms=probe_duration_ms(output_path, config),
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
    return [
        PitchHumFrame(
            time_s=float(time_s),
            pitch_hz=float(frequency) if frequency and frequency > 0 else None,
            intensity_db=_nearest_intensity(time_s, intensity_times, intensity_values),
        )
        for time_s, frequency in zip(pitch.xs(), pitch.selected_array["frequency"], strict=False)
    ]


def _write_pitch_hum_wav(
    output_path: Path,
    frames: Sequence[PitchHumFrame],
    duration_s: float,
    *,
    sample_rate: int = HUM_SAMPLE_RATE,
) -> None:
    samples = _synthesize_pitch_hum_pcm(frames, duration_s, sample_rate=sample_rate)
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
        frames,
        duration_s,
        sample_rate=sample_rate,
    )
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(samples.tobytes())


def _sorted_pitch_frames(frames: Sequence[PitchHumFrame]) -> list[PitchHumFrame]:
    return sorted(frames, key=lambda pitch_frame: pitch_frame.time_s)


def _max_voiced_intensity_db(frames: Sequence[PitchHumFrame]) -> float | None:
    voiced_levels = [
        pitch_frame.intensity_db
        for pitch_frame in frames
        if pitch_frame.pitch_hz is not None and pitch_frame.intensity_db is not None
    ]
    return max(voiced_levels) if voiced_levels else None


def _ramp_step(sample_rate: int) -> float:
    ramp_samples = max(1, round(sample_rate * HUM_RAMP_MS / 1000))
    return 1 / ramp_samples


def _sample_frame_pair(
    sorted_frames: Sequence[PitchHumFrame],
    frame_index: int,
    time_s: float,
) -> tuple[int, PitchHumFrame | None, PitchHumFrame | None]:
    while (
        frame_index + 1 < len(sorted_frames)
        and sorted_frames[frame_index + 1].time_s <= time_s
    ):
        frame_index += 1
    frame = sorted_frames[frame_index] if sorted_frames else None
    next_frame = (
        sorted_frames[frame_index + 1]
        if frame_index + 1 < len(sorted_frames)
        else None
    )
    return frame_index, frame, next_frame


def _frame_amplitude_for_pitch(
    frame: PitchHumFrame | None,
    pitch_hz: float | None,
    max_intensity_db: float | None,
) -> float:
    if frame is None or pitch_hz is None:
        return 0.0
    return _frame_amplitude(frame, max_intensity_db)


def _advance_envelope(envelope: float, target: float, ramp_step: float) -> float:
    if envelope < target:
        return min(target, envelope + ramp_step)
    return max(target, envelope - ramp_step)


def _synthesize_pitch_hum_pcm(
    frames: Sequence[PitchHumFrame],
    duration_s: float,
    *,
    sample_rate: int = HUM_SAMPLE_RATE,
) -> array[int]:
    sample_count = max(0, int(round(duration_s * sample_rate)))
    pcm = array("h")
    if sample_count == 0:
        return pcm
    sorted_frames = _sorted_pitch_frames(frames)
    max_intensity_db = _max_voiced_intensity_db(sorted_frames)
    ramp_step = _ramp_step(sample_rate)
    phase = 0.0
    envelope = 0.0
    frame_index = 0
    for sample_index in range(sample_count):
        time_s = sample_index / sample_rate
        frame_index, frame, next_frame = _sample_frame_pair(
            sorted_frames,
            frame_index,
            time_s,
        )
        pitch_hz = _frame_pitch_at(time_s, frame, next_frame)
        target = _frame_amplitude_for_pitch(frame, pitch_hz, max_intensity_db)
        envelope = _advance_envelope(envelope, target, ramp_step)
        if pitch_hz is None:
            pcm.append(0)
            continue
        phase = (phase + (2 * math.pi * pitch_hz / sample_rate)) % (2 * math.pi)
        sample = sum(weight * math.sin(phase * harmonic) for harmonic, weight in _HARMONICS)
        pcm.append(round(max(-1.0, min(1.0, sample * envelope)) * 32767))
    return _apply_nasal_onsets(pcm, sorted_frames, duration_s, sample_rate=sample_rate)


def _synthesize_pitch_tier_pcm(
    pitch_tier_sound: Any,
    frames: Sequence[PitchHumFrame],
    duration_s: float,
    *,
    sample_rate: int = HUM_SAMPLE_RATE,
) -> array[int]:
    sample_count = max(0, int(round(duration_s * sample_rate)))
    pcm = array("h")
    if sample_count == 0:
        return pcm
    source_samples = _normalized_sound_samples(pitch_tier_sound, sample_count)
    sorted_frames = _sorted_pitch_frames(frames)
    max_intensity_db = _max_voiced_intensity_db(sorted_frames)
    ramp_step = _ramp_step(sample_rate)
    envelope = 0.0
    frame_index = 0
    for sample_index, source_sample in enumerate(source_samples):
        time_s = sample_index / sample_rate
        frame_index, frame, next_frame = _sample_frame_pair(
            sorted_frames,
            frame_index,
            time_s,
        )
        pitch_hz = _frame_pitch_at(time_s, frame, next_frame)
        target = _frame_amplitude_for_pitch(frame, pitch_hz, max_intensity_db)
        envelope = _advance_envelope(envelope, target, ramp_step)
        if target <= 0.0:
            pcm.append(0)
            continue
        sample = max(-1.0, min(1.0, source_sample * envelope))
        pcm.append(round(sample * 32767))
    return _apply_nasal_onsets(pcm, sorted_frames, duration_s, sample_rate=sample_rate)


def _voiced_segments(
    frames: Sequence[PitchHumFrame],
    duration_s: float,
    *,
    max_unvoiced_gap_ms: int = NASAL_DROPOUT_MERGE_MS,
) -> list[tuple[float, float]]:
    sorted_frames = _sorted_pitch_frames(frames)
    duration_s = max(0.0, duration_s)
    max_gap_s = max(0.0, max_unvoiced_gap_ms / 1000)
    segments: list[tuple[float, float]] = []
    for index, pitch_frame in enumerate(sorted_frames):
        if pitch_frame.pitch_hz is None:
            continue
        start_s = max(0.0, min(duration_s, pitch_frame.time_s))
        end_s = duration_s
        if index + 1 < len(sorted_frames):
            end_s = max(start_s, min(duration_s, sorted_frames[index + 1].time_s))
        if end_s <= start_s:
            continue
        if not segments or start_s - segments[-1][1] > max_gap_s:
            segments.append((start_s, end_s))
            continue
        previous_start_s, previous_end_s = segments[-1]
        segments[-1] = (previous_start_s, max(previous_end_s, end_s))
    return segments


def _apply_nasal_onsets(
    pcm: array[int],
    frames: Sequence[PitchHumFrame],
    duration_s: float,
    *,
    sample_rate: int = HUM_SAMPLE_RATE,
) -> array[int]:
    if not pcm or sample_rate <= 0:
        return pcm
    sorted_frames = _sorted_pitch_frames(frames)
    if not sorted_frames:
        return pcm
    max_intensity_db = _max_voiced_intensity_db(sorted_frames)
    onset_samples = max(1, round(sample_rate * NASAL_ONSET_MS / 1000))
    fade_in_samples = max(1, round(sample_rate * NASAL_FADE_IN_MS / 1000))
    for start_s, end_s in _voiced_segments(sorted_frames, duration_s):
        start_sample = max(0, min(len(pcm), round(start_s * sample_rate)))
        end_sample = max(0, min(len(pcm), round(end_s * sample_rate)))
        _apply_nasal_onset(
            pcm,
            sorted_frames,
            max_intensity_db,
            start_sample,
            min(end_sample, start_sample + onset_samples),
            fade_in_samples,
            sample_rate,
        )
    return pcm


def _apply_nasal_onset(
    pcm: array[int],
    sorted_frames: Sequence[PitchHumFrame],
    max_intensity_db: float | None,
    start_sample: int,
    end_sample: int,
    fade_in_samples: int,
    sample_rate: int,
) -> None:
    if end_sample <= start_sample:
        return
    phase = 0.0
    frame_index = _frame_index_at(start_sample / sample_rate, sorted_frames)
    onset_sample_count = max(1, end_sample - start_sample)
    for sample_index in range(start_sample, end_sample):
        time_s = sample_index / sample_rate
        while (
            frame_index + 1 < len(sorted_frames)
            and sorted_frames[frame_index + 1].time_s <= time_s
        ):
            frame_index += 1
        frame = sorted_frames[frame_index]
        next_frame = (
            sorted_frames[frame_index + 1]
            if frame_index + 1 < len(sorted_frames)
            else None
        )
        pitch_hz = _frame_pitch_at(time_s, frame, next_frame)
        if pitch_hz is None:
            continue
        phase = (phase + (2 * math.pi * pitch_hz / sample_rate)) % (2 * math.pi)
        offset = sample_index - start_sample
        nasal_weight = 1.0 - _smoothstep(offset / max(1, onset_sample_count - 1))
        fade_in = _smoothstep(offset / fade_in_samples)
        nasal_sample = _nasal_sample(phase) * _frame_amplitude(frame, max_intensity_db)
        original_sample = pcm[sample_index]
        mixed_sample = (nasal_sample * fade_in * nasal_weight * 32767) + (
            original_sample * (1.0 - nasal_weight)
        )
        pcm[sample_index] = round(max(-32768, min(32767, mixed_sample)))


def _frame_index_at(
    time_s: float,
    sorted_frames: Sequence[PitchHumFrame],
) -> int:
    frame_index = 0
    while (
        frame_index + 1 < len(sorted_frames)
        and sorted_frames[frame_index + 1].time_s <= time_s
    ):
        frame_index += 1
    return frame_index


def _nasal_sample(phase: float) -> float:
    return sum(
        weight * math.sin(phase * harmonic)
        for harmonic, weight in _NASAL_HARMONICS
    )


def _smoothstep(progress: float) -> float:
    progress = max(0.0, min(1.0, progress))
    return progress * progress * (3 - (2 * progress))


def _normalized_sound_samples(sound: Any, sample_count: int) -> list[float]:
    values = getattr(sound, "values", None)
    if values is None or len(values) == 0:
        return [0.0] * sample_count
    channel = list(values[0])
    max_abs = max((abs(float(sample)) for sample in channel), default=0.0)
    if max_abs <= 0.0:
        return [0.0] * sample_count
    samples = [float(sample) / max_abs for sample in channel[:sample_count]]
    if len(samples) < sample_count:
        samples.extend([0.0] * (sample_count - len(samples)))
    return samples


def _frame_pitch_at(
    time_s: float,
    frame: PitchHumFrame | None,
    next_frame: PitchHumFrame | None,
) -> float | None:
    if frame is None or frame.pitch_hz is None:
        return None
    if next_frame is None or next_frame.pitch_hz is None or next_frame.time_s <= frame.time_s:
        return frame.pitch_hz
    progress = max(0.0, min(1.0, (time_s - frame.time_s) / (next_frame.time_s - frame.time_s)))
    return frame.pitch_hz + ((next_frame.pitch_hz - frame.pitch_hz) * progress)


def _frame_amplitude(frame: PitchHumFrame, max_intensity_db: float | None) -> float:
    if frame.intensity_db is None or max_intensity_db is None:
        return HUM_BASE_AMPLITUDE
    relative_gain = 10 ** ((frame.intensity_db - max_intensity_db) / 20)
    return HUM_BASE_AMPLITUDE * max(0.2, min(1.0, relative_gain))


def _sound_duration_s(sound: Any, frames: Sequence[PitchHumFrame]) -> float:
    get_total_duration = getattr(sound, "get_total_duration", None)
    if callable(get_total_duration):
        return max(0.0, float(get_total_duration()))
    if frames:
        return max(frame.time_s for frame in frames)
    return 0.0


def _nearest_intensity(
    time_s: float,
    intensity_times: list[float],
    intensity_values: list[Any],
) -> float | None:
    if not intensity_times or not intensity_values:
        return None
    index = min(range(len(intensity_times)), key=lambda idx: abs(intensity_times[idx] - time_s))
    if index >= len(intensity_values):
        return None
    try:
        return float(intensity_values[index])
    except (TypeError, ValueError):
        return None
