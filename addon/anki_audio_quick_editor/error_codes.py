"""Stable user-facing error codes and help-link payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

GITHUB_PAGES_BASE_URL = "https://ganqqwerty.github.io/anki-audio-tools/"

AQE_MEDIA_CURRENT_FIELD_AUDIO_MISSING = "AQE-MEDIA-001"
AQE_MEDIA_REFERENCED_AUDIO_MISSING = "AQE-MEDIA-002"
AQE_RUNTIME_FFMPEG_MISSING = "AQE-RUNTIME-001"
AQE_RUNTIME_FFPROBE_MISSING = "AQE-RUNTIME-002"
AQE_RUNTIME_ASSET_MISSING = "AQE-RUNTIME-003"
AQE_AUDIO_PROCESSING_FAILED = "AQE-AUDIO-001"
AQE_PLAYBACK_PREPARE_FAILED = "AQE-PLAYBACK-001"
AQE_GRAPH_ANALYSIS_FAILED = "AQE-GRAPH-001"
AQE_RECORDING_FAILED = "AQE-RECORDING-001"
AQE_BATCH_INVALID_REQUEST = "AQE-BATCH-001"
AQE_SETTINGS_INVALID_PAYLOAD = "AQE-SETTINGS-001"
AQE_FRONTEND_INVALID_ASYNC_RESULT = "AQE-FRONTEND-001"
AQE_FRONTEND_UNKNOWN_ASYNC_ERROR = "AQE-FRONTEND-002"
AQE_FRONTEND_UNEXPECTED = "AQE-FRONTEND-999"


@dataclass(frozen=True)
class UserFacingError:
    """Structured error data safe to display directly to users."""

    code: str
    message: str
    details: str = ""

    def to_dict(self) -> dict[str, str]:
        payload = {"code": self.code, "message": self.message}
        if self.details:
            payload["details"] = self.details
        return payload


def public_help_url(code: str) -> str:
    """Return the public GitHub Pages help URL for an error code."""
    return f"{GITHUB_PAGES_BASE_URL}errors/{code}/"


def coded_error(code: str, message: str, *, details: str = "") -> dict[str, str]:
    """Return a JSON-serializable user-facing error payload."""
    return UserFacingError(code, message, details=details).to_dict()


def coded_error_from_message(code: str, message: Any, *, details: str = "") -> dict[str, str]:
    """Return a coded error after normalizing a non-string message."""
    return coded_error(code, str(message), details=details)


def format_coded_message(code: str, message: str) -> str:
    """Return a code-prefixed string for display paths that are not structured yet."""
    rendered = message.strip()
    if rendered.startswith(f"{code}:"):
        return rendered
    return f"{code}: {rendered} Help: {public_help_url(code)}"
