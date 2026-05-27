"""Shared helpers for settings dialog E2E command tests."""

from __future__ import annotations

import json


def bridge_command(command: str, payload: object) -> str:
    return "bridge:" + json.dumps({"command": command, "payload": payload})
