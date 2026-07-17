"""Shared editor session value types."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts_generated import AutoplayKind


@dataclass(frozen=True)
class PostEditAutoplayPreference:
    """Pure practice program requested by the frontend for the next edit result."""

    kind: AutoplayKind = AutoplayKind.ONCE
    repeat_pause_ms: int = 0


@dataclass(frozen=True)
class PendingEditorStatus:
    """One status message to reapply after the editor controls remount."""

    field_index: int
    kind: str = "info"
    message: str = ""
