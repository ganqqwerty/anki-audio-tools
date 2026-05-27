"""Tests for Browser hook and dialog wiring."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import aqt

from anki_audio_quick_editor.audio_state import AudioProcessingConfig
from anki_audio_quick_editor.batch_operations import FieldGroup
from anki_audio_quick_editor.browser_dialog import BatchOperationsDialog
from anki_audio_quick_editor.browser_integration import (
    ACTION_LABEL,
    _on_browser_menus_did_init,
    _open_batch_dialog,
    register_browser_hooks,
)
from anki_audio_quick_editor.webview_bridge import WebviewBridgeCommand
from tests.browser_batch_fixtures import FakeNote


def test_register_browser_hooks() -> None:
    hooks = SimpleNamespace(browser_menus_did_init=MagicMock(), browser_will_show_context_menu=MagicMock())

    register_browser_hooks(hooks)

    hooks.browser_menus_did_init.append.assert_called_once()
    hooks.browser_will_show_context_menu.append.assert_not_called()


def test_browser_menu_action_is_added() -> None:
    browser = SimpleNamespace(form=SimpleNamespace(menu_Cards=MagicMock()))

    _on_browser_menus_did_init(browser)

    browser.form.menu_Cards.addAction.assert_called_once_with(ACTION_LABEL)
    assert aqt.qt.qconnect.called


def test_empty_selection_shows_warning() -> None:
    browser = SimpleNamespace(selected_notes=lambda: [], mw=MagicMock())

    _open_batch_dialog(browser)

    aqt.utils.showWarning.assert_called_once()


def test_selection_without_fields_shows_warning(monkeypatch) -> None:
    browser = SimpleNamespace(selected_notes=lambda: [1], mw=SimpleNamespace(col=MagicMock()))

    monkeypatch.setattr("anki_audio_quick_editor.browser_integration._snapshots_for_note_ids", lambda *_args: [])

    _open_batch_dialog(browser)

    aqt.utils.showWarning.assert_called_once_with(
        "The selected cards do not expose any note fields.",
        parent=browser,
    )


def test_open_batch_dialog_builds_field_groups_from_selected_notes(monkeypatch) -> None:
    dialog_calls: list[tuple[object, ...]] = []

    class Dialog:
        def exec(self) -> None:
            dialog_calls.append(("exec", ()))  # type: ignore[arg-type]

    def create_dialog(
        _browser: object,
        note_ids: list[int],
        groups: tuple[object, ...],
        config: AudioProcessingConfig,
    ) -> Dialog:
        dialog_calls.append((note_ids, groups, config))
        return Dialog()

    col = SimpleNamespace(get_note=lambda _note_id: FakeNote(int(_note_id)))
    addon_manager = SimpleNamespace(
        addonFromModule=lambda _module: "anki_audio_quick_editor",
        getConfig=lambda _addon_id: {
            "speed_step": 2.0,
            "volume_step_db": 6.0,
            "pause_aggressiveness": "aggressive",
        },
    )
    browser = SimpleNamespace(
        selected_notes=lambda: [2, 1, 2],
        mw=SimpleNamespace(col=col, addonManager=addon_manager),
    )
    monkeypatch.setattr("anki_audio_quick_editor.browser_integration._create_dialog", create_dialog)

    _open_batch_dialog(browser)

    assert dialog_calls[0][0] == [2, 1]
    groups = dialog_calls[0][1]
    assert len(groups) == 1
    assert groups[0].notetype_name == "Basic"
    assert groups[0].fields == ("Audio", "Image")
    config = dialog_calls[0][2]
    assert config.speed_step == 2.0
    assert config.volume_step_db == 6.0
    assert config.pause_aggressiveness == "aggressive"
    assert dialog_calls[1] == ("exec", ())


def test_batch_dialog_ignores_duplicate_start_while_running() -> None:
    started: list[tuple[object, object, list[int], object]] = []

    def fake_run_batch(browser, dialog, note_ids, request):
        started.append((browser, dialog, list(note_ids), request))

    browser = SimpleNamespace(mw=SimpleNamespace())
    dialog = BatchOperationsDialog(
        browser,
        note_ids=[101, 102],
        groups=(FieldGroup("Basic", ("Front", "Back")),),
        config=AudioProcessingConfig(),
        run_batch_in_background=fake_run_batch,
    )
    payload = {
        "operation": "faster",
        "source_field": "Front",
        "target_field": "Front",
        "parameters": {"speed_step": 0.1},
    }
    command = WebviewBridgeCommand("batch.start", payload=payload)

    assert dialog._handle_batch_start(command)
    assert dialog._handle_batch_start(command)

    assert len(started) == 1
    assert dialog._running is True
