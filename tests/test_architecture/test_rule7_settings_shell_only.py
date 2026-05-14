"""Rule 7: settings/__init__.py stays a thin shell around AnkiWebView."""

import ast

from .conftest import ADDON_DIR

SETTINGS_INIT = ADDON_DIR / "settings" / "__init__.py"
ALLOWED_QT_NAMES = {"QDialog", "QVBoxLayout", "AnkiWebView"}


def test_settings_shell_avoids_legacy_tab_widgets() -> None:
    tree = ast.parse(SETTINGS_INIT.read_text(encoding="utf-8"))
    names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }
    assert "QTabWidget" not in names
    assert "QDialogButtonBox" not in names


def test_settings_shell_uses_small_widget_surface() -> None:
    tree = ast.parse(SETTINGS_INIT.read_text(encoding="utf-8"))
    qt_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id.startswith("Q")
    }
    assert qt_names <= ALLOWED_QT_NAMES
