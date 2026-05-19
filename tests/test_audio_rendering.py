from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_processor import (
    _safe_filename_stem,
    format_ffmpeg_command,
    make_output_filename,
    probe_duration_ms,
    render_audio,
    render_audio_region_deleted,
    render_audio_region_kept,
    temp_final_path,
)
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.errors import (
    AudioProcessingError,
)
from tests.audio_fixtures import (
    FFMPEG_AVAILABLE,
    FFMPEG_SKIP_REASON,
)


def test_make_output_filename_is_mp3_and_timestamped() -> None:
    filename = make_output_filename("my sentence.wav", datetime(2026, 5, 14, 9, 8, 7), "abc12345")

    assert filename == "my_sentence__aqe_20260514_090807_000000_abc12345.mp3"


def test_make_output_filename_sanitizes_and_bounds_problematic_names() -> None:
    filename = make_output_filename(
        "../??? " + ("very long " * 30) + ".wav",
        datetime(2026, 5, 14, 9, 8, 7, 123456),
        "deadbeef",
    )

    assert filename.endswith("__aqe_20260514_090807_123456_deadbeef.mp3")
    assert "/" not in filename
    assert "?" not in filename
    assert len(filename) <= 120


def test_make_output_filename_uses_audio_for_empty_sanitized_stem() -> None:
    filename = make_output_filename("短い.wav", datetime(2026, 5, 14), "12345678")

    assert filename == "audio__aqe_20260514_000000_000000_12345678.mp3"


def test_make_output_filename_uses_audio_for_empty_source_name() -> None:
    filename = make_output_filename("", datetime(2026, 5, 14), "12345678")

    assert filename == "audio__aqe_20260514_000000_000000_12345678.mp3"


def test_make_output_filename_uses_eight_character_generated_token(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.uuid.uuid4",
        lambda: SimpleNamespace(hex="1234567890abcdef"),
    )

    filename = make_output_filename("clip.wav", datetime(2026, 5, 14))

    assert filename.endswith("_12345678.mp3")


def test_safe_filename_stem_collapses_invalid_runs_and_falls_back_to_audio() -> None:
    assert _safe_filename_stem("mix / of !! odd\tchars") == "mix_of_odd_chars"
    assert _safe_filename_stem("keep-hyphen_and_underscore") == "keep-hyphen_and_underscore"
    assert _safe_filename_stem("短い") == "audio"


def test_temp_final_path_preserves_basename_only() -> None:
    path = temp_final_path("../nested/clip.mp3")

    assert path.name == "clip.mp3"
    assert path.parent.name.startswith("aqe_final_")


def test_probe_duration_ms_uses_json_ffprobe_call_and_rounds(monkeypatch, tmp_path: Path) -> None:
    run_calls: list[tuple[list[str], bool, bool, bool]] = []
    ffmpeg_args: list[str | None] = []

    def fake_find_ffmpeg(path: str | None) -> Path:
        ffmpeg_args.append(path)
        return Path("/bin/ffmpeg")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", fake_find_ffmpeg)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffprobe", lambda _path: Path("/bin/ffprobe"))

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        run_calls.append((cmd, capture_output, text, check))
        return SimpleNamespace(returncode=0, stdout='{"format":{"duration":"1.2346"}}', stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    duration_ms = probe_duration_ms(tmp_path / "clip.wav", AudioProcessingConfig(ffmpeg_path="/custom/ffmpeg"))

    assert duration_ms == 1235
    assert ffmpeg_args == ["/custom/ffmpeg"]
    assert run_calls == [
        (
            [
                "/bin/ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(tmp_path / "clip.wav"),
            ],
            True,
            True,
            False,
        )
    ]


def test_probe_duration_ms_raises_with_ffprobe_stderr(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffprobe", lambda _path: Path("/bin/ffprobe"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="", stderr=" ffprobe failed \n"),
    )

    with pytest.raises(AudioProcessingError, match="ffprobe failed"):
        probe_duration_ms(tmp_path / "clip.wav", AudioProcessingConfig())


def test_probe_duration_ms_uses_exact_default_message_for_blank_stderr(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffprobe", lambda _path: Path("/bin/ffprobe"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="", stderr="   "),
    )

    with pytest.raises(AudioProcessingError) as exc_info:
        probe_duration_ms(tmp_path / "clip.wav", AudioProcessingConfig())

    assert str(exc_info.value) == "Could not inspect audio duration."


def test_probe_duration_ms_raises_for_unparseable_output(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffprobe", lambda _path: Path("/bin/ffprobe"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout='{"format":{}}', stderr=""),
    )

    with pytest.raises(AudioProcessingError, match="Could not parse audio duration."):
        probe_duration_ms(tmp_path / "clip.wav", AudioProcessingConfig())


def test_probe_duration_ms_keeps_zero_duration_at_zero(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffprobe", lambda _path: Path("/bin/ffprobe"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout='{"format":{"duration":"0.0"}}', stderr=""),
    )

    assert probe_duration_ms(tmp_path / "clip.wav", AudioProcessingConfig()) == 0


def test_render_audio_uses_expected_ffmpeg_invocation(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[list[str], bool, bool, bool]] = []
    durations = iter([1000, 825])
    commands: list[tuple[str, ...]] = []
    ffmpeg_args: list[str | None] = []

    def fake_find_ffmpeg(path: str | None) -> Path:
        ffmpeg_args.append(path)
        return Path("/bin/ffmpeg")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", fake_find_ffmpeg)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.build_audio_filters", lambda *_args: "atrim=start=0.100:end=0.900")

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        calls.append((cmd, capture_output, text, check))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "edited.mp3"
    state = AudioEditState("clip.wav", left_trim_ms=100)
    result = render_audio(
        tmp_path / "source.wav",
        state,
        AudioProcessingConfig(ffmpeg_path="/custom/ffmpeg"),
        output_path=output,
        on_command=commands.append,
    )

    expected_command = (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "source.wav"),
        "-vn",
        "-filter:a",
        "atrim=start=0.100:end=0.900",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(output),
    )
    assert ffmpeg_args == ["/custom/ffmpeg"]
    assert calls == [(list(expected_command), True, True, False)]
    assert commands == [expected_command]
    assert result.output_path == output
    assert result.command == expected_command
    assert result.duration_ms == 825


def test_render_audio_forwards_window_visibility_kwargs(monkeypatch, tmp_path: Path) -> None:
    run_kwargs: list[dict[str, object]] = []
    durations = iter([1000, 1000])

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor._external_command_run_kwargs",
        lambda: {"creationflags": 0x08000000},
    )

    def fake_run(
        _cmd: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
        **kwargs: object,
    ) -> SimpleNamespace:
        assert capture_output is True
        assert text is True
        assert check is False
        run_kwargs.append(kwargs)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    render_audio(
        tmp_path / "source.wav",
        AudioEditState("clip.wav"),
        AudioProcessingConfig(),
        output_path=tmp_path / "edited.mp3",
    )

    assert run_kwargs == [{"creationflags": 0x08000000}]


def test_render_audio_region_deleted_uses_concat_filter(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[list[str], bool, bool, bool]] = []
    durations = iter([2000, 1250])
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        calls.append((cmd, capture_output, text, check))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "cut.mp3"
    result = render_audio_region_deleted(
        tmp_path / "source.wav",
        500,
        1250,
        AudioProcessingConfig(),
        output_path=output,
        on_command=commands.append,
    )

    filter_complex = (
        "[0:a]atrim=start=0.000:end=0.500,asetpts=PTS-STARTPTS[a0];"
        "[0:a]atrim=start=1.250:end=2.000,asetpts=PTS-STARTPTS[a1];"
        "[a0][a1]concat=n=2:v=0:a=1[out]"
    )
    expected_command = (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "source.wav"),
        "-vn",
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(output),
    )
    assert calls == [(list(expected_command), True, True, False)]
    assert commands == [expected_command]
    assert result.output_path == output
    assert result.command == expected_command
    assert result.duration_ms == 1250


def test_render_audio_region_kept_uses_single_trim_filter(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[list[str], bool, bool, bool]] = []
    durations = iter([2000, 750])
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        calls.append((cmd, capture_output, text, check))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "kept.mp3"
    result = render_audio_region_kept(
        tmp_path / "source.wav",
        500,
        1250,
        AudioProcessingConfig(),
        output_path=output,
        on_command=commands.append,
    )

    filter_complex = "[0:a]atrim=start=0.500:end=1.250,asetpts=PTS-STARTPTS[out]"
    expected_command = (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "source.wav"),
        "-vn",
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(output),
    )
    assert calls == [(list(expected_command), True, True, False)]
    assert commands == [expected_command]
    assert result.output_path == output
    assert result.command == expected_command
    assert result.duration_ms == 750


def test_render_audio_uses_default_error_message_for_blank_stderr(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.build_audio_filters", lambda *_args: "filters")
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="", stderr="   "),
    )

    with pytest.raises(AudioProcessingError, match="Audio processing failed."):
        render_audio(
            tmp_path / "source.wav",
            AudioEditState("clip.wav"),
            AudioProcessingConfig(),
            output_path=tmp_path / "output.mp3",
        )


@pytest.mark.skipif(
    not FFMPEG_AVAILABLE,
    reason=FFMPEG_SKIP_REASON,
)
def test_render_audio_smoke_with_path_spaces_and_non_ascii(tmp_path: Path) -> None:
    source_dir = tmp_path / "media with spaces"
    source_dir.mkdir()
    source = source_dir / "短い clip.wav"
    output = tmp_path / "edited preview.mp3"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1",
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    result = render_audio(
        source,
        AudioEditState("短い clip.wav", left_trim_ms=100, speed=1.05),
        AudioProcessingConfig(),
        output_path=output,
    )

    assert result.output_path == output
    assert " -y -i " in format_ffmpeg_command(result.command)
    assert output.is_file()
    assert 700 <= probe_duration_ms(output, AudioProcessingConfig()) <= 1000


@pytest.mark.skipif(
    not FFMPEG_AVAILABLE,
    reason=FFMPEG_SKIP_REASON,
)
def test_render_audio_region_kept_smoke_outputs_selected_duration(tmp_path: Path) -> None:
    source = tmp_path / "source.wav"
    output = tmp_path / "kept.mp3"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=2",
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    result = render_audio_region_kept(
        source,
        500,
        1250,
        AudioProcessingConfig(),
        output_path=output,
    )
    probed_duration_ms = probe_duration_ms(output, AudioProcessingConfig())

    assert result.output_path == output
    assert output.is_file()
    assert result.duration_ms == probed_duration_ms
    assert 650 <= probed_duration_ms <= 900
