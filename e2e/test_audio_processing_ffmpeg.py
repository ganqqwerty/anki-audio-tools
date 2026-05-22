"""E2E tests that exercise real ffmpeg audio rendering."""

from __future__ import annotations

import math
import subprocess
import wave
from array import array
from pathlib import Path

import pytest

from e2e.helpers import generate_tone

FORMAT_FIXTURES = (
    ("aac", ("-c:a", "aac", "-f", "adts")),
    ("flac", ("-c:a", "flac")),
    ("m4a", ("-c:a", "aac", "-f", "mp4")),
    ("mp3", ("-c:a", "libmp3lame")),
    ("oga", ("-ac", "2", "-c:a", "vorbis", "-strict", "-2", "-f", "ogg")),
    ("ogg", ("-ac", "2", "-c:a", "vorbis", "-strict", "-2", "-f", "ogg")),
    ("opus", ("-ar", "48000", "-c:a", "opus", "-strict", "-2", "-f", "opus")),
    ("wav", ("-c:a", "pcm_s16le")),
    ("webm", ("-ar", "48000", "-c:a", "opus", "-strict", "-2", "-f", "webm")),
)


PITCH_HUM_SAMPLE_RATE = 22_050


def _write_voiced_silence_voiced_wav(path: Path) -> None:
    samples = array("h")
    for duration_s, pitch_hz in ((0.35, 220.0), (0.35, None), (0.35, 330.0)):
        segment_samples = round(duration_s * PITCH_HUM_SAMPLE_RATE)
        for sample_index in range(segment_samples):
            if pitch_hz is None:
                samples.append(0)
                continue
            phase = 2 * math.pi * pitch_hz * sample_index / PITCH_HUM_SAMPLE_RATE
            samples.append(round(math.sin(phase) * 0.35 * 32767))
    _write_mono_wav(path, samples)


def _write_rich_pitch_wav(path: Path, *, duration_s: float = 0.9) -> None:
    weights = ((1, 0.38), (2, 0.33), (3, 0.28), (4, 0.24), (5, 0.18))
    weight_sum = sum(weight for _harmonic, weight in weights)
    samples = array("h")
    for sample_index in range(round(duration_s * PITCH_HUM_SAMPLE_RATE)):
        sample = sum(
            weight
            * math.sin(2 * math.pi * 220.0 * harmonic * sample_index / PITCH_HUM_SAMPLE_RATE)
            for harmonic, weight in weights
        )
        samples.append(round(sample / weight_sum * 0.65 * 32767))
    _write_mono_wav(path, samples)


def _write_mono_wav(path: Path, samples: array[int]) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(PITCH_HUM_SAMPLE_RATE)
        wav_file.writeframes(samples.tobytes())


def _decode_mono_pcm(ffmpeg_config, path: Path) -> array[int]:
    result = subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-i",
            str(path),
            "-f",
            "s16le",
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            str(PITCH_HUM_SAMPLE_RATE),
            "-",
        ],
        check=True,
        capture_output=True,
    )
    samples = array("h")
    samples.frombytes(result.stdout)
    return samples


def _read_wav_pcm(path: Path) -> array[int]:
    with wave.open(str(path), "rb") as wav_file:
        samples = array("h")
        samples.frombytes(wav_file.readframes(wav_file.getnframes()))
    return samples


def _region(samples: array[int], start_s: float, end_s: float) -> array[int]:
    start = round(start_s * PITCH_HUM_SAMPLE_RATE)
    end = round(end_s * PITCH_HUM_SAMPLE_RATE)
    return samples[start:end]


def _region_rms(samples: array[int], start_s: float, end_s: float) -> float:
    region = _region(samples, start_s, end_s)
    if not region:
        return 0.0
    return math.sqrt(sum(sample * sample for sample in region) / len(region))


def _goertzel_power(samples: array[int], frequency_hz: float) -> float:
    if not samples:
        return 0.0
    coefficient = 2 * math.cos(2 * math.pi * frequency_hz / PITCH_HUM_SAMPLE_RATE)
    previous = 0.0
    previous2 = 0.0
    for sample in samples:
        current = float(sample) + coefficient * previous - previous2
        previous2 = previous
        previous = current
    return previous2 * previous2 + previous * previous - coefficient * previous * previous2


def _upper_harmonic_ratio(samples: array[int], start_s: float, end_s: float) -> float:
    region = _region(samples, start_s, end_s)
    fundamental = max(_goertzel_power(region, 220.0), 1.0)
    upper = sum(_goertzel_power(region, frequency) for frequency in (440.0, 660.0, 880.0))
    return upper / fundamental


def _generate_audio_fixture(ffmpeg_config, path: Path, output_args: tuple[str, ...]) -> None:
    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=0.8",
            "-vn",
            "-ac",
            "1",
            "-ar",
            "44100",
            *output_args,
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


# noinspection PyUnusedLocal
def test_trim_left_renders_shorter_recording(
    anki_mw,
    tmp_path: Path,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms, render_audio
    from anki_audio_quick_editor.audio_state import AudioEditState

    del anki_mw
    source = tmp_path / "sentence with spaces.wav"
    output = tmp_path / "trimmed.mp3"
    generate_tone(ffmpeg_config, source, duration_s=2.0)

    original_duration_ms = probe_duration_ms(source, ffmpeg_config)
    render_audio(
        source,
        AudioEditState(source_file=source.name, left_trim_ms=500),
        ffmpeg_config,
        output_path=output,
    )
    trimmed_duration_ms = probe_duration_ms(output, ffmpeg_config)

    assert 1900 <= original_duration_ms <= 2100
    assert 1350 <= trimmed_duration_ms <= 1650
    assert trimmed_duration_ms < original_duration_ms - 350


# noinspection PyUnusedLocal
def test_speed_up_renders_shorter_mp3(
    anki_mw,
    tmp_path: Path,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms, render_audio
    from anki_audio_quick_editor.audio_state import AudioEditState

    del anki_mw
    source = tmp_path / "speed-source.wav"
    output = tmp_path / "faster.mp3"
    generate_tone(ffmpeg_config, source, duration_s=2.0)

    original_duration_ms = probe_duration_ms(source, ffmpeg_config)
    render_audio(
        source,
        AudioEditState(source_file=source.name, speed=1.25),
        ffmpeg_config,
        output_path=output,
    )
    faster_duration_ms = probe_duration_ms(output, ffmpeg_config)

    assert 1500 <= faster_duration_ms <= 1750
    assert faster_duration_ms < original_duration_ms - 250


# noinspection PyUnusedLocal
def test_volume_gain_renders_new_mp3_with_db_filter(
    anki_mw,
    tmp_path: Path,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import (
        format_ffmpeg_command,
        render_audio,
    )
    from anki_audio_quick_editor.audio_state import AudioEditState

    del anki_mw
    source = tmp_path / "volume-source.wav"
    louder = tmp_path / "louder.mp3"
    quieter = tmp_path / "quieter.mp3"
    generate_tone(ffmpeg_config, source, duration_s=1.0)

    louder_result = render_audio(
        source,
        AudioEditState(source_file=source.name, volume_db=6.0),
        ffmpeg_config,
        output_path=louder,
    )
    quieter_result = render_audio(
        source,
        AudioEditState(source_file=source.name, volume_db=-6.0),
        ffmpeg_config,
        output_path=quieter,
    )

    assert louder.is_file()
    assert quieter.is_file()
    assert "volume=6.00dB" in format_ffmpeg_command(louder_result.command)
    assert "volume=-6.00dB" in format_ffmpeg_command(quieter_result.command)


# noinspection PyUnusedLocal
@pytest.mark.parametrize(("extension", "output_args"), FORMAT_FIXTURES)
def test_common_audio_input_format_renders_to_mp3(
    anki_mw,
    tmp_path: Path,
    ffmpeg_config,
    extension: str,
    output_args: tuple[str, ...],
) -> None:
    from anki_audio_quick_editor.audio_processor import probe_duration_ms, render_audio
    from anki_audio_quick_editor.audio_state import AudioEditState

    del anki_mw
    source = tmp_path / f"common-input.{extension}"
    output = tmp_path / f"rendered-{extension}.mp3"
    _generate_audio_fixture(ffmpeg_config, source, output_args)

    result = render_audio(
        source,
        AudioEditState(source_file=source.name, volume_db=-1.0),
        ffmpeg_config,
        output_path=output,
    )

    assert output.is_file()
    assert result.output_path == output
    assert result.output_path.suffix == ".mp3"
    assert "libmp3lame" in result.command
    assert probe_duration_ms(output, ffmpeg_config) > 0


def test_final_save_writes_new_anki_media_without_overwriting_original(
    anki_mw,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import (
        make_output_filename,
        probe_duration_ms,
        render_audio,
        temp_final_path,
    )
    from anki_audio_quick_editor.audio_state import AudioEditState

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "original_sentence.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.5)
    original_bytes = source.read_bytes()

    desired_name = make_output_filename(source.name)
    rendered_path = temp_final_path(desired_name)
    render_audio(
        source,
        AudioEditState(source_file=source.name, left_trim_ms=400),
        ffmpeg_config,
        output_path=rendered_path,
    )
    saved_name = anki_mw.col.media.write_data(desired_name, rendered_path.read_bytes())
    saved_path = media_dir / saved_name

    assert saved_name.endswith(".mp3")
    assert saved_path.is_file()
    assert source.read_bytes() == original_bytes
    assert probe_duration_ms(saved_path, ffmpeg_config) < probe_duration_ms(source, ffmpeg_config)


# noinspection PyUnusedLocal
def test_pitch_hum_algorithms_keep_unvoiced_regions_silent(
    anki_mw,
    tmp_path: Path,
    ffmpeg_config,
) -> None:
    pytest.importorskip("parselmouth")
    from anki_audio_quick_editor.audio_processor import (
        probe_duration_ms,
        render_pitch_hum_audio,
        render_pitch_tier_hum_audio,
    )

    del anki_mw
    source = tmp_path / "voiced-silence-voiced.wav"
    direct = tmp_path / "direct-hum.mp3"
    pitch_tier = tmp_path / "pitch-tier-hum.mp3"
    _write_voiced_silence_voiced_wav(source)

    render_pitch_hum_audio(source, ffmpeg_config, output_path=direct)
    render_pitch_tier_hum_audio(source, ffmpeg_config, output_path=pitch_tier)

    for output in (direct, pitch_tier):
        samples = _decode_mono_pcm(ffmpeg_config, output)
        voiced_rms = min(
            _region_rms(samples, 0.12, 0.28),
            _region_rms(samples, 0.82, 0.98),
        )
        gap_rms = _region_rms(samples, 0.47, 0.63)
        assert 900 <= probe_duration_ms(output, ffmpeg_config) <= 1250
        assert voiced_rms > 200
        assert gap_rms < voiced_rms * 0.25


# noinspection PyUnusedLocal
def test_pitch_tier_hum_removes_original_harmonic_timbre(
    anki_mw,
    tmp_path: Path,
    ffmpeg_config,
) -> None:
    pytest.importorskip("parselmouth")
    from anki_audio_quick_editor.audio_processor import render_pitch_tier_hum_audio

    del anki_mw
    source = tmp_path / "rich-harmonic-source.wav"
    pitch_tier = tmp_path / "pitch-tier-hum.mp3"
    _write_rich_pitch_wav(source)

    render_pitch_tier_hum_audio(source, ffmpeg_config, output_path=pitch_tier)

    source_ratio = _upper_harmonic_ratio(_read_wav_pcm(source), 0.12, 0.72)
    pitch_tier_ratio = _upper_harmonic_ratio(_decode_mono_pcm(ffmpeg_config, pitch_tier), 0.12, 0.72)
    assert source_ratio > 0.9
    assert pitch_tier_ratio < source_ratio * 0.35


# noinspection PyUnusedLocal
def test_dpdfnet_renders_from_locked_source_release_asset(
    anki_mw,
    tmp_path: Path,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import (
        current_platform_key,
        find_dpdfnet_bundle,
        probe_duration_ms,
        render_dpdfnet_audio,
    )

    del anki_mw
    if current_platform_key() != "macos-arm64":
        pytest.skip("DPDFNet Lite is bundled for macos-arm64 only in v1.")

    dpdfnet_path = find_dpdfnet_bundle()
    assert dpdfnet_path.parts[-3:] == ("bin", "macos-arm64", "dpdfnet")

    source = tmp_path / "dpdfnet-source.wav"
    output = tmp_path / "dpdfnet-rendered.mp3"
    generate_tone(ffmpeg_config, source, duration_s=0.8)

    result = render_dpdfnet_audio(source, ffmpeg_config, output_path=output)

    assert result.output_path == output
    assert result.command[:2] == (str(dpdfnet_path), "enhance")
    assert output.is_file()
    assert output.suffix == ".mp3"
    assert probe_duration_ms(output, ffmpeg_config) > 0
