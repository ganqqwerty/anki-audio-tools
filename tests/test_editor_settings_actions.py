from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.editor_session import EditorSession, LearnerRecordingState
from anki_audio_quick_editor.editor_settings_actions import show_learner_recording_file


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
