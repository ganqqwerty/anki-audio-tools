"""Build and reset the mocked Anki/aqt module tree used in tests."""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from unittest.mock import MagicMock

from tests._anki_test_mocks_stubs import (
    _DB,
    _GUI_HOOK_NAMES,
    _QT_MOCKS,
    _AddonManager,
    _AnkiQt,
    _AnkiWebView,
    _Collection,
    _configure_qt_static_methods,
    _DeckManager,
    _Editor,
    _MediaManager,
    _ModelManager,
    _named_mock,
    _Note,
    _reset_mock_tree,
    _SoundOrVideoTag,
    _TaskManager,
)


@dataclass(frozen=True)
class _MockState:
    modules: dict[str, types.ModuleType]
    qt_mocks: dict[str, MagicMock]
    mw: MagicMock
    aqt_utils: types.ModuleType
    aqt_gui_hooks: types.ModuleType
    aqt_sound: types.ModuleType
    aqt_browser: types.ModuleType
    anki_hooks: types.ModuleType


def _build_mock_modules() -> _MockState:
    _qt = types.ModuleType("aqt.qt")
    for _name, _mock in _QT_MOCKS.items():
        setattr(_qt, _name, _mock)

    _webview = types.ModuleType("aqt.webview")
    _webview.AnkiWebView = _AnkiWebView
    _webview.AnkiWebViewKind = types.SimpleNamespace(
        MAIN=types.SimpleNamespace(name="MAIN", value="main")
    )

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
    _aqt_utils.disable_help_button = _named_mock("aqt.utils.disable_help_button")

    _aqt_forms = types.ModuleType("aqt.forms")
    _aqt_forms_addfield = types.ModuleType("aqt.forms.addfield")
    _aqt_forms_addfield.Ui_Dialog = _named_mock("aqt.forms.addfield.Ui_Dialog")
    _aqt_forms.addfield = _aqt_forms_addfield

    _aqt_gui_hooks = types.ModuleType("aqt.gui_hooks")
    for _hook_name in _GUI_HOOK_NAMES:
        setattr(_aqt_gui_hooks, _hook_name, _named_mock(f"aqt.gui_hooks.{_hook_name}"))

    _aqt_browser = types.ModuleType("aqt.browser")
    _aqt_browser.Browser = _named_mock("aqt.browser.Browser")

    _aqt_sound = types.ModuleType("aqt.sound")
    _aqt_sound.av_player = _named_mock("aqt.sound.av_player")

    _aqt_mediacheck = types.ModuleType("aqt.mediacheck")
    _aqt_mediacheck.check_media_db = _named_mock("aqt.mediacheck.check_media_db")

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
    _anki_hooks = types.ModuleType("anki.hooks")
    _anki_hooks.field_filter = _named_mock("anki.hooks.field_filter")
    _anki_sound = types.ModuleType("anki.sound")
    _anki_sound.SoundOrVideoTag = _SoundOrVideoTag
    _anki.collection = _anki_collection
    _anki.db = _anki_db
    _anki.decks = _anki_decks
    _anki.hooks = _anki_hooks
    _anki.lang = _anki_lang
    _anki.media = _anki_media
    _anki.models = _anki_models
    _anki.notes = _anki_notes
    _anki.sound = _anki_sound

    mw = _named_mock("aqt.mw")

    _aqt = types.ModuleType("aqt")
    _aqt.mw = mw
    _aqt.addons = _aqt_addons
    _aqt.editor = _aqt_editor
    _aqt.forms = _aqt_forms
    _aqt.gui_hooks = _aqt_gui_hooks
    _aqt.main = _aqt_main
    _aqt.qt = _qt
    _aqt.sound = _aqt_sound
    _aqt.taskman = _aqt_taskman
    _aqt.utils = _aqt_utils
    _aqt.webview = _webview
    _aqt.mediacheck = _aqt_mediacheck
    modules = {
        "aqt": _aqt,
        "aqt.addons": _aqt_addons,
        "aqt.editor": _aqt_editor,
        "aqt.forms": _aqt_forms,
        "aqt.forms.addfield": _aqt_forms_addfield,
        "aqt.qt": _qt,
        "aqt.webview": _webview,
        "aqt.utils": _aqt_utils,
        "aqt.gui_hooks": _aqt_gui_hooks,
        "aqt.browser": _aqt_browser,
        "aqt.main": _aqt_main,
        "aqt.mediacheck": _aqt_mediacheck,
        "aqt.sound": _aqt_sound,
        "aqt.taskman": _aqt_taskman,
        "anki": _anki,
        "anki.collection": _anki_collection,
        "anki.db": _anki_db,
        "anki.decks": _anki_decks,
        "anki.hooks": _anki_hooks,
        "anki.media": _anki_media,
        "anki.models": _anki_models,
        "anki.notes": _anki_notes,
        "anki.lang": _anki_lang,
        "anki.sound": _anki_sound,
    }

    for module_name, module in modules.items():
        sys.modules[module_name] = module

    return _MockState(
        modules=modules,
        qt_mocks=_QT_MOCKS,
        mw=mw,
        aqt_utils=_aqt_utils,
        aqt_gui_hooks=_aqt_gui_hooks,
        aqt_sound=_aqt_sound,
        aqt_browser=_aqt_browser,
        anki_hooks=_anki_hooks,
    )


def _configure_av_player(aqt_sound: types.ModuleType) -> None:
    _reset_mock_tree(aqt_sound.av_player)
    aqt_sound.av_player.play_tags = _named_mock("aqt.sound.av_player.play_tags")
    aqt_sound.av_player.stop_and_clear_queue = _named_mock(
        "aqt.sound.av_player.stop_and_clear_queue"
    )
    aqt_sound.av_player.toggle_pause = _named_mock("aqt.sound.av_player.toggle_pause")


def _configure_mw(mw: MagicMock) -> None:
    _reset_mock_tree(mw)
    mw.addonManager = _named_mock("aqt.mw.addonManager")
    mw.addonManager.getConfig.return_value = {}
    mw.addonManager.addonConfigDefaults.return_value = {}
    mw.addonManager.addonFromModule.side_effect = lambda _module: "anki_audio_quick_editor"
    mw.addonManager.addonsFolder.return_value = "/tmp/anki-audio-quick-editor-addon"
    mw.taskman = _named_mock("aqt.mw.taskman")
    mw.taskman.run_on_main.side_effect = lambda fn: fn()
    mw.pm = _named_mock("aqt.mw.pm")
    mw.pm.profileFolder.return_value = "/tmp/anki-audio-quick-editor-profile"
    mw.col = _named_mock("aqt.mw.col")
    mw.col.decks.all_names_and_ids.return_value = []
    mw.col.models.all_names_and_ids.return_value = []
    mw.col.db.scalar.return_value = 0
    mw.form = _named_mock("aqt.mw.form")
    mw.app = _named_mock("aqt.mw.app")


def reset_static_mock_modules(mock_state: _MockState) -> None:
    for mock in mock_state.qt_mocks.values():
        _reset_mock_tree(mock)
    _configure_qt_static_methods()
    _reset_mock_tree(mock_state.aqt_utils.showInfo)
    _reset_mock_tree(mock_state.aqt_utils.showWarning)
    _reset_mock_tree(mock_state.aqt_utils.tooltip)
    _reset_mock_tree(mock_state.aqt_utils.openLink)
    _reset_mock_tree(mock_state.aqt_browser.Browser)
    _configure_av_player(mock_state.aqt_sound)

    for hook_name in _GUI_HOOK_NAMES:
        _reset_mock_tree(getattr(mock_state.aqt_gui_hooks, hook_name))
    _reset_mock_tree(mock_state.anki_hooks.field_filter)
    _configure_mw(mock_state.mw)


def install_mock_modules() -> _MockState:
    return _build_mock_modules()
