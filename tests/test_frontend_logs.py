"""Tests for shared frontend diagnostic log handling."""

from __future__ import annotations

import logging

import pytest

from anki_audio_quick_editor.diagnostics_runtime import latest_incident, reset_for_tests
from anki_audio_quick_editor.frontend_logs import handle_frontend_log_payload


def test_handle_frontend_log_payload_records_error_incident() -> None:
    reset_for_tests()

    handle_frontend_log_payload(
        {
            "scope": "batch",
            "level": "error",
            "message": "Boom",
            "stack": "trace",
            "context": {"field": "Audio"},
        },
        logger=logging.getLogger("anki_audio_quick_editor.test"),
        default_scope="batch",
        boundary="batch.frontend",
        log_prefix="batch frontend",
    )

    incident = latest_incident()
    assert incident is not None
    assert incident["boundary"] == "batch.frontend"
    assert incident["message"] == "Boom"
    assert incident["traceback"] == "trace"


def test_handle_frontend_log_payload_logs_invalid_payload(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)

    handle_frontend_log_payload(
        "not-json",
        logger=logging.getLogger("anki_audio_quick_editor.test"),
        default_scope="settings",
        boundary="settings.frontend",
        log_prefix="frontend",
        invalid_label="frontend_log",
    )

    assert "frontend_log: invalid payload" in caplog.text
