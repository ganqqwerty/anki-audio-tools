"""E2E test setup for Anki Audio Quick Editor."""

from __future__ import annotations

import copy
import importlib
import logging
import os
import shutil
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


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    setattr(item, f"rep_{call.when}", outcome.get_result())


def import_runtime_addon_module(module_suffix: str = ""):
    """Import the add-on as Anki loads it, using the installed numeric package id."""
    if module_suffix and not module_suffix.startswith("."):
        raise ValueError("module_suffix must be empty or start with '.'")
    return importlib.import_module(f"{ADDON_NUMERIC_ID}{module_suffix}")


def runtime_addon_import_path(module_suffix: str, attr: str | None = None) -> str:
    """Return a dotted import path rooted at the runtime numeric add-on package."""
    path = f"{ADDON_NUMERIC_ID}{module_suffix}"
    return f"{path}.{attr}" if attr else path


def _canonical_default_config(mw) -> dict[str, object]:
    """Build the E2E baseline through the production defaults and migration path."""
    migration = import_runtime_addon_module(".config_migration")
    ffmpeg_defaults = import_runtime_addon_module(".ffmpeg_defaults")
    defaults = ffmpeg_defaults.with_platform_ffmpeg_default(
        mw.addonManager.addonConfigDefaults(ADDON_NUMERIC_ID) or {}
    )
    migrated, _changed = migration.migrate_config({}, defaults)
    return migrated


def _save_config_through_runtime_path(config: dict[str, object]) -> None:
    """Apply E2E config through the same backend path as the Settings Save command."""
    commands = import_runtime_addon_module(".settings.commands")
    bridge = import_runtime_addon_module(".webview_bridge")

    class _AcceptedDialog:
        accepted = False

        def accept(self) -> None:
            self.accepted = True

    dialog = _AcceptedDialog()
    errors: list[str] = []
    commands._handle_settings_save(
        bridge.WebviewBridgeCommand("settings.save", copy.deepcopy(config)),
        errors.append,
        dialog,
    )
    assert errors == []
    assert dialog.accepted


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
        app.closeAllWindows()
        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.sendPostedEvents()
        app.processEvents()
        app.quit()


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
        import_runtime_addon_module(suffix)

    addon_manager = aqt.mw.addonManager
    addon_manager.writeConfig(ADDON_NUMERIC_ID, _canonical_default_config(aqt.mw))
    yield aqt.mw


@pytest.fixture(scope="session")
def anki_mw(anki_app):
    return anki_app


@pytest.fixture(scope="session")
def e2e_process_baseline(anki_mw):
    """Capture desktop state that must survive every randomized E2E item."""
    from PyQt6.QtWidgets import QApplication

    return {
        "clipboard": QApplication.clipboard().text(),
        "theme": anki_mw.pm.theme(),
    }


@pytest.fixture(autouse=True)
def _restore_canonical_config(anki_mw, request):
    """Prevent randomized E2E items from sharing mutable add-on configuration."""
    if request.node.get_closest_marker("preserve_e2e_config") is not None:
        yield
        return
    baseline = _canonical_default_config(anki_mw)
    _save_config_through_runtime_path(baseline)
    yield
    _save_config_through_runtime_path(baseline)


def _assert_window_leak_policy(request, leaked) -> None:
    sentinel = request.node.get_closest_marker("isolation_sentinel")
    if sentinel is None:
        assert not leaked, "E2E item leaked visible top-level windows: " + ", ".join(
            f"{type(widget).__name__}({widget.windowTitle()!r})" for widget in leaked
        )
        return
    expected_titles = [arg for arg in sentinel.args if isinstance(arg, str)]
    assert [widget.windowTitle() for widget in leaked] == expected_titles


@pytest.fixture(autouse=True)
def _isolate_process_global_state(anki_mw, request):
    from aqt import gui_hooks
    from PyQt6 import sip
    from PyQt6.QtWidgets import QApplication

    support = import_runtime_addon_module(".support")
    clipboard = QApplication.clipboard()
    clipboard_text = clipboard.text()
    original_theme = anki_mw.pm.theme()
    baseline_widgets = {id(widget) for widget in QApplication.topLevelWidgets()}
    baseline_theme_hooks = {id(callback) for callback in gui_hooks.theme_did_change._hooks}
    for clear in (
        support.clear_latest_denoise_support_incident,
        support.clear_latest_spleeter_support_incident,
        support.clear_latest_pause_pipeline_support_incident,
    ):
        clear()
    yield

    clipboard.setText(clipboard_text)
    if anki_mw.pm.theme() != original_theme:
        anki_mw.set_theme(original_theme)
    if anki_mw.state != "deckBrowser":
        anki_mw.moveToState("deckBrowser")
    for clear in (
        support.clear_latest_denoise_support_incident,
        support.clear_latest_spleeter_support_incident,
        support.clear_latest_pause_pipeline_support_incident,
    ):
        clear()

    leaked = [
        widget
        for widget in QApplication.topLevelWidgets()
        if id(widget) not in baseline_widgets and widget.isVisible()
    ]
    for widget in leaked:
        widget.close()
        widget.deleteLater()
    QApplication.processEvents()
    newly_dead_theme_hooks = []
    for callback in list(gui_hooks.theme_did_change._hooks):
        owner = getattr(callback, "__self__", None)
        if owner is not None and sip.isdeleted(owner):
            if id(callback) not in baseline_theme_hooks:
                newly_dead_theme_hooks.append(callback)
            gui_hooks.theme_did_change.remove(callback)
    report = getattr(request.node, "rep_call", None)
    if report is not None and report.passed:
        _assert_window_leak_policy(request, leaked)
        assert not newly_dead_theme_hooks, (
            "E2E item left theme hooks bound to deleted WebViews: "
            + ", ".join(repr(callback) for callback in newly_dead_theme_hooks)
        )


@pytest.fixture(autouse=True)
def _fail_on_unexpected_error_channels(request):
    from PyQt6.QtCore import QtMsgType, qInstallMessageHandler

    from e2e.harness_error_policy import unexpected_messages

    python_errors: list[str] = []
    qt_errors: list[str] = []

    class _ErrorHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            del self
            if record.levelno >= logging.ERROR and (
                record.name.startswith(ADDON_NUMERIC_ID)
                or record.name.startswith("anki_audio_quick_editor")
            ):
                python_errors.append(f"{record.name}: {record.getMessage()}")

    def qt_message_handler(message_type, _context, message) -> None:
        if message_type in {QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg}:
            qt_errors.append(str(message))

    handler = _ErrorHandler()
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    previous_qt_handler = qInstallMessageHandler(qt_message_handler)
    yield
    qInstallMessageHandler(previous_qt_handler)
    root_logger.removeHandler(handler)

    report = getattr(request.node, "rep_call", None)
    if report is not None and not report.passed:
        return
    allowed_patterns = tuple(
        pattern
        for marker in request.node.iter_markers("allow_error_log")
        for pattern in marker.args
        if isinstance(pattern, str)
    )
    unexpected = unexpected_messages(
        [*python_errors, *(f"Qt critical: {message}" for message in qt_errors)],
        allowed_patterns,
    )
    assert not unexpected, (
        "Unexpected E2E error channel output. Fix the failure or add a narrow "
        "allow_error_log regex with a reason:\n" + "\n".join(unexpected)
    )
@pytest.fixture
def ffmpeg_config(anki_mw):
    """Return config that points at runtime-managed ffmpeg, or fail when unavailable."""
    del anki_mw
    audio_processing_config = import_runtime_addon_module(".audio_state").AudioProcessingConfig
    audio_processor = import_runtime_addon_module(".audio_processor")
    missing_ffmpeg_error = import_runtime_addon_module(".errors").MissingFfmpegError

    try:
        return _runtime_ffmpeg_config(audio_processor, audio_processing_config)
    except missing_ffmpeg_error as exc:
        pytest.fail(f"ffmpeg and ffprobe are required for audio processing e2e tests: {exc}")


def _native_operation_guard(operation, original, *, allowed, operation_log, fake_playback_active):
    def guarded(*args, **kwargs):
        if fake_playback_active():
            return original(*args, **kwargs)
        if allowed:
            operation_log.append(operation)
            return None
        raise AssertionError(
            f"Unexpected native av_player {operation!r} operation. "
            "Use browser audio, a scoped fake, or an exact allow_native_playback operation contract."
        )

    return guarded


def _native_play_tags_guard(original, *, allowed, operation_log, fake_playback_active):
    def guarded(tags):
        if not fake_playback_active():
            if allowed:
                operation_log.append("start")
                return None
            pytest.fail(
                "Unexpected native av_player.play_tags() call outside _record_fake_playback. "
                "Editor playback tests must either use browser audio or explicitly fake legacy native playback."
            )
        return original(tags)

    return guarded


@pytest.fixture(autouse=True)
def _guard_unfaked_native_playback(monkeypatch, request):
    from aqt.sound import av_player

    from e2e.editor_playback_helpers import fake_playback_active

    guarded_methods = {
        "stop": ("stop_and_clear_queue", av_player.stop_and_clear_queue),
        "seek": ("seek_relative", av_player.seek_relative),
        "pause": ("toggle_pause", av_player.toggle_pause),
    }
    operation_log: list[str] = []
    native_marker = request.node.get_closest_marker("allow_native_playback")
    native_playback_allowed = native_marker is not None

    monkeypatch.setattr(
        av_player,
        "play_tags",
        _native_play_tags_guard(
            av_player.play_tags,
            allowed=native_playback_allowed,
            operation_log=operation_log,
            fake_playback_active=fake_playback_active,
        ),
    )
    for operation, (name, original) in guarded_methods.items():
        monkeypatch.setattr(
            av_player,
            name,
            _native_operation_guard(
                operation,
                original,
                allowed=native_playback_allowed,
                operation_log=operation_log,
                fake_playback_active=fake_playback_active,
            ),
        )
    yield
    if native_playback_allowed:
        expected = [value for value in native_marker.args if isinstance(value, str)]
        if expected:
            assert operation_log == expected, (
                f"native playback operation mismatch: expected {expected}, observed {operation_log}"
            )
        else:
            assert operation_log, "allow_native_playback marker recorded no native operations"
            assert operation_log[0] == "start", "approved native playback did not start with play_tags"


def _runtime_ffmpeg_config(audio_processor, audio_processing_config):
    """Build e2e audio config from the add-on's runtime-aware ffmpeg lookup."""
    configured = os.environ.get("AQE_FFMPEG_PATH") or os.environ.get("FFMPEG_PATH") or ""
    ffmpeg = audio_processor.find_ffmpeg(configured)
    audio_processor.find_ffprobe(ffmpeg)
    return audio_processing_config(ffmpeg_path=str(ffmpeg))
