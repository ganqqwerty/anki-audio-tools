"""Tests for the Qt runtime installer dialog."""

from __future__ import annotations

import importlib
import logging
import sys
from types import SimpleNamespace

import aqt


class FakeSignal:
    def __init__(self) -> None:
        self.callback = None


class FakeQDialog:
    def __init__(self, parent: object) -> None:
        self.parent = parent
        self.rejected = False
        self.accepted = False

    def setWindowTitle(self, title: str) -> None:
        self.window_title = title

    def setMinimumWidth(self, width: int) -> None:
        self.minimum_width = width

    def setMinimumHeight(self, height: int) -> None:
        self.minimum_height = height

    def setModal(self, modal: bool) -> None:
        self.modal = modal

    def exec(self) -> int:
        return 0

    def reject(self) -> None:
        self.rejected = True

    def accept(self) -> None:
        self.accepted = True

    def closeEvent(self, _event: object) -> None:
        pass


class FakeLayout:
    def __init__(self, parent: object | None = None) -> None:
        self.parent = parent
        self.widgets: list[object] = []
        self.layouts: list[object] = []

    def addWidget(self, widget: object) -> None:
        self.widgets.append(widget)

    def addLayout(self, layout: object) -> None:
        self.layouts.append(layout)

    def addStretch(self, _stretch: int) -> None:
        pass


class FakeLabel:
    def __init__(self, text: str = "", parent: object | None = None) -> None:
        del parent
        self.text = text

    def setText(self, text: str) -> None:
        self.text = text


class FakeProgressBar:
    def __init__(self, parent: object | None = None) -> None:
        del parent
        self.range = (0, 0)
        self.value = 0

    def setRange(self, minimum: int, maximum: int) -> None:
        self.range = (minimum, maximum)

    def setValue(self, value: int) -> None:
        self.value = value


class FakeTextEdit:
    def __init__(self, parent: object | None = None) -> None:
        del parent
        self.read_only = False
        self.lines: list[str] = []

    def setReadOnly(self, read_only: bool) -> None:
        self.read_only = read_only

    def append(self, line: str) -> None:
        self.lines.append(line)


class FakeButton:
    def __init__(self, text: str = "", parent: object | None = None) -> None:
        del parent
        self.text = text
        self.clicked = FakeSignal()

    def setText(self, text: str) -> None:
        self.text = text


class ImmediateThread:
    def __init__(self, target, daemon=True, name="") -> None:
        del daemon, name
        self._target = target

    def start(self) -> None:
        self._target()


def test_runtime_installer_dialog_sets_up_modal_controls(request) -> None:
    dialog_module = _reload_runtime_dialog_with_fake_qt(request)

    dialog = dialog_module.RuntimeInstallDialog(object(), "/addon", force_verify=False)

    assert dialog.window_title == "Audio Quick Editor Runtime"
    assert dialog.minimum_width == 560
    assert dialog.minimum_height == 360
    assert dialog.modal is True
    assert dialog._progress.range == (0, 100)
    assert dialog._log.read_only is True
    assert dialog._button.text == "Cancel"


def test_runtime_installer_reject_cancels_and_warns(request) -> None:
    dialog_module = _reload_runtime_dialog_with_fake_qt(request)
    dialog = dialog_module.RuntimeInstallDialog(object(), "/addon", force_verify=False)

    dialog.reject()

    assert dialog._cancel_event.is_set()
    assert dialog.rejected is True
    aqt.qt.QMessageBox.warning.assert_called_once_with(
        dialog,
        dialog_module.t("runtime_installer.cancel_warning.title"),
        dialog_module.t("runtime_installer.cancel_warning.message"),
    )


def test_runtime_installer_exec_updates_progress_and_final_status(monkeypatch, request) -> None:
    dialog_module = _reload_runtime_dialog_with_fake_qt(request)
    final_status = {
        "phase": "ready",
        "runtime_manifest_id": "runtime-test",
        "platform": "macos-arm64",
        "runtime_root": "/runtime",
        "progress": 100,
        "message": "Runtime is ready.",
        "error": "",
    }

    def ensure_runtime(_addon_dir, *, progress, cancel_event, force_verify):
        assert cancel_event.is_set() is False
        assert force_verify is True
        progress({"progress": 25, "step": "Download zip", "detail": "Downloaded bytes"})
        return final_status

    monkeypatch.setattr(dialog_module.threading, "Thread", ImmediateThread)
    monkeypatch.setattr("anki_audio_quick_editor.runtime_manager.ensure_runtime", ensure_runtime)

    dialog = dialog_module.RuntimeInstallDialog(object(), "/addon", force_verify=True)
    dialog.exec_install()

    assert dialog.final_status == final_status
    assert dialog._finished is True
    assert dialog._button.text == "Close"
    assert "Download zip: Downloaded bytes" in dialog._log.lines
    assert dialog._progress.value == 100


def test_runtime_installer_logs_displayed_final_error(monkeypatch, request, caplog) -> None:
    dialog_module = _reload_runtime_dialog_with_fake_qt(request)
    final_status = {
        "phase": "error",
        "runtime_manifest_id": "runtime-test",
        "platform": "macos-arm64",
        "runtime_root": "",
        "progress": 0,
        "message": "Runtime install failed.",
        "error": "Runtime manifest is not packaged.",
    }

    def ensure_runtime(_addon_dir, *, progress, cancel_event, force_verify):
        return final_status

    monkeypatch.setattr(dialog_module.threading, "Thread", ImmediateThread)
    monkeypatch.setattr("anki_audio_quick_editor.runtime_manager.ensure_runtime", ensure_runtime)
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.runtime_installer_dialog")

    dialog = dialog_module.RuntimeInstallDialog(object(), "/addon", force_verify=True)
    dialog.exec_install()

    assert dialog.final_status == final_status
    assert "runtime installer displayed error: Runtime manifest is not packaged." in caplog.text


def _reload_runtime_dialog_with_fake_qt(request):
    original_qdialog = aqt.qt.QDialog
    original_qvboxlayout = aqt.qt.QVBoxLayout
    original_qhboxlayout = aqt.qt.QHBoxLayout
    original_qlabel = aqt.qt.QLabel
    original_qtextedit = aqt.qt.QTextEdit
    original_qpushbutton = aqt.qt.QPushButton
    original_qprogressbar = aqt.qt.QProgressBar
    original_qmessagebox = aqt.qt.QMessageBox
    original_qconnect = aqt.qt.qconnect

    aqt.qt.QDialog = FakeQDialog
    aqt.qt.QVBoxLayout = FakeLayout
    aqt.qt.QHBoxLayout = FakeLayout
    aqt.qt.QLabel = FakeLabel
    aqt.qt.QTextEdit = FakeTextEdit
    aqt.qt.QPushButton = FakeButton
    aqt.qt.QProgressBar = FakeProgressBar
    aqt.qt.QMessageBox = SimpleNamespace(warning=aqt.qt.QMessageBox.warning)
    aqt.qt.qconnect = lambda signal, callback: setattr(signal, "callback", callback)
    runtime_installer_dialog = importlib.import_module(
        "anki_audio_quick_editor.runtime_installer_dialog"
    )

    def restore_runtime_dialog_module() -> None:
        aqt.qt.QDialog = original_qdialog
        aqt.qt.QVBoxLayout = original_qvboxlayout
        aqt.qt.QHBoxLayout = original_qhboxlayout
        aqt.qt.QLabel = original_qlabel
        aqt.qt.QTextEdit = original_qtextedit
        aqt.qt.QPushButton = original_qpushbutton
        aqt.qt.QProgressBar = original_qprogressbar
        aqt.qt.QMessageBox = original_qmessagebox
        aqt.qt.qconnect = original_qconnect
        if "anki_audio_quick_editor.runtime_installer_dialog" in sys.modules:
            importlib.reload(runtime_installer_dialog)

    request.addfinalizer(restore_runtime_dialog_module)
    return importlib.reload(runtime_installer_dialog)
