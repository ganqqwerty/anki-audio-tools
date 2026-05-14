"""Bootstrap import tests for the Audio Quick Editor entrypoint."""

from __future__ import annotations

import importlib

import aqt

import anki_audio_quick_editor


def test_entrypoint_registers_hooks_and_config_action() -> None:
    importlib.reload(anki_audio_quick_editor)

    assert aqt.gui_hooks.main_window_did_init.append.call_count == 5
    aqt.mw.addonManager.setConfigAction.assert_called_once()


def test_open_settings_keeps_dialog_reference() -> None:
    import anki_audio_quick_editor

    anki_audio_quick_editor._open_settings()

    assert anki_audio_quick_editor._settings_dialog is not None
