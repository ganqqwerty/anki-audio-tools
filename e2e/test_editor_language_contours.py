"""E2E tests for language-specific pitch contour rendering."""

from __future__ import annotations

import pytest
from tests.prosody_language_fixtures import window_named

from e2e.editor_language_helpers import (
    _language_contour_editor,
    _median_rendered_y,
    _rendered_language_contour,
)


def test_visualizer_shows_japanese_nakadaka_internal_pitch_drop(
    anki_mw,
    ffmpeg_config,
) -> None:
    with _language_contour_editor(anki_mw, ffmpeg_config, "ja_nakadaka_4mora_1_5s") as (
        editor,
        _parent,
        source,
        spec,
    ):
        rendered = _rendered_language_contour(editor, source.name)

        pre_drop_y = _median_rendered_y(rendered, window_named(spec, "pre_drop_high"))
        post_drop_y = _median_rendered_y(rendered, window_named(spec, "post_drop_low"))
        assert post_drop_y - pre_drop_y >= 16


@pytest.mark.praat
def test_visualizer_shows_japanese_odaka_drop_on_particle(
    anki_mw,
    ffmpeg_config,
) -> None:
    with _language_contour_editor(anki_mw, ffmpeg_config, "ja_odaka_3mora_particle_1_6s") as (
        editor,
        _parent,
        source,
        spec,
    ):
        rendered = _rendered_language_contour(editor, source.name)

        word_y = _median_rendered_y(rendered, window_named(spec, "word_high"))
        particle_y = _median_rendered_y(rendered, window_named(spec, "particle_low"))
        assert particle_y - word_y >= 16


@pytest.mark.praat
@pytest.mark.parametrize(
    ("spec_name", "earlier_window", "later_window", "direction"),
    [
        ("zh_tone2_rising_0_9s", "early", "late", "rise"),
        ("zh_tone4_falling_0_8s", "early", "late", "fall"),
    ],
)
def test_visualizer_shows_mandarin_tone2_and_tone4_opposite_slopes(
    anki_mw,
    ffmpeg_config,
    spec_name: str,
    earlier_window: str,
    later_window: str,
    direction: str,
) -> None:
    with _language_contour_editor(anki_mw, ffmpeg_config, spec_name) as (
        editor,
        _parent,
        source,
        spec,
    ):
        rendered = _rendered_language_contour(editor, source.name)

        earlier_y = _median_rendered_y(rendered, window_named(spec, earlier_window))
        later_y = _median_rendered_y(rendered, window_named(spec, later_window))
        if direction == "rise":
            assert earlier_y - later_y >= 16
        else:
            assert later_y - earlier_y >= 16


@pytest.mark.praat
def test_visualizer_shows_mandarin_tone3_dip(
    anki_mw,
    ffmpeg_config,
) -> None:
    with _language_contour_editor(anki_mw, ffmpeg_config, "zh_tone3_dipping_1_1s") as (
        editor,
        _parent,
        source,
        spec,
    ):
        rendered = _rendered_language_contour(editor, source.name)

        early_y = _median_rendered_y(rendered, window_named(spec, "early"))
        trough_y = _median_rendered_y(rendered, window_named(spec, "trough"))
        late_y = _median_rendered_y(rendered, window_named(spec, "late"))
        assert trough_y - early_y >= 16
        assert trough_y - late_y >= 16


@pytest.mark.praat
@pytest.mark.parametrize(
    ("spec_name", "earlier_window", "later_window", "direction"),
    [
        ("vi_sac_high_rising_0_9s", "early", "late", "rise"),
        ("vi_huyen_low_falling_0_9s", "early", "late", "fall"),
        ("vi_nang_low_checked_0_8s", "early", "late_low", "fall"),
    ],
)
def test_visualizer_shows_vietnamese_rising_and_falling_tones(
    anki_mw,
    ffmpeg_config,
    spec_name: str,
    earlier_window: str,
    later_window: str,
    direction: str,
) -> None:
    with _language_contour_editor(anki_mw, ffmpeg_config, spec_name) as (
        editor,
        _parent,
        source,
        spec,
    ):
        rendered = _rendered_language_contour(editor, source.name)

        earlier_y = _median_rendered_y(rendered, window_named(spec, earlier_window))
        later_y = _median_rendered_y(rendered, window_named(spec, later_window))
        if direction == "rise":
            assert earlier_y - later_y >= 16
        else:
            assert later_y - earlier_y >= 16


@pytest.mark.praat
def test_visualizer_shows_vietnamese_hoi_dip(
    anki_mw,
    ffmpeg_config,
) -> None:
    with _language_contour_editor(anki_mw, ffmpeg_config, "vi_hoi_dipping_1_0s") as (
        editor,
        _parent,
        source,
        spec,
    ):
        rendered = _rendered_language_contour(editor, source.name)

        early_y = _median_rendered_y(rendered, window_named(spec, "early"))
        trough_y = _median_rendered_y(rendered, window_named(spec, "trough"))
        late_y = _median_rendered_y(rendered, window_named(spec, "late"))
        assert trough_y - early_y >= 16
        assert trough_y - late_y >= 16


@pytest.mark.praat
def test_visualizer_shows_vietnamese_nga_broken_rise(
    anki_mw,
    ffmpeg_config,
) -> None:
    with _language_contour_editor(anki_mw, ffmpeg_config, "vi_nga_broken_rising_1_0s") as (
        editor,
        _parent,
        source,
        spec,
    ):
        rendered = _rendered_language_contour(editor, source.name)

        pre_break_y = _median_rendered_y(rendered, window_named(spec, "pre_break"))
        late_y = _median_rendered_y(rendered, window_named(spec, "late"))
        assert rendered["paths"] >= 2
        assert pre_break_y - late_y >= 16
