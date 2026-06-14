"""Bootstrap import tests for the Audio Quick Editor entrypoint."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import aqt

import anki_audio_quick_editor
from anki_audio_quick_editor import reviewer_integration
from anki_audio_quick_editor.editor_runtime import SettingsLifecycleCallbacks


class FakeAction:
    def __init__(self, label: str) -> None:
        self.label = label
        self.enabled = False
        self.triggered = object()

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def setText(self, label: str) -> None:
        self.label = label


class FakeMenu:
    def __init__(self) -> None:
        self.aboutToShow = object()
        self.actions: list[FakeAction] = []
        self.separator_count = 0

    def addAction(self, label: str) -> FakeAction:
        action = FakeAction(label)
        self.actions.append(action)
        return action

    def addSeparator(self) -> None:
        self.separator_count += 1


def test_entrypoint_registers_hooks_and_config_action() -> None:
    importlib.reload(anki_audio_quick_editor)

    assert aqt.gui_hooks.main_window_did_init.append.call_count == 10
    aqt.gui_hooks.addon_manager_will_install_addon.append.assert_called_once_with(
        anki_audio_quick_editor._release_install_blocking_files
    )
    aqt.gui_hooks.addon_manager_did_install_addon.append.assert_called_once_with(
        anki_audio_quick_editor._restore_install_logging
    )
    aqt.gui_hooks.addons_dialog_will_delete_addons.append.assert_called_once_with(
        anki_audio_quick_editor._release_delete_blocking_files
    )
    aqt.mw.addonManager.setConfigAction.assert_called_once()


def test_setup_menu_adds_reviewer_toggle_and_settings(monkeypatch) -> None:
    menu = FakeMenu()
    aqt.mw.form.menuTools.addMenu.return_value = menu
    connections: dict[object, object] = {}
    monkeypatch.setattr(
        anki_audio_quick_editor,
        "qconnect",
        lambda signal, callback: connections.setdefault(signal, callback),
    )
    monkeypatch.setattr(
        reviewer_integration,
        "qconnect",
        lambda signal, callback: connections.setdefault(signal, callback),
    )

    anki_audio_quick_editor._setup_menu()

    aqt.mw.form.menuTools.addMenu.assert_called_once_with("Anki Audio Quick Editor")
    assert [action.label for action in menu.actions] == [
        "Show audio editor",
        "Settings",
    ]
    assert menu.separator_count == 1
    assert menu.aboutToShow in connections
    assert menu.actions[0].triggered in connections
    assert menu.actions[1].triggered in connections


def test_setup_menu_refreshes_reviewer_toggle_enabled_state(monkeypatch) -> None:
    menu = FakeMenu()
    aqt.mw.form.menuTools.addMenu.return_value = menu
    connections: dict[object, object] = {}

    monkeypatch.setattr(
        anki_audio_quick_editor,
        "qconnect",
        lambda signal, callback: connections.setdefault(signal, callback),
    )
    monkeypatch.setattr(
        reviewer_integration,
        "qconnect",
        lambda signal, callback: connections.setdefault(signal, callback),
    )
    monkeypatch.setattr(
        reviewer_integration,
        "reviewer_editor_menu_label",
        lambda _reviewer=None: "Hide audio editor"
        if getattr(aqt.mw, "reviewer", None) is not None
        else "Show audio editor",
    )
    aqt.mw.reviewer = None

    anki_audio_quick_editor._setup_menu()

    assert menu.actions[0].enabled is False
    aqt.mw.reviewer = types.SimpleNamespace(card=object())
    connections[menu.aboutToShow]()

    assert menu.actions[0].label == "Hide audio editor"
    assert menu.actions[0].enabled is True


def test_open_settings_keeps_dialog_reference() -> None:
    import anki_audio_quick_editor

    anki_audio_quick_editor._open_settings()

    assert anki_audio_quick_editor._settings_dialog is not None


def test_setup_managed_runtime_skips_dialog_when_ready(monkeypatch) -> None:
    from anki_audio_quick_editor import runtime_manager

    monkeypatch.setattr(
        runtime_manager,
        "runtime_status",
        lambda _addon_dir: {
            "phase": "ready",
            "runtime_manifest_id": "runtime-test",
            "platform": "macos-arm64",
            "runtime_root": "/runtime",
            "progress": 100,
            "message": "Runtime is ready.",
            "error": "",
        },
    )
    dialog_module = types.ModuleType("anki_audio_quick_editor.runtime_installer_dialog")
    dialog_module.open_runtime_install_dialog = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("dialog should not open")
    )
    monkeypatch.setitem(sys.modules, "anki_audio_quick_editor.runtime_installer_dialog", dialog_module)

    anki_audio_quick_editor._setup_managed_runtime()


def test_setup_managed_runtime_opens_dialog_when_missing(monkeypatch) -> None:
    from anki_audio_quick_editor import runtime_manager

    monkeypatch.setattr(
        runtime_manager,
        "runtime_status",
        lambda _addon_dir: {
            "phase": "missing",
            "runtime_manifest_id": "runtime-test",
            "platform": "macos-arm64",
            "runtime_root": "",
            "progress": 0,
            "message": "Runtime assets are not installed.",
            "error": "",
        },
    )
    calls: list[tuple[object, object, bool]] = []
    dialog_module = types.ModuleType("anki_audio_quick_editor.runtime_installer_dialog")
    dialog_module.open_runtime_install_dialog = (
        lambda parent, addon_dir, *, force_verify: calls.append((parent, addon_dir, force_verify))
    )
    monkeypatch.setitem(sys.modules, "anki_audio_quick_editor.runtime_installer_dialog", dialog_module)

    anki_audio_quick_editor._setup_managed_runtime()

    assert calls == [(aqt.mw, Path("/tmp/anki-audio-quick-editor-addon"), False)]


def test_setup_managed_runtime_opens_dialog_when_error_with_manifest(monkeypatch) -> None:
    from anki_audio_quick_editor import runtime_manager

    monkeypatch.setattr(
        runtime_manager,
        "runtime_status",
        lambda _addon_dir: {
            "phase": "error",
            "runtime_manifest_id": "runtime-test",
            "platform": "macos-arm64",
            "runtime_root": "",
            "progress": 0,
            "message": "",
            "error": "Runtime failed verification.",
        },
    )
    calls: list[tuple[object, object, bool]] = []
    dialog_module = types.ModuleType("anki_audio_quick_editor.runtime_installer_dialog")
    dialog_module.open_runtime_install_dialog = (
        lambda parent, addon_dir, *, force_verify: calls.append((parent, addon_dir, force_verify))
    )
    monkeypatch.setitem(sys.modules, "anki_audio_quick_editor.runtime_installer_dialog", dialog_module)

    anki_audio_quick_editor._setup_managed_runtime()

    assert calls == [(aqt.mw, Path("/tmp/anki-audio-quick-editor-addon"), False)]


def test_setup_managed_runtime_skips_dialog_without_manifest(monkeypatch) -> None:
    from anki_audio_quick_editor import runtime_manager

    monkeypatch.setattr(
        runtime_manager,
        "runtime_status",
        lambda _addon_dir: {
            "phase": "missing",
            "runtime_manifest_id": "",
            "platform": "macos-arm64",
            "runtime_root": "",
            "progress": 0,
            "message": "Runtime manifest is not packaged.",
            "error": "",
        },
    )
    dialog_module = types.ModuleType("anki_audio_quick_editor.runtime_installer_dialog")
    dialog_module.open_runtime_install_dialog = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("dialog should not open without a manifest")
    )
    monkeypatch.setitem(sys.modules, "anki_audio_quick_editor.runtime_installer_dialog", dialog_module)

    anki_audio_quick_editor._setup_managed_runtime()


def test_show_settings_dialog_calls_on_closed_once_for_rejected_finished(monkeypatch) -> None:
    class FakeDialog:
        def __init__(self) -> None:
            self.accepted = object()
            self.finished = object()
            self.shown = False
            self.raised = False
            self.activated = False

        def show(self) -> None:
            self.shown = True

        def raise_(self) -> None:
            self.raised = True

        def activateWindow(self) -> None:
            self.activated = True

    dialog = FakeDialog()
    settings_module = types.ModuleType("anki_audio_quick_editor.settings")
    settings_module.SettingsDialog = lambda _parent: dialog
    monkeypatch.setitem(sys.modules, "anki_audio_quick_editor.settings", settings_module)
    connections: dict[object, object] = {}
    monkeypatch.setattr(anki_audio_quick_editor, "qconnect", lambda signal, callback: connections.setdefault(signal, callback))
    closed_calls: list[str] = []

    anki_audio_quick_editor._show_settings_dialog(
        SettingsLifecycleCallbacks(on_closed=lambda: closed_calls.append("closed"))
    )

    finished = connections[dialog.finished]
    finished(0)
    finished(0)

    assert closed_calls == ["closed"]
    assert dialog.shown is True
    assert dialog.raised is True
    assert dialog.activated is True


def test_show_settings_dialog_does_not_call_on_closed_for_accepted_finished(monkeypatch) -> None:
    class FakeDialog:
        def __init__(self) -> None:
            self.accepted = object()
            self.finished = object()

        def show(self) -> None:
            pass

        def raise_(self) -> None:
            pass

        def activateWindow(self) -> None:
            pass

    dialog = FakeDialog()
    settings_module = types.ModuleType("anki_audio_quick_editor.settings")
    settings_module.SettingsDialog = lambda _parent: dialog
    monkeypatch.setitem(sys.modules, "anki_audio_quick_editor.settings", settings_module)
    connections: dict[object, object] = {}
    monkeypatch.setattr(anki_audio_quick_editor, "qconnect", lambda signal, callback: connections.setdefault(signal, callback))
    saved_calls: list[str] = []
    closed_calls: list[str] = []

    anki_audio_quick_editor._show_settings_dialog(
        SettingsLifecycleCallbacks(
            on_saved=lambda: saved_calls.append("saved"),
            on_closed=lambda: closed_calls.append("closed"),
        )
    )

    connections[dialog.accepted]()
    connections[dialog.finished](1)

    assert saved_calls == ["saved"]
    assert closed_calls == []
