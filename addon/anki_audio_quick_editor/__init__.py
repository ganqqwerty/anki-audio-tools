"""Anki Audio Quick Editor add-on package."""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

from ._version import __version__ as __version__
from .diagnostics_runtime import (
    capture_exception,
    configure_runtime,
    record_breadcrumb,
    release_runtime_files,
    set_debug_enabled,
)
from .release_info import read_release_info

if TYPE_CHECKING:
    from .editor_runtime import SettingsLifecycleCallbacks

logging.basicConfig(level=logging.INFO, format="%(name)s: %(levelname)s: %(message)s")
logger = logging.getLogger("anki_audio_quick_editor")
logger.setLevel(logging.INFO)

_VENDOR_DIR = Path(__file__).parent / "vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

def _maybe_attach_debugger(*, wait_for_client: bool = True) -> None:
    """Attach debugpy when requested without making it a shipped dependency."""
    if not os.environ.get("DEBUG_ANKI"):
        return
    try:
        import debugpy
    except ImportError:
        logger.warning("DEBUG_ANKI is set, but debugpy is not installed; continuing without debugger.")
        return

    debugpy.listen(5678)
    logger.info("debugpy listening on port 5678")
    if wait_for_client:
        debugpy.wait_for_client()
        logger.info("debugger attached")


_maybe_attach_debugger()

from aqt import gui_hooks, mw  # noqa: E402
from aqt.qt import qconnect  # noqa: E402

_settings_dialog = None
_file_log_handler: logging.Handler | None = None


def _addon_loggers() -> tuple[logging.Logger, ...]:
    runtime_logger = logging.getLogger(__name__)
    if runtime_logger.name == logger.name:
        return (logger,)
    return logger, runtime_logger


def _migrate_config() -> None:
    """Deep-merge defaults into the user's config and stamp the schema version."""
    from .config_migration import migrate_config
    from .ffmpeg_defaults import with_platform_ffmpeg_default

    addon_id = mw.addonManager.addonFromModule(__name__)
    user_config = mw.addonManager.getConfig(addon_id) or {}
    defaults = with_platform_ffmpeg_default(mw.addonManager.addonConfigDefaults(addon_id) or {})
    migrated, changed = migrate_config(user_config, defaults)
    if changed:
        mw.addonManager.writeConfig(addon_id, migrated)
        logger.info("config migrated to version %s", migrated.get("_config_version"))


def _setup_file_logging() -> None:
    """Attach a rotating file handler inside the add-on directory."""
    global _file_log_handler

    _release_file_logging()
    addon_id = mw.addonManager.addonFromModule(__name__)
    addon_dir = Path(mw.addonManager.addonsFolder(addon_id))
    addon_dir.mkdir(parents=True, exist_ok=True)
    log_file = addon_dir / "anki_audio_quick_editor.log"

    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    for target_logger in _addon_loggers():
        target_logger.addHandler(handler)
    _file_log_handler = handler
    logger.debug("file logging initialized at %s", log_file)
    _log_release_info(addon_dir)


def _release_file_logging() -> None:
    """Detach and close the add-on file logger before Anki replaces the folder."""
    global _file_log_handler

    handler = _file_log_handler
    if handler is None:
        return
    for target_logger in _addon_loggers():
        if handler in target_logger.handlers:
            target_logger.removeHandler(handler)
    try:
        handler.flush()
    except (OSError, ValueError):
        pass
    try:
        handler.close()
    except (OSError, ValueError):
        pass
    _file_log_handler = None


def _log_release_info(addon_dir: Path) -> None:
    """Log packaged release provenance when available."""
    provenance = read_release_info(addon_dir)
    commit_hash = provenance["commit_hash"]
    commit_message = provenance["commit_message"]
    if commit_hash:
        logger.info("release provenance: commit=%s message=%s", commit_hash, commit_message)
    else:
        logger.info("release provenance: release_info.json not available")


def _is_this_addon(module: str, manager: object) -> bool:
    try:
        return bool(module == manager.addonFromModule(__name__))  # type: ignore[attr-defined]
    except (AttributeError, TypeError):
        return module == __name__.split(".", 1)[0]


def _release_install_blocking_files(manager: object, module: str) -> None:
    """Release open files before Anki deletes this add-on during install."""
    if not _is_this_addon(module, manager):
        return
    _release_file_logging()
    release_runtime_files()


def _restore_install_logging(manager: object, module: str) -> None:
    """Restore runtime logging after Anki has replaced this add-on's files."""
    if not _is_this_addon(module, manager):
        return
    _setup_file_logging()
    _setup_diagnostics()
    _apply_log_level()
    _setup_managed_runtime()


def _setup_diagnostics() -> None:
    """Initialize runtime diagnostics once the add-on directory is known."""
    addon_id = mw.addonManager.addonFromModule(__name__)
    addon_dir = Path(mw.addonManager.addonsFolder(addon_id))
    config = mw.addonManager.getConfig(addon_id) or {}
    configure_runtime(addon_dir, debug_enabled=bool(config.get("debug_logging", False)))


def _apply_log_level() -> None:
    """Apply the debug logging toggle from config to the console logger."""
    addon_id = mw.addonManager.addonFromModule(__name__)
    config = mw.addonManager.getConfig(addon_id) or {}
    level = logging.DEBUG if config.get("debug_logging", False) else logging.INFO
    for target_logger in _addon_loggers():
        target_logger.setLevel(level)
    set_debug_enabled(bool(config.get("debug_logging", False)))


def _setup_managed_runtime() -> None:
    """Start managed runtime installation after Anki has initialized the add-on."""
    from aqt.utils import tooltip

    from . import runtime_manager

    addon_id = mw.addonManager.addonFromModule(__name__)
    addon_dir = Path(mw.addonManager.addonsFolder(addon_id))

    def _notify(runtime_status_payload: dict[str, object]) -> None:
        phase = str(runtime_status_payload.get("phase", ""))
        raw_progress = runtime_status_payload.get("progress", 0)
        progress = raw_progress if isinstance(raw_progress, int) else 0
        record_breadcrumb(
            "runtime.status",
            source="runtime",
            operation="runtime.ensure",
            context={
                "phase": phase,
                "platform": runtime_status_payload.get("platform", ""),
                "runtime_manifest_id": runtime_status_payload.get("runtime_manifest_id", ""),
                "error": runtime_status_payload.get("error", ""),
            },
            flush=phase in {"ready", "error"},
        )
        if phase == runtime_manager.RUNTIME_PHASE_DOWNLOADING and progress:
            return
        message = _runtime_notice_message(runtime_status_payload)
        if not message:
            return
        mw.taskman.run_on_main(lambda: tooltip(message, period=5000))

    startup_status = runtime_manager.ensure_runtime_async(addon_dir, notify=_notify)
    if startup_status.get("phase") == runtime_manager.RUNTIME_PHASE_ERROR and startup_status.get("runtime_manifest_id"):
        _notify(startup_status)


def _runtime_notice_message(status: dict[str, object]) -> str:
    phase = str(status.get("phase", ""))
    if phase == "downloading":
        return "Audio Quick Editor is downloading runtime assets in the background."
    if phase == "ready":
        return "Audio Quick Editor runtime assets are ready."
    if phase == "error":
        error = str(status.get("error", "")).strip()
        suffix = f": {error}" if error else "."
        return f"Audio Quick Editor runtime install failed{suffix}"
    return ""


def _show_settings_dialog(callbacks: SettingsLifecycleCallbacks | None = None) -> None:
    """Open the settings dialog and optionally run a callback after Save."""
    global _settings_dialog
    settings_module = import_module(f"{__name__}.settings")
    settings_dialog_class = settings_module.SettingsDialog
    _settings_dialog = settings_dialog_class(mw)
    if callbacks is not None:
        close_notified = False

        def _notify_closed() -> None:
            nonlocal close_notified
            if close_notified or callbacks.on_closed is None:
                return
            close_notified = True
            callbacks.on_closed()

        if callbacks.on_saved is not None:
            qconnect(_settings_dialog.accepted, callbacks.on_saved)
        qconnect(
            _settings_dialog.finished,
            lambda result: _notify_closed() if int(result) == 0 else None,
        )
    _settings_dialog.show()
    _settings_dialog.raise_()
    _settings_dialog.activateWindow()


def _open_settings() -> bool:
    """Open the settings dialog and suppress Anki's JSON editor."""
    _show_settings_dialog()
    return False


def _setup_editor_integration() -> None:
    """Register editor hooks for inline audio controls."""
    import_module(f"{__name__}.editor_integration").register_editor_hooks(
        gui_hooks,
        settings_opener=_show_settings_dialog,
    )


def _setup_browser_integration() -> None:
    """Register browser hooks for batch visualization generation."""
    import_module(f"{__name__}.browser_integration").register_browser_hooks(gui_hooks)


def _setup_menu() -> None:
    """Register the add-on submenu under Tools."""
    from .i18n import t

    submenu = mw.form.menuTools.addMenu("Anki Audio Quick Editor")
    assert submenu is not None

    settings_action = submenu.addAction(t("settings.menu"))
    assert settings_action is not None
    qconnect(settings_action.triggered, _open_settings)


def _with_hook_boundary(name: str, func: Callable[[], None]) -> Callable[[], None]:
    """Wrap a startup hook so failures leave diagnostics before Anki reports them."""
    def _wrapped() -> None:
        try:
            func()
        except Exception as exc:
            capture_exception(f"hook.{name}", exc, operation=f"hook.{name}", log=logger)
            raise

    _wrapped.__name__ = getattr(func, "__name__", name)
    return _wrapped


gui_hooks.main_window_did_init.append(_with_hook_boundary("migrate_config", _migrate_config))
gui_hooks.main_window_did_init.append(_with_hook_boundary("setup_file_logging", _setup_file_logging))
gui_hooks.main_window_did_init.append(_with_hook_boundary("setup_diagnostics", _setup_diagnostics))
gui_hooks.main_window_did_init.append(_with_hook_boundary("apply_log_level", _apply_log_level))
gui_hooks.main_window_did_init.append(_with_hook_boundary("setup_managed_runtime", _setup_managed_runtime))
gui_hooks.main_window_did_init.append(_with_hook_boundary("setup_editor_integration", _setup_editor_integration))
gui_hooks.main_window_did_init.append(_with_hook_boundary("setup_browser_integration", _setup_browser_integration))
gui_hooks.main_window_did_init.append(_with_hook_boundary("setup_menu", _setup_menu))
gui_hooks.addon_manager_will_install_addon.append(_release_install_blocking_files)
gui_hooks.addon_manager_did_install_addon.append(_restore_install_logging)
mw.addonManager.setConfigAction(__name__, _open_settings)

logger.info("audio quick editor add-on loaded")
