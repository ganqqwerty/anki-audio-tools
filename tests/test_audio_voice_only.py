from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_processor import render_voice_only_audio
from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.errors import AudioProcessingError
from anki_audio_quick_editor.support import (
    clear_latest_spleeter_support_incident,
    latest_spleeter_support_incident,
)


def test_render_voice_only_audio_runs_prepare_spleeter_and_encode(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_spleeter_support_incident()
    calls: list[list[str]] = []
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_ffmpeg",
        lambda _path: Path("/bin/ffmpeg"),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_spleeter_bundle",
        lambda: (
            Path("/bin/sherpa-spleeter"),
            Path("/models/vocals.fp16.onnx"),
            Path("/models/accompaniment.fp16.onnx"),
        ),
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.probe_duration_ms",
        lambda *_args: 1234,
    )

    def fake_run(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: float | None = None,
    ) -> SimpleNamespace:
        calls.append(cmd)
        if cmd[0] == "/bin/sherpa-spleeter":
            vocals_arg = next(value for value in cmd if value.startswith("--output-vocals-wav="))
            Path(vocals_arg.split("=", 1)[1]).write_bytes(b"vocals")
            return SimpleNamespace(returncode=0, stdout='{"ok":true}', stderr="")
        if len(calls) == 3:
            Path(cmd[-1]).write_bytes(b"mp3")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "voice.mp3"
    result = render_voice_only_audio(
        tmp_path / "source.mp3",
        AudioProcessingConfig(),
        output_path=output,
        on_command=commands.append,
    )

    assert calls[0] == [
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "source.mp3"),
        "-vn",
        "-ac",
        "2",
        "-ar",
        "44100",
        "-codec:a",
        "pcm_s16le",
        calls[0][-1],
    ]
    assert calls[1] == [
        "/bin/sherpa-spleeter",
        "--spleeter-vocals=/models/vocals.fp16.onnx",
        "--spleeter-accompaniment=/models/accompaniment.fp16.onnx",
        f"--input-wav={calls[0][-1]}",
        calls[1][4],
        calls[1][5],
        "--num-threads=1",
    ]
    vocals_wav = calls[1][4].split("=", 1)[1]
    assert calls[1][4].startswith("--output-vocals-wav=")
    assert calls[1][5].startswith("--output-accompaniment-wav=")
    assert calls[2][0:4] == ["/bin/ffmpeg", "-y", "-i", vocals_wav]
    assert calls[2][-5:] == ["-codec:a", "libmp3lame", "-q:a", "4", str(output)]
    assert commands == [tuple(call) for call in calls]
    assert result.output_path == output
    assert result.command == tuple(calls[1])
    assert result.duration_ms == 1234
    assert latest_spleeter_support_incident() is None


def test_render_voice_only_audio_reports_spleeter_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_spleeter_support_incident()
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_spleeter_bundle",
        lambda: (
            Path("/bin/sherpa-spleeter"),
            Path("/models/vocals.fp16.onnx"),
            Path("/models/accompaniment.fp16.onnx"),
        ),
    )

    def fake_run(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: float | None = None,
    ) -> SimpleNamespace:
        if cmd[0] == "/bin/sherpa-spleeter":
            return SimpleNamespace(returncode=5, stdout='{"error":"invalid wav"}', stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="invalid wav"):
        render_voice_only_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "voice.mp3",
        )
    incident = latest_spleeter_support_incident()
    assert incident is not None
    assert incident["operation"] == "voice_only"
    assert incident["media_filename"] == "source.mp3"
    assert incident["ffmpeg_path"] == "/bin/ffmpeg"
    assert incident["spleeter_path"] == "/bin/sherpa-spleeter"
    assert incident["vocals_model_path"] == "/models/vocals.fp16.onnx"
    assert incident["accompaniment_model_path"] == "/models/accompaniment.fp16.onnx"
    assert len(incident["attempted_commands"]) == 2
    assert incident["attempted_commands"][1]["command"].startswith("/bin/sherpa-spleeter")
    assert incident["attempted_commands"][1]["returncode"] == 5
    assert incident["attempted_commands"][1]["stdout"] == '{"error":"invalid wav"}'


@pytest.mark.parametrize(
    ("run_behavior", "expected_message"),
    [
        ("missing_vocals", "did not produce vocals.wav"),
        ("launch_error", "Could not start Voice Only extraction"),
        ("encode_error", "encode failed"),
    ],
)
def test_render_voice_only_audio_reports_output_launch_and_encode_failures(
    run_behavior: str,
    expected_message: str,
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_spleeter_support_incident()
    work_dir = tmp_path / "spleeter-work"
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.tempfile.mkdtemp", lambda prefix: str(work_dir))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_spleeter_bundle",
        lambda: (
            Path("/bin/sherpa-spleeter"),
            Path("/models/vocals.fp16.onnx"),
            Path("/models/accompaniment.fp16.onnx"),
        ),
    )

    def fake_run(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: float | None = None,
    ) -> SimpleNamespace:
        if cmd[0] == "/bin/sherpa-spleeter":
            if run_behavior == "launch_error":
                raise PermissionError(13, "Permission denied", "/bin/sherpa-spleeter")
            if run_behavior != "missing_vocals":
                vocals_arg = next(value for value in cmd if value.startswith("--output-vocals-wav="))
                Path(vocals_arg.split("=", 1)[1]).write_bytes(b"vocals")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if len(list(work_dir.rglob("vocals.wav"))) == 1 and run_behavior == "encode_error":
            return SimpleNamespace(returncode=2, stdout="", stderr="encode failed")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match=expected_message):
        render_voice_only_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "voice.mp3",
        )

    assert not work_dir.exists()
    incident = latest_spleeter_support_incident()
    assert incident is not None
    assert expected_message in incident["user_message"]
