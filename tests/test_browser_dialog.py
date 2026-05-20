"""Tests for the Browser batch WebView dialog shell."""

from __future__ import annotations

import importlib
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import aqt

from anki_audio_quick_editor.audio_state import AudioProcessingConfig


class FakeQDialog:
    def __init__(self, parent: object) -> None:
        self.parent = parent
        self.rejected = False

    def setWindowTitle(self, title: str) -> None:
        self.window_title = title

    def setMinimumWidth(self, width: int) -> None:
        self.minimum_width = width

    def setMinimumHeight(self, height: int) -> None:
        self.minimum_height = height

    def exec(self) -> int:
        return 0

    def reject(self) -> None:
        self.rejected = True


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

    def page(self):
        return self.page_object


def test_render_batch_content_embeds_initial_state_and_bundle(monkeypatch, tmp_path) -> None:
    import anki_audio_quick_editor.browser_dialog as browser_dialog

    bundle_dir = tmp_path / "batch"
    bundle_dir.mkdir()
    bundle_js = bundle_dir / "batch_bundle.js"
    bundle_css = bundle_dir / "batch_bundle.css"
    bundle_js.write_text("window.__batchBundleLoaded = true;", encoding="utf-8")
    bundle_css.write_text(".batch-root { color: red; }", encoding="utf-8")
    monkeypatch.setattr(browser_dialog, "_BUNDLE_JS", bundle_js)
    monkeypatch.setattr(browser_dialog, "_BUNDLE_CSS", bundle_css)

    body, head = browser_dialog._render_batch_content({"danger": "</script>"})

    assert "<style>.batch-root { color: red; }</style>" in head
    assert "window.__AQE_BATCH_INITIAL_STATE__ = {\"danger\": \"<\\/script>\"};" in body
    assert "window.addEventListener(\"error\"" in body
    assert "frontend.log" in body
    assert "bridge:" in body
    assert "window.__batchBundleLoaded = true;" in body


def test_batch_dialog_bridge_start_cancel_copy_and_close(monkeypatch, request) -> None:
    dialog_module = _reload_browser_dialog_with_fake_qt(request)
    run_calls = []
    copied = []
    monkeypatch.setattr(dialog_module, "request_from_batch_start_payload", lambda _payload: "request")
    monkeypatch.setattr(dialog_module, "_clipboard_set_text", lambda text: copied.append(text))

    dialog = dialog_module.BatchOperationsDialog(
        browser=object(),
        note_ids=[1, 2],
        groups=(),
        config=AudioProcessingConfig(),
        run_batch_in_background=lambda *args: run_calls.append(args),
    )

    command = "bridge:" + json.dumps(
        {
            "command": "batch.start",
            "payload": {
                "operation": "graph",
                "source_field": "Audio",
                "target_field": "Image",
                "parameters": {},
            },
        }
    )
    assert dialog._webview.bridge(command) is True
    assert run_calls[0][2] == [1, 2]
    assert run_calls[0][3] == "request"

    dialog.append_log("line one")
    assert dialog._webview.bridge('bridge:{"command":"batch.copy_log"}') is True
    assert copied == ["line one"]
    assert dialog._webview.bridge('bridge:{"command":"batch.cancel"}') is True
    assert dialog.cancel_event.is_set()
    assert dialog._webview.bridge('bridge:{"command":"batch.close"}') is True
    assert dialog._dialog.rejected is True


def test_batch_dialog_validation_error_is_recoverable(monkeypatch, request) -> None:
    dialog_module = _reload_browser_dialog_with_fake_qt(request)
    run_calls = []
    monkeypatch.setattr(
        dialog_module,
        "request_from_batch_start_payload",
        lambda _payload: (_ for _ in ()).throw(ValueError("Choose a target field before starting.")),
    )

    dialog = dialog_module.BatchOperationsDialog(
        browser=object(),
        note_ids=[1],
        groups=(),
        config=AudioProcessingConfig(),
        run_batch_in_background=lambda *args: run_calls.append(args),
    )

    assert dialog._webview.bridge('bridge:{"command":"batch.start","payload":{}}') is True

    assert run_calls == []
    assert dialog._running is False
    assert dialog._finished is False
    assert any('"recoverable": true' in call for call in dialog._webview.eval_calls)


def _reload_browser_dialog_with_fake_qt(request):
    import anki_audio_quick_editor.browser_dialog as browser_dialog

    original_qdialog = aqt.qt.QDialog
    original_qvboxlayout = aqt.qt.QVBoxLayout
    original_webview = aqt.webview.AnkiWebView
    aqt.qt.QDialog = FakeQDialog
    aqt.qt.QVBoxLayout = FakeLayout
    aqt.webview.AnkiWebView = FakeWebView

    def restore_browser_dialog_module() -> None:
        aqt.qt.QDialog = original_qdialog
        aqt.qt.QVBoxLayout = original_qvboxlayout
        aqt.webview.AnkiWebView = original_webview
        importlib.reload(browser_dialog)

    request.addfinalizer(restore_browser_dialog_module)
    return importlib.reload(browser_dialog)
