"""Anki Audio Quick Editor add-on package."""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path

from ._version import __version__  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(name)s: %(levelname)s: %(message)s")
logger = logging.getLogger("anki_audio_quick_editor")
logger.setLevel(logging.INFO)

_VENDOR_DIR = Path(__file__).parent / "vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

if os.environ.get("DEBUG_ANKI"):
    import debugpy

    debugpy.listen(5678)
    logger.info("debugpy listening on port 5678")
    debugpy.wait_for_client()
    logger.info("debugger attached")

from aqt import gui_hooks, mw  # noqa: E402
from aqt.qt import qconnect  # noqa: E402

_settings_dialog = None


def _migrate_config() -> None:
    """Deep-merge defaults into the user's config and stamp the schema version."""
    from .config_migration import migrate_config

    addon_id = mw.addonManager.addonFromModule(__name__)
    user_config = mw.addonManager.getConfig(addon_id) or {}
    defaults = mw.addonManager.addonConfigDefaults(addon_id) or {}
    migrated, changed = migrate_config(user_config, defaults)
    if changed:
        mw.addonManager.writeConfig(addon_id, migrated)
        logger.info("config migrated to version %s", migrated.get("_config_version"))


def _setup_file_logging() -> None:
    """Attach a rotating file handler inside the add-on directory."""
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
    logger.addHandler(handler)
    logger.debug("file logging initialized at %s", log_file)


def _apply_log_level() -> None:
    """Apply the debug logging toggle from config to the console logger."""
    addon_id = mw.addonManager.addonFromModule(__name__)
    config = mw.addonManager.getConfig(addon_id) or {}
    logger.setLevel(logging.DEBUG if config.get("debug_logging", False) else logging.INFO)


def _open_settings() -> bool:
    """Open the settings dialog and suppress Anki's JSON editor."""
    from .settings import SettingsDialog

    global _settings_dialog
    _settings_dialog = SettingsDialog(mw)
    _settings_dialog.show()
    _settings_dialog.raise_()
    _settings_dialog.activateWindow()
    return False


def _setup_editor_integration() -> None:
    """Register editor hooks for inline audio controls."""
    from .editor_integration import register_editor_hooks

    register_editor_hooks(gui_hooks)


def _setup_menu() -> None:
    """Register the add-on submenu under Tools."""
    submenu = mw.form.menuTools.addMenu("Anki Audio Quick Editor")
    assert submenu is not None

    settings_action = submenu.addAction("Settings")
    assert settings_action is not None
    qconnect(settings_action.triggered, _open_settings)


gui_hooks.main_window_did_init.append(_migrate_config)
gui_hooks.main_window_did_init.append(_setup_file_logging)
gui_hooks.main_window_did_init.append(_apply_log_level)
gui_hooks.main_window_did_init.append(_setup_editor_integration)
gui_hooks.main_window_did_init.append(_setup_menu)
mw.addonManager.setConfigAction(__name__, _open_settings)

logger.info("audio quick editor add-on loaded")
