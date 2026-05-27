"""Tests for import-safe pause removal planning helpers."""

from __future__ import annotations

from datetime import datetime

from anki_audio_quick_editor.audio_pipeline import (
    SilenceInterval,
    TimelineSegment,
    atempo_filters,
    build_filter_complex_script,
    filter_silence_intervals_by_duration,
    make_pause_pipeline_run_id,
    merge_short_speech_gaps,
    parse_silencedetect_intervals,
    plan_pause_removal_timeline,
)


def test_parse_silencedetect_intervals_handles_complete_and_trailing_silence() -> None:
    stderr = "\n".join(
        [
            "[silencedetect @ 0x1] silence_start: 0.25",
            "[silencedetect @ 0x1] silence_end: 0.80 | silence_duration: 0.55",
            "[silencedetect @ 0x1] silence_start: 1.20",
        ]
    )

    intervals = parse_silencedetect_intervals(stderr, 1500)

    assert intervals == (
        SilenceInterval(start_ms=250, end_ms=800, duration_ms=550),
        SilenceInterval(start_ms=1200, end_ms=1500, duration_ms=300),
    )


def test_filter_complex_script_never_speeds_pause_segments() -> None:
    timeline = (
        TimelineSegment(
            kind="pause",
            start_ms=300,
            end_ms=800,
            speed_factor=5.0,
            output_duration_ms=100,
        ),
    )

    script = build_filter_complex_script(timeline, volume_db=3.0, speed=1.25)

    assert "atrim=start=0.300:end=0.800,asetpts=PTS-STARTPTS[a0]" in script
    assert "atempo=5" not in script
    assert "[cat]volume=3.00dB,atempo=1.250[out]" in script


def test_pause_removal_timeline_cuts_intervals_without_speed_segments() -> None:
    timeline = plan_pause_removal_timeline(
        1800,
        (
            SilenceInterval(start_ms=500, end_ms=1200, duration_ms=700),
            SilenceInterval(start_ms=1500, end_ms=1800, duration_ms=300),
        ),
    )

    assert [segment.kind for segment in timeline] == ["normal", "normal"]
    assert [(segment.start_ms, segment.end_ms, segment.speed_factor) for segment in timeline] == [
        (0, 500, 1.0),
        (1200, 1500, 1.0),
    ]


def test_pause_removal_timeline_clamps_overlaps_and_never_returns_negative_segments() -> None:
    timeline = plan_pause_removal_timeline(
        1000,
        (
            SilenceInterval(start_ms=-100, end_ms=300, duration_ms=400),
            SilenceInterval(start_ms=250, end_ms=500, duration_ms=250),
            SilenceInterval(start_ms=900, end_ms=1400, duration_ms=500),
        ),
    )

    assert [(segment.start_ms, segment.end_ms) for segment in timeline] == [(500, 900)]
    assert all(segment.output_duration_ms > 0 for segment in timeline)


def test_pause_removal_timeline_keeps_minimal_segment_for_full_clip_pause() -> None:
    assert plan_pause_removal_timeline(
        1000,
        (SilenceInterval(start_ms=0, end_ms=1000, duration_ms=1000),),
    )[0].end_ms == 1


def test_pause_interval_post_processing_merges_short_speech_and_filters_short_silence() -> None:
    merged = merge_short_speech_gaps(
        (
            SilenceInterval(start_ms=100, end_ms=300, duration_ms=200),
            SilenceInterval(start_ms=360, end_ms=700, duration_ms=340),
            SilenceInterval(start_ms=900, end_ms=970, duration_ms=70),
        ),
        1000,
        min_speech_ms=100,
    )

    assert merged == (
        SilenceInterval(start_ms=100, end_ms=700, duration_ms=600),
        SilenceInterval(start_ms=900, end_ms=970, duration_ms=70),
    )
    assert filter_silence_intervals_by_duration(merged, min_silence_ms=200) == (
        SilenceInterval(start_ms=100, end_ms=700, duration_ms=600),
    )


def test_parse_silencedetect_intervals_reconstructs_orphan_end_from_duration() -> None:
    stderr = "[silencedetect @ 0x1] silence_end: 1.20 | silence_duration: 0.40"

    intervals = parse_silencedetect_intervals(stderr, 2000)

    assert intervals == (SilenceInterval(start_ms=800, end_ms=1200, duration_ms=400),)


def test_parse_silencedetect_intervals_merges_overlaps_and_drops_invalid_ranges() -> None:
    stderr = "\n".join(
        [
            "[silencedetect @ 0x1] silence_start: -0.10",
            "[silencedetect @ 0x1] silence_end: 0.20 | silence_duration: 0.30",
            "[silencedetect @ 0x1] silence_start: 0.15",
            "[silencedetect @ 0x1] silence_end: 0.30 | silence_duration: 0.15",
            "[silencedetect @ 0x1] silence_end: 0.40",
            "[silencedetect @ 0x1] silence_start: 0.50",
            "[silencedetect @ 0x1] silence_end: 0.50 | silence_duration: 0.00",
            "[silencedetect @ 0x1] silence_start: 0.90",
            "[silencedetect @ 0x1] silence_end: 1.50 | silence_duration: 0.60",
        ]
    )

    intervals = parse_silencedetect_intervals(stderr, 1000)

    assert intervals == (
        SilenceInterval(start_ms=0, end_ms=300, duration_ms=300),
        SilenceInterval(start_ms=900, end_ms=1000, duration_ms=100),
    )


def test_filter_complex_script_uses_tiny_anull_fallback_for_empty_timeline() -> None:
    script = build_filter_complex_script((), volume_db=0.0, speed=1.0)

    assert "asplit" not in script
    assert "[0:a]atrim=start=0.000:end=0.001,asetpts=PTS-STARTPTS[a0]" in script
    assert "[a0]concat=n=1:v=0:a=1[cat]" in script
    assert "[cat]anull[out]" in script


def test_atempo_filters_handle_low_speed_below_half() -> None:
    assert atempo_filters(0.1) == [
        "atempo=0.500",
        "atempo=0.500",
        "atempo=0.500",
        "atempo=0.800",
    ]


def test_make_pause_pipeline_run_id_sanitizes_and_bounds_problematic_filename() -> None:
    run_id = make_pause_pipeline_run_id(
        "folder/短い clip name?.wav",
        now=datetime(2026, 5, 17, 9, 8, 7, 123456),
        token="deadbeef",
    )

    assert run_id == "clip_name__20260517_090807_123456_deadbeef"
    assert "/" not in run_id
    assert " " not in run_id
    assert "?" not in run_id
    assert len(run_id) <= 160
