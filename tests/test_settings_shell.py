"""Tests for the settings WebView shell."""

from __future__ import annotations

import importlib
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import aqt


class FakeSignal:
    def __init__(self) -> None:
        self.callbacks = []

    def connect(self, callback) -> None:
        self.callbacks.append(callback)

    def emit(self, *args: object) -> None:
        for callback in self.callbacks:
            callback(*args)


class FakeQDialog:
    def __init__(self, parent: object) -> None:
        self.parent = parent
        self.finished = FakeSignal()

    def setWindowTitle(self, title: str) -> None:
        self.window_title = title

    def setMinimumWidth(self, width: int) -> None:
        self.minimum_width = width

    def setMinimumHeight(self, height: int) -> None:
        self.minimum_height = height


class FakeLayout:
    def __init__(self, parent: object) -> None:
        self.parent = parent
        self.margins = None
        self.widgets = []
        parent.layout = self

    def setContentsMargins(self, *margins: int) -> None:
        self.margins = margins

    def addWidget(self, widget: object) -> None:
        self.widgets.append(widget)


class FakeWebView:
    def __init__(self, parent: object) -> None:
        self.parent = parent
        self.requiresCol = True
        self.eval_calls: list[str] = []
        self.page_object = SimpleNamespace(runJavaScript=MagicMock())
        self.bridge = None
        self.cleanup_calls = 0
        self.context = None
        self.html = ""

    def set_bridge_command(self, bridge, context: object) -> None:
        self.bridge = bridge
        self.context = context

    def stdHtml(self, *, body: str, head: str, context: object) -> None:
        self.html = f"<head>{head}</head><body>{body}</body>"
        self.std_html_context = context

    def eval(self, js: str) -> None:
        self.eval_calls.append(js)

    def cleanup(self) -> None:
        self.cleanup_calls += 1

    def page(self):
        return self.page_object


def test_render_settings_content_escapes_initial_state_and_includes_error_reporter(monkeypatch, tmp_path) -> None:
    import anki_audio_quick_editor.settings as settings

    bundle_dir = tmp_path / "settings"
    bundle_dir.mkdir()
    bundle_js = bundle_dir / "settings_bundle.js"
    bundle_css = bundle_dir / "settings_bundle.css"
    bundle_js.write_text("window.__bundleLoaded = true;", encoding="utf-8")
    bundle_css.write_text(".settings { color: red; }", encoding="utf-8")
    monkeypatch.setattr(settings, "_BUNDLE_JS", bundle_js)
    monkeypatch.setattr(settings, "_BUNDLE_CSS", bundle_css)
    monkeypatch.setattr(
        settings,
        "build_initial_state",
        lambda _config: json.dumps({"danger": "</script><script>evil()</script>"}),
    )

    body, head = settings._render_settings_content({"debug_logging": True})

    assert "<style>.settings { color: red; }</style>" in head
    assert "window.__INITIAL_STATE__ = {\"danger\": \"<\\/script><script>evil()<\\/script>\"};" in body
    assert "window.addEventListener(\"error\"" in body
    assert "window.addEventListener(\"unhandledrejection\"" in body
    assert "stack: event.error && event.error.stack" in body
    assert "stack: reason && reason.stack" in body
    assert "frontend.log" in body
    assert "bridge:" in body
    assert "window.__bundleLoaded = true;" in body


def test_render_settings_html_wraps_content_in_document_shell(monkeypatch) -> None:
    import anki_audio_quick_editor.settings as settings

    monkeypatch.setattr(
        settings,
        "_render_settings_content",
        lambda _config: ("<main>body</main>", "<meta name='x'>"),
    )

    html = settings._render_settings_html({})

    assert html.startswith("<!DOCTYPE html>")
    assert "<html lang=\"en\">" in html
    assert "<meta name='x'>" in html
    assert "<main>body</main>" in html


def test_settings_dialog_wires_webview_bridge_and_html(monkeypatch, request) -> None:
    settings = _reload_settings_with_fake_qt(request)

    aqt.mw.addonManager.addonFromModule.return_value = "addon-id"
    aqt.mw.addonManager.getConfig.return_value = {"debug_logging": True}
    handled: list[tuple[str, object]] = []
    monkeypatch.setattr(
        settings,
        "handle_settings_command",
        lambda cmd, _eval_fn, dialog: handled.append((cmd, dialog)) or True,
    )
    monkeypatch.setattr(settings, "build_initial_state", lambda config: json.dumps({"config": config}))

    dialog = settings.SettingsDialog(parent=object())

    assert dialog.window_title == "Anki Audio Quick Editor - Settings"
    assert dialog.minimum_width == 900
    assert dialog.minimum_height == 640
    assert dialog.layout.margins == (0, 0, 0, 0)
    assert dialog.layout.widgets == [dialog._webview]
    assert dialog._webview.requiresCol is False
    assert "window.__INITIAL_STATE__" in dialog._webview.html
    command = 'bridge:{"command":"settings.cancel"}'
    assert dialog._webview.bridge(command) is True
    assert handled == [(command, dialog)]


def test_settings_dialog_run_js_uses_eval_and_page_callback(monkeypatch, request) -> None:
    settings = _reload_settings_with_fake_qt(request)
    monkeypatch.setattr(settings, "build_initial_state", lambda config: json.dumps({"config": config}))
    dialog = settings.SettingsDialog(parent=object())
    callback = MagicMock()

    dialog.run_js("window.answer = 42")
    dialog.run_js("window.answer", callback)

    assert dialog._webview.eval_calls == ["window.answer = 42"]
    dialog._webview.page_object.runJavaScript.assert_called_once_with("window.answer", callback)


def test_settings_dialog_drops_async_publication_after_finished(monkeypatch, request) -> None:
    settings = _reload_settings_with_fake_qt(request)
    monkeypatch.setattr(settings, "build_initial_state", lambda config: json.dumps({"config": config}))
    eval_functions = []
    monkeypatch.setattr(
        settings,
        "handle_settings_command",
        lambda _cmd, eval_fn, _dialog: eval_functions.append(eval_fn) or True,
    )
    dialog = settings.SettingsDialog(parent=object())
    assert dialog._webview.bridge('bridge:{"command":"settings.async"}') is True
    eval_fn = eval_functions[0]

    eval_fn("window.onAsyncDone({before: true})")
    dialog.finished.emit(0)
    eval_fn("window.onAsyncDone({after: true})")

    assert dialog._accepts_async_publications is False
    assert dialog._cleaned_up is False
    assert dialog._webview.cleanup_calls == 0
    assert dialog._webview.eval_calls == ["window.onAsyncDone({before: true})"]


def test_settings_dialog_opens_runtime_installer(monkeypatch, request) -> None:
    settings = _reload_settings_with_fake_qt(request)
    import anki_audio_quick_editor.runtime_installer_dialog as runtime_installer_dialog

    monkeypatch.setattr(settings, "build_initial_state", lambda config: json.dumps({"config": config}))
    aqt.mw.addonManager.addonFromModule.return_value = "addon-id"
    aqt.mw.addonManager.addonsFolder.return_value = "/addon"
    calls: list[tuple[object, str, bool]] = []
    monkeypatch.setattr(
        runtime_installer_dialog,
        "open_runtime_install_dialog",
        lambda parent, addon_dir, *, force_verify: calls.append((parent, addon_dir, force_verify))
        or {"phase": "ready"},
    )
    dialog = settings.SettingsDialog(parent=object())

    assert dialog.open_runtime_installer() == {"phase": "ready"}
    assert calls == [(dialog, "/addon", True)]


def _reload_settings_with_fake_qt(request):
    import anki_audio_quick_editor.settings as settings

    original_qdialog = aqt.qt.QDialog
    original_qvboxlayout = aqt.qt.QVBoxLayout
    original_qconnect = aqt.qt.qconnect
    original_webview = aqt.webview.AnkiWebView
    aqt.qt.QDialog = FakeQDialog
    aqt.qt.QVBoxLayout = FakeLayout
    aqt.qt.qconnect = lambda signal, callback: signal.connect(callback)
    aqt.webview.AnkiWebView = FakeWebView

    def restore_settings_module() -> None:
        aqt.qt.QDialog = original_qdialog
        aqt.qt.QVBoxLayout = original_qvboxlayout
        aqt.qt.qconnect = original_qconnect
        aqt.webview.AnkiWebView = original_webview
        importlib.reload(settings)

    request.addfinalizer(restore_settings_module)
    return importlib.reload(settings)
