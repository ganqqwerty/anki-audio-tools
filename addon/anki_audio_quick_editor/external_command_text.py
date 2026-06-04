"""Stable text decoding policy for external command output."""

from __future__ import annotations

EXTERNAL_COMMAND_TEXT_ENCODING = "utf-8"
EXTERNAL_COMMAND_TEXT_ERRORS = "replace"


def external_command_text_kwargs() -> dict[str, str]:
    """Return subprocess text decoding kwargs for captured external command output."""
    return {
        "encoding": EXTERNAL_COMMAND_TEXT_ENCODING,
        "errors": EXTERNAL_COMMAND_TEXT_ERRORS,
    }
