from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.editor_session import EditorSession, LearnerRecordingState
from anki_audio_quick_editor.editor_settings_actions import (
    show_current_audio_file,
    show_learner_recording_file,
    show_media_file,
)
from anki_audio_quick_editor.errors import AudioProcessingError, MissingMediaError


class _Editor:
    pass


def test_show_learner_recording_file_reveals_ready_sidecar(tmp_path: Path, monkeypatch) -> None:
    editor = _Editor()
    editor.web = MagicMock()
    editor.mw = MagicMock()
    media_path = tmp_path / "target__aqe_voice.wav"
    media_path.write_bytes(b"RIFFfakeWAVE")
    session = EditorSession(
        learner_recording=LearnerRecordingState(
            status="ready",
            field_index=0,
            generation=2,
            source_filename="target.wav",
            target_duration_ms=1000,
            media_filename=media_path.name,
            media_path=media_path,
        )
    )
    revealed: list[Path] = []
    statuses: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_settings_actions.reveal_file",
        lambda path: revealed.append(path),
    )
    deps = SimpleNamespace(
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        is_busy=lambda _session: False,
        sessions={editor: session},
        still_processing_message="Still processing. Please wait.",
    )

    show_learner_recording_file(editor, deps)

    assert revealed == [media_path]
    assert statuses == [(f"Showing {media_path.name} in folder", "info")]


def test_show_current_audio_file_reports_missing_current_audio_with_media_code(tmp_path: Path) -> None:
    editor = _Editor()
    editor.web = MagicMock()
    editor.mw = MagicMock()
    statuses: list[tuple[object, str]] = []
    deps = SimpleNamespace(
        current_media_path=lambda _editor: (_ for _ in ()).throw(
            AudioProcessingError("No [sound:...] reference found in the current field.")
        ),
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
    )

    show_current_audio_file(editor, deps)

    assert statuses == [
        (
            {
                "code": "AQE-MEDIA-001",
                "message": "No [sound:...] reference found in the current field.",
            },
            "error",
        )
    ]


def test_show_current_audio_file_reports_missing_referenced_media_with_media_code(tmp_path: Path) -> None:
    editor = _Editor()
    editor.web = MagicMock()
    editor.mw = MagicMock()
    statuses: list[tuple[object, str]] = []
    deps = SimpleNamespace(
        current_media_path=lambda _editor: (_ for _ in ()).throw(
            MissingMediaError("The referenced audio file was not found in Anki's media folder.")
        ),
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
    )

    show_current_audio_file(editor, deps)

    assert statuses == [
        (
            {
                "code": "AQE-MEDIA-002",
                "message": "The referenced audio file was not found in Anki's media folder.",
            },
            "error",
        )
    ]


def test_show_learner_recording_file_rejects_missing_sidecar(tmp_path: Path) -> None:
    editor = _Editor()
    editor.web = MagicMock()
    editor.mw = MagicMock()
    missing_path = tmp_path / "missing.wav"
    session = EditorSession(
        learner_recording=LearnerRecordingState(
            status="ready",
            field_index=0,
            generation=2,
            source_filename="target.wav",
            target_duration_ms=1000,
            media_filename=missing_path.name,
            media_path=missing_path,
        )
    )
    statuses: list[tuple[object, str]] = []
    deps = SimpleNamespace(
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        is_busy=lambda _session: False,
        sessions={editor: session},
        still_processing_message="Still processing. Please wait.",
    )

    show_learner_recording_file(editor, deps)

    assert statuses == [
        (
            {
                "code": "AQE-MEDIA-002",
                "message": "The referenced audio file was not found in Anki's media folder.",
            },
            "error",
        )
    ]


def test_show_media_file_reports_missing_media_with_media_code(tmp_path: Path, monkeypatch) -> None:
    editor = _Editor()
    editor.web = MagicMock()
    editor.mw = MagicMock()
    media_path = tmp_path / "missing.wav"
    statuses: list[tuple[object, str]] = []
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_settings_actions.reveal_file",
        lambda _path: (_ for _ in ()).throw(
            MissingMediaError("The referenced audio file was not found in Anki's media folder.")
        ),
    )
    deps = SimpleNamespace(
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        is_busy=lambda _session: False,
        still_processing_message="Still processing. Please wait.",
    )

    show_media_file(editor, object(), media_path, deps)

    assert statuses == [
        (
            {
                "code": "AQE-MEDIA-002",
                "message": "The referenced audio file was not found in Anki's media folder.",
            },
            "error",
        )
    ]


def test_show_media_file_reports_reveal_failures_with_file_code(tmp_path: Path, monkeypatch) -> None:
    editor = _Editor()
    editor.web = MagicMock()
    editor.mw = MagicMock()
    media_path = tmp_path / "clip.wav"
    media_path.write_bytes(b"RIFFfakeWAVE")
    statuses: list[tuple[object, str]] = []
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_settings_actions.reveal_file",
        lambda _path: (_ for _ in ()).throw(AudioProcessingError("Could not open the containing folder.")),
    )
    deps = SimpleNamespace(
        eval_status=lambda _editor, message, kind="info": statuses.append((message, kind)),
        is_busy=lambda _session: False,
        still_processing_message="Still processing. Please wait.",
    )

    show_media_file(editor, object(), media_path, deps)

    assert statuses == [
        (
            {
                "code": "AQE-FILE-001",
                "message": "Could not open the containing folder.",
            },
            "error",
        )
    ]
