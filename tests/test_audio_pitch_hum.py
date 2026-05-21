"""Tests for Praat-guided pitch hum resynthesis."""

from __future__ import annotations

import math
import sys
import wave
from array import array
from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_pitch_hum import (
    HUM_SAMPLE_RATE,
    PitchHumFrame,
    _apply_nasal_onsets,
    _synthesize_pitch_hum_pcm,
    _synthesize_pitch_tier_pcm,
    _voiced_segments,
    render_pitch_hum_audio,
    render_pitch_tier_hum_audio,
)
from anki_audio_quick_editor.audio_pitch_hum_frames import sanitize_pitch_hum_frames
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.audio_types import AudioProcessingResult
from anki_audio_quick_editor.errors import AudioProcessingError


def _write_voiced_silence_voiced_wav(path: Path) -> None:
    samples = array("h")
    for duration_s, pitch_hz in ((0.35, 220.0), (0.35, None), (0.35, 330.0)):
        segment_samples = round(duration_s * HUM_SAMPLE_RATE)
        for sample_index in range(segment_samples):
            if pitch_hz is None:
                samples.append(0)
                continue
            phase = 2 * math.pi * pitch_hz * sample_index / HUM_SAMPLE_RATE
            samples.append(round(math.sin(phase) * 0.35 * 32767))
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(HUM_SAMPLE_RATE)
        wav_file.writeframes(samples.tobytes())


def _read_wav_pcm(path: Path) -> tuple[int, array[int]]:
    with wave.open(str(path), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        samples = array("h")
        samples.frombytes(wav_file.readframes(wav_file.getnframes()))
    return sample_rate, samples


def _region_rms(samples: array[int], sample_rate: int, start_s: float, end_s: float) -> float:
    start = round(start_s * sample_rate)
    end = round(end_s * sample_rate)
    region = samples[start:end]
    if not region:
        return 0.0
    return math.sqrt(sum(sample * sample for sample in region) / len(region))


def test_sanitize_pitch_hum_frames_clamps_to_pitch_range() -> None:
    frames = [
        PitchHumFrame(time_s=0.00, pitch_hz=40.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.01, pitch_hz=1200.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.02, pitch_hz=None, intensity_db=None),
    ]

    sanitized = sanitize_pitch_hum_frames(
        frames,
        pitch_floor_hz=75.0,
        pitch_ceiling_hz=500.0,
    )

    assert [frame.pitch_hz for frame in sanitized] == [75.0, 500.0, None]


def test_sanitize_pitch_hum_frames_drops_octave_spikes() -> None:
    frames = [
        PitchHumFrame(time_s=0.00, pitch_hz=220.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.01, pitch_hz=880.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.02, pitch_hz=225.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.03, pitch_hz=230.0, intensity_db=50.0),
    ]

    sanitized = sanitize_pitch_hum_frames(
        frames,
        pitch_floor_hz=75.0,
        pitch_ceiling_hz=1000.0,
    )

    assert [frame.pitch_hz for frame in sanitized] == [220.0, None, 225.0, 230.0]


def test_sanitize_pitch_hum_frames_drops_short_voiced_islands() -> None:
    frames = [
        PitchHumFrame(time_s=0.00, pitch_hz=None, intensity_db=None),
        PitchHumFrame(time_s=0.01, pitch_hz=200.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.02, pitch_hz=210.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.035, pitch_hz=None, intensity_db=None),
        PitchHumFrame(time_s=0.08, pitch_hz=230.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.12, pitch_hz=240.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.16, pitch_hz=250.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.20, pitch_hz=None, intensity_db=None),
    ]

    sanitized = sanitize_pitch_hum_frames(
        frames,
        pitch_floor_hz=75.0,
        pitch_ceiling_hz=500.0,
    )

    assert [frame.pitch_hz for frame in sanitized[:4]] == [None, None, None, None]
    assert [frame.pitch_hz for frame in sanitized[4:]] == [230.0, 240.0, 250.0, None]


def test_voiced_segments_merge_short_dropouts_without_merging_real_pauses() -> None:
    frames = [
        PitchHumFrame(time_s=0.00, pitch_hz=220.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.05, pitch_hz=225.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.10, pitch_hz=None, intensity_db=None),
        PitchHumFrame(time_s=0.18, pitch_hz=230.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.30, pitch_hz=None, intensity_db=None),
        PitchHumFrame(time_s=0.46, pitch_hz=240.0, intensity_db=50.0),
    ]

    segments = _voiced_segments(frames, 0.60, max_unvoiced_gap_ms=120)

    assert segments == [(0.0, 0.3), (0.46, 0.6)]


def test_apply_nasal_onsets_preserves_length_and_does_not_sound_short_dropouts() -> None:
    sample_rate = 1000
    frames = [
        PitchHumFrame(time_s=0.00, pitch_hz=200.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.10, pitch_hz=None, intensity_db=None),
        PitchHumFrame(time_s=0.18, pitch_hz=200.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.32, pitch_hz=None, intensity_db=None),
        PitchHumFrame(time_s=0.50, pitch_hz=200.0, intensity_db=50.0),
    ]
    pcm = array("h", [2000] * 650)
    for index in range(100, 180):
        pcm[index] = 0
    for index in range(320, 500):
        pcm[index] = 0
    original = array("h", pcm)

    result = _apply_nasal_onsets(pcm, frames, 0.65, sample_rate=sample_rate)

    assert result is pcm
    assert len(pcm) == len(original)
    assert max(abs(sample) for sample in pcm[100:180]) == 0
    assert pcm[:70] != original[:70]
    assert pcm[180:250] == original[180:250]
    assert pcm[500:570] != original[500:570]


def test_pitch_hum_and_pitch_tier_synthesis_apply_shared_nasal_onsets(monkeypatch) -> None:
    frames = [
        PitchHumFrame(time_s=0.0, pitch_hz=220.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.02, pitch_hz=220.0, intensity_db=50.0),
    ]
    calls: list[tuple[int, float, int]] = []

    def fake_apply(
        pcm: array[int],
        _frames,
        duration_s: float,
        *,
        sample_rate: int,
    ) -> array[int]:
        calls.append((len(pcm), duration_s, sample_rate))
        return pcm

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pitch_hum._apply_nasal_onsets",
        fake_apply,
    )
    _synthesize_pitch_hum_pcm(frames, 0.03, sample_rate=HUM_SAMPLE_RATE)
    pitch_tier_sound = SimpleNamespace(values=[[0.5] * round(0.03 * HUM_SAMPLE_RATE)])
    _synthesize_pitch_tier_pcm(pitch_tier_sound, frames, 0.03, sample_rate=HUM_SAMPLE_RATE)

    expected_sample_count = round(0.03 * HUM_SAMPLE_RATE)
    assert calls == [
        (expected_sample_count, 0.03, HUM_SAMPLE_RATE),
        (expected_sample_count, 0.03, HUM_SAMPLE_RATE),
    ]


def test_pitch_hum_synthesis_keeps_unvoiced_frames_silent() -> None:
    frames = [
        PitchHumFrame(time_s=0.0, pitch_hz=None, intensity_db=None),
        PitchHumFrame(time_s=0.01, pitch_hz=220.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.03, pitch_hz=None, intensity_db=None),
    ]

    pcm = _synthesize_pitch_hum_pcm(frames, 0.06, sample_rate=HUM_SAMPLE_RATE)

    first_region = pcm[: round(0.009 * HUM_SAMPLE_RATE)]
    voiced_region = pcm[round(0.015 * HUM_SAMPLE_RATE) : round(0.025 * HUM_SAMPLE_RATE)]
    tail_region = pcm[round(0.050 * HUM_SAMPLE_RATE) :]
    assert max(abs(sample) for sample in first_region) == 0
    assert max(abs(sample) for sample in voiced_region) > 0
    assert max(abs(sample) for sample in tail_region) == 0


def test_pitch_hum_synthesis_fades_out_before_silencing_unvoiced_tail() -> None:
    sample_rate = 1000
    frames = [
        PitchHumFrame(time_s=0.00, pitch_hz=100.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.02, pitch_hz=100.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.04, pitch_hz=None, intensity_db=None),
    ]

    pcm = _synthesize_pitch_hum_pcm(frames, 0.07, sample_rate=sample_rate)

    fade_tail = pcm[41:55]
    silent_tail = pcm[60:]
    assert max(abs(sample) for sample in fade_tail) > 0
    assert max(abs(sample) for sample in silent_tail) == 0


def test_pitch_hum_synthesis_interpolates_voiced_pitch_without_clicking_to_silence() -> None:
    frames = [
        PitchHumFrame(time_s=0.0, pitch_hz=200.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.02, pitch_hz=240.0, intensity_db=50.0),
    ]

    pcm = _synthesize_pitch_hum_pcm(frames, 0.03, sample_rate=HUM_SAMPLE_RATE)

    assert max(abs(sample) for sample in pcm[round(0.01 * HUM_SAMPLE_RATE) :]) > 0


def test_pitch_tier_synthesis_gates_praat_sine_to_voiced_regions() -> None:
    frames = [
        PitchHumFrame(time_s=0.0, pitch_hz=180.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.02, pitch_hz=None, intensity_db=None),
        PitchHumFrame(time_s=0.04, pitch_hz=220.0, intensity_db=50.0),
    ]
    sine_samples = [0.5] * round(0.06 * HUM_SAMPLE_RATE)
    pitch_tier_sound = SimpleNamespace(values=[sine_samples])

    pcm = _synthesize_pitch_tier_pcm(pitch_tier_sound, frames, 0.06)

    first_voiced = pcm[round(0.01 * HUM_SAMPLE_RATE) : round(0.018 * HUM_SAMPLE_RATE)]
    unvoiced = pcm[round(0.036 * HUM_SAMPLE_RATE) : round(0.039 * HUM_SAMPLE_RATE)]
    second_voiced = pcm[round(0.05 * HUM_SAMPLE_RATE) :]
    assert max(abs(sample) for sample in first_voiced) > 0
    assert max(abs(sample) for sample in unvoiced) == 0
    assert max(abs(sample) for sample in second_voiced) > 0


def test_pitch_tier_synthesis_fades_source_before_silencing_unvoiced_tail() -> None:
    sample_rate = 1000
    frames = [
        PitchHumFrame(time_s=0.00, pitch_hz=100.0, intensity_db=50.0),
        PitchHumFrame(time_s=0.03, pitch_hz=None, intensity_db=None),
    ]
    pitch_tier_sound = SimpleNamespace(values=[[0.5] * round(0.06 * sample_rate)])

    pcm = _synthesize_pitch_tier_pcm(
        pitch_tier_sound,
        frames,
        0.06,
        sample_rate=sample_rate,
    )

    fade_tail = pcm[31:44]
    silent_tail = pcm[50:]
    assert max(abs(sample) for sample in fade_tail) > 0
    assert max(abs(sample) for sample in silent_tail) == 0


def test_renderers_preserve_voiced_regions_and_silence_unvoiced_gap(
    monkeypatch,
    tmp_path: Path,
) -> None:
    pytest.importorskip("parselmouth")
    source = tmp_path / "voiced-silence-voiced.wav"
    _write_voiced_silence_voiced_wav(source)
    region_levels: dict[str, dict[str, float]] = {}

    def fake_encode(
        wav_path: Path,
        _config: AudioProcessingConfig,
        output_path: Path,
        _on_command,
        *,
        failure_message: str,
    ) -> AudioProcessingResult:
        sample_rate, samples = _read_wav_pcm(wav_path)
        label = "pitch_tier" if "PitchTier" in failure_message else "direct"
        region_levels[label] = {
            "first_voiced": _region_rms(samples, sample_rate, 0.12, 0.28),
            "gap": _region_rms(samples, sample_rate, 0.47, 0.63),
            "second_voiced": _region_rms(samples, sample_rate, 0.82, 0.98),
        }
        output_path.write_bytes(b"encoded")
        return AudioProcessingResult(output_path=output_path, command=(), duration_ms=1050)

    monkeypatch.setattr("anki_audio_quick_editor.audio_pitch_hum._encode_pitch_hum_wav", fake_encode)

    render_pitch_hum_audio(source, AudioProcessingConfig(), tmp_path / "direct.mp3")
    render_pitch_tier_hum_audio(source, AudioProcessingConfig(), tmp_path / "pitch-tier.mp3")

    assert set(region_levels) == {"direct", "pitch_tier"}
    for levels in region_levels.values():
        voiced_rms = min(levels["first_voiced"], levels["second_voiced"])
        assert voiced_rms > 500
        assert levels["gap"] < voiced_rms * 0.15


def test_render_pitch_tier_hum_uses_pitch_tier_sine_not_overlap_add(monkeypatch, tmp_path: Path) -> None:
    class FakeSound:
        def __init__(self, path: str) -> None:
            self.path = path

        def get_total_duration(self) -> float:
            return 0.02

        def to_pitch_ac(self, **_kwargs):
            return SimpleNamespace(
                selected_array={"frequency": [220.0, 220.0]},
                xs=lambda: [0.0, 0.01],
            )

        def to_intensity(self, **_kwargs):
            return SimpleNamespace(
                values=[[50.0, 50.0]],
                xs=lambda: [0.0, 0.01],
            )

    calls: list[str] = []

    def fake_call(_target, command: str, *_args):
        calls.append(command)
        if command == "To Manipulation":
            return object()
        if command == "Extract pitch tier":
            return object()
        if command == "To Sound (sine)":
            return SimpleNamespace(values=[[0.5] * round(0.02 * HUM_SAMPLE_RATE)])
        raise AssertionError(f"unexpected Praat command: {command}")

    def fake_encode(wav_path: Path, _config, output_path: Path, _on_command, *, failure_message: str):
        assert wav_path.exists()
        assert failure_message == "PitchTier rendering failed."
        return AudioProcessingResult(output_path=output_path, command=(), duration_ms=20)

    fake_parselmouth = SimpleNamespace(Sound=FakeSound)
    monkeypatch.setitem(sys.modules, "parselmouth", fake_parselmouth)
    monkeypatch.setattr("anki_audio_quick_editor.audio_pitch_hum._is_praat_available", lambda: True)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_pitch_hum.import_module",
        lambda name: SimpleNamespace(call=fake_call) if name == "parselmouth.praat" else None,
    )
    monkeypatch.setattr("anki_audio_quick_editor.audio_pitch_hum._encode_pitch_hum_wav", fake_encode)

    result = render_pitch_tier_hum_audio(tmp_path / "clip.wav", AudioProcessingConfig(), tmp_path / "out.mp3")

    assert result.duration_ms == 20
    assert calls == ["To Manipulation", "Extract pitch tier", "To Sound (sine)"]


def test_render_pitch_hum_requires_parselmouth(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_pitch_hum._is_praat_available", lambda: False)

    with pytest.raises(AudioProcessingError, match="Praat/Parselmouth is required"):
        render_pitch_hum_audio(tmp_path / "clip.wav", AudioProcessingConfig())


def test_render_pitch_tier_hum_requires_parselmouth(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_pitch_hum._is_praat_available", lambda: False)

    with pytest.raises(AudioProcessingError, match="Praat/Parselmouth is required"):
        render_pitch_tier_hum_audio(tmp_path / "clip.wav", AudioProcessingConfig())
