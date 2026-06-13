from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import anki_audio_quick_editor.audio_pitch_hum as audio_pitch_hum
from anki_audio_quick_editor.audio_output_policy import AudioOutputPolicy
from anki_audio_quick_editor.audio_pitch_hum import (
    _encode_pitch_hum_wav,
)
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.audio_types import AudioProcessingResult
from anki_audio_quick_editor.errors import AudioProcessingError


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
