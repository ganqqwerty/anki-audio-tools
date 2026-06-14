"""Reviewer audio workflow behavior tests for playback and editor actions."""

from __future__ import annotations

from e2e.conftest import ADDON_NUMERIC_ID
from e2e.editor_graph_helpers import _click_graph_and_wait
from e2e.editor_note_helpers import _button_selector, _sound_filename
from e2e.helpers import click_selector, wait_for_condition, wait_for_js_condition
from e2e.reviewer_css_isolation_helpers import (
    assert_reviewer_audio_controls_css_isolated,
    assert_reviewer_audio_controls_full_width,
    assert_reviewer_chorusing_marker_row_css_isolated,
    assert_reviewer_remove_pauses_popover_css_isolated,
    assert_reviewer_tooltip_css_isolated,
)
from e2e.test_reviewer_audio_editor_workflow import (
    _cleanup_reviewer_session,
    _menu_action,
    _open_reviewer_for_note,
    _prepare_reviewer_note,
    _reviewer_more_menu,
    _show_answer,
    _tools_audio_menu,
    _trigger_action,
    _wait_for_controls,
    _wait_for_no_controls,
)


def test_reviewer_audio_editor_answer_workflow(anki_mw, ffmpeg_config) -> None:
    hostile_css = """
    .card div {
      width: 100%;
      justify-content: space-between;
      border-color: transparent;
      padding: 16px;
    }
    .card button {
      margin: 20px;
      padding: 24px;
      border-width: 8px;
      text-transform: uppercase;
    }
    .card .aqe-split-menu-button {
      min-width: 36px;
      padding-left: 10px;
      padding-right: 10px;
    }
    .card svg {
      transform: scale(2);
    }
    .card details {
      display: inline;
      width: auto;
    }
    .card span,
    .card strong,
    .card h4,
    .card li,
    .card p,
    .card a,
    .card summary {
      font-family: Georgia, serif;
      font-size: 24px;
      line-height: 2;
      margin: 12px;
      padding: 12px;
      text-transform: uppercase;
    }
    """
    _media_dir, _source, note, deck_id, field_ord = _prepare_reviewer_note(
        anki_mw,
        ffmpeg_config,
        "reviewer_workflow_source.wav",
        card_css=hostile_css,
    )
    reviewer = _open_reviewer_for_note(anki_mw, note, deck_id)
    _wait_for_no_controls(reviewer.web)

    _show_answer(reviewer)
    _wait_for_controls(reviewer.web)
    wait_for_js_condition(
        reviewer.web,
        f"document.querySelector({(_button_selector('aqe:play', field_ord))!r}) !== null",
        lambda value: value is True,
        timeout=5.0,
    )
    assert_reviewer_audio_controls_full_width(reviewer, field_ord)
    _click_graph_and_wait(reviewer, ord_=field_ord, timeout=10.0)
    assert_reviewer_audio_controls_css_isolated(reviewer, field_ord)
    assert_reviewer_remove_pauses_popover_css_isolated(reviewer, field_ord)
    assert_reviewer_tooltip_css_isolated(reviewer)
    assert_reviewer_chorusing_marker_row_css_isolated(reviewer, field_ord)

    hide_action = _menu_action(_reviewer_more_menu(reviewer), "Hide audio editor")
    _trigger_action(hide_action)
    _wait_for_no_controls(reviewer.web)

    show_action = _menu_action(_reviewer_more_menu(reviewer), "Show audio editor")
    _trigger_action(show_action)
    _wait_for_controls(reviewer.web)

    tools_menu = _tools_audio_menu(anki_mw)
    tools_menu.aboutToShow.emit()
    _trigger_action(_menu_action(tools_menu, "Hide audio editor"))
    _wait_for_no_controls(reviewer.web)

    tools_menu.aboutToShow.emit()
    _trigger_action(_menu_action(tools_menu, "Show audio editor"))
    _wait_for_controls(reviewer.web)

    original_card_id = reviewer.card.id
    click_selector(reviewer.web, _button_selector("aqe:faster", field_ord), timeout=5.0)
    wait_for_condition(
        lambda: (
            (filename := _sound_filename(anki_mw.col.get_note(note.id).fields[field_ord])) != _source.name
            and "__aqe_" in filename
            and (_media_dir / filename).is_file()
        ),
        timeout=10.0,
        message="Reviewer processing did not replace note audio",
    )
    assert reviewer.card.id == original_card_id
    assert reviewer.state == "answer"

    config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
    original_editor_setting = bool(config.get("enable_reviewer_editor", True))
    hide_action = _menu_action(_reviewer_more_menu(reviewer), "Hide audio editor")
    _trigger_action(hide_action)
    _wait_for_no_controls(reviewer.web)
    try:
        config["enable_reviewer_editor"] = False
        anki_mw.addonManager.writeConfig(ADDON_NUMERIC_ID, config)
        action = _menu_action(_reviewer_more_menu(reviewer), "Show audio editor")
        assert action.isEnabled() is True
        _trigger_action(action)
        _wait_for_controls(reviewer.web)
    finally:
        config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
        config["enable_reviewer_editor"] = original_editor_setting
        anki_mw.addonManager.writeConfig(ADDON_NUMERIC_ID, config)
        _cleanup_reviewer_session(reviewer)
