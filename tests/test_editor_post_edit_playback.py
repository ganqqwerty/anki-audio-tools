"""Retryable editor bootstrap-intent tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor import editor_frontend
from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.contracts_generated import (
    AutoplayKind,
    EditorIntentReceipt,
    Outcome,
)
from anki_audio_quick_editor.editor_callbacks import _replace_current_field_after_render
from anki_audio_quick_editor.editor_pending_intent import (
    consume_editor_intent_receipt,
    create_pending_editor_intent,
    pending_editor_intent_payload,
)
from anki_audio_quick_editor.editor_runtime import SESSIONS
from anki_audio_quick_editor.editor_session import (
    EditorSession,
    PendingEditorStatus,
    ProcessingState,
)
from anki_audio_quick_editor.editor_session_types import PostEditAutoplayPreference


def test_standard_render_replacement_records_target_bound_pending_intent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    editor, session = _editor_with_session(tmp_path, field_index=0, filename="clip.mp3")
    session.processing = ProcessingState(next_status_summary="Increased volume by 15 dB.")
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    _replace_current_field_after_render(
        editor,
        AudioEditState("clip.mp3", volume_db=3.0),
        "clip__aqe.mp3",
    )

    intent = session.pending_editor_intent
    assert editor.note.fields == ["[sound:clip__aqe.mp3]"]
    assert session.pending_status == PendingEditorStatus(0, message="Increased volume by 15 dB.")
    assert intent is not None
    assert intent.source_kind.value == "generated_edit"
    assert intent.target.field_ord == 0
    assert intent.target.source_filename == "clip__aqe.mp3"
    assert intent.target.backend_media_generation == session.backend_media_generation


def test_standard_render_replacement_uses_session_field_when_focus_changes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    editor, session = _editor_with_session(tmp_path, field_index=1, filename="second.mp3")
    editor.currentField = 0
    editor.note.fields = ["[sound:first.mp3]", "[sound:second.mp3]"]
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    _replace_current_field_after_render(
        editor,
        AudioEditState("second.mp3", left_trim_ms=100),
        "second__aqe.mp3",
    )

    assert editor.note.fields == ["[sound:first.mp3]", "[sound:second__aqe.mp3]"]
    assert editor.loadNote.call_args.kwargs == {"focusTo": 1}
    assert session.pending_editor_intent is not None
    assert session.pending_editor_intent.target.field_ord == 1
    assert session.pending_editor_intent.target.source_filename == "second__aqe.mp3"


def test_pending_intent_payload_retries_until_exact_terminal_receipt() -> None:
    session = EditorSession(
        note_id=11,
        field_index=2,
        current_filename="clip__aqe.mp3",
        backend_media_generation=4,
    )
    create_pending_editor_intent(
        session,
        2,
        require_graph_redraw=True,
        source_kind="generated_edit",
        expected_duration_ms=1200,
        now_epoch_ms=100,
    )

    first = pending_editor_intent_payload(session, now_epoch_ms=101)
    second = pending_editor_intent_payload(session, now_epoch_ms=102)

    assert first == second
    assert first is not None
    assert first["schemaVersion"] == 1
    assert first["target"] == {
        "backendMediaGeneration": 4,
        "editorSessionId": session.editor_session_id,
        "fieldOrd": 2,
        "noteId": 11,
        "sourceFilename": "clip__aqe.mp3",
    }
    assert not consume_editor_intent_receipt(
        session,
        EditorIntentReceipt("other", session.editor_session_id, Outcome.FAILED, 1),
    )
    assert session.pending_editor_intent is not None

    delivery_id = session.pending_editor_intent.delivery_id
    assert consume_editor_intent_receipt(
        session,
        EditorIntentReceipt(
            delivery_id,
            session.editor_session_id,
            Outcome.AUTOPLAY_ACCEPTED,
            1,
        ),
    )
    assert pending_editor_intent_payload(session, now_epoch_ms=103) is None
    assert not consume_editor_intent_receipt(
        session,
        EditorIntentReceipt(
            delivery_id,
            session.editor_session_id,
            Outcome.AUTOPLAY_ACCEPTED,
            1,
        ),
    )


def test_pending_intent_payload_discards_expired_or_retargeted_delivery() -> None:
    session = EditorSession(
        note_id=11,
        field_index=0,
        current_filename="clip.mp3",
        backend_media_generation=3,
    )
    create_pending_editor_intent(
        session,
        0,
        require_graph_redraw=False,
        source_kind="existing_media",
        expected_duration_ms=None,
        now_epoch_ms=100,
    )
    session.backend_media_generation += 1

    assert pending_editor_intent_payload(session, now_epoch_ms=101) is None
    assert session.pending_editor_intent is None

    create_pending_editor_intent(
        session,
        0,
        require_graph_redraw=False,
        source_kind="existing_media",
        expected_duration_ms=None,
        now_epoch_ms=100,
    )
    assert pending_editor_intent_payload(session, now_epoch_ms=30_100) is None


def test_frontend_request_adapter_creates_existing_media_intent() -> None:
    class Editor:
        pass

    editor = Editor()
    session = EditorSession(
        note_id=11,
        field_index=1,
        current_filename="clip.mp3",
        backend_media_generation=8,
    )
    session.post_edit_autoplay_by_field[1] = PostEditAutoplayPreference(
        kind=AutoplayKind.REPEAT,
        repeat_pause_ms=500,
    )
    SESSIONS[editor] = session
    deps = SimpleNamespace(sessions=SESSIONS)

    editor_frontend.request_playback_after_edit(
        editor,
        1,
        deps,
        source_kind="existing_media",
        expected_duration_ms=1200,
    )

    payload = editor_frontend.pending_editor_intent_payload(session)
    assert payload is not None
    assert payload["sourceKind"] == "existing_media"
    assert payload["autoplay"]["expectedDurationMs"] == 1200
    assert payload["autoplay"]["kind"] == "repeat"
    assert payload["autoplay"]["repeatPauseMs"] == 500
    assert session.post_edit_autoplay_by_field == {}


def _editor_with_session(
    tmp_path: Path,
    *,
    field_index: int,
    filename: str,
) -> tuple[object, EditorSession]:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / filename).write_bytes(b"source")

    class Editor:
        pass

    editor = Editor()
    editor.currentField = field_index
    editor.note = SimpleNamespace(fields=[f"[sound:{filename}]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    session = EditorSession(
        note_id=11,
        state=AudioEditState(filename),
        field_index=field_index,
        current_filename=filename,
    )
    SESSIONS[editor] = session
    return editor, session
