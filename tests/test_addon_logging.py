"""Add-on bootstrap logging tests."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from types import SimpleNamespace


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
        addon._release_file_logging()
        _remove_added_handlers(runtime_logger, existing_runtime_handlers)
        _remove_added_handlers(static_logger, existing_static_handlers)


def test_file_logging_records_packaged_release_info(tmp_path: Path, monkeypatch) -> None:
    import anki_audio_quick_editor as addon

    static_logger = logging.getLogger("anki_audio_quick_editor")
    existing_handlers = list(static_logger.handlers)
    monkeypatch.setattr(addon.mw.addonManager, "addonFromModule", lambda _module: "anki_audio_quick_editor")
    monkeypatch.setattr(addon.mw.addonManager, "addonsFolder", lambda _addon_id: str(tmp_path))
    monkeypatch.setattr(addon.mw.addonManager, "getConfig", lambda _addon_id: {"debug_logging": False})
    (tmp_path / "release_info.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "commit_hash": "c" * 40,
                "commit_message": "Ship release diagnostics",
            }
        ),
        encoding="utf-8",
    )

    try:
        addon._setup_file_logging()
        for handler in static_logger.handlers:
            handler.flush()

        log_text = (tmp_path / "anki_audio_quick_editor.log").read_text(encoding="utf-8")
        assert "release provenance: commit=cccccccccccccccccccccccccccccccccccccccc" in log_text
        assert "message=Ship release diagnostics" in log_text
    finally:
        addon._release_file_logging()
        _remove_added_handlers(static_logger, existing_handlers)


def test_file_logging_release_closes_tracked_handler(tmp_path: Path, monkeypatch) -> None:
    import anki_audio_quick_editor as addon

    runtime_name = "1000000002"
    runtime_logger = logging.getLogger(runtime_name)
    static_logger = logging.getLogger("anki_audio_quick_editor")
    existing_runtime_handlers = list(runtime_logger.handlers)
    existing_static_handlers = list(static_logger.handlers)
    monkeypatch.setattr(addon, "__name__", runtime_name)
    monkeypatch.setattr(addon.mw.addonManager, "addonFromModule", lambda _module: runtime_name)
    monkeypatch.setattr(addon.mw.addonManager, "addonsFolder", lambda _addon_id: str(tmp_path))

    try:
        addon._setup_file_logging()
        handler = addon._file_log_handler

        assert handler is not None
        assert isinstance(handler, logging.FileHandler)
        assert handler in runtime_logger.handlers
        assert handler in static_logger.handlers

        addon._release_file_logging()
        addon._release_file_logging()

        assert addon._file_log_handler is None
        assert handler not in runtime_logger.handlers
        assert handler not in static_logger.handlers
        assert handler.stream is None
    finally:
        addon._release_file_logging()
        _remove_added_handlers(runtime_logger, existing_runtime_handlers)
        _remove_added_handlers(static_logger, existing_static_handlers)


def test_preinstall_release_only_for_current_addon(tmp_path: Path, monkeypatch) -> None:
    import anki_audio_quick_editor as addon

    runtime_name = "1000000002"
    runtime_logger = logging.getLogger(runtime_name)
    static_logger = logging.getLogger("anki_audio_quick_editor")
    existing_runtime_handlers = list(runtime_logger.handlers)
    existing_static_handlers = list(static_logger.handlers)
    release_calls: list[str] = []
    monkeypatch.setattr(addon, "__name__", runtime_name)
    monkeypatch.setattr(addon.mw.addonManager, "addonFromModule", lambda _module: runtime_name)
    monkeypatch.setattr(addon.mw.addonManager, "addonsFolder", lambda _addon_id: str(tmp_path))
    monkeypatch.setattr(addon, "release_runtime_files", lambda: release_calls.append("release"))

    try:
        addon._setup_file_logging()
        handler = addon._file_log_handler
        assert handler is not None
        assert isinstance(handler, logging.FileHandler)

        addon._release_install_blocking_files(addon.mw.addonManager, "other_addon")

        assert addon._file_log_handler is handler
        assert release_calls == []

        addon._release_install_blocking_files(addon.mw.addonManager, runtime_name)

        assert addon._file_log_handler is None
        assert release_calls == ["release"]
        assert handler not in runtime_logger.handlers
        assert handler not in static_logger.handlers
        assert handler.stream is None
    finally:
        addon._release_file_logging()
        _remove_added_handlers(runtime_logger, existing_runtime_handlers)
        _remove_added_handlers(static_logger, existing_static_handlers)


def test_postinstall_restore_only_for_current_addon(monkeypatch) -> None:
    import anki_audio_quick_editor as addon

    runtime_name = "1000000002"
    calls: list[str] = []
    manager = SimpleNamespace(addonFromModule=lambda _module: runtime_name)
    monkeypatch.setattr(addon, "__name__", runtime_name)
    monkeypatch.setattr(addon, "_setup_file_logging", lambda: calls.append("file"))
    monkeypatch.setattr(addon, "_setup_diagnostics", lambda: calls.append("diagnostics"))
    monkeypatch.setattr(addon, "_apply_log_level", lambda: calls.append("level"))

    addon._restore_install_logging(manager, "other_addon")
    assert calls == []

    addon._restore_install_logging(manager, runtime_name)
    assert calls == ["file", "diagnostics", "level"]


def _remove_added_handlers(
    logger: logging.Logger,
    existing_handlers: list[logging.Handler],
) -> None:
    for handler in list(logger.handlers):
        if handler in existing_handlers:
            continue
        logger.removeHandler(handler)
        handler.close()
