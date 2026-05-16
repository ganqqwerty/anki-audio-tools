"""Tests for ffmpeg command construction helpers."""

from __future__ import annotations

import importlib
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_processor import (
    _atempo_filters,
    _safe_filename_stem,
    build_audio_filters,
    build_deep_filter_command,
    build_deep_filter_prepare_command,
    build_mp3_encode_command,
    build_playback_segment_filters,
    find_deep_filter,
    find_ffmpeg,
    find_ffprobe,
    format_ffmpeg_command,
    make_output_filename,
    make_playback_segment_filename,
    probe_duration_ms,
    render_audio,
    render_noise_reduced_audio,
    render_playback_segment,
    select_deep_filter_output,
    temp_final_path,
)
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.errors import (
    AudioProcessingError,
    MissingDeepFilterError,
    MissingFfmpegError,
)


def test_find_ffmpeg_uses_default_path_lookup_when_unconfigured(monkeypatch) -> None:
    calls: list[str] = []

    def fake_which(name: str) -> str:
        calls.append(name)
        return "/usr/local/bin/ffmpeg"

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", fake_which)

    assert find_ffmpeg() == Path("/usr/local/bin/ffmpeg")
    assert calls == ["ffmpeg"]


def test_find_ffmpeg_default_override_stays_empty_string() -> None:
    audio_processor_module = importlib.import_module("anki_audio_quick_editor.audio_processor")

    assert audio_processor_module.find_ffmpeg.__defaults__ == ("",)


def test_find_ffmpeg_raises_exact_message_when_missing_and_unconfigured(monkeypatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", lambda _name: None)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.Path",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("configured path should not be consulted")),
    )

    with pytest.raises(MissingFfmpegError) as exc_info:
        find_ffmpeg()

    assert str(exc_info.value) == (
        "Audio Quick Editor requires ffmpeg. Please install ffmpeg and make sure it is "
        "available in PATH, or configure its path in the add-on settings."
    )


def test_find_ffmpeg_prefers_existing_configured_file(tmp_path: Path) -> None:
    ffmpeg = tmp_path / "ffmpeg"
    ffmpeg.write_text("")

    assert find_ffmpeg(str(ffmpeg)) == ffmpeg


def test_find_deep_filter_uses_default_path_lookup_when_unconfigured(monkeypatch) -> None:
    calls: list[str] = []

    def fake_which(name: str) -> str:
        calls.append(name)
        return "/usr/local/bin/deep-filter"

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", fake_which)

    assert find_deep_filter() == Path("/usr/local/bin/deep-filter")
    assert calls == ["deep-filter"]


def test_find_deep_filter_prefers_existing_configured_file(tmp_path: Path) -> None:
    deep_filter = tmp_path / "deep-filter"
    deep_filter.write_text("")

    assert find_deep_filter(str(deep_filter)) == deep_filter


def test_find_deep_filter_raises_when_missing(monkeypatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", lambda _name: None)

    with pytest.raises(MissingDeepFilterError, match="Remove noise requires DeepFilterNet"):
        find_deep_filter()


def test_find_ffprobe_prefers_sibling_binary(tmp_path: Path, monkeypatch) -> None:
    ffmpeg = tmp_path / "ffmpeg"
    ffprobe = tmp_path / "ffprobe"
    ffmpeg.write_text("")
    ffprobe.write_text("")
    called = False

    def fake_which(_name: str) -> str:
        nonlocal called
        called = True
        return "/usr/local/bin/ffprobe"

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", fake_which)

    assert find_ffprobe(ffmpeg) == ffprobe
    assert called is False


def test_find_ffprobe_falls_back_to_path_lookup(monkeypatch, tmp_path: Path) -> None:
    calls: list[str] = []

    def fake_which(name: str) -> str:
        calls.append(name)
        return "/usr/local/bin/ffprobe"

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", fake_which)

    assert find_ffprobe(tmp_path / "ffmpeg") == Path("/usr/local/bin/ffprobe")
    assert calls == ["ffprobe"]


def test_find_ffprobe_raises_when_no_binary_available(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", lambda _name: None)

    with pytest.raises(MissingFfmpegError) as exc_info:
        find_ffprobe(tmp_path / "ffmpeg")

    assert str(exc_info.value) == "Audio Quick Editor requires ffprobe alongside ffmpeg to inspect audio duration."


def test_build_audio_filters_includes_crop_speed_and_silence_steps() -> None:
    config = AudioProcessingConfig()
    state = AudioEditState(
        "clip.mp3",
        left_trim_ms=200,
        right_trim_ms=100,
        speed=1.15,
        volume_db=3.0,
        edge_trim_enabled=True,
        remove_internal_pauses_enabled=True,
    )

    filters = build_audio_filters(3000, state, config)
    edge_threshold = f"{config.edge_silence_threshold_db}dB"
    pause_threshold = f"{config.internal_pause_silence_threshold_db}dB"

    assert "atrim=start=0.200:end=2.900" in filters
    assert "silenceremove=start_periods=1" in filters
    assert "stop_periods=-1" in filters
    assert f"start_threshold={edge_threshold}" in filters
    assert f"stop_periods=1:stop_duration=0.100:stop_threshold={edge_threshold}" in filters
    assert f"stop_periods=-1:stop_duration=0.300:stop_threshold={pause_threshold}" in filters
    assert "stop_silence=0.100" in filters
    assert "volume=3.00dB" in filters
    assert "atempo=1.150" in filters
    assert filters.index("stop_silence=0.100") < filters.index("volume=3.00dB")
    assert filters.index("volume=3.00dB") < filters.index("atempo=1.150")


def test_build_audio_filters_omits_volume_filter_when_unchanged() -> None:
    filters = build_audio_filters(3000, AudioEditState("clip.mp3"), AudioProcessingConfig())

    assert "volume=" not in filters


def test_build_audio_filters_omits_atempo_when_speed_is_unchanged() -> None:
    filters = build_audio_filters(3000, AudioEditState("clip.mp3", speed=1.0), AudioProcessingConfig())

    assert "atempo=" not in filters


def test_build_audio_filters_uses_exact_pause_threshold_and_gap_values() -> None:
    config = AudioProcessingConfig(
        internal_pause_silence_threshold_db=-41,
        internal_pause_threshold_ms=275,
        internal_pause_target_gap_ms=125,
    )
    state = AudioEditState("clip.mp3", remove_internal_pauses_enabled=True)

    filters = build_audio_filters(3000, state, config)

    assert "stop_threshold=-41dB" in filters
    assert "stop_duration=0.275" in filters
    assert "stop_silence=0.125" in filters


def test_build_audio_filters_preserves_precise_silence_filter_parameters() -> None:
    config = AudioProcessingConfig(
        edge_silence_min_ms=509,
        internal_pause_silence_threshold_db=-47,
        internal_pause_threshold_ms=509,
        internal_pause_target_gap_ms=509,
    )
    state = AudioEditState(
        "clip.mp3",
        edge_trim_enabled=True,
        remove_internal_pauses_enabled=True,
    )

    filters = build_audio_filters(3000, state, config)
    edge_threshold = f"{config.edge_silence_threshold_db}dB"
    pause_threshold = f"{config.internal_pause_silence_threshold_db}dB"

    assert "start_duration=0.509" in filters
    assert "stop_duration=0.509" in filters
    assert "stop_silence=0.509" in filters
    assert filters.count("silenceremove=") == 2
    assert (
        "silenceremove="
        f"start_periods=1:start_duration=0.509:start_threshold={edge_threshold}:"
        f"stop_periods=1:stop_duration=0.509:stop_threshold={edge_threshold}"
    ) in filters
    assert (
        f",silenceremove=stop_periods=-1:stop_duration=0.509:stop_threshold={pause_threshold}:"
        "stop_silence=0.509"
    ) in filters


def test_build_audio_filters_preserves_precise_trim_boundaries() -> None:
    state = AudioEditState("clip.mp3", left_trim_ms=999, right_trim_ms=222)

    filters = build_audio_filters(3000, state, AudioProcessingConfig())

    assert filters.startswith("atrim=start=0.999:end=2.778,asetpts=PTS-STARTPTS")


def test_build_playback_segment_filters_starts_at_cursor_and_resets_timestamps() -> None:
    filters = build_playback_segment_filters(700)

    assert filters == "atrim=start=0.700,asetpts=PTS-STARTPTS"


def test_build_playback_segment_filters_clamps_negative_cursor_to_zero() -> None:
    filters = build_playback_segment_filters(-200)

    assert filters == "atrim=start=0.000,asetpts=PTS-STARTPTS"


def test_build_deep_filter_prepare_command_uses_48khz_mono_pcm(tmp_path: Path) -> None:
    command = build_deep_filter_prepare_command(
        Path("/bin/ffmpeg"),
        tmp_path / "source.mp3",
        tmp_path / "input.wav",
    )

    assert command == (
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
        "pcm_s16le",
        str(tmp_path / "input.wav"),
    )


def test_build_deep_filter_command_includes_post_filter_when_enabled(tmp_path: Path) -> None:
    command = build_deep_filter_command(
        Path("/bin/deep-filter"),
        tmp_path / "input.wav",
        tmp_path / "out",
        post_filter=True,
    )

    assert command == (
        "/bin/deep-filter",
        "-D",
        "--pf",
        "-o",
        str(tmp_path / "out"),
        str(tmp_path / "input.wav"),
    )


def test_build_deep_filter_command_omits_post_filter_when_disabled(tmp_path: Path) -> None:
    command = build_deep_filter_command(
        Path("/bin/deep-filter"),
        tmp_path / "input.wav",
        tmp_path / "out",
        post_filter=False,
    )

    assert "--pf" not in command
    assert command == (
        "/bin/deep-filter",
        "-D",
        "-o",
        str(tmp_path / "out"),
        str(tmp_path / "input.wav"),
    )


def test_build_mp3_encode_command_uses_existing_output_policy(tmp_path: Path) -> None:
    command = build_mp3_encode_command(
        Path("/bin/ffmpeg"),
        tmp_path / "cleaned.wav",
        tmp_path / "cleaned.mp3",
    )

    assert command == (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "cleaned.wav"),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(tmp_path / "cleaned.mp3"),
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


def test_make_playback_segment_filename_is_debuggable_and_sanitized() -> None:
    filename = make_playback_segment_filename("../短い test.wav", 700, "abc12345")

    assert filename == "aqe_playback_test__from_700ms_abc12345.mp3"


def test_make_playback_segment_filename_clamps_negative_start_and_bounds_length() -> None:
    filename = make_playback_segment_filename("x" * 500 + ".wav", -25, "abc12345")

    assert filename.startswith("aqe_playback_")
    assert "__from_0ms_abc12345.mp3" in filename
    assert len(filename) <= 160


def test_make_playback_segment_filename_uses_audio_for_empty_source_name() -> None:
    audio_processor_module = importlib.import_module("anki_audio_quick_editor.audio_processor")

    filename = audio_processor_module.make_playback_segment_filename("", 700, "abc12345")

    assert filename == "aqe_playback_audio__from_700ms_abc12345.mp3"


def test_make_playback_segment_filename_uses_eight_character_generated_token(monkeypatch) -> None:
    audio_processor_module = importlib.import_module("anki_audio_quick_editor.audio_processor")
    monkeypatch.setattr(audio_processor_module.uuid, "uuid4", lambda: SimpleNamespace(hex="1234567890abcdef"))

    filename = audio_processor_module.make_playback_segment_filename("clip.wav", 700)

    assert filename == "aqe_playback_clip__from_700ms_12345678.mp3"


def test_temp_playback_path_uses_generated_temp_dir_and_segment_filename(monkeypatch, tmp_path: Path) -> None:
    audio_processor_module = importlib.import_module("anki_audio_quick_editor.audio_processor")
    temp_dir = tmp_path / "aqe_playback_tmp"
    build_calls: list[tuple[str, int]] = []

    monkeypatch.setattr(audio_processor_module.tempfile, "mkdtemp", lambda prefix: str(temp_dir))
    monkeypatch.setattr(
        audio_processor_module,
        "make_playback_segment_filename",
        lambda source_filename, start_ms: build_calls.append((source_filename, start_ms)) or "segment.mp3",
    )

    path = audio_processor_module.temp_playback_path("clip.wav", 700)

    assert build_calls == [("clip.wav", 700)]
    assert path == temp_dir / "segment.mp3"


def test_temp_final_path_preserves_basename_only() -> None:
    path = temp_final_path("../nested/clip.mp3")

    assert path.name == "clip.mp3"
    assert path.parent.name.startswith("aqe_final_")


def test_atempo_filters_preserve_exact_boundary_values() -> None:
    assert _atempo_filters(2.0) == ["atempo=2.000"]
    assert _atempo_filters(2.5) == ["atempo=2.000", "atempo=1.250"]
    assert _atempo_filters(0.5) == ["atempo=0.500"]
    assert _atempo_filters(4.0) == ["atempo=2.000", "atempo=2.000"]
    assert _atempo_filters(0.25) == ["atempo=0.500", "atempo=0.500"]
    assert _atempo_filters(0.1) == ["atempo=0.500", "atempo=0.500", "atempo=0.500", "atempo=0.800"]


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


def test_render_playback_segment_rejects_cursor_at_end(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda *_args: Path("/tmp/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)

    with pytest.raises(AudioProcessingError, match="Cursor is at the end of the audio."):
        render_playback_segment(
            tmp_path / "source.wav",
            1000,
            AudioProcessingConfig(),
        )


def test_render_playback_segment_rejects_cursor_at_exact_end_threshold(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda *_args: Path("/tmp/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)

    with pytest.raises(AudioProcessingError, match="Cursor is at the end of the audio."):
        render_playback_segment(
            tmp_path / "source.wav",
            980,
            AudioProcessingConfig(),
        )


def test_render_playback_segment_rejects_tiny_audio_from_start(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda *_args: Path("/tmp/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 10)

    with pytest.raises(AudioProcessingError, match="Cursor is at the end of the audio."):
        render_playback_segment(
            tmp_path / "source.wav",
            0,
            AudioProcessingConfig(),
        )


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


def test_render_playback_segment_clamps_negative_start_and_invokes_ffmpeg(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[list[str], bool, bool, bool]] = []
    durations = iter([1000, 300])
    commands: list[tuple[str, ...]] = []
    ffmpeg_args: list[str | None] = []

    def fake_find_ffmpeg(path: str | None) -> Path:
        ffmpeg_args.append(path)
        return Path("/bin/ffmpeg")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", fake_find_ffmpeg)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        calls.append((cmd, capture_output, text, check))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "segment.mp3"
    result = render_playback_segment(
        tmp_path / "source.wav",
        -50,
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
        "atrim=start=0.000,asetpts=PTS-STARTPTS",
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
    assert result.duration_ms == 300


def test_render_playback_segment_allows_cursor_before_end_threshold(monkeypatch, tmp_path: Path) -> None:
    durations = iter([1000, 21])

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    result = render_playback_segment(
        tmp_path / "source.wav",
        979,
        AudioProcessingConfig(),
        output_path=tmp_path / "segment.mp3",
    )

    assert result.duration_ms == 21


def test_render_playback_segment_uses_default_error_message_for_blank_stderr(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="", stderr=""),
    )

    with pytest.raises(AudioProcessingError) as exc_info:
        render_playback_segment(
            tmp_path / "source.wav",
            100,
            AudioProcessingConfig(),
            output_path=tmp_path / "segment.mp3",
        )

    assert str(exc_info.value) == "Playback segment rendering failed."


def test_render_playback_segment_uses_exact_end_of_audio_message(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda *_args: Path("/tmp/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)

    with pytest.raises(AudioProcessingError) as exc_info:
        render_playback_segment(
            tmp_path / "source.wav",
            1000,
            AudioProcessingConfig(),
        )

    assert str(exc_info.value) == "Cursor is at the end of the audio."


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg and ffprobe are required for audio rendering smoke tests",
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
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg and ffprobe are required for audio rendering smoke tests",
)
def test_render_audio_remove_pauses_preserves_short_pause(tmp_path: Path) -> None:
    source = tmp_path / "short_pause.wav"
    output = tmp_path / "short_pause.mp3"
    _generate_short_pause_clip(source)
    source_duration_ms = probe_duration_ms(source, AudioProcessingConfig())

    result = render_audio(
        source,
        AudioEditState("short_pause.wav", remove_internal_pauses_enabled=True),
        AudioProcessingConfig(),
        output_path=output,
    )

    assert result.output_path == output
    assert abs((result.duration_ms or 0) - source_duration_ms) <= 25


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg and ffprobe are required for audio rendering smoke tests",
)
def test_render_audio_remove_pauses_compresses_obvious_long_pause(tmp_path: Path) -> None:
    source = tmp_path / "long_pause.wav"
    output = tmp_path / "long_pause.mp3"
    _generate_long_pause_clip(source)
    source_duration_ms = probe_duration_ms(source, AudioProcessingConfig())

    result = render_audio(
        source,
        AudioEditState("long_pause.wav", remove_internal_pauses_enabled=True),
        AudioProcessingConfig(),
        output_path=output,
    )

    assert result.output_path == output
    assert result.duration_ms is not None
    assert result.duration_ms <= source_duration_ms - 200


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg and ffprobe are required for audio rendering smoke tests",
)
def test_render_audio_remove_pauses_preserves_quiet_micro_word_between_pauses(
    tmp_path: Path,
) -> None:
    source = tmp_path / "quiet_micro_word.wav"
    output = tmp_path / "quiet_micro_word.mp3"
    _generate_quiet_micro_word_clip(source)
    source_duration_ms = probe_duration_ms(source, AudioProcessingConfig())

    result = render_audio(
        source,
        AudioEditState("quiet_micro_word.wav", remove_internal_pauses_enabled=True),
        AudioProcessingConfig(),
        output_path=output,
    )

    assert result.output_path == output
    assert abs((result.duration_ms or 0) - source_duration_ms) <= 25


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg and ffprobe are required for audio rendering smoke tests",
)
def test_render_playback_segment_from_70_percent_is_shorter(tmp_path: Path) -> None:
    source = tmp_path / "cursor source.wav"
    output = tmp_path / "cursor segment.mp3"

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

    result = render_playback_segment(
        source,
        700,
        AudioProcessingConfig(),
        output_path=output,
    )

    assert result.output_path == output
    assert "atrim=start=0.700" in format_ffmpeg_command(result.command)
    assert output.is_file()
    assert 220 <= probe_duration_ms(output, AudioProcessingConfig()) <= 380


def _generate_short_pause_clip(path: Path) -> None:
    _run_ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=220:duration=0.25",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono:d=0.25",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=300:duration=0.25",
        "-filter_complex",
        "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
        "-map",
        "[out]",
        str(path),
    )


def _generate_long_pause_clip(path: Path) -> None:
    _run_ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=220:duration=0.25",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono:d=0.75",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=300:duration=0.25",
        "-filter_complex",
        "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
        "-map",
        "[out]",
        str(path),
    )


def _generate_quiet_micro_word_clip(path: Path) -> None:
    _run_ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=220:duration=0.20",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono:d=0.31",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=260:duration=0.07,volume=0.08",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono:d=0.31",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=300:duration=0.20",
        "-filter_complex",
        "[0:a][1:a][2:a][3:a][4:a]concat=n=5:v=0:a=1[out]",
        "-map",
        "[out]",
        str(path),
    )


def _run_ffmpeg(*args: str) -> None:
    subprocess.run(
        ["ffmpeg", "-y", *args],
        check=True,
        capture_output=True,
        text=True,
    )
