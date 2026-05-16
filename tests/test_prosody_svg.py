"""Tests for SVG visualization media rendering."""

from __future__ import annotations

from datetime import datetime
import math

from anki_audio_quick_editor.prosody_svg import (
    PLOT,
    _append_pitch_path,
    _axis_ticks,
    _bounded,
    _format_time,
    _label_svg,
    _path_for_intensity,
    _pitch_paths,
    _safe_filename_stem,
    _x_axis_svg,
    _x_for_ms,
    _y_for_pitch,
    make_visualization_filename,
    render_prosody_svg,
)
from anki_audio_quick_editor.prosody_types import ProsodyPoint, ProsodyTrack


def test_visualization_filename_uses_source_stem_and_timestamp() -> None:
    filename = make_visualization_filename(
        "../Audio Clip!!.mp3",
        now=datetime(2026, 5, 16, 1, 2, 3, 456000),
    )

    assert filename == "Audio_Clip__aqe_viz_20260516_010203_456000.svg"


def test_visualization_filename_uses_audio_for_empty_source_and_generated_length_cap() -> None:
    empty_filename = make_visualization_filename(
        "",
        now=datetime(2026, 5, 16, 1, 2, 3, 456000),
    )
    long_filename = make_visualization_filename(
        "x" * 300 + ".mp3",
        now=datetime(2026, 5, 16, 1, 2, 3, 456000),
    )

    assert empty_filename == "audio__aqe_viz_20260516_010203_456000.svg"
    assert len(long_filename) == 120


def test_render_prosody_svg_contains_finite_intensity_pitch_and_labels() -> None:
    track = ProsodyTrack(
        duration_ms=1000,
        points=(
            ProsodyPoint(0, 120.0, -20.0, 0.1, True),
            ProsodyPoint(250, 180.0, -18.0, 0.4, True),
            ProsodyPoint(500, None, None, 0.0, False),
            ProsodyPoint(750, 240.0, -16.0, 0.8, True),
            ProsodyPoint(1000, 260.0, -14.0, 1.0, True),
        ),
        pitch_min_hz=120.0,
        pitch_max_hz=260.0,
        source_filename="clip.mp3",
        analyzer_name="test-analyzer",
    )

    svg = render_prosody_svg(track).decode("utf-8")

    assert svg.startswith("<svg ")
    assert "aqe-intensity" in svg
    assert svg.count("aqe-pitch-path") >= 2
    assert "XX" not in svg
    assert "260 Hz" in svg
    assert "120 Hz" in svg
    assert "test-analyzer" in svg
    assert 'aria-label="Audio visualization for clip.mp3"' in svg
    assert "<title>Audio visualization for clip.mp3</title>" in svg
    assert f'y2="{PLOT.height - PLOT.bottom}"' in svg
    assert f'y="{PLOT.height - 2}"' in svg
    assert f'd="{_path_for_intensity(track.points, 1000)}"' in svg
    assert "NaN" not in svg
    assert "Infinity" not in svg


def test_render_prosody_svg_zero_duration_uses_zero_tick_and_no_invalid_numbers() -> None:
    track = ProsodyTrack(
        duration_ms=0,
        points=(ProsodyPoint(0, None, None, 1.5, False),),
        pitch_min_hz=None,
        pitch_max_hz=None,
        source_filename="clip.mp3",
        analyzer_name="test-analyzer",
    )

    svg = render_prosody_svg(track).decode("utf-8")

    assert "0.00s" in svg
    assert "NaN" not in svg
    assert "Infinity" not in svg


def test_render_prosody_svg_switches_to_seconds_at_two_seconds() -> None:
    track = ProsodyTrack(
        duration_ms=2000,
        points=(
            ProsodyPoint(0, 120.0, -20.0, 0.2, True),
            ProsodyPoint(2000, 240.0, -15.0, 0.8, True),
        ),
        pitch_min_hz=120.0,
        pitch_max_hz=240.0,
        source_filename="clip.mp3",
        analyzer_name="test-analyzer",
    )

    svg = render_prosody_svg(track).decode("utf-8")

    assert "1.00s" in svg
    assert "2000 ms" not in svg


def test_safe_filename_stem_collapses_invalid_runs_and_falls_back_to_audio() -> None:
    assert _safe_filename_stem("voice / clip !!") == "voice_clip"
    assert _safe_filename_stem("voice-clip_ok") == "voice-clip_ok"
    assert _safe_filename_stem("短い") == "audio"


def test_x_for_ms_clamps_and_maps_single_millisecond_duration() -> None:
    assert _x_for_ms(-5, 1000) == float(PLOT.left)
    assert _x_for_ms(250, 1000) == float(PLOT.left + (PLOT.plot_width * 0.25))
    assert _x_for_ms(2000, 1000) == float(PLOT.left + PLOT.plot_width)
    assert _x_for_ms(1, 1) == float(PLOT.left + PLOT.plot_width)


def test_y_for_pitch_uses_bottom_for_invalid_ranges_and_maps_valid_pitch() -> None:
    bottom = float(PLOT.height - PLOT.bottom)

    assert _y_for_pitch(150.0, None, 300.0) == bottom
    assert _y_for_pitch(150.0, 100.0, None) == bottom
    assert _y_for_pitch(150.0, 200.0, 200.0) == bottom
    assert _y_for_pitch(100.0, 100.0, 300.0) == bottom
    assert _y_for_pitch(400.0, 100.0, 300.0) == float(PLOT.top)
    assert _y_for_pitch(200.0, 100.0, 300.0) == float(PLOT.top + (PLOT.plot_height / 2))


def test_path_for_intensity_requires_points_and_positive_duration() -> None:
    points = (
        ProsodyPoint(0, None, None, 0.25, False),
        ProsodyPoint(500, None, None, 0.5, False),
        ProsodyPoint(1000, None, None, 1.25, False),
    )
    tiny_duration_points = (
        ProsodyPoint(0, None, None, 0.5, False),
        ProsodyPoint(1, None, None, 0.75, False),
    )

    assert _path_for_intensity((), 1000) == ""
    assert _path_for_intensity(points, 0) == ""
    assert _path_for_intensity(tiny_duration_points, 1).startswith(f"M {PLOT.left:.2f} ")
    assert _path_for_intensity(points, 1000) == (
        f"M {PLOT.left:.2f} {PLOT.height - PLOT.bottom:.2f} "
        f"L {PLOT.left:.2f} {PLOT.height - PLOT.bottom - (0.25 * PLOT.plot_height):.2f} "
        f"L {_x_for_ms(500, 1000):.2f} {PLOT.height - PLOT.bottom - (0.5 * PLOT.plot_height):.2f} "
        f"L {PLOT.left + PLOT.plot_width:.2f} {PLOT.height - PLOT.bottom - PLOT.plot_height:.2f} "
        f"L {PLOT.left + PLOT.plot_width:.2f} {PLOT.height - PLOT.bottom:.2f} Z"
    )


def test_pitch_paths_split_unvoiced_regions_and_drop_singletons() -> None:
    track = ProsodyTrack(
        duration_ms=1000,
        points=(
            ProsodyPoint(0, 100.0, None, 0.1, True),
            ProsodyPoint(250, 150.0, None, 0.2, True),
            ProsodyPoint(500, None, None, 0.0, False),
            ProsodyPoint(750, 175.0, None, 0.3, True),
        ),
        pitch_min_hz=100.0,
        pitch_max_hz=200.0,
        source_filename="clip.mp3",
        analyzer_name="test-analyzer",
    )

    assert _pitch_paths(track) == [
        f"M {PLOT.left:.2f} {PLOT.height - PLOT.bottom:.2f} "
        f"L {_x_for_ms(250, 1000):.2f} {_y_for_pitch(150.0, 100.0, 200.0):.2f}"
    ]


def test_pitch_paths_break_on_unvoiced_points_and_resume_later_segments() -> None:
    track = ProsodyTrack(
        duration_ms=1000,
        points=(
            ProsodyPoint(0, 100.0, None, 0.1, True),
            ProsodyPoint(250, 150.0, None, 0.2, True),
            ProsodyPoint(500, 180.0, None, 0.0, False),
            ProsodyPoint(750, 175.0, None, 0.3, True),
            ProsodyPoint(1000, 200.0, None, 0.4, True),
        ),
        pitch_min_hz=100.0,
        pitch_max_hz=200.0,
        source_filename="clip.mp3",
        analyzer_name="test-analyzer",
    )

    assert _pitch_paths(track) == [
        f"M {PLOT.left:.2f} {PLOT.height - PLOT.bottom:.2f} "
        f"L {_x_for_ms(250, 1000):.2f} {_y_for_pitch(150.0, 100.0, 200.0):.2f}",
        f"M {_x_for_ms(750, 1000):.2f} {_y_for_pitch(175.0, 100.0, 200.0):.2f} "
        f"L {_x_for_ms(1000, 1000):.2f} {_y_for_pitch(200.0, 100.0, 200.0):.2f}",
    ]


def test_pitch_paths_split_when_unvoiced_point_still_has_pitch_value() -> None:
    track = ProsodyTrack(
        duration_ms=1000,
        points=(
            ProsodyPoint(0, 100.0, None, 0.1, True),
            ProsodyPoint(250, 150.0, None, 0.2, True),
            ProsodyPoint(500, 180.0, None, 0.0, False),
            ProsodyPoint(750, 175.0, None, 0.3, True),
            ProsodyPoint(1000, 200.0, None, 0.4, True),
        ),
        pitch_min_hz=100.0,
        pitch_max_hz=200.0,
        source_filename="clip.mp3",
        analyzer_name="test-analyzer",
    )

    assert len(_pitch_paths(track)) == 2


def test_append_pitch_path_requires_two_finite_points() -> None:
    paths: list[str] = []

    _append_pitch_path(paths, [(10.0, 20.0)])
    _append_pitch_path(paths, [(10.0, 20.0), (math.inf, 30.0)])
    _append_pitch_path(paths, [(10.0, 20.0), (15.0, 30.0)])

    assert paths == ["M 10.00 20.00", "M 10.00 20.00 L 15.00 30.00"]


def test_label_svg_uses_defaults_and_rounds_explicit_values() -> None:
    default_track = ProsodyTrack(
        duration_ms=0,
        points=(),
        pitch_min_hz=None,
        pitch_max_hz=None,
        source_filename="clip.mp3",
        analyzer_name="test-analyzer",
    )
    explicit_track = ProsodyTrack(
        duration_ms=0,
        points=(),
        pitch_min_hz=119.6,
        pitch_max_hz=260.4,
        source_filename="clip.mp3",
        analyzer_name="test-analyzer",
    )

    default_svg = _label_svg(default_track)
    explicit_svg = _label_svg(explicit_track)

    assert f'y="{PLOT.top + 10}"' in default_svg
    assert f'y="{PLOT.height - PLOT.bottom}"' in default_svg
    assert "500 Hz" in default_svg
    assert "75 Hz" in default_svg
    assert "260 Hz" in explicit_svg
    assert "120 Hz" in explicit_svg
    assert default_svg.count("\n") == 1


def test_axis_ticks_and_x_axis_svg_cover_zero_and_short_durations() -> None:
    assert _axis_ticks(0) == [0.0]
    assert _axis_ticks(1) == [0.0, 0.5, 1.0]

    axis_svg = _x_axis_svg(1)

    assert "0 ms" in axis_svg
    assert "1 ms" in axis_svg
    assert f'x="{PLOT.left + PLOT.plot_width:.2f}"' in axis_svg
    assert f'y1="{PLOT.height - PLOT.bottom}"' in axis_svg
    assert f'y2="{PLOT.height - PLOT.bottom + 4}"' in axis_svg
    assert f'y="{PLOT.height - 8}"' in axis_svg
    assert axis_svg.count("\n") == 5


def test_format_time_switches_at_two_seconds() -> None:
    assert _format_time(1500, 1500) == "1500 ms"
    assert _format_time(1546, 2000) == "1.55s"


def test_bounded_clamps_out_of_range_and_non_finite_values() -> None:
    assert _bounded(None) == 0.0
    assert _bounded(float("nan")) == 0.0
    assert _bounded(-0.5) == 0.0
    assert _bounded(1.5) == 1.0
