"""Tests for import-safe pause speed-up planning helpers."""

from __future__ import annotations

from anki_audio_quick_editor.audio_pipeline import (
    SilenceInterval,
    build_filter_complex_script,
    parse_silencedetect_intervals,
    plan_pause_timeline,
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


def test_plan_pause_timeline_preserves_short_pauses_and_targets_long_gap() -> None:
    intervals = (
        SilenceInterval(start_ms=200, end_ms=350, duration_ms=150),
        SilenceInterval(start_ms=600, end_ms=1100, duration_ms=500),
    )

    timeline = plan_pause_timeline(
        1400,
        intervals,
        min_pause_ms=300,
        target_gap_ms=100,
    )

    assert [segment.kind for segment in timeline] == ["normal", "pause", "normal"]
    assert timeline[0].start_ms == 0
    assert timeline[0].end_ms == 600
    assert timeline[1].start_ms == 600
    assert timeline[1].end_ms == 1100
    assert timeline[1].speed_factor == 5.0
    assert timeline[1].output_duration_ms == 100
    assert timeline[2].start_ms == 1100
    assert timeline[2].end_ms == 1400


def test_filter_complex_script_speeds_pause_segments_only() -> None:
    timeline = plan_pause_timeline(
        1000,
        (SilenceInterval(start_ms=300, end_ms=800, duration_ms=500),),
        min_pause_ms=300,
        target_gap_ms=100,
    )

    script = build_filter_complex_script(timeline, volume_db=3.0, speed=1.25)

    assert "asplit=3" in script
    assert "atrim=start=0.300:end=0.800,asetpts=PTS-STARTPTS,atempo=2.000,atempo=2.000,atempo=1.250" in script
    assert "atrim=start=0.000:end=0.300,asetpts=PTS-STARTPTS[a0]" in script
    assert "concat=n=3:v=0:a=1[cat]" in script
    assert "[cat]volume=3.00dB,atempo=1.250[out]" in script
