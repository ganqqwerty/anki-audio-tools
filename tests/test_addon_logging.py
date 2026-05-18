"""Add-on bootstrap logging tests."""

from __future__ import annotations

import logging
from pathlib import Path


def test_file_logging_captures_runtime_addon_package_logs(tmp_path: Path, monkeypatch) -> None:
    import anki_audio_quick_editor as addon

    runtime_name = "1000000002"
    runtime_logger = logging.getLogger(runtime_name)
    static_logger = logging.getLogger("anki_audio_quick_editor")
    existing_runtime_handlers = list(runtime_logger.handlers)
    existing_static_handlers = list(static_logger.handlers)
    monkeypatch.setattr(addon, "__name__", runtime_name)
    monkeypatch.setattr(addon.mw.addonManager, "addonFromModule", lambda _module: runtime_name)
    monkeypatch.setattr(addon.mw.addonManager, "addonsFolder", lambda _addon_id: str(tmp_path))
    monkeypatch.setattr(addon.mw.addonManager, "getConfig", lambda _addon_id: {"debug_logging": False})

    try:
        addon._setup_file_logging()
        addon._apply_log_level()
        logging.getLogger(f"{runtime_name}.editor_bridge").info("runtime bridge log")
        for handler in runtime_logger.handlers:
            handler.flush()

        assert "runtime bridge log" in (tmp_path / "anki_audio_quick_editor.log").read_text(
            encoding="utf-8"
        )
    finally:
        _remove_added_handlers(runtime_logger, existing_runtime_handlers)
        _remove_added_handlers(static_logger, existing_static_handlers)


def _remove_added_handlers(
    logger: logging.Logger,
    existing_handlers: list[logging.Handler],
) -> None:
    for handler in list(logger.handlers):
        if handler in existing_handlers:
            continue
        logger.removeHandler(handler)
        handler.close()
