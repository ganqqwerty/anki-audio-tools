"""Tests for ffmpeg command construction helpers."""

from __future__ import annotations

import importlib
import json
import math
import random
import shutil
import subprocess
import sys
import wave
from array import array
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor.audio_processor import (
    _atempo_filters,
    _render_external_error_message,
    _safe_filename_stem,
    build_audio_filters,
    build_deep_filter_command,
    build_deep_filter_prepare_command,
    build_mp3_encode_command,
    build_mp_senet_command,
    build_mp_senet_prepare_command,
    build_playback_segment_filters,
    build_rnnoise_command,
    build_rnnoise_encode_command,
    build_rnnoise_prepare_command,
    build_silencedetect_command,
    build_working_original_filters,
    find_deep_filter,
    find_ffmpeg,
    find_ffprobe,
    find_mp_senet_bundle,
    find_rnnoise_bundle,
    format_ffmpeg_command,
    make_output_filename,
    make_playback_segment_filename,
    probe_duration_ms,
    render_audio,
    render_mp_senet_audio,
    render_noise_reduced_audio,
    render_playback_segment,
    render_rnnoise_audio,
    select_deep_filter_output,
    temp_final_path,
)
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.errors import (
    AudioProcessingError,
    MissingDeepFilterError,
    MissingFfmpegError,
    MissingMpSenetError,
    MissingRnnoiseError,
)
from anki_audio_quick_editor.support import (
    clear_latest_mp_senet_support_incident,
    clear_latest_pause_pipeline_support_incident,
    clear_latest_rnnoise_support_incident,
    latest_mp_senet_support_incident,
    latest_pause_pipeline_support_incident,
    latest_rnnoise_support_incident,
)

FFMPEG_SKIP_REASON = "ffmpeg and ffprobe are required for audio rendering smoke tests"


def _deep_filter_available() -> bool:
    try:
        find_deep_filter()
    except MissingDeepFilterError:
        return False
    return True


def _fake_deep_filter_executable(tmp_path: Path, *, fail: bool = False) -> Path:
    script_path = tmp_path / "fake_deep_filter.py"
    script_path.write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "import shutil",
                "import sys",
                "from pathlib import Path",
                f"FAIL = {fail!r}",
                "args = sys.argv[1:]",
                "if FAIL:",
                "    sys.stderr.write('fake deep-filter failed')",
                "    raise SystemExit(12)",
                "output_dir = Path(args[args.index('-o') + 1])",
                "input_wav = Path(args[-1])",
                "output_dir.mkdir(parents=True, exist_ok=True)",
                "shutil.copyfile(input_wav, output_dir / 'clean.wav')",
            ]
        ),
        encoding="utf-8",
    )
    executable = tmp_path / "deep-filter"
    executable.write_text(
        "#!/bin/sh\n"
        f"exec {sys.executable!r} {str(script_path)!r} \"$@\"\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
DEEP_FILTER_AVAILABLE = _deep_filter_available()


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

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor._bundled_deep_filter_path", lambda: None)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", fake_which)

    assert find_deep_filter() == Path("/usr/local/bin/deep-filter")
    assert calls == ["deep-filter"]


def test_find_deep_filter_uses_bundled_binary_before_path_lookup(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundled = tmp_path / "deep-filter"
    bundled.write_text("")
    calls: list[str] = []

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor._bundled_deep_filter_path",
        lambda: bundled,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.shutil.which",
        lambda name: calls.append(name) or "/usr/local/bin/deep-filter",
    )

    assert find_deep_filter() == bundled
    assert calls == []


def test_find_deep_filter_prefers_existing_configured_file(tmp_path: Path) -> None:
    deep_filter = tmp_path / "deep-filter"
    deep_filter.write_text("")

    assert find_deep_filter(str(deep_filter)) == deep_filter


def test_find_deep_filter_raises_when_missing(monkeypatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor._bundled_deep_filter_path", lambda: None)
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.shutil.which", lambda _name: None)

    with pytest.raises(MissingDeepFilterError, match="DeepFilterNet.*Standard denoise.*Shorten Pauses"):
        find_deep_filter()


def test_find_mp_senet_bundle_uses_bundled_directory_when_complete(tmp_path: Path, monkeypatch) -> None:
    bundled_dir = tmp_path / "mp-senet-cli-macos-arm64"
    mp_senet_path = bundled_dir / "bin" / "mp-senet-cli"
    model_path = bundled_dir / "models" / "mp_senet_vb.torchscript.pt"
    mp_senet_path.parent.mkdir(parents=True)
    model_path.parent.mkdir(parents=True)
    mp_senet_path.write_text("")
    (bundled_dir / "bin" / "mp-senet-cli-real").write_text("")
    model_path.write_text("")

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_mp_senet_dir",
        lambda: bundled_dir,
    )

    assert find_mp_senet_bundle() == (mp_senet_path, model_path)


def test_find_mp_senet_bundle_raises_when_bundle_is_incomplete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundled_dir = tmp_path / "mp-senet-cli-macos-arm64"
    (bundled_dir / "bin").mkdir(parents=True)
    (bundled_dir / "bin" / "mp-senet-cli").write_text("")
    (bundled_dir / "models").mkdir(parents=True)

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_mp_senet_dir",
        lambda: bundled_dir,
    )

    with pytest.raises(MissingMpSenetError, match="bundled mp-senet-cli runtime and model file"):
        find_mp_senet_bundle()


def test_find_rnnoise_bundle_uses_bundled_executable_when_complete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundled_dir = tmp_path / "rnnoise-cli-macos-arm64"
    rnnoise_path = bundled_dir / "bin" / "rnnoise-cli"
    rnnoise_path.parent.mkdir(parents=True)
    rnnoise_path.write_text("")

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_rnnoise_dir",
        lambda: bundled_dir,
    )

    assert find_rnnoise_bundle() == rnnoise_path


def test_find_rnnoise_bundle_raises_when_bundle_is_incomplete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundled_dir = tmp_path / "rnnoise-cli-macos-arm64"
    (bundled_dir / "bin").mkdir(parents=True)

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.expected_bundled_rnnoise_dir",
        lambda: bundled_dir,
    )

    with pytest.raises(MissingRnnoiseError, match="bundled rnnoise-cli executable"):
        find_rnnoise_bundle()


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
    state = AudioEditState(
        "clip.mp3",
        left_trim_ms=200,
        right_trim_ms=100,
        speed=1.15,
        volume_db=3.0,
        remove_internal_pauses_enabled=True,
    )

    filters = build_audio_filters(3000, state)

    assert "atrim=start=0.200:end=2.900" in filters
    assert "silenceremove" not in filters
    assert "volume=3.00dB" in filters
    assert "atempo=1.150" in filters
    assert filters.index("volume=3.00dB") < filters.index("atempo=1.150")


def test_build_audio_filters_omits_volume_filter_when_unchanged() -> None:
    filters = build_audio_filters(3000, AudioEditState("clip.mp3"))

    assert "volume=" not in filters


def test_build_audio_filters_omits_atempo_when_speed_is_unchanged() -> None:
    filters = build_audio_filters(3000, AudioEditState("clip.mp3", speed=1.0))

    assert "atempo=" not in filters


def test_build_working_original_filters_omits_volume_speed_and_internal_pause_processing() -> None:
    filters = build_working_original_filters(
        3000,
        AudioEditState(
            "clip.mp3",
            speed=1.25,
            volume_db=3.0,
            remove_internal_pauses_enabled=True,
        ),
    )

    assert filters == "atrim=start=0.000:end=3.000,asetpts=PTS-STARTPTS"


def test_build_silencedetect_command_uses_exact_pause_threshold_and_gap_values(tmp_path: Path) -> None:
    config = AudioProcessingConfig(
        internal_pause_silence_threshold_db=-41,
        internal_pause_threshold_ms=275,
        internal_pause_target_gap_ms=125,
    )

    command = build_silencedetect_command(
        Path("/bin/ffmpeg"),
        tmp_path / "analysis.wav",
        threshold_db=config.internal_pause_silence_threshold_db,
        min_duration_ms=config.internal_pause_threshold_ms,
    )

    assert command == (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "analysis.wav"),
        "-af",
        "silencedetect=noise=-41dB:d=0.275",
        "-f",
        "null",
        "-",
    )


def test_build_audio_filters_omits_edge_silence_filter_parameters() -> None:
    config = AudioProcessingConfig(
        internal_pause_silence_threshold_db=-47,
        internal_pause_threshold_ms=509,
        internal_pause_target_gap_ms=509,
    )
    state = AudioEditState(
        "clip.mp3",
        remove_internal_pauses_enabled=True,
    )

    filters = build_audio_filters(3000, state)
    pause_threshold = f"{config.internal_pause_silence_threshold_db}dB"

    assert "silenceremove" not in filters
    assert "start_duration=0.509" not in filters
    assert pause_threshold not in filters


def test_build_audio_filters_preserves_precise_trim_boundaries() -> None:
    state = AudioEditState("clip.mp3", left_trim_ms=999, right_trim_ms=222)

    filters = build_audio_filters(3000, state)

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


def test_build_mp_senet_prepare_command_uses_16khz_mono_pcm(tmp_path: Path) -> None:
    command = build_mp_senet_prepare_command(
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
        "16000",
        "-codec:a",
        "pcm_s16le",
        str(tmp_path / "input.wav"),
    )


def test_build_mp_senet_command_includes_model_path_and_json(tmp_path: Path) -> None:
    command = build_mp_senet_command(
        Path("/bin/mp-senet-cli"),
        tmp_path / "input.wav",
        tmp_path / "output.wav",
        tmp_path / "models" / "mp_senet_vb.torchscript.pt",
    )

    assert command == (
        "/bin/mp-senet-cli",
        "denoise",
        "--input",
        str(tmp_path / "input.wav"),
        "--output",
        str(tmp_path / "output.wav"),
        "--model",
        str(tmp_path / "models" / "mp_senet_vb.torchscript.pt"),
        "--overwrite",
        "--json",
    )


def test_build_rnnoise_prepare_command_uses_48khz_mono_raw_pcm(tmp_path: Path) -> None:
    command = build_rnnoise_prepare_command(
        Path("/bin/ffmpeg"),
        tmp_path / "source.mp3",
        tmp_path / "input.s16le",
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
        "-f",
        "s16le",
        "-codec:a",
        "pcm_s16le",
        str(tmp_path / "input.s16le"),
    )


def test_build_rnnoise_command_includes_json_and_overwrite(tmp_path: Path) -> None:
    command = build_rnnoise_command(
        Path("/bin/rnnoise-cli"),
        tmp_path / "input.s16le",
        tmp_path / "denoised.s16le",
    )

    assert command == (
        "/bin/rnnoise-cli",
        "denoise",
        "--input",
        str(tmp_path / "input.s16le"),
        "--output",
        str(tmp_path / "denoised.s16le"),
        "--overwrite",
        "--json",
    )


def test_build_rnnoise_encode_command_reads_raw_pcm(tmp_path: Path) -> None:
    command = build_rnnoise_encode_command(
        Path("/bin/ffmpeg"),
        tmp_path / "denoised.s16le",
        tmp_path / "denoised.mp3",
    )

    assert command == (
        "/bin/ffmpeg",
        "-y",
        "-f",
        "s16le",
        "-ar",
        "48000",
        "-ac",
        "1",
        "-i",
        str(tmp_path / "denoised.s16le"),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(tmp_path / "denoised.mp3"),
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


def test_render_audio_pause_pipeline_records_launch_error_for_out_of_disk(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_pause_pipeline_support_incident()
    source = tmp_path / "source.mp3"
    source.write_bytes(b"source")
    output = tmp_path / "out.mp3"
    artifact_root = tmp_path / "artifacts"

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_deep_filter",
        lambda _path: Path("/bin/deep-filter"),
    )
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)

    def fake_run(*_args, **_kwargs) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="No space left on device"):
        render_audio(
            source,
            AudioEditState("source.mp3", remove_internal_pauses_enabled=True),
            AudioProcessingConfig(),
            output_path=output,
            artifact_root=artifact_root,
        )

    run_dirs = list(artifact_root.iterdir())
    assert len(run_dirs) == 1
    manifest_path = run_dirs[0] / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["stages"][0]["name"] == "render_working_original"
    assert "No space left on device" in manifest["stages"][0]["launch_error"]
    incident = latest_pause_pipeline_support_incident()
    assert incident is not None
    assert incident["manifest_path"] == str(manifest_path)
    assert incident["attempted_commands"][0]["launch_error"].startswith("Could not start working-audio preparation.")


def test_render_mp_senet_audio_runs_prepare_denoise_and_encode(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_mp_senet_support_incident()
    calls: list[list[str]] = []
    commands: list[tuple[str, ...]] = []
    model_path = tmp_path / "models" / "mp_senet_vb.torchscript.pt"

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_mp_senet_bundle",
        lambda: (Path("/bin/mp-senet-cli"), model_path),
    )
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        calls.append(cmd)
        if cmd[0] == "/bin/mp-senet-cli":
            Path(cmd[cmd.index("--output") + 1]).write_bytes(b"denoised")
            return SimpleNamespace(returncode=0, stdout='{"ok":true}', stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "denoised.mp3"
    result = render_mp_senet_audio(
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
        "1",
        "-ar",
        "16000",
        "-codec:a",
        "pcm_s16le",
        calls[0][-1],
    ]
    assert calls[1][0] == "/bin/mp-senet-cli"
    assert "--model" in calls[1]
    assert "--json" in calls[1]
    assert calls[2][0:4] == ["/bin/ffmpeg", "-y", "-i", calls[2][3]]
    assert calls[2][-5:] == ["-codec:a", "libmp3lame", "-q:a", "4", str(output)]
    assert commands == [tuple(call) for call in calls]
    assert result.output_path == output
    assert result.command == tuple(calls[1])
    assert result.duration_ms == 1000
    assert latest_mp_senet_support_incident() is None


def test_render_mp_senet_audio_reports_denoise_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_mp_senet_support_incident()
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_mp_senet_bundle",
        lambda: (Path("/bin/mp-senet-cli"), tmp_path / "models" / "mp_senet_vb.torchscript.pt"),
    )

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        if cmd[0] == "/bin/mp-senet-cli":
            return SimpleNamespace(returncode=5, stdout='{"error":"TorchScript load failed"}', stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="TorchScript load failed"):
        render_mp_senet_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "denoised.mp3",
        )
    incident = latest_mp_senet_support_incident()
    assert incident is not None
    assert incident["operation"] == "mp_senet_denoise"
    assert incident["media_filename"] == "source.mp3"
    assert incident["ffmpeg_path"] == "/bin/ffmpeg"
    assert incident["mp_senet_path"] == "/bin/mp-senet-cli"
    assert len(incident["attempted_commands"]) == 2
    assert incident["attempted_commands"][1]["command"].startswith("/bin/mp-senet-cli denoise")
    assert incident["attempted_commands"][1]["returncode"] == 5
    assert incident["attempted_commands"][1]["stdout"] == '{"error":"TorchScript load failed"}'


def test_render_mp_senet_audio_reports_launch_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_mp_senet_support_incident()
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_mp_senet_bundle",
        lambda: (Path("/bin/mp-senet-cli"), tmp_path / "models" / "mp_senet_vb.torchscript.pt"),
    )

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        if cmd[0] == "/bin/mp-senet-cli":
            raise PermissionError(13, "Permission denied", "/bin/mp-senet-cli")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="Could not start MP-SENet denoise"):
        render_mp_senet_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "denoised.mp3",
        )
    incident = latest_mp_senet_support_incident()
    assert incident is not None
    assert incident["attempted_commands"][1]["launch_error"].startswith(
        "Could not start MP-SENet denoise."
    )


def test_render_rnnoise_audio_runs_prepare_denoise_and_encode(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_rnnoise_support_incident()
    calls: list[list[str]] = []
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_rnnoise_bundle",
        lambda: Path("/bin/rnnoise-cli"),
    )
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: 1000)

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        calls.append(cmd)
        if cmd[0] == "/bin/rnnoise-cli":
            Path(cmd[cmd.index("--output") + 1]).write_bytes(b"denoised")
            return SimpleNamespace(returncode=0, stdout='{"ok":true}', stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "denoised.mp3"
    result = render_rnnoise_audio(
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
        "1",
        "-ar",
        "48000",
        "-f",
        "s16le",
        "-codec:a",
        "pcm_s16le",
        calls[0][-1],
    ]
    assert calls[1][0] == "/bin/rnnoise-cli"
    assert calls[1][1:] == [
        "denoise",
        "--input",
        calls[1][3],
        "--output",
        calls[1][5],
        "--overwrite",
        "--json",
    ]
    assert calls[2][0:8] == ["/bin/ffmpeg", "-y", "-f", "s16le", "-ar", "48000", "-ac", "1"]
    assert calls[2][-5:] == ["-codec:a", "libmp3lame", "-q:a", "4", str(output)]
    assert commands == [tuple(call) for call in calls]
    assert result.output_path == output
    assert result.command == tuple(calls[1])
    assert result.duration_ms == 1000
    assert latest_rnnoise_support_incident() is None


def test_render_rnnoise_audio_reports_denoise_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_rnnoise_support_incident()
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_rnnoise_bundle",
        lambda: Path("/bin/rnnoise-cli"),
    )

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        if cmd[0] == "/bin/rnnoise-cli":
            return SimpleNamespace(returncode=5, stdout='{"error":"invalid raw input"}', stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="invalid raw input"):
        render_rnnoise_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "denoised.mp3",
        )
    incident = latest_rnnoise_support_incident()
    assert incident is not None
    assert incident["operation"] == "rnnoise_denoise"
    assert incident["media_filename"] == "source.mp3"
    assert incident["ffmpeg_path"] == "/bin/ffmpeg"
    assert incident["rnnoise_path"] == "/bin/rnnoise-cli"
    assert len(incident["attempted_commands"]) == 2
    assert incident["attempted_commands"][1]["command"].startswith("/bin/rnnoise-cli denoise")
    assert incident["attempted_commands"][1]["returncode"] == 5
    assert incident["attempted_commands"][1]["stdout"] == '{"error":"invalid raw input"}'


def test_render_rnnoise_audio_reports_launch_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    clear_latest_rnnoise_support_incident()
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_processor.find_rnnoise_bundle",
        lambda: Path("/bin/rnnoise-cli"),
    )

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        if cmd[0] == "/bin/rnnoise-cli":
            raise PermissionError(13, "Permission denied", "/bin/rnnoise-cli")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    with pytest.raises(AudioProcessingError, match="Could not start RNNoise denoise"):
        render_rnnoise_audio(
            tmp_path / "source.mp3",
            AudioProcessingConfig(),
            output_path=tmp_path / "denoised.mp3",
        )
    incident = latest_rnnoise_support_incident()
    assert incident is not None
    assert incident["attempted_commands"][1]["launch_error"].startswith("Could not start RNNoise denoise.")


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
def test_render_audio_remove_pauses_preserves_short_pause(tmp_path: Path) -> None:
    source = tmp_path / "short_pause.wav"
    output = tmp_path / "short_pause.mp3"
    artifact_root = tmp_path / "artifacts"
    fake_deep_filter = _fake_deep_filter_executable(tmp_path)
    _generate_short_pause_clip(source)
    source_duration_ms = probe_duration_ms(source, AudioProcessingConfig())

    result = render_audio(
        source,
        AudioEditState("short_pause.wav", remove_internal_pauses_enabled=True),
        AudioProcessingConfig(deep_filter_path=str(fake_deep_filter)),
        output_path=output,
        artifact_root=artifact_root,
    )

    assert result.output_path == output
    assert abs((result.duration_ms or 0) - source_duration_ms) <= 25
    assert result.artifact_manifest_path is not None
    manifest = json.loads(result.artifact_manifest_path.read_text(encoding="utf-8"))
    assert manifest["timeline"] == [
        {
            "end_ms": source_duration_ms,
            "kind": "normal",
            "output_duration_ms": source_duration_ms,
            "speed_factor": 1.0,
            "start_ms": 0,
        }
    ]


@pytest.mark.skipif(
    not FFMPEG_AVAILABLE,
    reason=FFMPEG_SKIP_REASON,
)
def test_render_audio_remove_pauses_compresses_obvious_long_pause(tmp_path: Path) -> None:
    source = tmp_path / "long_pause.wav"
    output = tmp_path / "long_pause.mp3"
    artifact_root = tmp_path / "artifacts"
    fake_deep_filter = _fake_deep_filter_executable(tmp_path)
    _generate_long_pause_clip(source)
    source_duration_ms = probe_duration_ms(source, AudioProcessingConfig())

    result = render_audio(
        source,
        AudioEditState("long_pause.wav", remove_internal_pauses_enabled=True),
        AudioProcessingConfig(deep_filter_path=str(fake_deep_filter)),
        output_path=output,
        artifact_root=artifact_root,
    )

    assert result.output_path == output
    assert result.duration_ms is not None
    assert result.duration_ms <= source_duration_ms - 200
    assert result.artifact_manifest_path is not None
    run_dir = result.artifact_manifest_path.parent
    assert (run_dir / "01_working_original.wav").is_file()
    assert (run_dir / "02_analysis_input_48k_mono.wav").is_file()
    assert (run_dir / "03_deep_filter_output" / "clean.wav").is_file()
    assert (run_dir / "04_silencedetect_stderr.txt").is_file()
    assert (run_dir / "04_silence_intervals.json").is_file()
    assert (run_dir / "05_timeline.json").is_file()
    assert (run_dir / "06_filter_complex.ffscript").is_file()
    assert (run_dir / "07_final_output.mp3").is_file()
    filter_script = (run_dir / "06_filter_complex.ffscript").read_text(encoding="utf-8")
    assert "atempo=" in filter_script
    manifest = json.loads(result.artifact_manifest_path.read_text(encoding="utf-8"))
    assert manifest["operation"] == "deep_filter_pause_speedup"
    assert manifest["source"]["filename"] == "long_pause.wav"
    assert manifest["silence_intervals"]
    assert any(segment["kind"] == "pause" for segment in manifest["timeline"])
    render_stage = next(stage for stage in manifest["stages"] if stage["name"] == "render_final_output")
    assert "01_working_original.wav" in render_stage["command"]
    assert "06_filter_complex.ffscript" in render_stage["command"]


@pytest.mark.skipif(
    not FFMPEG_AVAILABLE,
    reason=FFMPEG_SKIP_REASON,
)
def test_render_audio_remove_pauses_keeps_partial_manifest_on_deep_filter_failure(
    tmp_path: Path,
) -> None:
    clear_latest_pause_pipeline_support_incident()
    source = tmp_path / "long_pause.wav"
    output = tmp_path / "long_pause.mp3"
    artifact_root = tmp_path / "artifacts"
    fake_deep_filter = _fake_deep_filter_executable(tmp_path, fail=True)
    _generate_long_pause_clip(source)

    with pytest.raises(AudioProcessingError, match="fake deep-filter failed"):
        render_audio(
            source,
            AudioEditState("long_pause.wav", remove_internal_pauses_enabled=True),
            AudioProcessingConfig(deep_filter_path=str(fake_deep_filter)),
            output_path=output,
            artifact_root=artifact_root,
        )

    run_dirs = list(artifact_root.iterdir())
    assert len(run_dirs) == 1
    manifest_path = run_dirs[0] / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["errors"] == ["fake deep-filter failed"]
    assert [stage["name"] for stage in manifest["stages"]] == [
        "render_working_original",
        "prepare_deep_filter_input",
        "deep_filter_analysis",
    ]
    assert not output.exists()
    incident = latest_pause_pipeline_support_incident()
    assert incident is not None
    assert incident["manifest_path"] == str(manifest_path)
    assert incident["artifact_dir"] == str(run_dirs[0])


@pytest.mark.skipif(
    not FFMPEG_AVAILABLE,
    reason=FFMPEG_SKIP_REASON,
)
def test_render_audio_remove_pauses_preserves_quiet_micro_word_between_pauses(
    tmp_path: Path,
) -> None:
    source = tmp_path / "quiet_micro_word.wav"
    output = tmp_path / "quiet_micro_word.mp3"
    fake_deep_filter = _fake_deep_filter_executable(tmp_path)
    _generate_quiet_micro_word_clip(source)
    source_duration_ms = probe_duration_ms(source, AudioProcessingConfig())

    result = render_audio(
        source,
        AudioEditState("quiet_micro_word.wav", remove_internal_pauses_enabled=True),
        AudioProcessingConfig(deep_filter_path=str(fake_deep_filter)),
        output_path=output,
        artifact_root=tmp_path / "artifacts",
    )

    assert result.output_path == output
    assert result.duration_ms is not None
    assert result.duration_ms < source_duration_ms
    assert result.duration_ms > 550
    assert result.artifact_manifest_path is not None
    manifest = json.loads(result.artifact_manifest_path.read_text(encoding="utf-8"))
    assert sum(1 for segment in manifest["timeline"] if segment["kind"] == "pause") == 2


@pytest.mark.skipif(
    not FFMPEG_AVAILABLE,
    reason=FFMPEG_SKIP_REASON,
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


def _generate_noisy_speech_like_clip(path: Path) -> None:
    sample_rate = 48_000
    duration_s = 1.6
    noise_only_s = 0.4
    rng = random.Random(42)
    samples: list[int] = []
    for index in range(round(sample_rate * duration_s)):
        time_s = index / sample_rate
        noise = rng.uniform(-0.08, 0.08)
        signal = 0.0
        if noise_only_s <= time_s < duration_s - noise_only_s:
            speech_time = time_s - noise_only_s
            envelope = 0.55 + 0.45 * math.sin(2 * math.pi * 4.5 * speech_time) ** 2
            signal = envelope * (
                0.16 * math.sin(2 * math.pi * 180 * speech_time)
                + 0.08 * math.sin(2 * math.pi * 360 * speech_time)
                + 0.04 * math.sin(2 * math.pi * 540 * speech_time)
            )
        value = max(-0.95, min(0.95, signal + noise))
        samples.append(round(value * 32767))

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(array("h", samples).tobytes())


def _decode_mono_pcm16(path: Path, sample_rate: int = 48_000) -> list[int]:
    result = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-f",
            "s16le",
            "pipe:1",
        ],
        check=True,
        capture_output=True,
    )
    samples = array("h")
    samples.frombytes(result.stdout)
    return list(samples)


def _window_rms(
    samples: list[int],
    *,
    start_s: float,
    end_s: float,
    sample_rate: int = 48_000,
) -> float:
    start = round(start_s * sample_rate)
    end = round(end_s * sample_rate)
    window = samples[start:end]
    assert window
    return math.sqrt(sum((sample / 32768) ** 2 for sample in window) / len(window))


def _db_drop(before: float, after: float) -> float:
    floor = 1e-9
    return 20 * math.log10(max(before, floor) / max(after, floor))


def _run_ffmpeg(*args: str) -> None:
    subprocess.run(
        ["ffmpeg", "-y", *args],
        check=True,
        capture_output=True,
        text=True,
    )
