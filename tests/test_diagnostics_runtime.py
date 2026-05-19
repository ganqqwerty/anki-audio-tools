"""Tests for runtime diagnostics and exception-boundary support."""

from __future__ import annotations

import json
import logging
import sys
import threading
from types import SimpleNamespace

import pytest

from anki_audio_quick_editor import diagnostics_runtime as diagnostics


@pytest.fixture(autouse=True)
def _reset_diagnostics() -> None:
    diagnostics.reset_for_tests()
    yield
    diagnostics.reset_for_tests()


def test_breadcrumb_ring_keeps_recent_events_in_order(tmp_path) -> None:
    diagnostics.configure_runtime(tmp_path, debug_enabled=False)

    for index in range(125):
        diagnostics.record_breadcrumb("event", source="test", context={"index": index})

    events = diagnostics.recent_breadcrumbs(200)
    assert len(events) == 100
    assert [event["context"]["index"] for event in events[:2]] == [25, 26]
    assert [event["seq"] for event in events] == sorted(event["seq"] for event in events)


def test_debug_breadcrumbs_are_written_as_jsonl_and_flushed(tmp_path) -> None:
    diagnostics.configure_runtime(tmp_path, debug_enabled=True)

    event = diagnostics.record_breadcrumb(
        "operation.started",
        source="test",
        operation="test.operation",
        operation_id="op-1",
        context={"value": "ok"},
        flush=True,
    )

    log_path = tmp_path / "anki_audio_quick_editor_events.jsonl"
    parsed = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert parsed[-1]["seq"] == event["seq"]
    assert parsed[-1]["operation_id"] == "op-1"
    assert parsed[-1]["context"] == {"value": "ok"}


def test_exception_boundary_logs_stack_context_and_records_incident(
    tmp_path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    diagnostics.configure_runtime(tmp_path, debug_enabled=True)
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.diagnostics_runtime")

    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:
        incident = diagnostics.capture_exception(
            "test.boundary",
            exc,
            operation="test.operation",
            operation_id="op-err",
            user_message="user saw boom",
            context={"safe": object()},
            log=logging.getLogger("anki_audio_quick_editor.diagnostics_runtime"),
        )

    assert incident["boundary"] == "test.boundary"
    assert incident["operation_id"] == "op-err"
    assert incident["user_message"] == "user saw boom"
    assert incident["context"] == {"safe": "[object]"}
    assert "RuntimeError: boom" in incident["traceback"]
    assert "boundary failed: test.boundary" in caplog.text
    assert "Traceback (most recent call last)" in caplog.text
    assert diagnostics.latest_incident() == incident


def test_support_report_context_includes_crash_paths_and_dirty_session(tmp_path) -> None:
    marker = tmp_path / "anki_audio_quick_editor_session.json"
    marker.write_text(
        json.dumps(
            {
                "session_id": "previous",
                "pid": 123,
                "started_at": "2026-05-19T00:00:00+00:00",
                "updated_at": "2026-05-19T00:01:00+00:00",
                "clean_exit": False,
                "last_event_seq": 7,
            }
        ),
        encoding="utf-8",
    )

    diagnostics.configure_runtime(tmp_path, debug_enabled=True)
    context = diagnostics.support_report_context()

    assert context["crash_forensics"]["previous_dirty_session"]["session_id"] == "previous"
    assert context["crash_forensics"]["event_log_path"].endswith("anki_audio_quick_editor_events.jsonl")
    assert context["crash_forensics"]["crash_log_path"].endswith("anki_audio_quick_editor_crash.log")


def test_process_hooks_log_uncaught_exceptions(tmp_path, caplog: pytest.LogCaptureFixture, monkeypatch) -> None:
    monkeypatch.setattr(sys, "excepthook", sys.__excepthook__)
    monkeypatch.setattr(threading, "excepthook", threading.__excepthook__)
    diagnostics.configure_runtime(tmp_path, debug_enabled=False)
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.diagnostics_runtime")

    try:
        raise ValueError("uncaught")
    except ValueError as exc:
        sys.excepthook(type(exc), exc, exc.__traceback__)

    assert "process.sys_excepthook" in caplog.text
    assert "ValueError: uncaught" in caplog.text

    try:
        raise RuntimeError("thread failed")
    except RuntimeError as exc:
        args = SimpleNamespace(exc_type=type(exc), exc_value=exc, exc_traceback=exc.__traceback__, thread=SimpleNamespace(name="worker-1"))
        threading.excepthook(args)  # type: ignore[arg-type]

    assert "process.threading_excepthook" in caplog.text
    assert "RuntimeError: thread failed" in caplog.text
