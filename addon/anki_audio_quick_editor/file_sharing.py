"""Stdlib-only file upload helpers for Catbox and Litterbox."""

from __future__ import annotations

import mimetypes
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Final

CATBOX_UPLOAD_URL: Final[str] = "https://catbox.moe/user/api.php"
LITTERBOX_UPLOAD_URL: Final[str] = "https://litterbox.catbox.moe/resources/internals/api.php"
LITTERBOX_RETENTION: Final[str] = "72h"
DEFAULT_TIMEOUT_SECONDS: Final[float] = 60.0


class FileSharingError(RuntimeError):
    """Raised when a remote upload cannot be completed."""


def upload_file(path: Path, target: str, timeout_s: float = DEFAULT_TIMEOUT_SECONDS) -> str:
    """Upload ``path`` to the requested host and return the direct URL."""
    file_path = Path(path)
    if target not in {"catbox", "litterbox"}:
        raise FileSharingError(f"Unsupported share target: {target}")
    if not file_path.is_file():
        raise FileSharingError(f"Missing upload file: {file_path}")

    fields = [("reqtype", "fileupload")]
    url = CATBOX_UPLOAD_URL
    if target == "litterbox":
        url = LITTERBOX_UPLOAD_URL
        fields.append(("time", LITTERBOX_RETENTION))

    content_type, body = _multipart_body(fields, file_path)
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": content_type,
            "User-Agent": "anki-audio-quick-editor/1",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:  # nosec B310
            raw_text = _read_response_text(response)
    except TimeoutError as exc:
        raise FileSharingError("Upload timed out") from exc
    except urllib.error.HTTPError as exc:
        raise FileSharingError(f"Upload failed with HTTP {exc.code}: {_http_error_message(exc)}") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise FileSharingError(f"Upload failed: {reason}") from exc
    except OSError as exc:
        raise FileSharingError(f"Upload failed: {exc}") from exc

    if not raw_text.startswith("https://"):
        raise FileSharingError(f"Unexpected upload response: {raw_text}")
    return raw_text


def _multipart_body(fields: list[tuple[str, str]], path: Path) -> tuple[str, bytes]:
    boundary = f"----aqe-{uuid.uuid4().hex}"
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    parts: list[bytes] = []

    for name, value in fields:
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )

    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        (
            f'Content-Disposition: form-data; name="fileToUpload"; filename="{path.name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode()
    )
    parts.append(path.read_bytes())
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return f"multipart/form-data; boundary={boundary}", b"".join(parts)


def _http_error_message(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace").strip()
    except OSError:
        body = ""
    return body or str(exc.reason) or "unknown error"


def _read_response_text(response: Any) -> str:
    return bytes(response.read()).decode("utf-8", errors="replace").strip()
