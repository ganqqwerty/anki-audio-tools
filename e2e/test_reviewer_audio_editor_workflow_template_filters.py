"""Template-filter behavior tests for reviewer audio control visibility."""

from __future__ import annotations

from e2e.conftest import ADDON_NUMERIC_ID
from e2e.editor_note_helpers import _button_selector
from e2e.helpers import click_selector, wait_for_js_condition
from e2e.test_reviewer_audio_editor_workflow import (
    _cleanup_reviewer_session,
    _open_reviewer_for_note,
    _prepare_reviewer_note,
    _show_answer,
    _wait_for_controls,
    _wait_for_no_controls,
    _wait_for_template_target_controls,
)


def test_reviewer_audio_panel_template_filter_opens_controls(anki_mw, ffmpeg_config) -> None:
    _media_dir, _source, note, deck_id, field_ord = _prepare_reviewer_note(
        anki_mw,
        ffmpeg_config,
        "reviewer_template_filter_source.wav",
        answer_template="{{FrontSide}}<hr id=answer>{{aqe-audio-panel:Back}}",
    )
    reviewer = _open_reviewer_for_note(anki_mw, note, deck_id)
    _wait_for_no_controls(reviewer.web)

    _show_answer(reviewer)
    _wait_for_no_controls(reviewer.web)
    wait_for_js_condition(
        reviewer.web,
        f"document.querySelector('[data-testid=\"aqe-review-audio-panel-trigger-{field_ord}\"]') !== null",
        lambda value: value is True,
        timeout=5.0,
    )

    click_selector(
        reviewer.web,
        f'[data-testid="aqe-review-audio-panel-trigger-{field_ord}"]',
        timeout=5.0,
    )
    _wait_for_controls(reviewer.web)
    _wait_for_template_target_controls(reviewer.web, field_ord)
    wait_for_js_condition(
        reviewer.web,
        f"document.querySelector({(_button_selector('aqe:play', field_ord))!r}) !== null",
        lambda value: value is True,
        timeout=5.0,
    )
    _cleanup_reviewer_session(reviewer)


def test_reviewer_audio_panel_template_filter_opens_front_field_controls(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, note, deck_id, field_ord = _prepare_reviewer_note(
        anki_mw,
        ffmpeg_config,
        "reviewer_template_filter_front_source.wav",
        audio_field="Front",
        answer_template="{{FrontSide}}<hr id=answer>{{aqe-audio-panel:Front}}{{Back}}",
    )
    reviewer = _open_reviewer_for_note(anki_mw, note, deck_id)
    _wait_for_no_controls(reviewer.web)

    _show_answer(reviewer)
    _wait_for_no_controls(reviewer.web)
    wait_for_js_condition(
        reviewer.web,
        f"document.querySelector('[data-testid=\"aqe-review-audio-panel-trigger-{field_ord}\"]') !== null",
        lambda value: value is True,
        timeout=5.0,
    )

    click_selector(
        reviewer.web,
        f'[data-testid="aqe-review-audio-panel-trigger-{field_ord}"]',
        timeout=5.0,
    )
    _wait_for_controls(reviewer.web)
    _wait_for_template_target_controls(reviewer.web, field_ord)
    wait_for_js_condition(
        reviewer.web,
        f"document.querySelector({(_button_selector('aqe:play', field_ord))!r}) !== null",
        lambda value: value is True,
        timeout=5.0,
    )
    _cleanup_reviewer_session(reviewer)


def test_reviewer_audio_panel_template_filter_ignores_disabled_setting(
    anki_mw,
    ffmpeg_config,
) -> None:
    _media_dir, _source, note, deck_id, field_ord = _prepare_reviewer_note(
        anki_mw,
        ffmpeg_config,
        "reviewer_template_filter_disabled_source.wav",
        answer_template="{{FrontSide}}<hr id=answer>{{aqe-audio-panel:Back}}{{Back}}",
    )
    config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
    config["enable_reviewer_editor"] = False
    anki_mw.addonManager.writeConfig(ADDON_NUMERIC_ID, config)
    reviewer = _open_reviewer_for_note(anki_mw, note, deck_id)
    try:
        _show_answer(reviewer)
        _wait_for_no_controls(reviewer.web)
        wait_for_js_condition(
            reviewer.web,
            f"document.querySelector('[data-testid=\"aqe-review-audio-panel-trigger-{field_ord}\"]') !== null",
            lambda value: value is True,
            timeout=5.0,
        )
        click_selector(
            reviewer.web,
            f'[data-testid="aqe-review-audio-panel-trigger-{field_ord}"]',
            timeout=5.0,
        )
        _wait_for_controls(reviewer.web)
        _wait_for_template_target_controls(reviewer.web, field_ord)
    finally:
        config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
        config["enable_reviewer_editor"] = True
        anki_mw.addonManager.writeConfig(ADDON_NUMERIC_ID, config)
        _cleanup_reviewer_session(reviewer)

