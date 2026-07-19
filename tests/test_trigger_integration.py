"""Tests for trigger hook integration."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.trigger_integration import register_trigger_hooks
from anki_audio_quick_editor.trigger_runner import TRIGGER_UPDATE_INITIATOR


class _Hook(list):
    def append(self, item):  # type: ignore[no-untyped-def]
        super().append(item)


class _AddCardsMode:
    def __str__(self) -> str:
        return "EditorMode.ADD_CARDS"


def test_register_trigger_hooks_schedules_add_and_editor_edit(monkeypatch) -> None:
    calls: list[tuple[object, object, str]] = []
    hooks = SimpleNamespace(add_cards_did_add_note=_Hook(), operation_did_execute=_Hook())
    mw = object()
    note = object()
    editor = SimpleNamespace(note=note, _save_current_note=lambda: None)

    monkeypatch.setattr(
        "anki_audio_quick_editor.trigger_integration.schedule_trigger_event",
        lambda mw_arg, note_arg, event: calls.append((mw_arg, note_arg, event)) or 1,
    )

    register_trigger_hooks(hooks, mw_provider=lambda: mw)
    hooks.add_cards_did_add_note[0](note)
    hooks.operation_did_execute[0](SimpleNamespace(note_text=True), editor)

    assert calls == [(mw, note, "add"), (mw, note, "edit")]


def test_operation_hook_ignores_trigger_and_add_cards_handlers(monkeypatch) -> None:
    schedule = MagicMock()
    hooks = SimpleNamespace(add_cards_did_add_note=_Hook(), operation_did_execute=_Hook())
    add_cards_editor = SimpleNamespace(
        note=object(),
        editorMode=_AddCardsMode(),
        _save_current_note=lambda: None,
    )

    monkeypatch.setattr(
        "anki_audio_quick_editor.trigger_integration.schedule_trigger_event",
        schedule,
    )

    register_trigger_hooks(hooks, mw_provider=lambda: object())
    hooks.operation_did_execute[0](object(), TRIGGER_UPDATE_INITIATOR)
    hooks.operation_did_execute[0](object(), add_cards_editor)
    hooks.operation_did_execute[0](object(), None)

    schedule.assert_not_called()


def test_operation_hook_ignores_editor_operations_without_note_changes(monkeypatch) -> None:
    schedule = MagicMock()
    hooks = SimpleNamespace(add_cards_did_add_note=_Hook(), operation_did_execute=_Hook())
    editor = SimpleNamespace(note=object(), _save_current_note=lambda: None)

    monkeypatch.setattr(
        "anki_audio_quick_editor.trigger_integration.schedule_trigger_event",
        schedule,
    )

    register_trigger_hooks(hooks, mw_provider=lambda: object())
    hooks.operation_did_execute[0](SimpleNamespace(note=False, note_text=False), editor)

    schedule.assert_not_called()
