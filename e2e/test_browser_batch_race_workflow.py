from __future__ import annotations

import json

import pytest

from .conftest import import_runtime_addon_module
from .helpers import run_js, wait_for_condition


def test_batch_dialog_duplicate_start_does_not_launch_second_run(anki_mw) -> None:
    audio_state = import_runtime_addon_module(".audio_state")
    batch_operations = import_runtime_addon_module(".batch_operations")
    browser_dialog = import_runtime_addon_module(".browser_dialog")
    batch_dialog_class = browser_dialog.BatchOperationsDialog

    started: list[dict[str, object]] = []

    def fake_run_batch(browser, run_dialog, note_ids, request):
        started.append({"browser": browser, "dialog": run_dialog, "note_ids": list(note_ids), "request": request})

    dialog = batch_dialog_class(
        anki_mw,
        [1, 2],
        (batch_operations.FieldGroup("Basic", ("Front", "Back")),),
        audio_state.AudioProcessingConfig(),
        fake_run_batch,
    )
    start_payload = {
        "operation": "faster",
        "source_field": "Front",
        "target_field": "Front",
        "parameters": {"speed_step": 0.1},
    }
    command = "bridge:" + json.dumps({"command": "batch.start", "payload": start_payload})

    dialog._dialog.show()
    try:
        run_js(dialog._webview, f"pycmd({command!r}); pycmd({command!r});")
        wait_for_condition(lambda: len(started) >= 1, timeout=2.0)

        assert len(started) == 1
        assert dialog._running is True
    finally:
        dialog._dialog.close()


def test_batch_dialog_duplicate_start_keeps_single_progress_stream(
    anki_mw,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audio_state = import_runtime_addon_module(".audio_state")
    batch_operations = import_runtime_addon_module(".batch_operations")
    browser_dialog = import_runtime_addon_module(".browser_dialog")
    batch_dialog_class = browser_dialog.BatchOperationsDialog
    emitted: list[tuple[str, object]] = []

    def fake_emit(_self, name, event_payload=None):
        emitted.append((name, event_payload))

    def fake_run_batch(_browser, run_dialog, _note_ids, _request):
        run_dialog.append_log("first run")

    monkeypatch.setattr(browser_dialog.BatchOperationsDialog, "_emit", fake_emit)

    dialog = batch_dialog_class(
        anki_mw,
        [1, 2, 3],
        (batch_operations.FieldGroup("Basic", ("Front", "Back")),),
        audio_state.AudioProcessingConfig(),
        fake_run_batch,
    )
    start_payload = {
        "operation": "volume_up",
        "source_field": "Front",
        "target_field": "Front",
        "parameters": {"volume_step_db": 3.0},
    }
    command = "bridge:" + json.dumps({"command": "batch.start", "payload": start_payload})

    dialog._dialog.show()
    try:
        run_js(dialog._webview, f"pycmd({command!r}); pycmd({command!r});")
        wait_for_condition(lambda: any(name == "onBatchProgress" for name, _payload in emitted), timeout=2.0)

        progress_events = [payload for name, payload in emitted if name == "onBatchProgress"]
        assert len(progress_events) == 1
        assert dialog._log_lines == ["first run"]
    finally:
        dialog._dialog.close()
