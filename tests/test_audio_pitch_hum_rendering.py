from __future__ import annotations

import sys
import wave
from array import array
from pathlib import Path
from types import SimpleNamespace

import pytest

import anki_audio_quick_editor.audio_pitch_hum as audio_pitch_hum
from anki_audio_quick_editor.audio_output_policy import (
    AudioOutputPolicy,
    AudioSourceMetadata,
)
from anki_audio_quick_editor.audio_pitch_hum import (
    HUM_SAMPLE_RATE,
    PitchHumFrame,
    _encode_pitch_hum_wav,
    _pitch_hum_frames,
    _pitch_hum_output_policy,
    _write_pitch_hum_wav,
    _write_pitch_tier_hum_wav,
    render_pitch_hum_audio,
    render_pitch_tier_hum_audio,
)
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.audio_types import AudioProcessingResult
from anki_audio_quick_editor.errors import AudioProcessingError


def test_render_pitch_hum_uses_generated_output_path_when_none_provided(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.wav"
    generated_output = tmp_path / "generated.oga"
    frames = [PitchHumFrame(time_s=0.0, pitch_hz=220.0, intensity_db=50.0)]
    recorded: dict[str, object] = {}

    fake_parselmouth = SimpleNamespace(
        Sound=lambda source_text: SimpleNamespace(source_text=source_text)
    )
    monkeypatch.setitem(sys.modules, "parselmouth", fake_parselmouth)
    monkeypatch.setattr(audio_pitch_hum, "_is_praat_available", lambda: True)
    monkeypatch.setattr(
        audio_pitch_hum,
        "_pitch_hum_output_policy",
        lambda *_args: SimpleNamespace(extension=".oga"),
    )
    monkeypatch.setattr(
        audio_pitch_hum.tempfile,
        "mkstemp",
        lambda prefix, suffix: (0, str(generated_output)),
    )
    monkeypatch.setattr(audio_pitch_hum, "_pitch_hum_frames", lambda *_args: frames)
    monkeypatch.setattr(audio_pitch_hum, "_sound_duration_s", lambda *_args: 0.25)

    def fake_write(
        wav_path: Path,
        written_frames: list[PitchHumFrame],
        duration_s: float,
    ) -> None:
        recorded["wav_path"] = wav_path
        recorded["frames"] = written_frames
        recorded["duration_s"] = duration_s
        wav_path.write_bytes(b"wav")

    def fake_encode(
        wav_path: Path,
        _config: AudioProcessingConfig,
        output_path: Path,
        _on_command,
        *,
        failure_message: str,
    ) -> AudioProcessingResult:
        recorded["encoded_wav_path"] = wav_path
        recorded["output_path"] = output_path
        recorded["failure_message"] = failure_message
        return AudioProcessingResult(output_path=output_path, command=(), duration_ms=250)

    monkeypatch.setattr(audio_pitch_hum, "_write_pitch_hum_wav", fake_write)
    monkeypatch.setattr(audio_pitch_hum, "_encode_pitch_hum_wav", fake_encode)

    result = render_pitch_hum_audio(source, AudioProcessingConfig())

    assert result == AudioProcessingResult(output_path=generated_output, command=(), duration_ms=250)
    assert recorded["wav_path"] == recorded["encoded_wav_path"]
    assert Path(recorded["wav_path"]).name == "pitch_hum.wav"
    assert recorded["frames"] == frames
    assert recorded["duration_s"] == 0.25
    assert recorded["output_path"] == generated_output
    assert recorded["failure_message"] == "Pitch hum rendering failed."


def test_render_pitch_tier_uses_generated_output_path_when_none_provided(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.wav"
    generated_output = tmp_path / "generated.webm"
    frames = [PitchHumFrame(time_s=0.0, pitch_hz=220.0, intensity_db=50.0)]
    calls: list[str] = []
    recorded: dict[str, object] = {}

    class FakeSound:
        def __init__(self, source_text: str) -> None:
            recorded["source_text"] = source_text

    def fake_call(_target: object, command: str, *_args: object) -> object:
        calls.append(command)
        if command == "To Manipulation":
            return "manipulation"
        if command == "Extract pitch tier":
            return "pitch-tier"
        if command == "To Sound (sine)":
            return SimpleNamespace(values=[[0.5] * round(0.1 * HUM_SAMPLE_RATE)])
        raise AssertionError(f"Unexpected Praat command: {command}")

    fake_parselmouth = SimpleNamespace(Sound=FakeSound)
    monkeypatch.setitem(sys.modules, "parselmouth", fake_parselmouth)
    monkeypatch.setattr(audio_pitch_hum, "_is_praat_available", lambda: True)
    monkeypatch.setattr(
        audio_pitch_hum,
        "import_module",
        lambda name: SimpleNamespace(call=fake_call) if name == "parselmouth.praat" else None,
    )
    monkeypatch.setattr(
        audio_pitch_hum,
        "_pitch_hum_output_policy",
        lambda *_args: SimpleNamespace(extension=".webm"),
    )
    monkeypatch.setattr(
        audio_pitch_hum.tempfile,
        "mkstemp",
        lambda prefix, suffix: (0, str(generated_output)),
    )
    monkeypatch.setattr(audio_pitch_hum, "_pitch_hum_frames", lambda *_args: frames)
    monkeypatch.setattr(audio_pitch_hum, "_sound_duration_s", lambda *_args: 0.1)

    def fake_write(
        wav_path: Path,
        pitch_tier_sound: object,
        written_frames: list[PitchHumFrame],
        duration_s: float,
    ) -> None:
        recorded["wav_path"] = wav_path
        recorded["pitch_tier_sound"] = pitch_tier_sound
        recorded["frames"] = written_frames
        recorded["duration_s"] = duration_s
        wav_path.write_bytes(b"wav")

    def fake_encode(
        wav_path: Path,
        _config: AudioProcessingConfig,
        output_path: Path,
        _on_command,
        *,
        failure_message: str,
    ) -> AudioProcessingResult:
        recorded["encoded_wav_path"] = wav_path
        recorded["output_path"] = output_path
        recorded["failure_message"] = failure_message
        return AudioProcessingResult(output_path=output_path, command=(), duration_ms=100)

    monkeypatch.setattr(audio_pitch_hum, "_write_pitch_tier_hum_wav", fake_write)
    monkeypatch.setattr(audio_pitch_hum, "_encode_pitch_hum_wav", fake_encode)

    result = render_pitch_tier_hum_audio(source, AudioProcessingConfig())

    assert result == AudioProcessingResult(output_path=generated_output, command=(), duration_ms=100)
    assert calls == ["To Manipulation", "Extract pitch tier", "To Sound (sine)"]
    assert recorded["wav_path"] == recorded["encoded_wav_path"]
    assert Path(recorded["wav_path"]).name == "pitch_tier.wav"
    assert recorded["frames"] == frames
    assert recorded["duration_s"] == 0.1
    assert recorded["output_path"] == generated_output
    assert recorded["failure_message"] == "PitchTier rendering failed."


def test_encode_pitch_hum_wav_reports_command_and_duration_on_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    wav_path = tmp_path / "pitch_hum.wav"
    output_path = tmp_path / "pitch_hum.mp3"
    policy = AudioOutputPolicy(
        output_format="mp3",
        extension=".mp3",
        mime_type="audio/mpeg",
        codec_args=("-codec:a", "libmp3lame", "-q:a", "4"),
    )
    command = ("ffmpeg", "-i", str(wav_path), str(output_path))
    seen_commands: list[tuple[str, ...]] = []

    monkeypatch.setattr(audio_pitch_hum, "find_ffmpeg", lambda _path: Path("ffmpeg"))
    monkeypatch.setattr(audio_pitch_hum, "_pitch_hum_output_policy", lambda *_args: policy)
    monkeypatch.setattr(audio_pitch_hum, "build_audio_encode_command", lambda *_args: command)
    monkeypatch.setattr(
        audio_pitch_hum.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stderr="", stdout=""),
    )
    monkeypatch.setattr(audio_pitch_hum, "probe_duration_ms", lambda *_args: 321)

    result = _encode_pitch_hum_wav(
        wav_path,
        AudioProcessingConfig(),
        output_path,
        seen_commands.append,
        failure_message="Pitch hum rendering failed.",
    )

    assert seen_commands == [command]
    assert result == AudioProcessingResult(output_path=output_path, command=command, duration_ms=321)


def test_encode_pitch_hum_wav_uses_stderr_when_encoder_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    policy = AudioOutputPolicy(
        output_format="mp3",
        extension=".mp3",
        mime_type="audio/mpeg",
        codec_args=(),
    )

    monkeypatch.setattr(audio_pitch_hum, "find_ffmpeg", lambda _path: Path("ffmpeg"))
    monkeypatch.setattr(audio_pitch_hum, "_pitch_hum_output_policy", lambda *_args: policy)
    monkeypatch.setattr(
        audio_pitch_hum,
        "build_audio_encode_command",
        lambda *_args: ("ffmpeg", "encode"),
    )
    monkeypatch.setattr(
        audio_pitch_hum.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stderr="encoder failed\n", stdout=""),
    )

    with pytest.raises(AudioProcessingError, match="encoder failed"):
        _encode_pitch_hum_wav(
            tmp_path / "pitch_hum.wav",
            AudioProcessingConfig(),
            tmp_path / "pitch_hum.mp3",
            None,
            failure_message="Pitch hum rendering failed.",
        )


def test_encode_pitch_hum_wav_uses_fallback_message_when_encoder_is_silent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    policy = AudioOutputPolicy(
        output_format="mp3",
        extension=".mp3",
        mime_type="audio/mpeg",
        codec_args=(),
    )

    monkeypatch.setattr(audio_pitch_hum, "find_ffmpeg", lambda _path: Path("ffmpeg"))
    monkeypatch.setattr(audio_pitch_hum, "_pitch_hum_output_policy", lambda *_args: policy)
    monkeypatch.setattr(
        audio_pitch_hum,
        "build_audio_encode_command",
        lambda *_args: ("ffmpeg", "encode"),
    )
    monkeypatch.setattr(
        audio_pitch_hum.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stderr=" \n", stdout=""),
    )

    with pytest.raises(AudioProcessingError, match="Pitch hum rendering failed."):
        _encode_pitch_hum_wav(
            tmp_path / "pitch_hum.wav",
            AudioProcessingConfig(),
            tmp_path / "pitch_hum.mp3",
            None,
            failure_message="Pitch hum rendering failed.",
        )


def test_encode_pitch_hum_wav_wraps_launch_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    policy = AudioOutputPolicy(
        output_format="mp3",
        extension=".mp3",
        mime_type="audio/mpeg",
        codec_args=(),
    )

    monkeypatch.setattr(audio_pitch_hum, "find_ffmpeg", lambda _path: Path("ffmpeg"))
    monkeypatch.setattr(audio_pitch_hum, "_pitch_hum_output_policy", lambda *_args: policy)
    monkeypatch.setattr(
        audio_pitch_hum,
        "build_audio_encode_command",
        lambda *_args: ("ffmpeg", "encode"),
    )
    monkeypatch.setattr(
        audio_pitch_hum,
        "launch_error_message",
        lambda prefix, exc: f"{prefix} ({exc.strerror})",
    )

    def raise_permission_error(*_args: object, **_kwargs: object) -> SimpleNamespace:
        raise PermissionError(13, "Permission denied", "ffmpeg")

    monkeypatch.setattr(audio_pitch_hum.subprocess, "run", raise_permission_error)

    with pytest.raises(AudioProcessingError, match="Could not start pitch hum encoding."):
        _encode_pitch_hum_wav(
            tmp_path / "pitch_hum.wav",
            AudioProcessingConfig(),
            tmp_path / "pitch_hum.mp3",
            None,
            failure_message="Pitch hum rendering failed.",
        )


def test_pitch_hum_output_policy_falls_back_to_synthetic_metadata_when_probe_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_resolve(
        metadata: AudioSourceMetadata,
        *,
        requested_format: object,
        output_path: Path | None = None,
    ) -> AudioOutputPolicy:
        captured["metadata"] = metadata
        captured["requested_format"] = requested_format
        captured["output_path"] = output_path
        return AudioOutputPolicy(
            output_format="ogg",
            extension=".ogg",
            mime_type="audio/ogg",
            codec_args=("-codec:a", "libvorbis"),
        )

    monkeypatch.setattr(
        audio_pitch_hum,
        "probe_audio_metadata",
        lambda *_args: (_ for _ in ()).throw(AudioProcessingError("ffprobe unavailable")),
    )
    monkeypatch.setattr(
        audio_pitch_hum,
        "resolve_output_policy_from_metadata",
        fake_resolve,
    )

    output_path = Path("pitch-hum.ogg")
    policy = _pitch_hum_output_policy(
        Path("source.wav"),
        AudioProcessingConfig(output_format="ogg"),
        output_path,
    )

    metadata = captured["metadata"]
    assert isinstance(metadata, AudioSourceMetadata)
    assert metadata.path == Path("source.wav")
    assert metadata.visible_format == "ogg"
    assert metadata.codec_name == "pcm_s16le"
    assert metadata.sample_rate == HUM_SAMPLE_RATE
    assert metadata.channels == 1
    assert captured["requested_format"] == "ogg"
    assert captured["output_path"] == output_path
    assert policy.extension == ".ogg"


def test_pitch_hum_frames_use_ac_analysis_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSound:
        def to_pitch_ac(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(
                xs=lambda: [0.0, 0.1],
                selected_array={"frequency": [220.0, 0.0]},
            )

        def to_pitch(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(
                xs=lambda: [0.0, 0.1],
                selected_array={"frequency": [110.0, 110.0]},
            )

        def to_intensity(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(
                xs=lambda: [0.0, 0.1],
                values=[[45.0, 55.0]],
            )

    monkeypatch.setattr(
        audio_pitch_hum,
        "sanitize_pitch_hum_frames",
        lambda frames, **_kwargs: frames,
    )

    frames = _pitch_hum_frames(FakeSound(), AudioProcessingConfig())

    assert frames == [
        PitchHumFrame(time_s=0.0, pitch_hz=220.0, intensity_db=45.0),
        PitchHumFrame(time_s=0.1, pitch_hz=None, intensity_db=55.0),
    ]


def test_pitch_hum_frames_fall_back_to_basic_pitch_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSound:
        def to_pitch(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(
                xs=lambda: [0.0, 0.2],
                selected_array={"frequency": [-5.0, 330.0]},
            )

        def to_intensity(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(
                xs=lambda: [0.0, 0.2],
                values=[[40.0, 60.0]],
            )

    monkeypatch.setattr(
        audio_pitch_hum,
        "sanitize_pitch_hum_frames",
        lambda frames, **_kwargs: frames,
    )

    frames = _pitch_hum_frames(FakeSound(), AudioProcessingConfig())

    assert frames == [
        PitchHumFrame(time_s=0.0, pitch_hz=None, intensity_db=40.0),
        PitchHumFrame(time_s=0.2, pitch_hz=330.0, intensity_db=60.0),
    ]


def test_write_pitch_hum_wav_emits_mono_pcm16_wave(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "pitch_hum.wav"
    samples = array("h", [120, -240, 360])

    monkeypatch.setattr(
        audio_pitch_hum,
        "_synthesize_pitch_hum_pcm",
        lambda *_args, **_kwargs: samples,
    )

    _write_pitch_hum_wav(output_path, [], 0.1, sample_rate=12345)

    with wave.open(str(output_path), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 12345
        assert wav_file.readframes(wav_file.getnframes()) == samples.tobytes()


def test_write_pitch_tier_hum_wav_emits_mono_pcm16_wave(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "pitch_tier.wav"
    samples = array("h", [90, -180, 270, -360])

    monkeypatch.setattr(
        audio_pitch_hum,
        "_synthesize_pitch_tier_pcm",
        lambda *_args, **_kwargs: samples,
    )

    _write_pitch_tier_hum_wav(
        output_path,
        SimpleNamespace(values=[[0.5] * len(samples)]),
        [],
        0.2,
        sample_rate=16000,
    )

    with wave.open(str(output_path), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 16000
        assert wav_file.readframes(wav_file.getnframes()) == samples.tobytes()
