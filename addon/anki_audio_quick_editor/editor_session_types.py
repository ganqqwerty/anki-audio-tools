"""Shared editor session value types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PendingEditorStatus:
    """One status message to reapply after the editor controls remount."""

    field_index: int
    kind: str = "info"
    message: str = ""
