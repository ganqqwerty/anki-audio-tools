from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_processor import (
    format_ffmpeg_command,
    _safe_filename_stem,
    make_output_filename,
    probe_duration_ms,
    render_audio,
    temp_final_path,
)
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.errors import (
    AudioProcessingError,
)

from tests.audio_fixtures import FFMPEG_AVAILABLE, _run_ffmpeg, FFMPEG_SKIP_REASON

FFMPEG = str(Path("/bin/ffmpeg"))
FFPROBE = str(Path("/bin/ffprobe"))

INPUT_FORMAT_FIXTURES = (
    ("aac", ("-c:a", "aac", "-f", "adts")),
    ("flac", ("-c:a", "flac")),
    ("m4a", ("-c:a", "aac", "-f", "mp4")),
    ("oga", ("-ac", "2", "-c:a", "vorbis", "-strict", "-2", "-f", "ogg")),
    ("ogg", ("-ac", "2", "-c:a", "vorbis", "-strict", "-2", "-f", "ogg")),
    ("opus", ("-ar", "48000", "-c:a", "opus", "-strict", "-2", "-f", "opus")),
    ("wav", ("-c:a", "pcm_s16le")),
    ("webm", ("-ar", "48000", "-c:a", "opus", "-strict", "-2", "-f", "webm")),
)


def _generate_tone(path: Path, *, duration_s: float = 1.0) -> None:
    _run_ffmpeg(
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={duration_s}",
        "-vn",
        str(path),
    )


def _generate_input_format(path: Path, *, output_args: tuple[str, ...]) -> None:
    _run_ffmpeg(
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
    )


def _run_real_audio_processing_skip() -> None:
    if not FFMPEG_AVAILABLE:
        pytest.skip(FFMPEG_SKIP_REASON)


def test_make_output_filename_preserves_source_extension_and_timestamp() -> None:
    filename = make_output_filename("my sentence.wav", datetime(2026, 5, 14, 9, 8, 7), "abc12345")

    assert filename == "my_sentence__aqe_20260514_090807_000000_abc12345.wav"


def test_make_output_filename_preserves_source_extension_with_trailing_os_characters() -> None:
    filename = make_output_filename("clip.opus .", datetime(2026, 5, 14), "12345678")

    assert filename == "clip_opus__aqe_20260514_000000_000000_12345678.opus"


def test_make_output_filename_respects_output_format() -> None:
    filename = make_output_filename(
        "my sentence.wav",
        datetime(2026, 5, 14, 9, 8, 7),
        "abc12345",
        output_format="flac",
    )

    assert filename == "my_sentence__aqe_20260514_090807_000000_abc12345.flac"


def test_make_output_filename_sanitizes_and_bounds_problematic_names() -> None:
    filename = make_output_filename(
        "../??? " + ("very long " * 30) + ".wav",
        datetime(2026, 5, 14, 9, 8, 7, 123456),
        "deadbeef",
    )

    assert filename.endswith("__aqe_20260514_090807_123456_deadbeef.wav")
    assert "/" not in filename
    assert "?" not in filename
    assert len(filename) <= 120


def test_make_output_filename_uses_audio_for_empty_sanitized_stem() -> None:
    filename = make_output_filename("短い.wav", datetime(2026, 5, 14), "12345678")

    assert filename == "audio__aqe_20260514_000000_000000_12345678.wav"


def test_make_output_filename_uses_audio_for_empty_source_name() -> None:
    filename = make_output_filename("", datetime(2026, 5, 14), "12345678")

    assert filename == "audio__aqe_20260514_000000_000000_12345678.mp3"


def test_make_output_filename_uses_eight_character_generated_token(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.uuid.uuid4",
        lambda: SimpleNamespace(hex="1234567890abcdef"),
    )

    filename = make_output_filename("clip.wav", datetime(2026, 5, 14))

    assert filename.endswith("_12345678.wav")


def test_safe_filename_stem_collapses_invalid_runs_and_falls_back_to_audio() -> None:
    assert _safe_filename_stem("mix / of !! odd\tchars") == "mix_of_odd_chars"
    assert _safe_filename_stem("keep-hyphen_and_underscore") == "keep-hyphen_and_underscore"
    assert _safe_filename_stem("短い") == "audio"


def test_temp_final_path_preserves_basename_only() -> None:
    path = temp_final_path("../nested/clip.mp3")

    assert path.name == "clip.mp3"
    assert path.parent.name.startswith("aqe_final_")


@pytest.mark.allow_managed_runtime
def test_render_audio_writes_temp_final_output_without_mutating_source_file(tmp_path: Path) -> None:
    if not FFMPEG_AVAILABLE:
        pytest.skip(FFMPEG_SKIP_REASON)

    source = tmp_path / "source.wav"
    _generate_tone(source, duration_s=1.0)
    original_source_bytes = source.read_bytes()
    desired_name = make_output_filename(source.name)
    final_output = temp_final_path(desired_name)
    output = render_audio(
        source,
        AudioEditState(source_file=source.name, left_trim_ms=250),
        AudioProcessingConfig(),
        output_path=final_output,
    )

    assert source.is_file()
    assert source.read_bytes() == original_source_bytes
    assert output.output_path == final_output
    assert output.output_path.suffix == ".wav"
    assert output.output_path.exists()


def _mp3_policy() -> SimpleNamespace:
    return SimpleNamespace(
        extension=".mp3",
        mime_type="audio/mpeg",
        codec_args=("-codec:a", "libmp3lame", "-q:a", "4"),
    )


def test_probe_duration_ms_uses_json_ffprobe_call_and_rounds(monkeypatch, tmp_path: Path) -> None:
    run_calls: list[tuple[list[str], bool, bool, bool]] = []
    ffmpeg_args: list[str | None] = []

    def fake_find_ffmpeg(path: str | None) -> Path:
        ffmpeg_args.append(path)
        return Path("/bin/ffmpeg")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", fake_find_ffmpeg)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffprobe", lambda _path: Path("/bin/ffprobe"))

    def fake_run(
            cmd: list[str],
            capture_output: bool,
            text: bool,
            check: bool,
            **_kwargs: object,
    ) -> SimpleNamespace:
        run_calls.append((cmd, capture_output, text, check))
        return SimpleNamespace(returncode=0, stdout='{"format":{"duration":"1.2346"}}', stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    duration_ms = probe_duration_ms(tmp_path / "clip.wav", AudioProcessingConfig(ffmpeg_path="/custom/ffmpeg"))

    assert duration_ms == 1235
    assert ffmpeg_args == ["/custom/ffmpeg"]
    assert run_calls == [
        (
            [
                FFPROBE,
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
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.build_audio_filters",
                        lambda *_args: "atrim=start=0.100:end=0.900")
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.resolve_output_policy",
                        lambda *_args, **_kwargs: _mp3_policy())

    def fake_run(
            cmd: list[str],
            capture_output: bool,
            text: bool,
            check: bool,
            **_kwargs: object,
    ) -> SimpleNamespace:
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
        FFMPEG,
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


def test_render_audio_uses_stable_text_decoding_for_non_ascii_sources(
        monkeypatch,
        tmp_path: Path,
) -> None:
    durations = iter([1000, 1000])
    source = tmp_path / "Даии_青山_voice.opus"
    output = tmp_path / "edited.mp3"
    run_kwargs: list[dict[str, object]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.resolve_output_policy",
                        lambda *_args, **_kwargs: _mp3_policy())

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
        if kwargs.get("encoding") != "utf-8" or kwargs.get("errors") != "replace":
            raise UnicodeDecodeError("charmap", b"\xe9\x9d\x92", 1, 2, "character maps to <undefined>")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    render_audio(
        source,
        AudioEditState(source.name, speed=0.67),
        AudioProcessingConfig(),
        output_path=output,
    )

    assert run_kwargs
    assert run_kwargs[0]["encoding"] == "utf-8"
    assert run_kwargs[0]["errors"] == "replace"


def test_render_audio_forwards_window_visibility_kwargs(monkeypatch, tmp_path: Path) -> None:
    run_kwargs: list[dict[str, object]] = []
    durations = iter([1000, 1000])

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.resolve_output_policy",
                        lambda *_args, **_kwargs: _mp3_policy())
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

    assert run_kwargs == [{"encoding": "utf-8", "errors": "replace", "creationflags": 0x08000000}]


@pytest.mark.allow_managed_runtime
def test_render_audio_left_trim_reduces_output_duration_on_real_ffmpeg(tmp_path: Path) -> None:
    _run_real_audio_processing_skip()

    source = tmp_path / "source.wav"
    output = tmp_path / "trimmed.mp3"
    _generate_tone(source, duration_s=2.0)

    result = render_audio(
        source,
        AudioEditState(source.name, left_trim_ms=500),
        AudioProcessingConfig(),
        output_path=output,
    )
    original_duration = probe_duration_ms(source, AudioProcessingConfig())
    output_duration = probe_duration_ms(output, AudioProcessingConfig())

    assert 1900 <= original_duration <= 2100
    assert 1350 <= output_duration <= 1650
    assert output_duration < original_duration - 350
    assert result.output_path == output


@pytest.mark.allow_managed_runtime
def test_render_audio_speed_up_shows_reduced_duration_on_real_ffmpeg(tmp_path: Path) -> None:
    _run_real_audio_processing_skip()

    source = tmp_path / "speed.wav"
    output = tmp_path / "faster.mp3"
    _generate_tone(source, duration_s=2.0)

    result = render_audio(
        source,
        AudioEditState(source.name, speed=1.25),
        AudioProcessingConfig(),
        output_path=output,
    )
    output_duration = probe_duration_ms(output, AudioProcessingConfig())

    assert 1500 <= output_duration <= 1750
    assert result.duration_ms == output_duration
    assert result.output_path == output


@pytest.mark.allow_managed_runtime
def test_render_audio_volume_gain_adds_expected_filters_on_real_ffmpeg(tmp_path: Path) -> None:
    _run_real_audio_processing_skip()

    source = tmp_path / "gain.wav"
    louder = tmp_path / "louder.mp3"
    quieter = tmp_path / "quieter.mp3"
    _generate_tone(source, duration_s=1.0)

    louder_result = render_audio(
        source,
        AudioEditState(source.name, volume_db=6.0),
        AudioProcessingConfig(),
        output_path=louder,
    )
    quieter_result = render_audio(
        source,
        AudioEditState(source.name, volume_db=-6.0),
        AudioProcessingConfig(),
        output_path=quieter,
    )

    assert "volume=6.00dB" in format_ffmpeg_command(louder_result.command)
    assert "volume=-6.00dB" in format_ffmpeg_command(quieter_result.command)
    assert louder_result.output_path == louder
    assert quieter_result.output_path == quieter


@pytest.mark.parametrize(("extension", "output_args"), INPUT_FORMAT_FIXTURES)
@pytest.mark.allow_managed_runtime
def test_render_audio_accepts_multiple_input_encodings_on_real_ffmpeg(
    extension: str,
    output_args: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _run_real_audio_processing_skip()

    source = tmp_path / f"source.{extension}"
    output = tmp_path / f"rendered.{extension}.mp3"
    _generate_input_format(source, output_args=output_args)

    result = render_audio(
        source,
        AudioEditState(source.name, volume_db=-1.0),
        AudioProcessingConfig(),
        output_path=output,
    )

    assert output.is_file()
    assert result.output_path == output
    assert result.output_path.suffix == ".mp3"
    assert "libmp3lame" in format_ffmpeg_command(result.command)
    assert probe_duration_ms(output, AudioProcessingConfig()) > 0
