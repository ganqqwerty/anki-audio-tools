"""Tests for shared WebView bridge command decoding."""

from __future__ import annotations

import json

import pytest

from anki_audio_quick_editor.webview_bridge import (
    decode_webview_bridge_command,
)


def test_decode_webview_bridge_envelope() -> None:
    command = decode_webview_bridge_command(
        'bridge:{"command":"batch.start","payload":{"source_field":"Audio"}}'
    )

    assert command.name == "batch.start"
    assert command.payload == {"source_field": "Audio"}


def test_decode_webview_bridge_rejects_legacy_command_prefix() -> None:
    with pytest.raises(ValueError, match="shared envelope"):
        decode_webview_bridge_command('batch_start:{"source_field":"Audio"}')


def test_decode_webview_bridge_rejects_invalid_envelope() -> None:
    with pytest.raises(ValueError, match="missing a command"):
        decode_webview_bridge_command(f"bridge:{json.dumps({'payload': {}})}")
