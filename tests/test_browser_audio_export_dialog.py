from __future__ import annotations

import importlib
import json
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

import aqt

from anki_audio_quick_editor.audio_export_types import AudioExportReport
from anki_audio_quick_editor.batch_operation_types import FieldGroup
from anki_audio_quick_editor.browser_audio_export_dialog import AudioExportDialog


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
        self.bridge = None

    def set_bridge_command(self, bridge, context: object) -> None:
        self.bridge = bridge
        self.context = context

    def stdHtml(self, *, body: str, head: str, context: object) -> None:
        self.html = f"<head>{head}</head><body>{body}</body>"
        self.std_html_context = context

    def eval(self, js: str) -> None:
        self.eval_calls.append(js)


def test_audio_export_dialog_handles_cancel_when_running() -> None:
    dialog = SimpleNamespace(
        _running=True,
        cancel_event=threading.Event(),
        append_log=MagicMock(),
        tr=lambda key, values=None: key,
    )

    AudioExportDialog._cancel_or_close(dialog)  # type: ignore[arg-type]

    assert dialog.cancel_event.is_set()
    dialog.append_log.assert_called_once_with("audio_export.cancel_requested")


def test_render_audio_export_content_embeds_batch_initial_state_name(monkeypatch, tmp_path) -> None:
    import anki_audio_quick_editor.browser_audio_export_dialog as dialog_module

    bundle_dir = tmp_path / "batch"
    bundle_dir.mkdir()
    bundle_js = bundle_dir / "batch_bundle.js"
    bundle_css = bundle_dir / "batch_bundle.css"
    bundle_js.write_text("window.__batchBundleLoaded = true;", encoding="utf-8")
    bundle_css.write_text(".batch-root { color: red; }", encoding="utf-8")
    monkeypatch.setattr(dialog_module, "_BUNDLE_JS", bundle_js)
    monkeypatch.setattr(dialog_module, "_BUNDLE_CSS", bundle_css)

    body, head = dialog_module._render_audio_export_content({"surface": "audio_export"})

    assert "<style>.batch-root { color: red; }</style>" in head
    assert 'window.__AQE_BATCH_INITIAL_STATE__ = {"surface": "audio_export"};' in body
    assert "window.__batchBundleLoaded = true;" in body


def test_audio_export_dialog_bridge_start_cancel_copy_and_close(monkeypatch, request) -> None:
    dialog_module = _reload_audio_export_dialog_with_fake_qt(request)
    run_calls = []
    copied = []
    monkeypatch.setattr(dialog_module, "request_from_audio_export_start_payload", lambda _payload: "request")
    monkeypatch.setattr(dialog_module, "_clipboard_set_text", lambda text: copied.append(text))
    monkeypatch.setattr(dialog_module, "run_audio_export_in_background", lambda *args: run_calls.append(args))

    dialog = dialog_module.AudioExportDialog(
        browser=object(),
        note_ids=[1, 2],
        groups=(FieldGroup("Basic", ("Audio",)),),
        snapshots=(),
    )

    command = "bridge:" + json.dumps({"command": "audio-export.start", "payload": {"mode": "zip"}})
    assert dialog._webview.bridge(command) is True
    assert run_calls[0][2] == ()
    assert run_calls[0][3] == "request"

    dialog.append_log("line one")
    assert dialog._webview.bridge('bridge:{"command":"audio-export.copy_log"}') is True
    assert copied == ["line one"]
    assert dialog._webview.bridge('bridge:{"command":"audio-export.cancel"}') is True
    assert dialog.cancel_event.is_set()
    assert dialog._webview.bridge('bridge:{"command":"audio-export.close"}') is True
    assert dialog._dialog.rejected is True


def test_audio_export_dialog_start_clears_prior_cancel_event(monkeypatch, request) -> None:
    dialog_module = _reload_audio_export_dialog_with_fake_qt(request)
    run_calls = []
    monkeypatch.setattr(dialog_module, "request_from_audio_export_start_payload", lambda _payload: "request")
    monkeypatch.setattr(dialog_module, "run_audio_export_in_background", lambda *args: run_calls.append(args))

    dialog = dialog_module.AudioExportDialog(
        browser=object(),
        note_ids=[1],
        groups=(FieldGroup("Basic", ("Audio",)),),
        snapshots=(),
    )
    dialog.cancel_event.set()

    command = "bridge:" + json.dumps({"command": "audio-export.start", "payload": {"mode": "zip"}})
    assert dialog._webview.bridge(command) is True

    assert dialog.cancel_event.is_set() is False
    assert len(run_calls) == 1


def test_default_audio_export_filename_uses_mode_extension() -> None:
    from anki_audio_quick_editor.browser_audio_export_dialog import (
        _default_export_filename,
    )

    assert _default_export_filename("zip").endswith(".zip")
    assert _default_export_filename("combined_mp3").endswith(".mp3")


def test_audio_export_dialog_choose_destination_emits_selected_path(monkeypatch, request) -> None:
    dialog_module = _reload_audio_export_dialog_with_fake_qt(request)
    monkeypatch.setattr(
        dialog_module,
        "_choose_export_destination",
        lambda _parent, mode: f"/tmp/export.{mode}",
    )

    dialog = dialog_module.AudioExportDialog(
        browser=object(),
        note_ids=[1],
        groups=(FieldGroup("Basic", ("Audio",)),),
        snapshots=(),
    )

    command = "bridge:" + json.dumps(
        {"command": "audio-export.choose-destination", "payload": {"mode": "combined_mp3"}}
    )
    assert dialog._webview.bridge(command) is True

    assert any("onAudioExportDestination" in call for call in dialog._webview.eval_calls)
    assert any("/tmp/export.combined_mp3" in call for call in dialog._webview.eval_calls)


def test_audio_export_dialog_finish_payloads(monkeypatch, request) -> None:
    dialog_module = _reload_audio_export_dialog_with_fake_qt(request)
    dialog = dialog_module.AudioExportDialog(
        browser=object(),
        note_ids=[1],
        groups=(),
        snapshots=(),
    )
    report = AudioExportReport(total=1, processed=1, exported=1, output_path="/tmp/out.zip")

    dialog.finish_with_report(report)
    dialog.finish_with_error("Export failed", user_error={"code": "AQE-BATCH-001", "message": "Export failed"})

    assert any("onAudioExportFinish" in call for call in dialog._webview.eval_calls)
    assert any("onAudioExportError" in call for call in dialog._webview.eval_calls)


def _reload_audio_export_dialog_with_fake_qt(request):
    import anki_audio_quick_editor.browser_audio_export_dialog as dialog_module

    original_qdialog = aqt.qt.QDialog
    original_qvboxlayout = aqt.qt.QVBoxLayout
    original_webview = aqt.webview.AnkiWebView
    aqt.qt.QDialog = FakeQDialog
    aqt.qt.QVBoxLayout = FakeLayout
    aqt.webview.AnkiWebView = FakeWebView

    def restore_dialog_module() -> None:
        aqt.qt.QDialog = original_qdialog
        aqt.qt.QVBoxLayout = original_qvboxlayout
        aqt.webview.AnkiWebView = original_webview
        importlib.reload(dialog_module)

    request.addfinalizer(restore_dialog_module)
    return importlib.reload(dialog_module)
