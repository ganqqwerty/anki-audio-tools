"""Settings dialog shell for Anki Audio Quick Editor."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from aqt import mw
from aqt.qt import QDialog, QVBoxLayout
from aqt.webview import AnkiWebView

from ..i18n import active_locale, t
from ..webview_shell import render_webview_content
from .commands import handle_settings_command
from .initial_state import build_initial_state

logger = logging.getLogger(__name__)

_BUNDLE_DIR = Path(__file__).parent.parent / "templates" / "settings"
_BUNDLE_JS = _BUNDLE_DIR / "settings_bundle.js"
_BUNDLE_CSS = _BUNDLE_DIR / "settings_bundle.css"


class SettingsDialog(QDialog):
    """Settings dialog backed by a single Anki webview."""

    def __init__(self, parent: object) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.setWindowTitle(t("settings.window_title"))
        self.setMinimumWidth(900)
        self.setMinimumHeight(640)

        addon_id = mw.addonManager.addonFromModule(__name__)
        config = mw.addonManager.getConfig(addon_id) or {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._webview = AnkiWebView(parent=self)
        self._webview.requiresCol = False

        def _eval_fn(js: str) -> None:
            self._webview.eval(js)

        def _on_bridge_cmd(cmd: str) -> bool:
            return handle_settings_command(cmd, _eval_fn, self)

        self._webview.set_bridge_command(_on_bridge_cmd, self)
        body, head = _render_settings_content(config)
        self._webview.stdHtml(body=body, head=head, context=self)
        layout.addWidget(self._webview)

    def run_js(self, script: str, callback: Any = None) -> None:
        """Evaluate JavaScript in the settings webview."""
        if callback is None:
            self._webview.eval(script)
            return
        self._webview.page().runJavaScript(script, callback)


def _render_settings_content(config: dict[str, Any]) -> tuple[str, str]:
    """Render settings webview body/head fragments for Anki's themed HTML shell."""
    return render_webview_content(
        initial_state_name="__INITIAL_STATE__",
        initial_state=build_initial_state(config),
        bundle_js=_BUNDLE_JS,
        bundle_css=_BUNDLE_CSS,
        scope="settings",
    )


def _render_settings_html(config: dict[str, Any]) -> str:
    """Render settings fragments inside a minimal HTML shell for tests."""
    body, head = _render_settings_content(config)
    lang = active_locale()
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  {head}
</head>
<body>
{body}
</body>
</html>"""
