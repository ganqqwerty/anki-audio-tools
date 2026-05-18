from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_processor import (
    _render_external_error_message,
    render_noise_reduced_audio,
    select_deep_filter_output,
)
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.errors import (
    AudioProcessingError,
)
from tests.audio_fixtures import (
    DEEP_FILTER_AVAILABLE,
    FFMPEG_AVAILABLE,
    _db_drop,
    _decode_mono_pcm16,
    _generate_noisy_speech_like_clip,
    _window_rms,
)


def test_select_deep_filter_output_accepts_exactly_one_wav(tmp_path: Path) -> None:
    output = tmp_path / "cleaned.wav"
    output.write_bytes(b"wav")
    (tmp_path / "notes.txt").write_text("ignored")

    assert select_deep_filter_output(tmp_path) == output


def test_select_deep_filter_output_rejects_zero_or_multiple_wavs(tmp_path: Path) -> None:
    with pytest.raises(AudioProcessingError, match="did not produce"):
        select_deep_filter_output(tmp_path)

    (tmp_path / "a.wav").write_bytes(b"a")
    (tmp_path / "b.wav").write_bytes(b"b")

    with pytest.raises(AudioProcessingError, match="multiple"):
        select_deep_filter_output(tmp_path)


def test_render_noise_reduced_audio_runs_prepare_deep_filter_and_encode(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: list[list[str]] = []
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda _path: Path("/bin/deep-filter"),
    )
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        calls.append(cmd)
        if cmd[0] == "/bin/deep-filter":
            output_dir = Path(cmd[cmd.index("-o") + 1])
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "input_48k_mono.wav").write_bytes(b"cleaned")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "cleaned.mp3"
    result = render_noise_reduced_audio(
        tmp_path / "source.mp3",
        AudioProcessingConfig(deep_filter_path="/custom/deep-filter", deep_filter_post_filter=True),
        output_path=output,
        on_command=commands.append,
    )

    assert calls[0][:10] == [
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "source.mp3"),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "48000",
        "-codec:a",
    ]
    assert calls[1][0:3] == ["/bin/deep-filter", "-D", "--pf"]
    assert calls[2][0:4] == ["/bin/ffmpeg", "-y", "-i", calls[2][3]]
    assert calls[2][-5:] == ["-codec:a", "libmp3lame", "-q:a", "4", str(output)]
    assert commands == [tuple(call) for call in calls]
    assert result.output_path == output
    assert result.command == tuple(calls[1])
    assert result.duration_ms == 1000


def test_render_noise_reduced_audio_reports_deep_filter_parameter_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda _path: Path("/bin/deep-filter"),
    )

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        if cmd[0] == "/bin/deep-filter":
            return SimpleNamespace(returncode=2, stdout="", stderr="error: unexpected argument '--atten-lim'")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="unexpected argument '--atten-lim'"):
        render_noise_reduced_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "cleaned.mp3",
        )


def test_render_noise_reduced_audio_reports_deep_filter_launch_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda _path: Path("/bin/deep-filter"),
    )

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        if cmd[0] == "/bin/deep-filter":
            raise PermissionError(13, "Permission denied", "/bin/deep-filter")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="Could not start DeepFilterNet noise removal"):
        render_noise_reduced_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "cleaned.mp3",
        )


def test_render_noise_reduced_audio_reports_prepare_failure_before_deep_filter(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: list[list[str]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda _path: Path("/bin/deep-filter"),
    )

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        calls.append(cmd)
        return SimpleNamespace(returncode=1, stdout="", stderr="prepare failed")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="prepare failed"):
        render_noise_reduced_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "cleaned.mp3",
        )

    assert len(calls) == 1
    assert calls[0][0] == "/bin/ffmpeg"


def test_render_noise_reduced_audio_reports_encode_failure_after_deep_filter(
    monkeypatch,
    tmp_path: Path,
) -> None:
    output = tmp_path / "cleaned.mp3"
    calls: list[list[str]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda _path: Path("/bin/deep-filter"),
    )

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        calls.append(cmd)
        if cmd[0] == "/bin/deep-filter":
            output_dir = Path(cmd[cmd.index("-o") + 1])
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "clean.wav").write_bytes(b"cleaned")
        if cmd[-1] == str(output):
            return SimpleNamespace(returncode=1, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError) as exc_info:
        render_noise_reduced_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=output,
        )

    assert str(exc_info.value) == "Could not encode DeepFilterNet output."
    assert [call[0] for call in calls] == ["/bin/ffmpeg", "/bin/deep-filter", "/bin/ffmpeg"]


def test_render_noise_reduced_audio_uses_default_temp_output_path(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda _path: Path("/bin/deep-filter"),
    )
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1234)

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        if cmd[0] == "/bin/deep-filter":
            output_dir = Path(cmd[cmd.index("-o") + 1])
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "clean.wav").write_bytes(b"cleaned")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    result = render_noise_reduced_audio(tmp_path / "source.mp3", AudioProcessingConfig())

    assert result.output_path.name.startswith("aqe_denoised_")
    assert result.output_path.suffix == ".mp3"
    assert result.duration_ms == 1234


@pytest.mark.parametrize(
    ("result", "default_message", "expected"),
    [
        (
            SimpleNamespace(stderr='{"error":"stderr json failed"}', stdout=""),
            "default failure",
            "stderr json failed",
        ),
        (
            SimpleNamespace(stderr="", stdout='{"error":"stdout json failed"}'),
            "default failure",
            "stdout json failed",
        ),
        (
            SimpleNamespace(stderr=" plain stderr failed ", stdout='{"error":"ignored"}'),
            "default failure",
            "plain stderr failed",
        ),
        (
            SimpleNamespace(stderr="   ", stdout=""),
            "default failure",
            "default failure",
        ),
    ],
)
def test_render_external_error_message_prefers_structured_and_plain_output(
    result: SimpleNamespace,
    default_message: str,
    expected: str,
) -> None:
    assert _render_external_error_message(result, default_message) == expected


@pytest.mark.skipif(
    not FFMPEG_AVAILABLE or not DEEP_FILTER_AVAILABLE,
    reason="deep-filter, ffmpeg, and ffprobe are required for denoise quality smoke tests",
)
def test_render_noise_reduced_audio_reduces_measured_noise_floor(tmp_path: Path) -> None:
    source = tmp_path / "noisy_speech_like.wav"
    output = tmp_path / "denoised.mp3"
    _generate_noisy_speech_like_clip(source)

    input_samples = _decode_mono_pcm16(source)
    input_noise_rms = _window_rms(input_samples, start_s=0.05, end_s=0.30)
    input_signal_rms = _window_rms(input_samples, start_s=0.55, end_s=1.10)

    result = render_noise_reduced_audio(
        source,
        AudioProcessingConfig(deep_filter_post_filter=True),
        output_path=output,
    )

    output_samples = _decode_mono_pcm16(output)
    output_noise_rms = _window_rms(output_samples, start_s=0.05, end_s=0.30)
    output_signal_rms = _window_rms(output_samples, start_s=0.55, end_s=1.10)

    assert result.output_path == output
    assert output.is_file()
    assert result.duration_ms is not None
    assert 1400 <= result.duration_ms <= 1800
    assert _db_drop(input_noise_rms, output_noise_rms) >= 3.0
    assert _db_drop(input_signal_rms, output_signal_rms) < 12.0
