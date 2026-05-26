"""Shared WebView bridge command decoding."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

BRIDGE_PREFIX = "bridge:"


@dataclass(frozen=True)
class WebviewBridgeCommand:
    """One command received from a WebView frontend."""

    name: str
    payload: Any = None


def decode_webview_bridge_command(cmd: str) -> WebviewBridgeCommand:
    """Decode the shared JSON bridge envelope."""
    if not cmd.startswith(BRIDGE_PREFIX):
        raise ValueError("Bridge command must use the shared envelope")

    raw = json.loads(cmd[len(BRIDGE_PREFIX):])
    if not isinstance(raw, dict):
        raise ValueError("Bridge command envelope must be an object")
    name = raw.get("command")
    if not isinstance(name, str) or not name:
        raise ValueError("Bridge command envelope is missing a command")
    return WebviewBridgeCommand(name=name, payload=raw.get("payload"))
