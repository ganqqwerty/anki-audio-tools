"""E2E test setup for Anki Audio Quick Editor."""

from __future__ import annotations

import importlib
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("aqt")
pytest.importorskip("anki.collection")

ADDON_DIR = Path(__file__).parent.parent / "addon" / "anki_audio_quick_editor"
ADDON_NUMERIC_ID = "1000000002"


def _default_config() -> dict:
    return {
        "_config_version": 3,
        "enabled": True,
        "debug_logging": False,
        "show_ffmpeg_commands": False,
        "manual_trim_small_ms": 100,
        "manual_trim_large_ms": 500,
        "speed_step": 0.05,
        "min_speed": 0.75,
        "max_speed": 1.5,
        "edge_silence_threshold_db": -35,
        "edge_silence_min_ms": 100,
        "internal_pause_threshold_ms": 300,
        "internal_pause_target_gap_ms": 100,
        "output_format": "mp3",
        "ffmpeg_path": "",
    }


def _find_ffmpeg() -> Path | None:
    configured = os.environ.get("AQE_FFMPEG_PATH") or os.environ.get("FFMPEG_PATH")
    candidates = [
        Path(configured).expanduser() if configured else None,
        Path("/opt/homebrew/bin/ffmpeg"),
        Path("/usr/local/bin/ffmpeg"),
        Path(found) if (found := shutil.which("ffmpeg")) else None,
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    return None


def _process_events_until(predicate, timeout_s: float, message: str) -> None:
    from PyQt6.QtWidgets import QApplication

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        QApplication.processEvents()
        if predicate():
            return
        time.sleep(0.02)
    pytest.fail(message)


def _start_anki_runtime() -> None:
    import aqt
    from aqt.profiles import ProfileManager

    def _skip_lang_dialog(self, idx: int) -> None:
        del idx
        self.meta["defaultLang"] = "en_US"

    startup_argv = ["anki"]
    with (
        patch.object(ProfileManager, "setDefaultLang", _skip_lang_dialog),
        patch.object(aqt.AnkiApp, "secondInstance", lambda self: False),
        patch.object(sys, "argv", startup_argv.copy()),
    ):
        aqt._run(exec=False, argv=startup_argv)


@pytest.fixture(scope="session")
def anki_base(tmp_path_factory):
    base = tmp_path_factory.mktemp("anki_base")
    addons = base / "addons21"
    addons.mkdir()
    (addons / ADDON_NUMERIC_ID).symlink_to(ADDON_DIR.resolve())
    os.environ["ANKI_BASE"] = str(base)
    yield base


@pytest.fixture(scope="session")
def qapp(anki_base):
    import aqt
    from PyQt6.QtCore import QEvent
    from PyQt6.QtWidgets import QApplication

    original_event = aqt.AnkiApp.event

    def _event_without_file_open(self, event):
        if event is not None and event.type() == QEvent.Type.FileOpen:
            return True
        return original_event(self, event)

    with patch.object(aqt.AnkiApp, "event", _event_without_file_open):
        app = QApplication.instance()
        if app is None or not isinstance(app, aqt.AnkiApp):
            _start_anki_runtime()
            app = QApplication.instance()
        if app is None or not isinstance(app, aqt.AnkiApp):
            raise RuntimeError(
                "E2E tests require a real aqt.AnkiApp; "
                f"got {type(app).__name__ if app is not None else 'None'} instead."
            )
        yield app


@pytest.fixture(scope="session")
def anki_app(anki_base, qapp):
    import aqt

    _process_events_until(
        lambda: aqt.mw is not None and aqt.mw.col is not None,
        timeout_s=10.0,
        message="Anki did not finish initializing within 10s",
    )
    aqt.mw.hide()

    for suffix in (
        "",
        ".settings",
        ".settings.commands",
        ".settings.initial_state",
        ".editor_integration",
    ):
        try:
            importlib.import_module(f"{ADDON_NUMERIC_ID}{suffix}")
        except Exception:
            pass

    for key in list(sys.modules.keys()):
        if key == ADDON_NUMERIC_ID or key.startswith(ADDON_NUMERIC_ID + "."):
            alias = "anki_audio_quick_editor" + key[len(ADDON_NUMERIC_ID):]
            if alias not in sys.modules:
                sys.modules[alias] = sys.modules[key]

    addon_manager = aqt.mw.addonManager
    addon_manager.writeConfig(ADDON_NUMERIC_ID, _default_config())
    yield aqt.mw


@pytest.fixture(scope="session")
def anki_mw(anki_app):
    return anki_app


@pytest.fixture
def ffmpeg_config():
    """Return config that points at real ffmpeg, or skip when unavailable."""
    from anki_audio_quick_editor.audio_state import AudioProcessingConfig

    ffmpeg = _find_ffmpeg()
    if ffmpeg is None or not ffmpeg.with_name("ffprobe").is_file():
        pytest.skip("ffmpeg and ffprobe are required for audio processing e2e tests")
    return AudioProcessingConfig(ffmpeg_path=str(ffmpeg))


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    """Force-exit after pytest prints the summary to avoid Qt WebEngine teardown hangs."""
    del session, exitstatus
    yield

    for stream in (sys.stdout, sys.stderr):
        flush = getattr(stream, "flush", None)
        if callable(flush):
            flush()

    try:
        result = subprocess.run(
            ["pgrep", "-P", str(os.getpid())],
            capture_output=True,
            text=True,
            timeout=2,
        )
        for pid_str in result.stdout.split():
            try:
                os.kill(int(pid_str), signal.SIGKILL)
            except (ValueError, OSError):
                pass
    except Exception:
        pass

    os._exit(0)
