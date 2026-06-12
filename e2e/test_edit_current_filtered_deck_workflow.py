"""Edit-current audio editor coverage for cards reviewed from filtered decks."""

from __future__ import annotations

import json
import time
from pathlib import Path

import aqt
import pytest

from e2e.editor_note_helpers import _button_selector, _configure_ffmpeg
from e2e.helpers import (
    generate_tone,
    wait_for_condition,
    wait_for_js,
    wait_for_js_condition,
)
from e2e.test_reviewer_audio_editor_workflow import _reviewer_note, _show_answer


def _unique_name(prefix: str) -> str:
    return f"{prefix} {time.time_ns()}"


def _create_filtered_deck_for_note(anki_mw, note, *, reschedule: bool) -> int:
    deck = anki_mw.col.sched.get_or_create_filtered_deck(0)
    deck.name = _unique_name("AQE E2E Filtered Reviewer Deck")
    deck.config.reschedule = reschedule
    del deck.config.search_terms[:]
    deck.config.search_terms.add(search=f"nid:{note.id}", limit=1, order=5)
    out = anki_mw.col.sched.add_or_update_filtered_deck(deck)
    return int(out.id)


def _open_filtered_reviewer_for_note(anki_mw, note, deck_id: int):
    if anki_mw.state != "deckBrowser":
        anki_mw.moveToState("deckBrowser")
    anki_mw.col.decks.select(deck_id)
    anki_mw.moveToState("review")
    wait_for_condition(
        lambda: anki_mw.state == "review",
        timeout=10.0,
        message="Anki did not enter review state for filtered deck",
    )
    reviewer = anki_mw.reviewer
    wait_for_condition(
        lambda: (
            reviewer.card is not None
            and reviewer.card.nid == note.id
            and int(reviewer.card.did) == deck_id
        ),
        timeout=10.0,
        message="Reviewer did not load the expected filtered-deck card",
    )
    wait_for_js_condition(
        reviewer.web,
        "document.querySelector('#qa') !== null",
        lambda value: value is True,
        timeout=10.0,
    )
    wait_for_js_condition(
        reviewer.web,
        "document.body ? document.body.innerText.includes('Prompt') : false",
        lambda value: value is True,
        timeout=10.0,
    )
    return reviewer


def _open_edit_current_from_reviewer_link(reviewer, note):
    reviewer._linkHandler("edit")
    edit_current = aqt.dialogs._dialogs["EditCurrent"][1]
    wait_for_condition(
        lambda: (
            edit_current.editor.note is not None
            and edit_current.editor.note.id == note.id
        ),
        timeout=10.0,
        message="Edit Current dialog did not load the reviewed note",
    )
    return edit_current


def _close_edit_current(edit_current) -> None:
    edit_current.cleanup()
    edit_current.close()


def _install_delayed_edit_current_fields_hook(delay_ms: int = 1250):
    from aqt import gui_hooks

    def _delay_set_fields(js: str, note, editor) -> str:
        del note
        editor_mode = getattr(getattr(editor, "editorMode", None), "name", "")
        if editor_mode != "EDIT_CURRENT":
            return js
        return js.replace(
            "setFields(",
            f"""
            (() => {{
              const aqeOriginalSetFields = setFields;
              setFields = (...args) => {{
                window.setTimeout(() => aqeOriginalSetFields(...args), {int(delay_ms)});
                setFields = aqeOriginalSetFields;
              }};
            }})();
            setFields(""",
            1,
        )

    gui_hooks.editor_will_load_note.append(_delay_set_fields)
    return lambda: gui_hooks.editor_will_load_note.remove(_delay_set_fields)


def _wait_for_edit_current_audio_controls(edit_current, field_ord: int) -> None:
    selector = _button_selector("aqe:play", field_ord)
    try:
        wait_for_js_condition(
            edit_current.editor.web,
            f"document.querySelector({json.dumps(selector)}) !== null",
            lambda value: value is True,
            timeout=10.0,
        )
    except TimeoutError as exc:
        diagnostics = wait_for_js(
            edit_current.editor.web,
            """
            (() => ({
              controls: document.querySelectorAll('.aqe-controls').length,
              audioFieldIndices: window.__AQE_EDITOR_CONFIG__?.audioFieldIndices ?? null,
              fieldContainers: Array.from(document.querySelectorAll('.field-container')).map((node) => ({
                index: node.getAttribute('data-index'),
                text: node.textContent,
              })),
              contenteditable: Array.from(document.querySelectorAll('[contenteditable="true"]')).map((node) => ({
                text: node.textContent,
                html: node.innerHTML,
              })),
              body: document.body ? document.body.outerHTML.slice(0, 2000) : '',
            }))()
            """,
            timeout=1.0,
        )
        raise TimeoutError(f"{exc}; diagnostics={diagnostics!r}") from exc


@pytest.mark.parametrize("reschedule", [True, False])
@pytest.mark.parametrize("review_side", ["question", "answer"])
def test_edit_current_from_filtered_deck_shows_audio_controls(
    anki_mw,
    ffmpeg_config,
    reschedule: bool,
    review_side: str,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "filtered_edit_current_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.5)
    note, _original_deck_id, field_ord = _reviewer_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    filtered_deck_id = _create_filtered_deck_for_note(
        anki_mw,
        note,
        reschedule=reschedule,
    )
    reviewer = _open_filtered_reviewer_for_note(anki_mw, note, filtered_deck_id)
    if review_side == "answer":
        _show_answer(reviewer)
    edit_current = _open_edit_current_from_reviewer_link(reviewer, note)
    try:
        _wait_for_edit_current_audio_controls(edit_current, field_ord)
    finally:
        _close_edit_current(edit_current)
        reviewer.mw.moveToState("deckBrowser")


def test_edit_current_from_filtered_deck_recovers_when_fields_render_late(
    anki_mw,
    ffmpeg_config,
) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "filtered_edit_current_delayed_fields_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=0.5)
    note, _original_deck_id, field_ord = _reviewer_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)
    filtered_deck_id = _create_filtered_deck_for_note(anki_mw, note, reschedule=True)
    reviewer = _open_filtered_reviewer_for_note(anki_mw, note, filtered_deck_id)
    remove_hook = _install_delayed_edit_current_fields_hook()
    edit_current = None
    try:
        edit_current = _open_edit_current_from_reviewer_link(reviewer, note)
        _wait_for_edit_current_audio_controls(edit_current, field_ord)
    finally:
        remove_hook()
        if edit_current is not None:
            _close_edit_current(edit_current)
        reviewer.mw.moveToState("deckBrowser")
