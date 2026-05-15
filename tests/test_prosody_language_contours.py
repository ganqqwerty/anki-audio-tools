"""Praat-generated language contour tests for learner-facing pitch graphs."""

from __future__ import annotations

from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.prosody_praat import analyze_with_praat

from .prosody_language_fixtures import (
    LANGUAGE_CONTOUR_SPECS,
    ContourSpec,
    ContourWindow,
    expected_hz,
    generate_praat_vowel_fixture,
    median,
    median_intensity,
    median_pitch,
    points_in_window,
    require_praat_and_ffmpeg,
    window_named,
)
from .prosody_visualizer_harness import render_pitch_points

pytestmark = pytest.mark.praat

PITCH_TOLERANCE_HZ = 32
MIN_VISIBLE_CONTOUR_PX = 16


@pytest.mark.parametrize("spec_name", sorted(LANGUAGE_CONTOUR_SPECS))
def test_praat_language_fixture_analyzer_tracks_expected_windows(
    tmp_path: Path,
    spec_name: str,
) -> None:
    spec, track = _analyze_spec(tmp_path, spec_name)

    for window in spec.windows:
        voiced = _voiced_points(track.points, window)
        assert voiced, f"{spec.name}:{window.name} produced no voiced pitch"
        observed_hz = median_pitch(voiced)
        target_hz = window.expected_hz or expected_hz(spec, (window.start_ms + window.end_ms) / 2)
        assert abs(observed_hz - target_hz) <= PITCH_TOLERANCE_HZ
        assert 0.75 <= observed_hz / target_hz <= 1.35

    for gap in spec.gaps:
        inner = ContourWindow("gap", gap.start_ms + 40, gap.end_ms - 40)
        if inner.start_ms < inner.end_ms:
            assert not _voiced_points(track.points, inner), f"{spec.name} bridged voiceless gap"


def test_praat_japanese_pitch_accent_contours_expose_expected_drops(tmp_path: Path) -> None:
    heiban, heiban_track = _analyze_spec(tmp_path, "ja_heiban_4mora_particle_1_6s")
    assert _hz(heiban_track, heiban, "mid_high") - _hz(heiban_track, heiban, "early_low") >= 35
    assert abs(_hz(heiban_track, heiban, "mid_high") - _hz(heiban_track, heiban, "particle_high")) <= 30

    atamadaka, atamadaka_track = _analyze_spec(tmp_path, "ja_atamadaka_3mora_particle_1_4s")
    assert _hz(atamadaka_track, atamadaka, "initial_high") - _hz(atamadaka_track, atamadaka, "post_drop_low") >= 55
    assert _hz(atamadaka_track, atamadaka, "initial_high") - _hz(atamadaka_track, atamadaka, "particle_low") >= 55

    nakadaka, nakadaka_track = _analyze_spec(tmp_path, "ja_nakadaka_4mora_1_5s")
    assert _hz(nakadaka_track, nakadaka, "pre_drop_high") - _hz(nakadaka_track, nakadaka, "post_drop_low") >= 60

    odaka, odaka_track = _analyze_spec(tmp_path, "ja_odaka_3mora_particle_1_6s")
    assert _hz(odaka_track, odaka, "word_high") - _hz(odaka_track, odaka, "particle_low") >= 60
    assert _hz(odaka_track, odaka, "word_high") - _hz(odaka_track, odaka, "early_low") >= 35


def test_praat_mandarin_tone_contours_expose_expected_shapes(tmp_path: Path) -> None:
    tone1, tone1_track = _analyze_spec(tmp_path, "zh_tone1_high_level_0_9s")
    tone1_hz = [_hz(tone1_track, tone1, name) for name in ("early", "mid", "late")]
    assert max(tone1_hz) - min(tone1_hz) <= 30

    tone2, tone2_track = _analyze_spec(tmp_path, "zh_tone2_rising_0_9s")
    assert _hz(tone2_track, tone2, "late") - _hz(tone2_track, tone2, "early") >= 55

    tone3, tone3_track = _analyze_spec(tmp_path, "zh_tone3_dipping_1_1s")
    assert _hz(tone3_track, tone3, "early") - _hz(tone3_track, tone3, "trough") >= 40
    assert _hz(tone3_track, tone3, "late") - _hz(tone3_track, tone3, "trough") >= 45

    tone4, tone4_track = _analyze_spec(tmp_path, "zh_tone4_falling_0_8s")
    assert _hz(tone4_track, tone4, "early") - _hz(tone4_track, tone4, "late") >= 80

    neutral, neutral_track = _analyze_spec(tmp_path, "zh_neutral_after_tone4_1_2s")
    assert _hz(neutral_track, neutral, "tone4_early") - _hz(neutral_track, neutral, "tone4_late") >= 70
    assert _intensity(neutral_track, neutral, "neutral") < _intensity(neutral_track, neutral, "tone4_early")


@pytest.mark.parametrize("spec_name", ["zh_1_4", "zh_2_3", "zh_3_3", "zh_4_1"])
def test_praat_mandarin_tone_pairs_keep_syllable_shapes(
    tmp_path: Path,
    spec_name: str,
) -> None:
    spec, track = _analyze_spec(tmp_path, spec_name)

    if spec_name == "zh_1_4":
        assert _hz(track, spec, "first") - _hz(track, spec, "second_late") >= 70
    elif spec_name == "zh_2_3":
        assert _hz(track, spec, "first_late") - _hz(track, spec, "first_early") >= 35
        assert _hz(track, spec, "second_late") - _hz(track, spec, "second_trough") >= 45
    elif spec_name == "zh_3_3":
        assert _hz(track, spec, "first_late") - _hz(track, spec, "first_early") >= 30
        assert _hz(track, spec, "second_late") - _hz(track, spec, "second_trough") >= 45
    else:
        assert _hz(track, spec, "first_early") - _hz(track, spec, "first_late") >= 70
        assert abs(_hz(track, spec, "second") - _hz(track, spec, "first_early")) <= 35


def test_praat_vietnamese_tone_contours_expose_expected_shapes(tmp_path: Path) -> None:
    ngang, ngang_track = _analyze_spec(tmp_path, "vi_ngang_mid_level_0_9s")
    ngang_hz = [_hz(ngang_track, ngang, name) for name in ("early", "mid", "late")]
    assert max(ngang_hz) - min(ngang_hz) <= 30

    sac, sac_track = _analyze_spec(tmp_path, "vi_sac_high_rising_0_9s")
    assert _hz(sac_track, sac, "late") - _hz(sac_track, sac, "early") >= 45

    huyen, huyen_track = _analyze_spec(tmp_path, "vi_huyen_low_falling_0_9s")
    assert _hz(huyen_track, huyen, "early") - _hz(huyen_track, huyen, "late") >= 35

    hoi, hoi_track = _analyze_spec(tmp_path, "vi_hoi_dipping_1_0s")
    assert _hz(hoi_track, hoi, "early") - _hz(hoi_track, hoi, "trough") >= 35
    assert _hz(hoi_track, hoi, "late") - _hz(hoi_track, hoi, "trough") >= 35

    nga, nga_track = _analyze_spec(tmp_path, "vi_nga_broken_rising_1_0s")
    assert _hz(nga_track, nga, "late") - _hz(nga_track, nga, "pre_break") >= 60

    nang, nang_track = _analyze_spec(tmp_path, "vi_nang_low_checked_0_8s")
    assert _hz(nang_track, nang, "early") - _hz(nang_track, nang, "late_low") >= 40
    assert _intensity(nang_track, nang, "late_low") < _intensity(nang_track, nang, "early")


@pytest.mark.parametrize(
    ("spec_name", "high_window", "low_window"),
    [
        ("ja_nakadaka_4mora_1_5s", "pre_drop_high", "post_drop_low"),
        ("ja_odaka_3mora_particle_1_6s", "word_high", "particle_low"),
        ("zh_tone4_falling_0_8s", "early", "late"),
        ("vi_huyen_low_falling_0_9s", "early", "late"),
        ("vi_nang_low_checked_0_8s", "early", "late_low"),
    ],
)
def test_visualizer_renders_expected_drops_as_visible_pixel_changes(
    tmp_path: Path,
    spec_name: str,
    high_window: str,
    low_window: str,
) -> None:
    spec, track = _analyze_spec(tmp_path, spec_name)
    rendered = render_pitch_points(track.to_payload())

    assert rendered["paths"]
    assert all("NaN" not in path and "Infinity" not in path for path in rendered["paths"])
    high_y = _rendered_y(rendered["rendered"], window_named(spec, high_window))
    low_y = _rendered_y(rendered["rendered"], window_named(spec, low_window))
    assert low_y - high_y >= MIN_VISIBLE_CONTOUR_PX


@pytest.mark.parametrize(
    ("spec_name", "early_window", "late_window"),
    [
        ("zh_tone2_rising_0_9s", "early", "late"),
        ("vi_sac_high_rising_0_9s", "early", "late"),
        ("vi_nga_broken_rising_1_0s", "pre_break", "late"),
    ],
)
def test_visualizer_renders_expected_rises_as_visible_pixel_changes(
    tmp_path: Path,
    spec_name: str,
    early_window: str,
    late_window: str,
) -> None:
    spec, track = _analyze_spec(tmp_path, spec_name)
    rendered = render_pitch_points(track.to_payload())

    early_y = _rendered_y(rendered["rendered"], window_named(spec, early_window))
    late_y = _rendered_y(rendered["rendered"], window_named(spec, late_window))
    assert early_y - late_y >= MIN_VISIBLE_CONTOUR_PX


def test_visualizer_renders_tone3_as_visible_dip(tmp_path: Path) -> None:
    spec, track = _analyze_spec(tmp_path, "zh_tone3_dipping_1_1s")
    rendered = render_pitch_points(track.to_payload())

    early_y = _rendered_y(rendered["rendered"], window_named(spec, "early"))
    trough_y = _rendered_y(rendered["rendered"], window_named(spec, "trough"))
    late_y = _rendered_y(rendered["rendered"], window_named(spec, "late"))
    assert trough_y - early_y >= MIN_VISIBLE_CONTOUR_PX
    assert trough_y - late_y >= MIN_VISIBLE_CONTOUR_PX


@pytest.mark.parametrize("spec_name", ["vi_hoi_dipping_1_0s"])
def test_visualizer_renders_vietnamese_dipping_tones_as_visible_dips(
    tmp_path: Path,
    spec_name: str,
) -> None:
    spec, track = _analyze_spec(tmp_path, spec_name)
    rendered = render_pitch_points(track.to_payload())

    early_y = _rendered_y(rendered["rendered"], window_named(spec, "early"))
    trough_y = _rendered_y(rendered["rendered"], window_named(spec, "trough"))
    late_y = _rendered_y(rendered["rendered"], window_named(spec, "late"))
    assert trough_y - early_y >= MIN_VISIBLE_CONTOUR_PX
    assert trough_y - late_y >= MIN_VISIBLE_CONTOUR_PX


def test_visualizer_renders_vietnamese_broken_rise_as_separate_paths(tmp_path: Path) -> None:
    spec, track = _analyze_spec(tmp_path, "vi_nga_broken_rising_1_0s")
    rendered = render_pitch_points(track.to_payload())

    pre_break_y = _rendered_y(rendered["rendered"], window_named(spec, "pre_break"))
    late_y = _rendered_y(rendered["rendered"], window_named(spec, "late"))
    assert len(rendered["paths"]) >= 2
    assert pre_break_y - late_y >= MIN_VISIBLE_CONTOUR_PX


def _analyze_spec(tmp_path: Path, spec_name: str):
    require_praat_and_ffmpeg()
    spec = LANGUAGE_CONTOUR_SPECS[spec_name]
    source = generate_praat_vowel_fixture(tmp_path / f"{spec.name}.wav", spec)
    return spec, analyze_with_praat(source, AudioProcessingConfig())


def _voiced_points(points, window: ContourWindow):
    return [point for point in points_in_window(points, window) if point.pitch_hz is not None]


def _hz(track, spec: ContourSpec, window_name: str) -> float:
    return median_pitch(_voiced_points(track.points, window_named(spec, window_name)))


def _intensity(track, spec: ContourSpec, window_name: str) -> float:
    return median_intensity(points_in_window(track.points, window_named(spec, window_name)))


def _rendered_y(rendered_points: list[dict], window: ContourWindow) -> float:
    values = [
        point["y"]
        for point in rendered_points
        if window.start_ms <= point["timeMs"] <= window.end_ms
    ]
    return median(values)
