"""Tests for shared WebView bridge command decoding."""

from __future__ import annotations

import json

import pytest

from anki_audio_quick_editor.webview_bridge import (
    decode_webview_bridge_command,
    legacy_json_payload,
)


def test_decode_webview_bridge_envelope() -> None:
    command = decode_webview_bridge_command(
        'bridge:{"command":"batch.start","payload":{"source_field":"Audio"}}'
    )

    assert command.name == "batch.start"
    assert command.payload == {"source_field": "Audio"}
    assert command.is_legacy is False
    assert legacy_json_payload(command) == {"source_field": "Audio"}


def test_decode_legacy_bridge_command() -> None:
    command = decode_webview_bridge_command('batch_start:{"source_field":"Audio"}')

    assert command.name == "batch_start"
    assert command.legacy_payload == '{"source_field":"Audio"}'
    assert command.is_legacy is True
    assert legacy_json_payload(command) == {"source_field": "Audio"}


def test_decode_webview_bridge_rejects_invalid_envelope() -> None:
    with pytest.raises(ValueError, match="missing a command"):
        decode_webview_bridge_command(f"bridge:{json.dumps({'payload': {}})}")
