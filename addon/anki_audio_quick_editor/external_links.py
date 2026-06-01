"""Validation helpers for user-facing external links."""

from __future__ import annotations

from logging import Logger
from typing import Any
from urllib.parse import urlparse

from .errors import AudioQuickEditorError
from .file_reveal import open_external_url

TRUSTED_EXTERNAL_URL_HOST = "ganqqwerty.github.io"
TRUSTED_EXTERNAL_URL_PATH = "/anki-audio-tools"
TRUSTED_EXTERNAL_URL_PATH_PREFIX = f"{TRUSTED_EXTERNAL_URL_PATH}/"


def trusted_external_url_or_none(value: Any) -> str | None:
    """Return a trusted first-party URL, or ``None`` for unsafe input."""
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    if parsed.scheme != "https":
        return None
    if parsed.hostname != TRUSTED_EXTERNAL_URL_HOST:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    if parsed.path != TRUSTED_EXTERNAL_URL_PATH and not parsed.path.startswith(
        TRUSTED_EXTERNAL_URL_PATH_PREFIX
    ):
        return None
    return value


def trusted_external_url_from_payload(payload: Any) -> str | None:
    """Extract a trusted URL from a WebView bridge payload."""
    if not isinstance(payload, dict):
        return None
    return trusted_external_url_or_none(payload.get("url"))


def open_trusted_external_url_from_payload(payload: Any, *, logger: Logger) -> None:
    """Open a trusted WebView URL payload, logging rejected or failed requests."""
    url = trusted_external_url_from_payload(payload)
    if url is None:
        logger.warning("webview.open_url: rejected external URL")
        return
    try:
        open_external_url(url)
    except AudioQuickEditorError as exc:
        logger.warning("webview.open_url: %s", exc)
