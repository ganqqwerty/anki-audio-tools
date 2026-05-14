"""Settings dialog shell for Anki Audio Quick Editor."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from aqt import mw
from aqt.qt import QDialog, QVBoxLayout
from aqt.webview import AnkiWebView

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
        self.setWindowTitle("Anki Audio Quick Editor - Settings")
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
        self._webview.setHtml(_render_settings_html(config))
        layout.addWidget(self._webview)

    def run_js(self, script: str, callback: Any = None) -> None:
        """Evaluate JavaScript in the settings webview."""
        if callback is None:
            self._webview.eval(script)
            return
        self._webview.page().runJavaScript(script, callback)


def _render_settings_html(config: dict[str, Any]) -> str:
    """Render the settings webview HTML with the compiled Svelte bundle embedded."""
    initial_state_json = build_initial_state(config).replace("</script>", "<\\/script>")
    bundle_js = _BUNDLE_JS.read_text(encoding="utf-8") if _BUNDLE_JS.exists() else ""
    bundle_css = _BUNDLE_CSS.read_text(encoding="utf-8") if _BUNDLE_CSS.exists() else ""

    js_error_reporter = r"""
window.addEventListener("error", function(event) {
  var payload = JSON.stringify({
    level: "error",
    message: (event.message || "unknown") + " @ " + (event.filename || "?") + ":" + (event.lineno || "?")
  });
  if (typeof pycmd === "function") {
    pycmd("frontend_log:" + payload);
  }
});
window.addEventListener("unhandledrejection", function(event) {
  var payload = JSON.stringify({
    level: "error",
    message: "Unhandled rejection: " + String(event.reason || "unknown")
  });
  if (typeof pycmd === "function") {
    pycmd("frontend_log:" + payload);
  }
});
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>{bundle_css}</style>
</head>
<body>
  <div id="app"></div>
  <script>window.__INITIAL_STATE__ = {initial_state_json};</script>
  <script>{js_error_reporter}</script>
  <script>{bundle_js}</script>
</body>
</html>"""
