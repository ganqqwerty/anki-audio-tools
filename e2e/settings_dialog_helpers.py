"""Helpers for settings dialog E2E tests."""

from __future__ import annotations

from PyQt6.QtWidgets import QApplication

from e2e.conftest import import_runtime_addon_module
from e2e.helpers import wait_for_condition


def open_settings_dialog(anki_mw):
    runtime_addon = import_runtime_addon_module()
    settings_dialog = import_runtime_addon_module(".settings").SettingsDialog

    submenu_holder = [None]

    def find_submenu() -> bool:
        submenu_holder[0] = next(
            (
                action.menu()
                for action in anki_mw.form.menuTools.actions()
                if action.menu() and action.menu().title() == "Anki Audio Quick Editor"
            ),
            None,
        )
        return submenu_holder[0] is not None

    wait_for_condition(find_submenu, timeout=5.0, message="Audio Quick Editor Tools menu did not initialize")
    submenu = submenu_holder[0]
    assert submenu is not None
    settings_action = next(action for action in submenu.actions() if action.text() == "Settings")
    settings_action.trigger()
    QApplication.processEvents()

    wait_for_condition(
        lambda: isinstance(runtime_addon._settings_dialog, settings_dialog)
        and runtime_addon._settings_dialog.isVisible(),
        timeout=5.0,
    )
    return runtime_addon._settings_dialog
