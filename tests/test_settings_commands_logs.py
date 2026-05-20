from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from anki_audio_quick_editor.settings.commands import (
    handle_settings_command,
)
from anki_audio_quick_editor.support import (
    clear_latest_denoise_support_incident,
    clear_latest_pause_pipeline_support_incident,
)
from tests.settings_command_fixtures import (
    _capture_eval,
    _full_config,
    _make_dialog,
    _parse_callback,
)


class _ImmediateThread:
    def __init__(self, target, daemon=True):
        self._target = target

    def start(self) -> None:
        self._target()


def test_async_support_report_handles_missing_log_file() -> None:
    clear_latest_pause_pipeline_support_incident()
    clear_latest_denoise_support_incident()
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps({"id": "job-1", "op": "support_report", "payload": {"config": _full_config()}})

    with patch("threading.Thread", _ImmediateThread):
        handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog)

    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    report_text = result["result"]["reportText"]
    assert "No external denoise failure has been captured in this session." in report_text
    assert "No pause-shortening failure has been captured in this session." in report_text
    assert "Log file not found:" in report_text or "(log file is empty)" in report_text


def test_async_show_log_file_reveals_path(tmp_path: Path) -> None:
    from aqt import mw

    addon_dir = tmp_path / "addon"
    addon_dir.mkdir()
    log_path = addon_dir / "anki_audio_quick_editor.log"
    log_path.write_text("log", encoding="utf-8")
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps({"id": "job-1", "op": "show_log_file", "payload": {}})

    with (
        patch("threading.Thread", _ImmediateThread),
        patch.object(mw.addonManager, "addonsFolder", return_value=str(addon_dir)),
        patch("anki_audio_quick_editor.file_reveal.reveal_file") as reveal_file,
    ):
        handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog)

    reveal_file.assert_called_once_with(
        log_path,
        missing_message="The Audio Quick Editor log file was not found.",
    )
    done_calls = [call for call in calls if call.startswith("window.onAsyncDone(")]
    result = _parse_callback(done_calls[0], "onAsyncDone")
    assert result["result"] == {"logFilePath": str(log_path)}


def test_async_show_log_file_reports_reveal_failure(tmp_path: Path) -> None:
    from aqt import mw

    addon_dir = tmp_path / "addon"
    addon_dir.mkdir()
    dialog = _make_dialog()
    calls, eval_fn = _capture_eval()
    payload = json.dumps({"id": "job-log", "op": "show_log_file", "payload": {}})

    with (
        patch("threading.Thread", _ImmediateThread),
        patch.object(mw.addonManager, "addonsFolder", return_value=str(addon_dir)),
        patch("anki_audio_quick_editor.file_reveal.reveal_file", side_effect=RuntimeError("missing log")),
    ):
        assert handle_settings_command(f"async_cmd:{payload}", eval_fn, dialog) is True

    result = _parse_callback(calls[-1], "onAsyncDone")
    assert result == {
        "id": "job-log",
        "ok": False,
        "error": "missing log",
    }
