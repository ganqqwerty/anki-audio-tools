"""Mock aqt/anki so add-on code can be imported in a normal pytest run.

The add-on imports ``aqt`` objects at module scope, so these modules must
exist in ``sys.modules`` before test collection. We keep the top-level mock
objects stable for imported aliases like ``from aqt import mw``, then reset
their state before each test.
"""

from __future__ import annotations

import importlib
import inspect
import os
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
        "QProgressBar",
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
        "QApplication",
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
    "browser_menus_did_init",
    "browser_will_show_context_menu",
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
_aqt.qt = _qt
_aqt.utils = _aqt_utils

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
        "browser_menus_did_init",
        "browser_will_show_context_menu",
        "reviewer_will_show_context_menu",
        "deck_browser_will_show_options_menu",
    ):
        _reset_mock_tree(getattr(_aqt_gui_hooks, hook_name))

    _configure_mw()


_reset_static_mock_modules()

def _addon_import_root() -> Path:
    """Return the path to place on sys.path for add-on imports."""
    root = Path(__file__).resolve().parent.parent
    if os.environ.get("MUTANT_UNDER_TEST"):
        return root
    return root / "addon"


def _configure_mutmut_module_alias() -> None:
    """Reuse the active mutmut main module instead of importing it twice."""
    if not os.environ.get("MUTANT_UNDER_TEST"):
        return
    main_module = sys.modules.get("__main__")
    if main_module is None or not hasattr(main_module, "record_trampoline_hit"):
        return
    sys.modules.setdefault("mutmut.__main__", main_module)


def _configure_mutmut_package_aliases() -> None:
    """Map test imports onto addon-prefixed mutmut module names."""
    if not os.environ.get("MUTANT_UNDER_TEST"):
        return
    module_names = [
        "addon.anki_audio_quick_editor",
        "addon.anki_audio_quick_editor.audio_state",
        "addon.anki_audio_quick_editor.audio_processor",
        "addon.anki_audio_quick_editor.batch_visualization",
        "addon.anki_audio_quick_editor.config_migration",
        "addon.anki_audio_quick_editor.errors",
        "addon.anki_audio_quick_editor.prosody_cache",
        "addon.anki_audio_quick_editor.prosody_svg",
        "addon.anki_audio_quick_editor.prosody_types",
        "addon.anki_audio_quick_editor.settings_state",
        "addon.anki_audio_quick_editor.sound_refs",
    ]
    for module_name in module_names:
        module = importlib.import_module(module_name)
        _retarget_module_members_for_mutmut(module, module_name)
        sys.modules.setdefault(module_name.removeprefix("addon."), module)


def _retarget_module_members_for_mutmut(module: types.ModuleType, module_name: str) -> None:
    """Align trampoline hit names with mutmut's addon-prefixed file identifiers."""
    original_module_name = module.__name__
    module.__name__ = module_name
    for value in vars(module).values():
        if inspect.isfunction(value):
            if value.__module__ != original_module_name:
                continue
            value.__module__ = module_name
            continue
        if not inspect.isclass(value):
            continue
        if value.__module__ != original_module_name:
            continue
        value.__module__ = module_name
        for member in vars(value).values():
            function = None
            if inspect.isfunction(member):
                function = member
            elif isinstance(member, (staticmethod, classmethod)):
                function = member.__func__
            if function is not None and function.__module__ == original_module_name:
                function.__module__ = module_name


# Make addon/ importable: ``from anki_audio_quick_editor.config_migration import …``
sys.path.insert(0, str(_addon_import_root()))
_configure_mutmut_module_alias()
_configure_mutmut_package_aliases()


@pytest.fixture(autouse=True)
def _reset_anki_test_mocks() -> None:
    """Reset stable aqt mocks so tests do not leak state into each other."""
    _reset_static_mock_modules()
