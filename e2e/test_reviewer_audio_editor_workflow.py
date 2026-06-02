"""E2E tests for Audio Quick Editor controls in Anki Reviewer."""

from __future__ import annotations

import time
from pathlib import Path

from PyQt6.QtWidgets import QMenu

from e2e.conftest import ADDON_NUMERIC_ID, import_runtime_addon_module
from e2e.editor_note_helpers import _button_selector, _configure_ffmpeg, _sound_filename
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js,
    wait_for_js_condition,
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


def _menu_action(menu: QMenu, label: str):
    for action in menu.actions():
        if action.text() == label:
            return action
    labels = [action.text() for action in menu.actions()]
    raise AssertionError(f"menu action {label!r} not found; saw {labels!r}")


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
    wait_for_js_condition(
        reviewer.web,
        f"document.querySelector({(_button_selector('aqe:play', field_ord))!r}) !== null",
        lambda value: value is True,
        timeout=5.0,
    )
    _cleanup_reviewer_session(reviewer)


def test_reviewer_audio_editor_answer_workflow(anki_mw, ffmpeg_config) -> None:
    hostile_css = """
    .card div {
      width: 100%;
      justify-content: space-between;
      border-color: transparent;
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

    style = wait_for_js_condition(
        reviewer.web,
        f"""
        (() => {{
          const controls = document.querySelector('.aqe-controls[data-aqe-field-ord="{field_ord}"]');
          const button = document.querySelector({(_button_selector('aqe:play', field_ord))!r});
          const splitMenu = document.querySelector('[data-testid="aqe-split-{field_ord}-play-menu"]');
          const icon = button?.querySelector('svg, .aqe-button-icon');
          if (!controls || !button || !splitMenu) return null;
          const controlsStyle = getComputedStyle(controls);
          const buttonStyle = getComputedStyle(button);
          const splitMenuStyle = getComputedStyle(splitMenu);
          const iconStyle = icon ? getComputedStyle(icon) : null;
          const host = controls.closest('.aqe-mount-host');
          const hostClone = host ? host.cloneNode(true) : null;
          let naturalControlsWidth = controls.getBoundingClientRect().width;
          if (hostClone instanceof HTMLElement) {{
            hostClone.style.left = '-10000px';
            hostClone.style.maxWidth = 'none';
            hostClone.style.position = 'absolute';
            hostClone.style.visibility = 'hidden';
            hostClone.style.width = 'auto';
            document.body.appendChild(hostClone);
            naturalControlsWidth = hostClone.querySelector('.aqe-controls').getBoundingClientRect().width;
            hostClone.remove();
          }}
          const toolbarItems = Array.from(controls.children)
            .filter((node) => !node.matches('.aqe-help, .aqe-visualizer, .aqe-status-row'));
          const maxRowGap = toolbarItems.reduce((maxGap, node, index) => {{
            const next = toolbarItems[index + 1];
            if (!next) return maxGap;
            const rect = node.getBoundingClientRect();
            const nextRect = next.getBoundingClientRect();
            if (Math.abs(nextRect.top - rect.top) > 4) return maxGap;
            return Math.max(maxGap, nextRect.left - rect.right);
          }}, 0);
          return {{
            controlsBorderColor: controlsStyle.borderTopColor,
            controlsJustifyContent: controlsStyle.justifyContent,
            controlsWidth: controls.getBoundingClientRect().width,
            maxRowGap,
            naturalControlsWidth,
            borderTopWidth: buttonStyle.borderTopWidth,
            marginLeft: buttonStyle.marginLeft,
            paddingLeft: buttonStyle.paddingLeft,
            splitMenuPaddingLeft: splitMenuStyle.paddingLeft,
            splitMenuWidth: splitMenu.getBoundingClientRect().width,
            textTransform: buttonStyle.textTransform,
            viewportWidth: document.documentElement.clientWidth,
            iconTransform: iconStyle ? iconStyle.transform : null,
          }};
        }})()
        """,
        lambda value: isinstance(value, dict),
        timeout=5.0,
    )

    assert style["borderTopWidth"] == "1px"
    assert style["controlsBorderColor"] not in {"rgba(0, 0, 0, 0)", "transparent"}
    assert style["controlsJustifyContent"] == "flex-start"
    assert style["controlsWidth"] <= style["naturalControlsWidth"] + 4
    assert style["maxRowGap"] <= 8
    assert style["marginLeft"] == "0px"
    assert style["paddingLeft"] != "24px"
    assert style["splitMenuPaddingLeft"] == "0px"
    assert style["splitMenuWidth"] <= 18
    assert style["textTransform"] != "uppercase"
    if style["iconTransform"] is not None:
        assert style["iconTransform"] in {"none", "matrix(1, 0, 0, 1, 0, 0)"}

    hide_action = _menu_action(_reviewer_more_menu(reviewer), "Hide audio editor")
    hide_action.trigger()
    _wait_for_no_controls(reviewer.web)

    show_action = _menu_action(_reviewer_more_menu(reviewer), "Show audio editor")
    show_action.trigger()
    _wait_for_controls(reviewer.web)

    tools_menu = _tools_audio_menu(anki_mw)
    tools_menu.aboutToShow.emit()
    _menu_action(tools_menu, "Hide audio editor").trigger()
    _wait_for_no_controls(reviewer.web)

    tools_menu.aboutToShow.emit()
    _menu_action(tools_menu, "Show audio editor").trigger()
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
    _show_answer(reviewer)
    _wait_for_no_controls(reviewer.web)
    action = _menu_action(_reviewer_more_menu(reviewer), "Show audio editor")
    assert action.isEnabled() is False
    _cleanup_reviewer_session(reviewer)
