"""E2E test setup for Anki Audio Quick Editor."""

from __future__ import annotations

import hashlib
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

PROJECT_ROOT = Path(__file__).parent.parent
ADDON_DIR = PROJECT_ROOT / "addon" / "anki_audio_quick_editor"
ADDON_NUMERIC_ID = "1000000002"
LOCAL_DPDFNET_BUILD = Path("/Users/iuriikatkov/IdeaProjects/DPDFNet/dist/lite/dpdfnet")


def _default_config() -> dict:
    return {
        "_config_version": 16,
        "enabled": True,
        "debug_logging": False,
        "show_ffmpeg_commands": False,
        "repeat_playback_by_default": False,
        "repeat_pause_seconds": 0.0,
        "show_graph_by_default": False,
        "manual_trim_small_ms": 100,
        "manual_trim_large_ms": 500,
        "speed_step": 0.05,
        "min_speed": 0.75,
        "max_speed": 1.5,
        "volume_step_db": 3.0,
        "min_volume_db": -24.0,
        "max_volume_db": 24.0,
        "internal_pause_silence_threshold_db": -45,
        "internal_pause_threshold_ms": 300,
        "internal_pause_target_gap_ms": 100,
        "output_format": "mp3",
        "ffmpeg_path": "",
        "deep_filter_path": "",
        "deep_filter_post_filter": True,
        "dpdfnet_attn_limit_db": 12.0,
        "denoise_algorithm": "standard",
        "pitch_hum_mode": "direct",
        "pause_aggressiveness": "normal",
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

    # noinspection PyUnusedLocal
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


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _dpdfnet_source_candidate() -> Path | None:
    configured = os.environ.get("AQE_DPDFNET_PATH")
    candidates = [
        Path(configured).expanduser() if configured else None,
        LOCAL_DPDFNET_BUILD,
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    return None


def _stage_dpdfnet_bundle(addon_dir: Path) -> None:
    from scripts import release_assets

    if release_assets.current_target_key() != "macos-arm64":
        return

    cache_path = PROJECT_ROOT / ".release-assets" / "bin" / "macos-arm64" / "dpdfnet"
    if cache_path.is_file():
        release_assets.stage_assets(
            release_assets.load_lock(),
            destination=addon_dir / "bin",
            target_keys=["macos-arm64"],
            tool_names=["dpdfnet"],
        )
        return

    source_path = _dpdfnet_source_candidate()
    if source_path is None:
        return

    lock = release_assets.load_lock()
    expected_sha = lock["targets"]["macos-arm64"]["tools"]["dpdfnet"]["sha256"]
    if _sha256(source_path) != expected_sha:
        return

    destination = addon_dir / "bin" / "macos-arm64" / "dpdfnet"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)
    destination.chmod(destination.stat().st_mode | 0o755)

@pytest.fixture(scope="session")
def anki_base(tmp_path_factory):
    base = tmp_path_factory.mktemp("anki_base")
    addons = base / "addons21"
    addons.mkdir()
    addon_dir = addons / ADDON_NUMERIC_ID
    shutil.copytree(
        ADDON_DIR.resolve(),
        addon_dir,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
            "*.log",
            "aqe_artifacts",
            "meta.json",
        ),
    )
    _stage_dpdfnet_bundle(addon_dir)
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


# noinspection PyUnusedLocal
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    """Force-exit after pytest prints the summary to avoid Qt WebEngine teardown hangs."""
    del session
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

    os._exit(int(exitstatus))
