"""Tests for the settings initial state JSON."""

from __future__ import annotations

import json

from anki_audio_quick_editor.settings.initial_state import build_initial_state


def test_initial_state_has_required_keys() -> None:
    state = json.loads(build_initial_state({"enabled": True, "debug_logging": False}))

    assert set(state) == {
        "config",
        "version",
        "addon_dir",
        "log_file_path",
        "diagnostics",
    }
    assert state["diagnostics"]["addon_id"] == "anki_audio_quick_editor"
