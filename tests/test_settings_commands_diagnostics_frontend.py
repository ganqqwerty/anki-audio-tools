from __future__ import annotations

import logging
from unittest.mock import patch

import pytest

from anki_audio_quick_editor.settings.commands import handle_settings_command
from tests.settings_command_fixtures import (
    _bridge_command,
    _capture_eval,
    _make_dialog,
)


def test_frontend_log_handles_invalid_payload(caplog: pytest.LogCaptureFixture) -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    caplog.set_level(logging.WARNING, logger="anki_audio_quick_editor.settings.commands")

    assert handle_settings_command(_bridge_command("frontend.log", "not-json"), eval_fn, dialog) is True
    assert "frontend_log: invalid payload" in caplog.text


@pytest.mark.parametrize(
    ("level", "expected_level"),
    [
        ("debug", logging.DEBUG),
        ("info", logging.INFO),
        ("warn", logging.WARNING),
        ("error", logging.ERROR),
        ("unknown", logging.INFO),
    ],
)
def test_frontend_log_renders_level_message_and_context(
    level: str,
    expected_level: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    caplog.set_level(logging.DEBUG, logger="anki_audio_quick_editor.settings.commands")
    payload = {"level": level, "message": "loaded", "context": {"tab": "diagnostics"}}

    assert handle_settings_command(_bridge_command("frontend.log", payload), eval_fn, dialog) is True

    record = caplog.records[-1]
    assert record.levelno == expected_level
    assert record.message == "frontend: loaded | {'tab': 'diagnostics'}"


def test_frontend_error_payload_records_stack_for_support_report(
    caplog: pytest.LogCaptureFixture,
) -> None:
    from anki_audio_quick_editor.diagnostics_runtime import (
        latest_incident,
        reset_for_tests,
    )

    reset_for_tests()
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    caplog.set_level(logging.ERROR, logger="anki_audio_quick_editor.settings.commands")
    payload = {
        "scope": "settings",
        "level": "error",
        "message": "frontend exploded",
        "stack": "Error: frontend exploded\n    at SettingsApp",
        "context": {"tab": "diagnostics"},
    }

    assert handle_settings_command(_bridge_command("frontend.log", payload), eval_fn, dialog) is True

    assert "Error: frontend exploded" in caplog.text
    incident = latest_incident()
    assert incident is not None
    assert incident["boundary"] == "settings.frontend"
    assert incident["traceback"] == "Error: frontend exploded\n    at SettingsApp"


def test_settings_open_url_opens_trusted_external_url() -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()
    url = "https://ganqqwerty.github.io/anki-audio-tools/errors/AQE-RUNTIME-001/"

    with patch("anki_audio_quick_editor.external_links.open_external_url") as open_external_url:
        assert (
            handle_settings_command(
                _bridge_command("webview.open_url", {"url": url}),
                eval_fn,
                dialog,
            )
            is True
        )

    open_external_url.assert_called_once_with(url)


def test_settings_open_url_rejects_untrusted_external_url() -> None:
    dialog = _make_dialog()
    _, eval_fn = _capture_eval()

    with patch("anki_audio_quick_editor.external_links.open_external_url") as open_external_url:
        assert handle_settings_command(
            _bridge_command("webview.open_url", {"url": "https://example.invalid/"}),
            eval_fn,
            dialog,
        ) is True

    open_external_url.assert_not_called()
