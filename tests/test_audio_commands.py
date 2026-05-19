from __future__ import annotations

from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_processor import (
    _atempo_filters,
    build_audio_filters,
    build_deep_filter_command,
    build_deep_filter_prepare_command,
    build_mp3_encode_command,
    build_playback_segment_filters,
    build_region_delete_plan,
    build_region_keep_plan,
    build_rnnoise_command,
    build_rnnoise_encode_command,
    build_rnnoise_prepare_command,
    build_silencedetect_command,
    build_working_original_filters,
    select_deep_filter_output,
)
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.errors import (
    AudioProcessingError,
)


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


def test_build_region_delete_plan_concats_audio_around_middle_selection() -> None:
    plan = build_region_delete_plan(500, 1250, 2000)

    assert plan.removed_duration_ms == 750
    assert plan.expected_duration_ms == 1250
    assert plan.filter_complex == (
        "[0:a]atrim=start=0.000:end=0.500,asetpts=PTS-STARTPTS[a0];"
        "[0:a]atrim=start=1.250:end=2.000,asetpts=PTS-STARTPTS[a1];"
        "[a0][a1]concat=n=2:v=0:a=1[out]"
    )


def test_build_region_delete_plan_handles_prefix_and_suffix_deletion() -> None:
    assert build_region_delete_plan(0, 400, 2000).filter_complex == (
        "[0:a]atrim=start=0.400,asetpts=PTS-STARTPTS[out]"
    )
    assert build_region_delete_plan(1400, 2000, 2000).filter_complex == (
        "[0:a]atrim=end=1.400,asetpts=PTS-STARTPTS[out]"
    )


def test_build_region_delete_plan_rejects_whole_audio_deletion() -> None:
    with pytest.raises(AudioProcessingError, match="whole audio"):
        build_region_delete_plan(0, 2000, 2000)


def test_build_region_keep_plan_keeps_middle_selection() -> None:
    plan = build_region_keep_plan(500, 1250, 2000)

    assert plan.kept_duration_ms == 750
    assert plan.removed_duration_ms == 1250
    assert plan.expected_duration_ms == 750
    assert plan.filter_complex == (
        "[0:a]atrim=start=0.500:end=1.250,asetpts=PTS-STARTPTS[out]"
    )


def test_build_region_keep_plan_handles_edge_selections() -> None:
    assert build_region_keep_plan(0, 400, 2000).filter_complex == (
        "[0:a]atrim=start=0.000:end=0.400,asetpts=PTS-STARTPTS[out]"
    )
    assert build_region_keep_plan(1400, 2000, 2000).filter_complex == (
        "[0:a]atrim=start=1.400:end=2.000,asetpts=PTS-STARTPTS[out]"
    )


def test_build_region_keep_plan_rejects_empty_and_whole_audio_selection() -> None:
    with pytest.raises(AudioProcessingError, match="Select a region"):
        build_region_keep_plan(500, 500, 2000)
    with pytest.raises(AudioProcessingError, match="already covers the whole audio clip"):
        build_region_keep_plan(0, 2000, 2000)


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



def test_atempo_filters_preserve_exact_boundary_values() -> None:
    assert _atempo_filters(2.0) == ["atempo=2.000"]
    assert _atempo_filters(2.5) == ["atempo=2.000", "atempo=1.250"]
    assert _atempo_filters(0.5) == ["atempo=0.500"]
    assert _atempo_filters(4.0) == ["atempo=2.000", "atempo=2.000"]
    assert _atempo_filters(0.25) == ["atempo=0.500", "atempo=0.500"]
    assert _atempo_filters(0.1) == ["atempo=0.500", "atempo=0.500", "atempo=0.500", "atempo=0.800"]

