"""Mock aqt/anki so add-on code can be imported in a normal pytest run.

The add-on imports ``aqt`` objects at module scope, so these modules must
exist in ``sys.modules`` before test collection. We keep the top-level mock
objects stable for imported aliases like ``from aqt import mw``, then reset
their state before each test.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

from tests.mutmut_support import (
    addon_import_root,
    configure_mutmut_module_alias,
    configure_mutmut_package_aliases,
)


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


class _AddonManager:
    def addonFromModule(self, module: str) -> str:
        return module

    def getConfig(self, module: str) -> dict | None:
        del module
        return {}

    def writeConfig(self, module: str, conf: dict) -> None:
        del module, conf

    def addonConfigDefaults(self, module: str) -> dict | None:
        del module
        return {}

    def addonsFolder(self, module: str | None = None) -> str:
        del module
        return "/tmp/anki-audio-quick-editor-addon"

    def setConfigAction(self, module: str, fn: object) -> None:
        del module, fn


class _AnkiQt:
    def update_undo_actions(self) -> None:
        pass


class _TaskManager:
    def run_on_main(self, closure: object) -> None:
        if callable(closure):
            closure()

    def run_in_background(
        self,
        task: object,
        on_done: object = None,
        args: dict[str, object] | None = None,
        uses_collection: bool = True,
    ) -> object:
        del args, uses_collection
        if callable(task):
            result = task()
            if callable(on_done):
                on_done(types.SimpleNamespace(result=lambda: result))
            return result
        return object()


class _Editor:
    def loadNote(self, focusTo: int | None = None) -> None:
        del focusTo


class _AnkiWebView:
    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        self.requiresCol = True
        self._bridge_command = None
        self._bridge_context = None
        self._html = ""
        self._page = types.SimpleNamespace(
            runJavaScript=lambda _script, callback=None: callback(None) if callback else None
        )

    def set_bridge_command(self, func: object, context: object) -> None:
        self._bridge_command = func
        self._bridge_context = context

    def setHtml(self, html: str, *_args: object) -> None:
        self._html = html

    def stdHtml(
        self,
        body: str,
        *,
        head: str = "",
        context: object | None = None,
        **_kwargs: object,
    ) -> None:
        del context
        self._html = f"<!doctype html><html><head>{head}</head><body>{body}</body></html>"

    def eval(self, js: str) -> None:
        del js

    def evalWithCallback(self, js: str, cb: object) -> None:
        del js
        if callable(cb):
            cb(None)

    def page(self) -> object:
        return self._page


class _Collection:
    def get_note(self, id: object) -> object:
        del id
        return _Note()

    def update_note(self, note: object, skip_undo_entry: bool = False) -> object:
        del note, skip_undo_entry
        return object()

    def add_custom_undo_entry(self, name: str) -> int:
        del name
        return 1

    def merge_undo_entries(self, target: int) -> object:
        del target
        return object()


class _DeckManager:
    def all_names_and_ids(
        self,
        skip_empty_default: bool = False,
        include_filtered: bool = True,
    ) -> list[object]:
        del skip_empty_default, include_filtered
        return []


class _ModelManager:
    def all_names_and_ids(self) -> list[object]:
        return []


class _DB:
    def scalar(self, *a: object, **kw: object) -> object:
        del a, kw
        return 0


class _MediaManager:
    def dir(self) -> str:
        return "/tmp/anki-audio-quick-editor-media"

    def write_data(self, desired_fname: str, data: bytes) -> str:
        del data
        return desired_fname


class _Note:
    def __init__(self) -> None:
        self._fields: dict[str, str] = {}

    def items(self) -> list[tuple[str, str]]:
        return list(self._fields.items())

    def note_type(self) -> dict[str, str]:
        return {"name": "Basic"}

    def __setitem__(self, key: str, value: str) -> None:
        self._fields[key] = value


class _SoundOrVideoTag:
    def __init__(self, filename: str) -> None:
        self.filename = filename


_qt = types.ModuleType("aqt.qt")
_QT_CLASS_NAMES = """
    QAction qconnect QDialog QVBoxLayout QHBoxLayout QLabel QTextEdit QPushButton
    QGroupBox QScrollArea QPlainTextEdit QProgressBar QComboBox QLineEdit QTabWidget
    QDialogButtonBox QWidget QGridLayout QCheckBox QDesktopServices QMessageBox QMenu
    Qt QFileDialog QApplication QTimer QUrl
""".split()
_QT_MOCKS = {name: _named_mock(f"aqt.qt.{name}") for name in _QT_CLASS_NAMES}
for _name, _mock in _QT_MOCKS.items():
    setattr(_qt, _name, _mock)

_QT_STATIC_METHODS = {
    "QApplication": ("clipboard",),
    "QDesktopServices": ("openUrl",),
    "QMessageBox": ("warning",),
    "QTimer": ("singleShot",),
    "QUrl": ("fromLocalFile",),
}


def _configure_qt_static_methods() -> None:
    for class_name, method_names in _QT_STATIC_METHODS.items():
        qt_class = _QT_MOCKS[class_name]
        for method_name in method_names:
            setattr(qt_class, method_name, _named_mock(f"aqt.qt.{class_name}.{method_name}"))

_webview = types.ModuleType("aqt.webview")
_webview.AnkiWebView = _AnkiWebView

_aqt_addons = types.ModuleType("aqt.addons")
_aqt_addons.AddonManager = _AddonManager

_aqt_main = types.ModuleType("aqt.main")
_aqt_main.AnkiQt = _AnkiQt

_aqt_taskman = types.ModuleType("aqt.taskman")
_aqt_taskman.TaskManager = _TaskManager

_aqt_editor = types.ModuleType("aqt.editor")
_aqt_editor.Editor = _Editor

_aqt_utils = types.ModuleType("aqt.utils")
_aqt_utils.showInfo = _named_mock("aqt.utils.showInfo")
_aqt_utils.showWarning = _named_mock("aqt.utils.showWarning")
_aqt_utils.tooltip = _named_mock("aqt.utils.tooltip")
_aqt_utils.openLink = _named_mock("aqt.utils.openLink")

_aqt_gui_hooks = types.ModuleType("aqt.gui_hooks")
_GUI_HOOK_NAMES = (
    "overview_did_refresh",
    "overview_will_render_bottom",
    "main_window_did_init",
    "editor_did_init",
    "editor_will_load_note",
    "browser_menus_did_init",
    "browser_will_show_context_menu",
    "operation_did_execute",
    "reviewer_will_show_context_menu",
    "deck_browser_will_show_options_menu",
)
for _hook_name in _GUI_HOOK_NAMES:
    setattr(_aqt_gui_hooks, _hook_name, _named_mock(f"aqt.gui_hooks.{_hook_name}"))

_aqt_browser = types.ModuleType("aqt.browser")
_aqt_browser.Browser = _named_mock("aqt.browser.Browser")

_aqt_sound = types.ModuleType("aqt.sound")
_aqt_sound.av_player = _named_mock("aqt.sound.av_player")

_anki = types.ModuleType("anki")
_anki_collection = types.ModuleType("anki.collection")
_anki_collection.Collection = _Collection
_anki_db = types.ModuleType("anki.db")
_anki_db.DB = _DB
_anki_decks = types.ModuleType("anki.decks")
_anki_decks.DeckManager = _DeckManager
_anki_media = types.ModuleType("anki.media")
_anki_media.MediaManager = _MediaManager
_anki_models = types.ModuleType("anki.models")
_anki_models.ModelManager = _ModelManager
_anki_notes = types.ModuleType("anki.notes")
_anki_notes.Note = _Note
_anki_lang = types.ModuleType("anki.lang")
_anki_lang.current_lang = "en"
_anki_lang.is_rtl = lambda _lang: False
_anki_sound = types.ModuleType("anki.sound")
_anki_sound.SoundOrVideoTag = _SoundOrVideoTag
_anki.collection = _anki_collection
_anki.db = _anki_db
_anki.decks = _anki_decks
_anki.lang = _anki_lang
_anki.media = _anki_media
_anki.models = _anki_models
_anki.notes = _anki_notes
_anki.sound = _anki_sound

_mw = _named_mock("aqt.mw")
_aqt = types.ModuleType("aqt")
_aqt.mw = _mw
_aqt.addons = _aqt_addons
_aqt.editor = _aqt_editor
_aqt.gui_hooks = _aqt_gui_hooks
_aqt.main = _aqt_main
_aqt.qt = _qt
_aqt.sound = _aqt_sound
_aqt.taskman = _aqt_taskman
_aqt.utils = _aqt_utils
_aqt.webview = _webview

sys.modules["aqt"] = _aqt
sys.modules["aqt.addons"] = _aqt_addons
sys.modules["aqt.editor"] = _aqt_editor
sys.modules["aqt.qt"] = _qt
sys.modules["aqt.webview"] = _webview
sys.modules["aqt.utils"] = _aqt_utils
sys.modules["aqt.gui_hooks"] = _aqt_gui_hooks
sys.modules["aqt.browser"] = _aqt_browser
sys.modules["aqt.main"] = _aqt_main
sys.modules["aqt.sound"] = _aqt_sound
sys.modules["aqt.taskman"] = _aqt_taskman
sys.modules["anki"] = _anki
sys.modules["anki.collection"] = _anki_collection
sys.modules["anki.db"] = _anki_db
sys.modules["anki.decks"] = _anki_decks
sys.modules["anki.media"] = _anki_media
sys.modules["anki.models"] = _anki_models
sys.modules["anki.notes"] = _anki_notes
sys.modules["anki.lang"] = _anki_lang
sys.modules["anki.sound"] = _anki_sound


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


def _configure_av_player() -> None:
    _reset_mock_tree(_aqt_sound.av_player)
    _aqt_sound.av_player.play_tags = _named_mock("aqt.sound.av_player.play_tags")
    _aqt_sound.av_player.stop_and_clear_queue = _named_mock(
        "aqt.sound.av_player.stop_and_clear_queue"
    )
    _aqt_sound.av_player.toggle_pause = _named_mock("aqt.sound.av_player.toggle_pause")


def _reset_static_mock_modules() -> None:
    for mock in _QT_MOCKS.values():
        _reset_mock_tree(mock)
    _configure_qt_static_methods()
    _reset_mock_tree(_aqt_utils.showInfo)
    _reset_mock_tree(_aqt_utils.showWarning)
    _reset_mock_tree(_aqt_utils.tooltip)
    _reset_mock_tree(_aqt_utils.openLink)
    _reset_mock_tree(_aqt_browser.Browser)
    _configure_av_player()

    for hook_name in _GUI_HOOK_NAMES:
        _reset_mock_tree(getattr(_aqt_gui_hooks, hook_name))

    _configure_mw()


_reset_static_mock_modules()


# Make addon/ importable: ``from anki_audio_quick_editor.config_migration import …``
sys.path.insert(0, str(addon_import_root()))
configure_mutmut_module_alias()
configure_mutmut_package_aliases()


@pytest.fixture(autouse=True)
def _reset_anki_test_mocks() -> None:
    """Reset stable aqt mocks so tests do not leak state into each other."""
    _reset_static_mock_modules()
