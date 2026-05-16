"""Tests for import-safe settings initial state construction."""

from __future__ import annotations

import json

from anki_audio_quick_editor.settings_state import (
    build_initial_state_payload,
    encode_initial_state,
)


def test_build_initial_state_payload_has_settings_webview_shape() -> None:
    payload = build_initial_state_payload(
        {"enabled": True},
        version="0.1.0",
        addon_id="anki_audio_quick_editor",
        addon_dir="/tmp/addon",
        collection_available=True,
    )

    assert payload == {
        "config": {"enabled": True},
        "version": "0.1.0",
        "addon_dir": "/tmp/addon",
        "log_file_path": "/tmp/addon/anki_audio_quick_editor.log",
        "diagnostics": {
            "addon_id": "anki_audio_quick_editor",
            "collection_available": True,
        },
    }


def test_encode_initial_state_returns_json() -> None:
    payload = build_initial_state_payload(
        {},
        version="0.1.0",
        addon_id="addon",
        addon_dir="/tmp/addon",
        collection_available=False,
    )

    assert json.loads(encode_initial_state(payload)) == payload


def test_build_initial_state_payload_preserves_false_diagnostics_and_log_path() -> None:
    payload = build_initial_state_payload(
        {"enabled": False},
        version="0.1.0",
        addon_id="addon",
        addon_dir="/tmp/custom-addon",
        collection_available=False,
    )

    assert payload["diagnostics"]["collection_available"] is False
    assert payload["log_file_path"] == "/tmp/custom-addon/anki_audio_quick_editor.log"
