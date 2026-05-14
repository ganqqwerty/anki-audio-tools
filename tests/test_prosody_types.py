"""Tests for import-safe prosody data structures."""

from __future__ import annotations

import json

from anki_audio_quick_editor.prosody_types import (
    ProsodyPoint,
    build_prosody_track,
    clamp_cursor_ms,
    normalize_intensity,
)


def test_intensity_normalization_is_bounded_and_stable() -> None:
    points = [
        ProsodyPoint(0, None, -80, 0.0, False),
        ProsodyPoint(10, 220, -40, 0.0, True),
        ProsodyPoint(20, 230, -20, 0.0, True),
    ]

    normalized = normalize_intensity(points)

    assert all(0.0 <= point.intensity_norm <= 1.0 for point in normalized)
    assert normalized[0].intensity_norm < normalized[-1].intensity_norm


def test_cursor_clamping_keeps_values_in_duration_range() -> None:
    assert clamp_cursor_ms(-5, 1000) == 0
    assert clamp_cursor_ms(500, 1000) == 500
    assert clamp_cursor_ms(1500, 1000) == 1000
    assert clamp_cursor_ms("bad", 1000) == 0


def test_track_payload_is_compact_and_json_serializable() -> None:
    track = build_prosody_track(
        duration_ms=100,
        points=[
            ProsodyPoint(0, None, -80, 0.0, False),
            ProsodyPoint(10, 220.1234, -20, 0.0, True),
        ],
        source_filename="clip.wav",
        analyzer_name="unit",
    )

    payload = track.to_payload()

    assert payload["durationMs"] == 100
    assert payload["pitchMinHz"] == 220.12
    assert payload["points"][0] == [0, None, 0.0, False]
    assert json.loads(json.dumps(payload)) == payload
