"""Editor frontend logging callback tests."""

from __future__ import annotations

import logging
from collections.abc import Callable

import pytest

from anki_audio_quick_editor.editor_integration import _handle_bridge_command


def test_editor_frontend_log_callback_records_levels(caplog: pytest.LogCaptureFixture) -> None:
    class Web:
        def evalWithCallback(self, _expression: str, callback: Callable[[object], None]) -> None:
            callback({"level": "warn", "message": "drag canceled", "context": {"ord": 1}})

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = Web()
    caplog.set_level(logging.DEBUG, logger="anki_audio_quick_editor.editor_integration")

    _handle_bridge_command(editor, "aqe:frontend-log")

    record = caplog.records[-1]
    assert record.levelno == logging.WARNING
    assert record.message == "editor frontend: drag canceled | {'ord': 1}"


def test_invalid_editor_frontend_log_payload_is_ignored(caplog: pytest.LogCaptureFixture) -> None:
    class Web:
        def evalWithCallback(self, _expression: str, callback: Callable[[object], None]) -> None:
            callback({"level": "warn", "context": {"missing": "message"}})

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = Web()
    caplog.set_level(logging.WARNING, logger="anki_audio_quick_editor.editor_integration")

    _handle_bridge_command(editor, "aqe:frontend-log")

    assert "editor frontend_log: invalid payload" in caplog.text


def test_editor_frontend_error_payload_records_stack(caplog: pytest.LogCaptureFixture) -> None:
    from anki_audio_quick_editor.diagnostics_runtime import (
        latest_incident,
        reset_for_tests,
    )

    reset_for_tests()

    class Web:
        def evalWithCallback(self, _expression: str, callback: Callable[[object], None]) -> None:
            callback(
                {
                    "scope": "editor",
                    "level": "error",
                    "message": "editor exploded",
                    "stack": "Error: editor exploded\n    at EditorControls",
                    "context": {"ord": 1},
                }
            )

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = Web()
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.editor_integration")

    _handle_bridge_command(editor, "aqe:frontend-log")

    assert "Error: editor exploded" in caplog.text
    incident = latest_incident()
    assert incident is not None
    assert incident["boundary"] == "editor.frontend"
    assert incident["traceback"] == "Error: editor exploded\n    at EditorControls"
