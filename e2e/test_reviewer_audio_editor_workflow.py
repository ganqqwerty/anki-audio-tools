"""E2E tests for Audio Quick Editor controls in Anki Reviewer."""

from __future__ import annotations

import time
from pathlib import Path

from PyQt6.QtWidgets import QMenu

from e2e.conftest import ADDON_NUMERIC_ID, import_runtime_addon_module
from e2e.editor_graph_helpers import _click_graph_and_wait
from e2e.editor_note_helpers import _button_selector, _configure_ffmpeg, _sound_filename
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js,
    wait_for_js_condition,
)
from e2e.reviewer_css_isolation_helpers import (
    assert_reviewer_audio_controls_css_isolated,
    assert_reviewer_audio_controls_full_width,
    assert_reviewer_chorusing_marker_row_css_isolated,
    assert_reviewer_remove_pauses_popover_css_isolated,
    assert_reviewer_tooltip_css_isolated,
)


def _reviewer_module():
    return import_runtime_addon_module(".reviewer_integration")


def _unique_name(prefix: str) -> str:
    return f"{prefix} {time.time_ns()}"


def _set_reviewer_editor_visible(enabled: bool = True) -> None:
    _reviewer_module()._reviewer_editor_visible = enabled


def _reviewer_note(
    anki_mw,
    audio_filename: str,
    *,
    audio_field: str = "Back",
    card_css: str = "",
    answer_template: str | None = None,
):
    models = anki_mw.col.models
    notetype = models.new(_unique_name("AQE E2E Reviewer"))
    models.add_field(notetype, models.new_field("Front"))
    models.add_field(notetype, models.new_field("Back"))
    template = models.new_template("Card 1")
    template["qfmt"] = "{{Front}}"
    template["afmt"] = answer_template or "{{FrontSide}}<hr id=answer>{{Back}}"
    notetype["css"] = card_css
    models.add_template(notetype, template)
    models.add(notetype)
    note = anki_mw.col.new_note(notetype)
    if audio_field == "Front":
        note["Front"] = f"Prompt [sound:{audio_filename}]"
        note["Back"] = "Answer"
        field_ord = 0
    elif audio_field == "Back":
        note["Front"] = "Prompt"
        note["Back"] = f"Answer [sound:{audio_filename}]"
        field_ord = 1
    else:
        raise ValueError(f"unsupported audio field {audio_field!r}")
    deck_id = anki_mw.col.decks.id(_unique_name("AQE E2E Reviewer Deck"))
    assert deck_id is not None
    anki_mw.col.add_note(note, deck_id)
    return note, deck_id, field_ord


def _open_reviewer_for_note(anki_mw, note, deck_id: int):
    _set_reviewer_editor_visible(True)
    if anki_mw.state != "deckBrowser":
        anki_mw.moveToState("deckBrowser")
    anki_mw.col.decks.select(deck_id)
    anki_mw.moveToState("review")
    wait_for_condition(
        lambda: anki_mw.state == "review",
        timeout=10.0,
        message="Anki did not enter review state",
    )
    reviewer = anki_mw.reviewer
    card_ids = note.card_ids()
    assert card_ids
    reviewer.card = anki_mw.col.get_card(card_ids[0])
    reviewer.card.start_timer()
    reviewer._initWeb()
    try:
        wait_for_js_condition(
            reviewer.web,
            "document.querySelector('#qa') !== null",
            lambda value: value is True,
            timeout=10.0,
        )
    except TimeoutError as exc:
        body = wait_for_js(
            reviewer.web,
            "document.body ? document.body.outerHTML.slice(0, 2000) : ''",
            timeout=1.0,
        )
        raise TimeoutError(f"{exc}; initial reviewer body={body!r}") from exc
    reviewer._showQuestion()
    wait_for_condition(
        lambda: (
            anki_mw.state == "review"
            and reviewer.card is not None
            and reviewer.card.nid == note.id
        ),
        timeout=10.0,
        message="Reviewer did not open expected note within 10s",
    )
    wait_for_js_condition(
        reviewer.web,
        "document.body ? document.body.innerText.includes('Prompt') : false",
        lambda value: value is True,
        timeout=10.0,
    )
    return reviewer


def _show_answer(reviewer) -> None:
    reviewer._showAnswer()
    wait_for_condition(
        lambda: reviewer.state == "answer",
        timeout=5.0,
        message="Reviewer did not reveal the answer",
    )


def _wait_for_controls(web, count: int = 1) -> None:
    try:
        wait_for_js_condition(
            web,
            "document.querySelectorAll('.aqe-controls').length",
            lambda value: value == count,
            timeout=10.0,
        )
    except TimeoutError as exc:
        diagnostics = wait_for_js(
            web,
            """
            (() => ({
              controls: document.querySelectorAll('.aqe-controls').length,
              targets: document.querySelectorAll('.aqe-review-audio-target').length,
              body: document.body ? document.body.outerHTML.slice(0, 2000) : '',
            }))()
            """,
            timeout=1.0,
        )
        raise TimeoutError(f"{exc}; diagnostics={diagnostics!r}") from exc


def _wait_for_no_controls(web) -> None:
    wait_for_js_condition(
        web,
        "document.querySelectorAll('.aqe-controls').length",
        lambda value: value == 0,
        timeout=5.0,
    )


def _wait_for_template_target_controls(web, field_ord: int) -> None:
    wait_for_js_condition(
        web,
        (
            "document.querySelector("
            f"'.aqe-review-audio-target[data-field-ord=\"{field_ord}\"] "
            f".aqe-controls[data-aqe-field-ord=\"{field_ord}\"]'"
            ") !== null"
        ),
        lambda value: value is True,
        timeout=5.0,
    )


def _menu_action(menu: QMenu, label: str):
    for action in menu.actions():
        if action.text() == label:
            return action
    labels = [action.text() for action in menu.actions()]
    raise AssertionError(f"menu action {label!r} not found; saw {labels!r}")


def _trigger_action(action) -> None:
    action.triggered.emit()


def _reviewer_more_menu(reviewer) -> QMenu:
    from aqt import gui_hooks

    menu = QMenu(reviewer.mw)
    reviewer._addMenuItems(menu, reviewer._contextMenu())
    gui_hooks.reviewer_will_show_context_menu(reviewer, menu)
    return menu


def _cleanup_reviewer_session(reviewer) -> None:
    from aqt import gui_hooks

    if getattr(reviewer, "card", None) is not None:
        gui_hooks.reviewer_did_answer_card(reviewer, reviewer.card, 3)
    reviewer.mw.moveToState("deckBrowser")


def _tools_audio_menu(anki_mw) -> QMenu:
    for action in anki_mw.form.menuTools.actions():
        if action.text() == "Anki Audio Quick Editor" and action.menu() is not None:
            return action.menu()
    labels = [action.text() for action in anki_mw.form.menuTools.actions()]
    raise AssertionError(f"Anki Audio Quick Editor Tools menu not found; saw {labels!r}")


def _prepare_reviewer_note(
    anki_mw,
    ffmpeg_config,
    filename: str,
    *,
    audio_field: str = "Back",
    card_css: str = "",
    answer_template: str | None = None,
):
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / filename
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note, deck_id, field_ord = _reviewer_note(
        anki_mw,
        source.name,
        audio_field=audio_field,
        card_css=card_css,
        answer_template=answer_template,
    )
    _configure_ffmpeg(anki_mw, ffmpeg_config, enable_reviewer_editor=True)
    return media_dir, source, note, deck_id, field_ord


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
    config["enable_reviewer_editor"] = False
    anki_mw.addonManager.writeConfig(ADDON_NUMERIC_ID, config)
    reviewer_module = _reviewer_module()
    reviewer_module._on_reviewer_did_show_card_side(reviewer.card)
    _wait_for_no_controls(reviewer.web)
    action = _menu_action(_reviewer_more_menu(reviewer), "Show audio editor")
    assert action.isEnabled() is True
    _trigger_action(action)
    _wait_for_controls(reviewer.web)
    _cleanup_reviewer_session(reviewer)
