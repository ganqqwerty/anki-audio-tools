from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.editor_actions import EditorCommandPayload
from anki_audio_quick_editor.editor_sharing import (
    finish_shared_audio,
    share_current_audio_file,
)


def _message(key: str, values: dict[str, str] | None = None) -> str:
    values = values or {}
    if key == "editor.status.shared_catbox":
        return f"Copied Catbox link for {values['filename']}"
    if key == "editor.status.shared_litterbox":
        return f"Copied Litterbox link for {values['filename']}"
    if key == "editor.status.share_clipboard_unavailable":
        return f"Uploaded {values['filename']}: {values['url']}"
    if key == "editor.status.share_invalid_target":
        return "Unsupported share target."
    raise KeyError(key)


def test_share_current_audio_file_rejects_invalid_target_without_upload(tmp_path: Path) -> None:
    editor = SimpleNamespace(currentField=0, web=MagicMock(), mw=MagicMock())
    session = SimpleNamespace(processing=False, analysis_busy=False, analysis_busy_fields=set(), playback_preparing=False)
    statuses: list[tuple[str, str]] = []

    deps = SimpleNamespace(
        current_media_path=lambda _editor: (session, tmp_path / "clip.mp3"),
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        finish_shared_audio=lambda *_args, **_kwargs: None,
        is_busy=lambda _session: False,
        logger=MagicMock(),
        main=lambda _editor, callback: callback(),
        set_busy=lambda *_args, **_kwargs: None,
        share_failed=lambda *_args, **_kwargs: None,
        still_processing_message="Still processing. Please wait.",
        t=_message,
        upload_file=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not upload")),
    )

    share_current_audio_file(editor, EditorCommandPayload(command="aqe:share", field_ord=0), deps)

    assert statuses == [("Unsupported share target.", "error")]


def test_finish_shared_audio_copies_url_to_clipboard_and_reports_success(monkeypatch) -> None:
    clipboard = MagicMock()
    monkeypatch.setattr("aqt.qt.QApplication.clipboard", lambda: clipboard)

    editor = SimpleNamespace(web=MagicMock())
    statuses: list[tuple[str, str]] = []
    busy_calls: list[tuple[bool, str, str]] = []

    deps = SimpleNamespace(
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        logger=MagicMock(),
        set_busy=lambda _editor, busy, message="", command="": busy_calls.append((busy, message, command)),
        t=_message,
    )

    finish_shared_audio(editor, "catbox", "clip.mp3", "https://files.catbox.moe/share123.mp3", deps)

    clipboard.setText.assert_called_once_with("https://files.catbox.moe/share123.mp3")
    assert statuses == [("Copied Catbox link for clip.mp3", "info")]
    assert busy_calls[-1] == (False, "", "")


def test_finish_shared_audio_falls_back_to_status_when_clipboard_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr("aqt.qt.QApplication.clipboard", lambda: None)

    editor = SimpleNamespace(web=MagicMock())
    statuses: list[tuple[str, str]] = []

    deps = SimpleNamespace(
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        logger=MagicMock(),
        set_busy=lambda *_args, **_kwargs: None,
        t=_message,
    )

    finish_shared_audio(
        editor,
        "litterbox",
        "clip.mp3",
        "https://litterbox.catbox.moe/abc123/clip.mp3",
        deps,
    )

    assert statuses == [("Uploaded clip.mp3: https://litterbox.catbox.moe/abc123/clip.mp3", "warning")]
