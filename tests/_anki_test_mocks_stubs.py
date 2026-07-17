"""Shared mock primitives for Anki/aqt test bootstrapping."""

from __future__ import annotations

import types
from collections.abc import Callable
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock


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


@dataclass(frozen=True)
class _ScheduledTask:
    task: Callable[[], Any]
    on_done: Callable[[Future[Any]], None] | None
    future: Future[Any]
    uses_collection: bool


class _TaskManager:
    """Controllable task manager preserving Anki's Future callback contract."""

    def __init__(self, *, auto_run: bool = True) -> None:
        self.auto_run = auto_run
        self.main_queue: list[Callable[[], Any]] = []
        self.background_queue: list[_ScheduledTask] = []

    def run_on_main(self, closure: Callable[[], Any]) -> None:
        self.main_queue.append(closure)
        if self.auto_run:
            self.flush_main()

    def run_in_background(
        self,
        task: Callable[[], Any],
        on_done: Callable[[Future[Any]], None] | None = None,
        args: dict[str, object] | None = None,
        uses_collection: bool = True,
    ) -> Future[Any]:
        del args
        scheduled = _ScheduledTask(task, on_done, Future(), uses_collection)
        self.background_queue.append(scheduled)
        if self.auto_run:
            self.complete_next_background()
        return scheduled.future

    def flush_main(self) -> None:
        while self.main_queue:
            self.main_queue.pop(0)()

    def complete_next_background(self) -> Future[Any]:
        if not self.background_queue:
            raise AssertionError("No background task is scheduled.")
        scheduled = self.background_queue.pop(0)
        try:
            scheduled.future.set_result(scheduled.task())
        except BaseException as exc:
            scheduled.future.set_exception(exc)
        if scheduled.on_done is not None:
            scheduled.on_done(scheduled.future)
        return scheduled.future


class _Editor:
    def loadNote(self, focusTo: int | None = None) -> None:
        del focusTo


class _AnkiWebView:
    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        self.requiresCol = True
        self._bridge_command: object | None = None
        self._bridge_context: object | None = None
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

    def cleanup(self) -> None:
        pass


class _UndoStatus:
    def __init__(self) -> None:
        self.last_step = 1


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

    def undo_status(self) -> _UndoStatus:
        return _UndoStatus()

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
    fields: dict[str, str] = {}

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


_QT_CLASS_NAMES = """
    QAction qconnect QDialog QVBoxLayout QHBoxLayout QLabel QTextEdit QPushButton
    QGroupBox QScrollArea QPlainTextEdit QProgressBar QComboBox QDoubleSpinBox
    QLineEdit QTabWidget QDialogButtonBox QWidget QGridLayout QCheckBox QDesktopServices
    QMessageBox QMenu Qt QFileDialog QApplication QTimer QUrl
""".split()

_QT_MOCKS = {name: _named_mock(f"aqt.qt.{name}") for name in _QT_CLASS_NAMES}

_QT_STATIC_METHODS = {
    "QApplication": ("clipboard",),
    "QDesktopServices": ("openUrl",),
    "QFileDialog": ("getSaveFileName",),
    "QMessageBox": ("warning",),
    "QTimer": ("singleShot",),
    "QUrl": ("fromLocalFile",),
}

_GUI_HOOK_NAMES = (
    "overview_did_refresh",
    "overview_will_render_bottom",
    "main_window_did_init",
    "addon_manager_will_install_addon",
    "addon_manager_did_install_addon",
    "addons_dialog_will_delete_addons",
    "editor_did_init",
    "editor_will_load_note",
    "webview_did_receive_js_message",
    "collection_will_temporarily_close",
    "profile_will_close",
    "card_review_webview_did_init",
    "card_layout_will_show",
    "card_will_show",
    "reviewer_did_show_question",
    "reviewer_did_show_answer",
    "reviewer_did_answer_card",
    "browser_menus_did_init",
    "browser_will_show_context_menu",
    "operation_did_execute",
    "add_cards_did_add_note",
    "reviewer_will_show_context_menu",
    "deck_browser_will_show_options_menu",
)


def _configure_qt_static_methods() -> None:
    """Create static-like methods on selected `aqt.qt` classes."""
    for class_name, method_names in _QT_STATIC_METHODS.items():
        qt_class = _QT_MOCKS[class_name]
        for method_name in method_names:
            setattr(qt_class, method_name, _named_mock(f"aqt.qt.{class_name}.{method_name}"))
