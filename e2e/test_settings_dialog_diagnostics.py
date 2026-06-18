"""Diagnostics tab E2E tests for the settings dialog."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from e2e.conftest import import_runtime_addon_module
from e2e.helpers import click_selector, wait_for_condition
from e2e.settings_dialog_helpers import open_settings_dialog


def test_diagnostics_can_reveal_support_report_and_open_log_file(anki_mw) -> None:
    support = import_runtime_addon_module(".support")
    file_reveal = import_runtime_addon_module(".file_reveal")

    support.clear_latest_denoise_support_incident()
    support.record_latest_denoise_support_incident(
        operation="rnnoise_denoise",
        media_filename="3d8ca69aee6.mp3",
        source_path="/tmp/3d8ca69aee6.mp3",
        user_message="RNNoise denoise failed.",
        exception_type="AudioProcessingError",
    )
    dialog = open_settings_dialog(anki_mw)

    click_selector(dialog, '[data-testid="settings-tab-diagnostics"]', timeout=5.0)

    report_paths: list[Path] = []
    with patch.object(file_reveal, "reveal_file", lambda path, **_kwargs: report_paths.append(Path(path))):
        click_selector(dialog, '[data-testid="reveal-support-report"]', timeout=5.0)
        wait_for_condition(
            lambda: bool(report_paths) and report_paths[0].is_file(),
            timeout=30.0,
            message="Support report file was not revealed",
        )

    report_text = report_paths[0].read_text(encoding="utf-8")
    assert report_paths[0].name.startswith("support-report-")
    assert report_paths[0].parent.name == "support_reports"
    assert "3d8ca69aee6.mp3" in report_text
    assert "RNNoise denoise failed." in report_text

    revealed_logs: list[str] = []
    with patch.object(file_reveal, "reveal_file", lambda path, **_kwargs: revealed_logs.append(str(path))):
        click_selector(dialog, '[data-testid="show-log-file"]', timeout=5.0)
        wait_for_condition(lambda: bool(revealed_logs), timeout=5.0)

    assert revealed_logs[0].endswith("anki_audio_quick_editor.log")


def test_diagnostics_can_open_check_media(anki_mw) -> None:
    dialog = open_settings_dialog(anki_mw)

    with patch("aqt.mediacheck.check_media_db") as check_media_db:
        click_selector(dialog, '[data-testid="settings-tab-diagnostics"]', timeout=5.0)
        click_selector(dialog, '[data-testid="check-media"]', timeout=5.0)
        wait_for_condition(lambda: check_media_db.called, timeout=5.0)

    check_media_db.assert_called_once_with(anki_mw)
