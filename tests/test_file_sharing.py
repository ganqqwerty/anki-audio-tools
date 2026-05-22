from __future__ import annotations

import io
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from anki_audio_quick_editor.file_sharing import (
    CATBOX_UPLOAD_URL,
    LITTERBOX_RETENTION,
    LITTERBOX_UPLOAD_URL,
    FileSharingError,
    upload_file,
)


class _Response:
    def __init__(self, text: str) -> None:
        self._text = text

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self._text.encode("utf-8")


def test_upload_file_posts_to_catbox_without_retention(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    captured: dict[str, object] = {}

    def fake_urlopen(request: urllib.request.Request, *, timeout: float) -> _Response:
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["content_type"] = request.get_header("Content-type")
        captured["body"] = request.data
        return _Response("https://files.catbox.moe/share123.mp3")

    monkeypatch.setattr("anki_audio_quick_editor.file_sharing.urllib.request.urlopen", fake_urlopen)

    result = upload_file(source, "catbox")

    assert result == "https://files.catbox.moe/share123.mp3"
    assert captured["url"] == CATBOX_UPLOAD_URL
    assert captured["timeout"] == 60.0
    assert b'name="reqtype"' in captured["body"]
    assert b"fileupload" in captured["body"]
    assert b'name="fileToUpload"; filename="clip.mp3"' in captured["body"]
    assert b'name="time"' not in captured["body"]


def test_upload_file_posts_to_litterbox_with_fixed_72h_retention(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    captured: dict[str, object] = {}

    def fake_urlopen(request: urllib.request.Request, *, timeout: float) -> _Response:
        del timeout
        captured["url"] = request.full_url
        captured["body"] = request.data
        return _Response("https://litterbox.catbox.moe/abc123/clip.mp3")

    monkeypatch.setattr("anki_audio_quick_editor.file_sharing.urllib.request.urlopen", fake_urlopen)

    result = upload_file(source, "litterbox")

    assert result == "https://litterbox.catbox.moe/abc123/clip.mp3"
    assert captured["url"] == LITTERBOX_UPLOAD_URL
    assert LITTERBOX_RETENTION == "72h"
    assert b'name="time"' in captured["body"]
    assert b"72h" in captured["body"]


def test_upload_file_rejects_non_url_response(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")

    monkeypatch.setattr(
        "anki_audio_quick_editor.file_sharing.urllib.request.urlopen",
        lambda request, *, timeout: _Response("nope"),
    )

    with pytest.raises(FileSharingError, match="Unexpected upload response: nope"):
        upload_file(source, "catbox")


def test_upload_file_maps_timeout_to_file_sharing_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")

    def fake_urlopen(request: urllib.request.Request, *, timeout: float) -> _Response:
        del request, timeout
        raise TimeoutError("timed out")

    monkeypatch.setattr("anki_audio_quick_editor.file_sharing.urllib.request.urlopen", fake_urlopen)

    with pytest.raises(FileSharingError, match="Upload timed out"):
        upload_file(source, "catbox")


def test_upload_file_maps_http_errors_to_file_sharing_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")

    def fake_urlopen(request: urllib.request.Request, *, timeout: float) -> _Response:
        del timeout
        raise urllib.error.HTTPError(
            request.full_url,
            503,
            "service unavailable",
            hdrs={},
            fp=io.BytesIO(b"slow down"),
        )

    monkeypatch.setattr("anki_audio_quick_editor.file_sharing.urllib.request.urlopen", fake_urlopen)

    with pytest.raises(FileSharingError, match="Upload failed with HTTP 503: slow down"):
        upload_file(source, "catbox")


def test_upload_file_rejects_unknown_target_before_network(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")

    with pytest.raises(FileSharingError, match="Unsupported share target: somewhere"):
        upload_file(source, "somewhere")
