from __future__ import annotations

from pathlib import Path

import pytest

from anki_audio_quick_editor.editor_session import EditorSession
from anki_audio_quick_editor.errors import AudioProcessingError
from anki_audio_quick_editor.recorder.model import (
    BackendMediaGeneration,
    CaptureSpec,
    RecorderTarget,
)
from anki_audio_quick_editor.recorder.service import RecorderService


class Controller:
    def cancel(self, _reason: str) -> None:
        pass

    def dispose(self) -> None:
        pass


def test_backend_source_mutation_guard_rejects_active_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = RecorderService()
    session = EditorSession(note_id=7, field_index=0, current_filename="source.wav")
    service.begin(
        RecorderTarget(
            session.editor_session_id,
            session.note_id,
            0,
            "source.wav",
            BackendMediaGeneration(session.backend_media_generation),
        ),
        CaptureSpec("take.wav", tmp_path / "take.wav", 1000, 0),
        Controller(),
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_session.RECORDER_SERVICE", service)

    with pytest.raises(AudioProcessingError, match="voice recording"):
        session.begin_processing(field_index=0, source_filename="source.wav")

    assert session.processing.active is False
    assert service.is_busy
