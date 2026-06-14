"""Helpers for real Browser end-to-end workflows."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import aqt
from anki.collection import SearchNode
from PyQt6.QtWidgets import QApplication

from e2e.helpers import click_selector, wait_for_condition, wait_for_js_condition


def add_basic_audio_note(anki_mw, filenames: tuple[str, ...]):
    notetype = anki_mw.col.models.by_name("Basic")
    assert notetype is not None
    note = anki_mw.col.new_note(notetype)
    note["Front"] = " ".join(f"[sound:{filename}]" for filename in filenames)
    note["Back"] = "Back"
    deck_id = anki_mw.col.decks.id("Default")
    assert deck_id is not None
    anki_mw.col.add_note(note, deck_id)
    return note


def front_field(anki_mw, note_id: int) -> str:
    return anki_mw.col.get_note(note_id)["Front"]


def open_browser_for_note(anki_mw, note: Any) -> Any:
    browser = aqt.dialogs.open("Browser", anki_mw, search=(SearchNode(nid=int(note.id)),))
    wait_for_condition(
        lambda: browser.isVisible() and browser.table.len() >= 1,
        timeout=10.0,
        message="Browser did not open with the target note search",
    )
    return browser


def select_browser_note_row(browser: Any, note_id: int) -> None:
    card_ids = browser.col.get_note(note_id).card_ids()
    assert card_ids, "Browser workflow fixture note must have at least one card"
    browser.table.select_single_card(card_ids[0])
    QApplication.processEvents()
    wait_for_condition(
        lambda: int(note_id) in [int(value) for value in browser.selected_notes()],
        timeout=5.0,
        message="Browser row selection did not select the expected note",
    )


def trigger_cards_menu_action(browser: Any, label: str) -> None:
    action = next(
        (candidate for candidate in browser.form.menu_Cards.actions() if candidate.text() == label),
        None,
    )
    labels = [candidate.text() for candidate in browser.form.menu_Cards.actions()]
    assert action is not None, f"Cards menu action {label!r} not found; saw {labels!r}"
    action.trigger()
    QApplication.processEvents()


@contextmanager
def non_blocking_dialog_exec(dialog_class: type[Any]) -> Iterator[list[Any]]:
    opened: list[Any] = []
    original_exec = dialog_class.exec

    def fake_exec(self: Any) -> int:
        opened.append(self)
        self._dialog.show()
        QApplication.processEvents()
        return 0

    dialog_class.exec = fake_exec
    try:
        yield opened
    finally:
        dialog_class.exec = original_exec
        for dialog in opened:
            if getattr(dialog, "_running", False):
                dialog.cancel_event.set()
            dialog._dialog.close()


def wait_for_batch_dialog_ready(dialog: Any) -> None:
    wait_for_js_condition(
        dialog._webview,
        "Boolean(document.querySelector('[data-testid=\"batch-operation\"]'))",
        lambda value: value is True,
        timeout=10.0,
    )


def select_batch_operation(dialog: Any, operation: str) -> None:
    wait_for_js_condition(
        dialog._webview,
        f"""
        (() => {{
          const node = document.querySelector('[data-testid="batch-operation"]');
          if (!node) return false;
          node.value = {operation!r};
          node.dispatchEvent(new Event('change', {{ bubbles: true }}));
          return node.value;
        }})()
        """,
        lambda value: value == operation,
        timeout=5.0,
    )


def click_batch_start(dialog: Any) -> None:
    click_selector(dialog._webview, '[data-testid="batch-start"]', timeout=5.0)


def wait_for_dialog_finished(dialog: Any, *, timeout: float = 30.0) -> None:
    wait_for_condition(
        lambda: getattr(dialog, "_finished", False) is True,
        timeout=timeout,
        message=f"Dialog did not finish; log={getattr(dialog, '_log_lines', [])!r}",
    )


def open_batch_dialog(
    anki_mw,
    note,
    dialog_class: type[Any],
    *,
    action_label: str = "Run Audio Batch Operation...",
):
    browser = open_browser_for_note(anki_mw, note)
    select_browser_note_row(browser, int(note.id))
    return browser, non_blocking_dialog_exec(dialog_class), action_label


def open_audio_export_dialog(
    anki_mw,
    note,
    dialog_class: type[Any],
    *,
    action_label: str = "Export Audio...",
):
    browser = open_browser_for_note(anki_mw, note)
    select_browser_note_row(browser, int(note.id))
    return browser, non_blocking_dialog_exec(dialog_class), action_label
