"""Mock aqt/anki so add-on code can be imported in a normal pytest run.

The add-on imports ``aqt`` objects at module scope, so these modules must
exist in ``sys.modules`` before test collection. We keep the top-level mock
objects stable for imported aliases like ``from aqt import mw``, then reset
their state before each test.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _named_mock(name: str) -> MagicMock:
    return MagicMock(name=name)


def _reset_mock_tree(mock: MagicMock) -> None:
    """Clear call history and dynamically-added children from a stable mock."""
    mock.reset_mock(return_value=True, side_effect=True)

    for attr in list(mock.__dict__.keys()):
        # Preserve MagicMock's own public bookkeeping. Removing method_calls
        # corrupts append()/attribute-call tracking and can recurse during
        # addon hook registration at import time.
        if not attr.startswith("_") and attr != "method_calls":
            delattr(mock, attr)

    children = getattr(mock, "_mock_children", None)
    if isinstance(children, dict):
        children.clear()


_qt = types.ModuleType("aqt.qt")
_QT_MOCKS = {
    name: _named_mock(f"aqt.qt.{name}")
    for name in (
        "QAction",
        "qconnect",
        "QDialog",
        "QVBoxLayout",
        "QHBoxLayout",
        "QLabel",
        "QTextEdit",
        "QPushButton",
        "QGroupBox",
        "QScrollArea",
        "QPlainTextEdit",
        "QComboBox",
        "QLineEdit",
        "QTabWidget",
        "QDialogButtonBox",
        "QWidget",
        "QGridLayout",
        "QCheckBox",
        "QMessageBox",
        "QMenu",
        "Qt",
        "QFileDialog",
    )
}
for _name, _mock in _QT_MOCKS.items():
    setattr(_qt, _name, _mock)

_webview = types.ModuleType("aqt.webview")
_webview.AnkiWebView = _named_mock("aqt.webview.AnkiWebView")

_aqt_utils = types.ModuleType("aqt.utils")
_aqt_utils.showInfo = _named_mock("aqt.utils.showInfo")
_aqt_utils.showWarning = _named_mock("aqt.utils.showWarning")
_aqt_utils.tooltip = _named_mock("aqt.utils.tooltip")
_aqt_utils.openLink = _named_mock("aqt.utils.openLink")

_aqt_gui_hooks = types.ModuleType("aqt.gui_hooks")
for _hook_name in (
    "overview_did_refresh",
    "overview_will_render_bottom",
    "main_window_did_init",
    "editor_did_init",
    "editor_will_load_note",
    "reviewer_will_show_context_menu",
    "deck_browser_will_show_options_menu",
):
    setattr(_aqt_gui_hooks, _hook_name, _named_mock(f"aqt.gui_hooks.{_hook_name}"))

_aqt_browser = types.ModuleType("aqt.browser")
_aqt_browser.Browser = _named_mock("aqt.browser.Browser")

_aqt_sound = types.ModuleType("aqt.sound")
_aqt_sound.av_player = _named_mock("aqt.sound.av_player")

_mw = _named_mock("aqt.mw")
_aqt = types.ModuleType("aqt")
_aqt.mw = _mw
_aqt.gui_hooks = _aqt_gui_hooks

sys.modules["aqt"] = _aqt
sys.modules["aqt.qt"] = _qt
sys.modules["aqt.webview"] = _webview
sys.modules["aqt.utils"] = _aqt_utils
sys.modules["aqt.gui_hooks"] = _aqt_gui_hooks
sys.modules["aqt.browser"] = _aqt_browser
sys.modules["aqt.sound"] = _aqt_sound


def _configure_mw() -> None:
    _reset_mock_tree(_mw)
    _mw.addonManager = _named_mock("aqt.mw.addonManager")
    _mw.addonManager.getConfig.return_value = {}
    _mw.addonManager.addonConfigDefaults.return_value = {}
    _mw.addonManager.addonFromModule.side_effect = lambda _module: "anki_audio_quick_editor"
    _mw.addonManager.addonsFolder.return_value = "/tmp/anki-audio-quick-editor-addon"
    _mw.taskman = _named_mock("aqt.mw.taskman")
    _mw.taskman.run_on_main.side_effect = lambda fn: fn()
    _mw.pm = _named_mock("aqt.mw.pm")
    _mw.pm.profileFolder.return_value = "/tmp/anki-audio-quick-editor-profile"
    _mw.col = _named_mock("aqt.mw.col")
    _mw.col.decks.all_names_and_ids.return_value = []
    _mw.col.models.all_names_and_ids.return_value = []
    _mw.col.db.scalar.return_value = 0
    _mw.form = _named_mock("aqt.mw.form")
    _mw.app = _named_mock("aqt.mw.app")


def _reset_static_mock_modules() -> None:
    for mock in _QT_MOCKS.values():
        _reset_mock_tree(mock)
    _reset_mock_tree(_webview.AnkiWebView)
    _reset_mock_tree(_aqt_utils.showInfo)
    _reset_mock_tree(_aqt_utils.showWarning)
    _reset_mock_tree(_aqt_utils.tooltip)
    _reset_mock_tree(_aqt_utils.openLink)
    _reset_mock_tree(_aqt_browser.Browser)
    _reset_mock_tree(_aqt_sound.av_player)

    for hook_name in (
        "overview_did_refresh",
        "overview_will_render_bottom",
        "main_window_did_init",
        "editor_did_init",
        "editor_will_load_note",
        "reviewer_will_show_context_menu",
        "deck_browser_will_show_options_menu",
    ):
        _reset_mock_tree(getattr(_aqt_gui_hooks, hook_name))

    _configure_mw()


_reset_static_mock_modules()

# Make addon/ importable: ``from anki_audio_quick_editor.config_migration import …``
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "addon"))


@pytest.fixture(autouse=True)
def _reset_anki_test_mocks() -> None:
    """Reset stable aqt mocks so tests do not leak state into each other."""
    _reset_static_mock_modules()
