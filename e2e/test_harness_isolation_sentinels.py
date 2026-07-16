"""Order-independent sentinels for process-global E2E isolation."""

from __future__ import annotations

import copy

import pytest
from PyQt6.QtWidgets import QApplication, QDialog

from e2e.conftest import (
    ADDON_NUMERIC_ID,
    _canonical_default_config,
    _save_config_through_runtime_path,
    import_runtime_addon_module,
)

WINDOW_TITLE = "AQE isolation sentinel"
pytestmark = pytest.mark.shared_desktop


@pytest.mark.isolation_sentinel(WINDOW_TITLE)
def test_isolation_sentinel_mutates_process_global_state(
    anki_mw,
    e2e_process_baseline,
) -> None:
    from aqt.theme import Theme

    support = import_runtime_addon_module(".support")
    mutated = copy.deepcopy(_canonical_default_config(anki_mw))
    mutated["debug_logging"] = not bool(mutated["debug_logging"])
    _save_config_through_runtime_path(mutated)
    support.record_latest_denoise_support_incident(
        operation="isolation_sentinel",
        media_filename="sentinel.wav",
        source_path="/tmp/sentinel.wav",
        user_message="sentinel",
        exception_type="SentinelError",
    )
    QApplication.clipboard().setText("aqe-isolation-mutated")
    other_theme = Theme.DARK if e2e_process_baseline["theme"] != Theme.DARK else Theme.LIGHT
    anki_mw.set_theme(other_theme)
    window = QDialog(anki_mw)
    window.setWindowTitle(WINDOW_TITLE)
    window.show()
    assert window.isVisible()


def test_isolation_sentinel_observes_canonical_baseline(
    anki_mw,
    e2e_process_baseline,
) -> None:
    support = import_runtime_addon_module(".support")
    diagnostics = import_runtime_addon_module(".diagnostics_runtime")
    baseline = _canonical_default_config(anki_mw)

    assert anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) == baseline
    assert diagnostics.is_debug_enabled() is bool(baseline["debug_logging"])
    assert support.latest_denoise_support_incident() is None
    assert QApplication.clipboard().text() == e2e_process_baseline["clipboard"]
    assert anki_mw.pm.theme() == e2e_process_baseline["theme"]
    assert anki_mw.state == "deckBrowser"
    assert not any(
        widget.isVisible() and widget.windowTitle() == WINDOW_TITLE
        for widget in QApplication.topLevelWidgets()
    )
