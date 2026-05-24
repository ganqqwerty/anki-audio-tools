from __future__ import annotations

from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_processor import (
    build_audio_filters,
    build_convert_audio_command,
    build_region_delete_plan,
    build_region_keep_plan,
    build_silencedetect_command,
    build_working_original_filters,
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


@pytest.mark.parametrize(
    ("target_format", "codec_args"),
    [
        ("mp3", ("-codec:a", "libmp3lame", "-q:a", "4")),
        ("m4a", ("-codec:a", "aac", "-b:a", "192k")),
        ("wav", ("-codec:a", "pcm_s16le")),
        ("flac", ("-codec:a", "flac", "-compression_level", "5")),
    ],
)
def test_build_convert_audio_command_uses_format_codec_args(
    target_format: str,
    codec_args: tuple[str, ...],
    tmp_path: Path,
) -> None:
    command = build_convert_audio_command(
        Path("/bin/ffmpeg"),
        tmp_path / "source.wav",
        tmp_path / f"converted.{target_format}",
        target_format,
    )

    assert command == (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "source.wav"),
        "-vn",
        *codec_args,
        str(tmp_path / f"converted.{target_format}"),
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

