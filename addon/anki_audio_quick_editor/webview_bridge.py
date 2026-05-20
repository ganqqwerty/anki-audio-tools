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
    legacy_payload: str | None = None

    @property
    def is_legacy(self) -> bool:
        """Return true when the command used the old ``name:json`` form."""
        return self.legacy_payload is not None


def decode_webview_bridge_command(cmd: str) -> WebviewBridgeCommand:
    """Decode the shared JSON bridge envelope, falling back to legacy commands."""
    if not cmd.startswith(BRIDGE_PREFIX):
        return _decode_legacy_command(cmd)

    raw = json.loads(cmd[len(BRIDGE_PREFIX):])
    if not isinstance(raw, dict):
        raise ValueError("Bridge command envelope must be an object")
    name = raw.get("command")
    if not isinstance(name, str) or not name:
        raise ValueError("Bridge command envelope is missing a command")
    return WebviewBridgeCommand(name=name, payload=raw.get("payload"))


def legacy_json_payload(command: WebviewBridgeCommand) -> Any:
    """Return a JSON payload for a legacy command."""
    if command.legacy_payload is None:
        return command.payload
    return json.loads(command.legacy_payload)


def _decode_legacy_command(cmd: str) -> WebviewBridgeCommand:
    name, separator, payload = cmd.partition(":")
    return WebviewBridgeCommand(
        name=name,
        legacy_payload=payload if separator else None,
    )
