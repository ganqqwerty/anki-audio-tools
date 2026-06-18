"""Shared E2E helpers for Audio Quick Editor controls in the Anki reviewer."""

from __future__ import annotations

import time
from pathlib import Path

from PyQt6.QtWidgets import QMenu

from e2e.conftest import import_runtime_addon_module
from e2e.editor_note_helpers import _configure_ffmpeg
from e2e.helpers import (
    generate_tone,
    run_js,
    wait_for_condition,
    wait_for_js,
    wait_for_js_condition,
)


def _reviewer_module():
    return import_runtime_addon_module(".reviewer_integration")


def _unique_name(prefix: str) -> str:
    return f"{prefix} {time.time_ns()}"


def _set_reviewer_editor_visible(reviewer, enabled: bool = True) -> None:
    if enabled:
        reviewer_module = _reviewer_module()
        if reviewer_module.reviewer_editor_menu_label(reviewer) == "Hide audio editor":
            return
        _trigger_action(_menu_action(_reviewer_more_menu(reviewer), "Show audio editor"))


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
    wait_for_condition(
        lambda: (
            anki_mw.state == "review"
            and reviewer.card is not None
            and reviewer.card.nid == note.id
        ),
        timeout=15.0,
        message="Reviewer did not open expected note within 15s",
    )
    _wait_for_reviewer_question_dom(reviewer)
    wait_for_js_condition(
        reviewer.web,
        "document.body ? document.body.innerText.includes('Prompt') : false",
        lambda value: value is True,
        timeout=10.0,
    )
    _set_reviewer_editor_visible(reviewer)
    return reviewer


def _wait_for_reviewer_question_dom(reviewer) -> None:
    try:
        wait_for_js_condition(
            reviewer.web,
            "document.querySelector('#qa') !== null",
            lambda value: value is True,
            timeout=30.0,
        )
    except TimeoutError as exc:
        body = wait_for_js(
            reviewer.web,
            "document.body ? document.body.outerHTML.slice(0, 4000) : ''",
            timeout=1.0,
        )
        raise TimeoutError(f"{exc}; initial reviewer body={body!r}") from exc


def _show_answer(reviewer) -> None:
    run_js(reviewer.web, "pycmd('ans')")
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
    if getattr(reviewer, "state", "") == "answer":
        run_js(reviewer.web, "pycmd('ease3')")
        wait_for_condition(
            lambda: reviewer.mw.state in {"review", "deckBrowser"},
            timeout=5.0,
            message="Reviewer did not accept the answer during cleanup",
        )
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
