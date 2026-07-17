from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.editor_actions import EditorCommandPayload
from anki_audio_quick_editor.editor_session import EditorSession
from anki_audio_quick_editor.editor_sharing import (
    finish_shared_audio,
    share_current_audio_file,
    share_failed,
    share_learner_recording_file,
)
from anki_audio_quick_editor.errors import AudioProcessingError, MissingMediaError
from tests.recorder_test_helpers import learner_take
from tests.thread_fakes import ImmediateThread as _ImmediateThread


def _message(key: str, values: dict[str, str] | None = None) -> str:
    values = values or {}
    if key == "editor.status.shared_catbox":
        return f"Copied Catbox link for {values['filename']}: {values['url']}"
    if key == "editor.status.shared_litterbox":
        return f"Copied Litterbox link for {values['filename']}: {values['url']}"
    if key == "editor.status.share_clipboard_unavailable":
        return f"Uploaded {values['filename']}: {values['url']}"
    if key == "editor.status.share_invalid_target":
        return "Unsupported share target."
    if key == "editor.status.referenced_audio_missing":
        return "The referenced audio file was not found in Anki's media folder."
    if key == "editor.status.sharing_catbox":
        return "Sharing with Catbox"
    if key == "editor.status.sharing_litterbox":
        return "Sharing with Litterbox"
    if key == "editor.status.share_failed":
        return f"Share failed: {values['error']}"
    raise KeyError(key)


class _Editor:
    pass


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

    assert statuses == [
        (
            {"code": "AQE-SHARE-001", "message": "Unsupported share target."},
            "error",
        )
    ]


def test_share_current_audio_file_reports_missing_current_audio_with_media_code(tmp_path: Path) -> None:
    editor = SimpleNamespace(currentField=0, web=MagicMock(), mw=MagicMock())
    statuses: list[tuple[object, str]] = []
    busy_calls: list[tuple[bool, str, str]] = []

    deps = SimpleNamespace(
        current_media_path=lambda _editor: (_ for _ in ()).throw(
            AudioProcessingError("No [sound:...] reference found in the current field.")
        ),
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        set_busy=lambda _editor, busy, message="", command="": busy_calls.append((busy, message, command)),
        t=_message,
    )

    share_current_audio_file(
        editor,
        EditorCommandPayload(command="aqe:share", field_ord=0, share_target="catbox"),
        deps,
    )

    assert statuses == [
        (
            {
                "code": "AQE-MEDIA-001",
                "message": "No [sound:...] reference found in the current field.",
            },
            "error",
        )
    ]
    assert busy_calls == [(False, "", "")]


def test_share_current_audio_file_reports_missing_referenced_media_with_media_code(tmp_path: Path) -> None:
    editor = SimpleNamespace(currentField=0, web=MagicMock(), mw=MagicMock())
    statuses: list[tuple[object, str]] = []
    busy_calls: list[tuple[bool, str, str]] = []

    deps = SimpleNamespace(
        current_media_path=lambda _editor: (_ for _ in ()).throw(
            MissingMediaError("The referenced audio file was not found in Anki's media folder.")
        ),
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        set_busy=lambda _editor, busy, message="", command="": busy_calls.append((busy, message, command)),
        t=_message,
    )

    share_current_audio_file(
        editor,
        EditorCommandPayload(command="aqe:share", field_ord=0, share_target="catbox"),
        deps,
    )

    assert statuses == [
        (
            {
                "code": "AQE-MEDIA-002",
                "message": "The referenced audio file was not found in Anki's media folder.",
            },
            "error",
        )
    ]
    assert busy_calls == [(False, "", "")]


def test_share_learner_recording_rejects_missing_ready_media(tmp_path: Path) -> None:
    editor = _Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    editor.mw = MagicMock()
    session = EditorSession()
    statuses: list[tuple[object, str]] = []
    busy_calls: list[tuple[bool, str, str]] = []

    deps = SimpleNamespace(
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        finish_shared_audio=lambda *_args, **_kwargs: None,
        is_busy=lambda _session: False,
        main=lambda _editor, callback: callback(),
        set_busy=lambda _editor, busy, message="", command="": busy_calls.append((busy, message, command)),
        share_failed=lambda *_args, **_kwargs: None,
        sessions={editor: session},
        still_processing_message="Still processing. Please wait.",
        t=_message,
        upload_file=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not upload")),
    )

    share_learner_recording_file(
        editor,
        EditorCommandPayload(command="aqe:share-recording", field_ord=0, share_target="catbox"),
        deps,
    )

    assert statuses == [
        (
            {
                "code": "AQE-MEDIA-002",
                "message": "The referenced audio file was not found in Anki's media folder.",
            },
            "error",
        )
    ]
    assert busy_calls == [(False, "", "")]


def test_share_learner_recording_rejects_invalid_target_without_upload(tmp_path: Path) -> None:
    editor = _Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    editor.mw = MagicMock()
    session = EditorSession()
    statuses: list[tuple[object, str]] = []
    busy_calls: list[tuple[bool, str, str]] = []

    deps = SimpleNamespace(
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        set_busy=lambda _editor, busy, message="", command="": busy_calls.append((busy, message, command)),
        sessions={editor: session},
        t=_message,
        upload_file=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not upload")),
    )

    share_learner_recording_file(
        editor,
        EditorCommandPayload(command="aqe:share-recording", field_ord=0),
        deps,
    )

    assert statuses == [
        (
            {"code": "AQE-SHARE-001", "message": "Unsupported share target."},
            "error",
        )
    ]
    assert busy_calls == [(False, "", "")]


def test_share_learner_recording_uploads_ready_sidecar(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.editor_sharing.threading.Thread", _ImmediateThread)
    editor = _Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:target.wav]"])
    editor.web = MagicMock()
    editor.mw = MagicMock()
    media_path = tmp_path / "target__aqe_voice.wav"
    media_path.write_bytes(b"RIFFfakeWAVE")
    session = EditorSession()
    session.learner_take = learner_take(media_path, editor_session_id=session.editor_session_id)
    busy_calls: list[tuple[bool, str, str]] = []
    finished: list[tuple[str, str, str]] = []

    deps = SimpleNamespace(
        eval_status=lambda *_args, **_kwargs: None,
        finish_shared_audio=lambda _editor, target, filename, url: finished.append((target, filename, url)),
        is_busy=lambda _session: False,
        logger=MagicMock(),
        main=lambda _editor, callback: callback(),
        set_busy=lambda _editor, busy, message="", command="": busy_calls.append((busy, message, command)),
        share_failed=lambda *_args, **_kwargs: None,
        sessions={editor: session},
        still_processing_message="Still processing. Please wait.",
        t=_message,
        upload_file=lambda path, target: f"https://example.test/{target}/{path.name}",
    )

    share_learner_recording_file(
        editor,
        EditorCommandPayload(command="aqe:share-recording", field_ord=0, share_target="litterbox"),
        deps,
    )

    assert busy_calls == [(True, "Sharing with Litterbox", "aqe:share-recording")]
    assert finished == [
        (
            "litterbox",
            "target__aqe_voice.wav",
            "https://example.test/litterbox/target__aqe_voice.wav",
        )
    ]
    assert editor.note.fields == ["[sound:target.wav]"]


def test_share_learner_recording_reports_upload_failures_with_share_code(
    tmp_path: Path,
    monkeypatch,
    caplog,
) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.editor_sharing.threading.Thread", _ImmediateThread)
    editor = _Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:target.wav]"])
    editor.web = MagicMock()
    editor.mw = MagicMock()
    media_path = tmp_path / "target__aqe_voice.wav"
    media_path.write_bytes(b"RIFFfakeWAVE")
    session = EditorSession()
    session.learner_take = learner_take(media_path, editor_session_id=session.editor_session_id)
    statuses: list[tuple[object, str]] = []
    busy_calls: list[tuple[bool, str, str]] = []

    caplog.set_level(logging.INFO, logger="anki_audio_quick_editor.editor_sharing")
    deps = SimpleNamespace(
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        finish_shared_audio=lambda *_args, **_kwargs: None,
        is_busy=lambda _session: False,
        logger=MagicMock(),
        main=lambda _editor, callback: callback(),
        set_busy=lambda _editor, busy, message="", command="": busy_calls.append((busy, message, command)),
        sessions={editor: session},
        still_processing_message="Still processing. Please wait.",
        t=_message,
        upload_file=lambda _path, _target: (_ for _ in ()).throw(RuntimeError("network down")),
    )
    deps.share_failed = lambda _editor, error: share_failed(_editor, error, deps)

    share_learner_recording_file(
        editor,
        EditorCommandPayload(command="aqe:share-recording", field_ord=0, share_target="catbox"),
        deps,
    )

    assert busy_calls[0] == (True, "Sharing with Catbox", "aqe:share-recording")
    assert busy_calls[-1] == (False, "", "")
    assert statuses == [
        (
            {"code": "AQE-SHARE-001", "message": "Share failed: network down"},
            "error",
        )
    ]
    assert "Editor share upload start" in caplog.text


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
    assert statuses == [("Copied Catbox link for clip.mp3: https://files.catbox.moe/share123.mp3", "info")]
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
