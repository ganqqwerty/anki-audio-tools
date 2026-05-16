"""Tests for SVG visualization media rendering."""

from __future__ import annotations

from datetime import datetime

from anki_audio_quick_editor.prosody_svg import (
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
    assert "260 Hz" in svg
    assert "120 Hz" in svg
    assert "test-analyzer" in svg
    assert "NaN" not in svg
    assert "Infinity" not in svg
