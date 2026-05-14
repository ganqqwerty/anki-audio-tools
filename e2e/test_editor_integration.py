"""E2E smoke checks for editor hook registration."""

from __future__ import annotations


def test_editor_hooks_are_registered(anki_mw) -> None:
    from aqt import gui_hooks

    del anki_mw
    assert gui_hooks.editor_did_init.count() > 0
    assert gui_hooks.editor_will_load_note.count() > 0
