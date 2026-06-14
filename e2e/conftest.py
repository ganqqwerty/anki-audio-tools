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
from scripts.dev_tasks.e2e_preflight import ensure_e2e_runtime_artifacts

importlib.import_module("anki.collection")
aqt = importlib.import_module("aqt")

PROJECT_ROOT = Path(__file__).parent.parent
ADDON_DIR = PROJECT_ROOT / "addon" / "anki_audio_quick_editor"
ADDON_NUMERIC_ID = "1000000002"


def import_runtime_addon_module(module_suffix: str = ""):
    """Import the add-on as Anki loads it, using the installed numeric package id."""
    if module_suffix and not module_suffix.startswith("."):
        raise ValueError("module_suffix must be empty or start with '.'")
    return importlib.import_module(f"{ADDON_NUMERIC_ID}{module_suffix}")


def runtime_addon_import_path(module_suffix: str, attr: str | None = None) -> str:
    """Return a dotted import path rooted at the runtime numeric add-on package."""
    path = f"{ADDON_NUMERIC_ID}{module_suffix}"
    return f"{path}.{attr}" if attr else path


def _default_config() -> dict:
    return {
        "_config_version": 23,
        "enabled": True,
        "debug_logging": False,
        "show_ffmpeg_commands": False,
        "repeat_playback_by_default": True,
        "repeat_pause_seconds": 0.0,
        "chorusing_pause_seconds": 0.0,
        "chorusing_auto_advance_by_default": False,
        "chorusing_auto_advance_repeats": 3,
        "voice_recording_countdown_seconds": 0,
        "share_target": "litterbox",
        "show_graph_by_default": True,
        "selection_marker_shift_buttons_enabled": False,
        "visible_editor_buttons": [
            "aqe:play",
            "aqe:analyze",
            "aqe:chorusing-practice",
            "aqe:chorusing-previous",
            "aqe:chorusing-next",
            "aqe:show-file",
            "aqe:share",
            "aqe:preset",
            "aqe:remove-pauses",
            "aqe:denoise-standard",
            "aqe:slower",
            "aqe:faster",
            "aqe:delete-selection",
            "aqe:delete-rest",
            "aqe:undo",
            "aqe:redo",
            "aqe:settings",
        ],
        "editor_button_modes": {
            "aqe:play": "icon",
            "aqe:analyze": "icon",
            "aqe:chorusing-practice": "icon",
            "aqe:chorusing-previous": "icon",
            "aqe:chorusing-next": "icon",
            "aqe:record-voice": "icon",
            "aqe:play-recording": "icon",
            "aqe:show-file": "icon",
            "aqe:share": "icon",
            "aqe:preset": "text",
            "aqe:convert": "text",
            "aqe:remove-pauses": "text",
            "aqe:denoise-standard": "text",
            "aqe:pitch-hum": "text",
            "aqe:slower": "icon",
            "aqe:faster": "icon",
            "aqe:delete-selection": "icon",
            "aqe:delete-rest": "icon",
            "aqe:volume-down": "icon",
            "aqe:volume-up": "icon",
            "aqe:undo": "icon",
            "aqe:redo": "icon",
            "aqe:settings": "icon",
        },
        "audio_processing_presets": [],
        "speed_step": 1.5,
        "min_speed": 0.2,
        "max_speed": 5.0,
        "volume_step_db": 15.0,
        "min_volume_db": -40.0,
        "max_volume_db": 40.0,
        "pause_detection_algorithm": "silencedetect",
        "pause_aggressiveness": "normal",
        "pause_silencedetect_threshold_db": -45.0,
        "pause_silencedetect_min_silence_seconds": 0.3,
        "pause_silencedetect_min_speech_seconds": 0.1,
        "pause_silencedetect_preprocess_denoise": True,
        "pause_silero_threshold": 0.5,
        "pause_silero_min_silence_seconds": 0.45,
        "pause_silero_min_speech_seconds": 0.1,
        "pause_silero_preprocess_denoise": False,
        "output_format": "source",
        # Let e2e exercise the add-on's runtime-aware ffmpeg lookup.
        "ffmpeg_path": "",
        "deep_filter_post_filter": True,
        "dpdfnet_attn_limit_db": 12.0,
        "denoise_algorithm": "standard",
        "pitch_hum_mode": "direct",
    }


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


@pytest.fixture(scope="session")
def anki_base(tmp_path_factory):
    try:
        ensure_e2e_runtime_artifacts()
    except RuntimeError as exc:
        pytest.fail(str(exc))
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
            ".downloads",
            "aqe_artifacts",
            "meta.json",
        ),
    )
    os.environ["ANKI_BASE"] = str(base)
    yield base


@pytest.fixture(scope="session")
def qapp(anki_base):
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
            import_runtime_addon_module(suffix)
        except Exception:
            pass

    addon_manager = aqt.mw.addonManager
    addon_manager.writeConfig(ADDON_NUMERIC_ID, _default_config())
    yield aqt.mw


@pytest.fixture(scope="session")
def anki_mw(anki_app):
    return anki_app


@pytest.fixture
def ffmpeg_config(anki_mw):
    """Return config that points at runtime-managed ffmpeg, or fail when unavailable."""
    del anki_mw
    audio_processing_config = import_runtime_addon_module(".audio_state").AudioProcessingConfig
    audio_processor = import_runtime_addon_module(".audio_processor")

    try:
        return _runtime_ffmpeg_config(audio_processor, audio_processing_config)
    except Exception as exc:
        pytest.fail(f"ffmpeg and ffprobe are required for audio processing e2e tests: {exc}")


@pytest.fixture(autouse=True)
def _fail_on_unfaked_native_playback(monkeypatch):
    from aqt.sound import av_player
    from e2e.editor_playback_helpers import fake_playback_active

    original_play_tags = av_player.play_tags
    original_stop = av_player.stop_and_clear_queue

    def guarded_play_tags(tags):
        if not fake_playback_active():
            return None
        return original_play_tags(tags)

    def guarded_stop_and_clear_queue():
        if fake_playback_active():
            return original_stop()
        return None

    monkeypatch.setattr(av_player, "play_tags", guarded_play_tags)
    monkeypatch.setattr(av_player, "stop_and_clear_queue", guarded_stop_and_clear_queue)


def _runtime_ffmpeg_config(audio_processor, audio_processing_config):
    """Build e2e audio config from the add-on's runtime-aware ffmpeg lookup."""
    configured = os.environ.get("AQE_FFMPEG_PATH") or os.environ.get("FFMPEG_PATH") or ""
    ffmpeg = audio_processor.find_ffmpeg(configured)
    audio_processor.find_ffprobe(ffmpeg)
    return audio_processing_config(ffmpeg_path=str(ffmpeg))


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
