"""Generated editor lifecycle-envelope validation tests."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from tempfile import mkdtemp
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor import editor_lifecycle_bridge
from anki_audio_quick_editor.editor_pending_intent import create_pending_editor_intent
from anki_audio_quick_editor.editor_runtime import SESSIONS
from anki_audio_quick_editor.editor_session import EditorSession


def test_intent_receipt_consumes_only_exact_current_delivery() -> None:
    editor, session = _editor_and_session()
    create_pending_editor_intent(
        session,
        0,
        require_graph_redraw=False,
        source_kind="generated_edit",
        expected_duration_ms=None,
    )
    delivery_id = session.pending_editor_intent.delivery_id

    stale = _envelope("editor.intent-receipt", {
        "deliveryId": "other",
        "editorSessionId": session.editor_session_id,
        "outcome": "autoplay_accepted",
        "schemaVersion": 1,
    })
    assert editor_lifecycle_bridge.on_editor_lifecycle_message((False, None), stale, editor) == (
        True,
        None,
    )
    assert session.pending_editor_intent is not None

    exact = _envelope("editor.intent-receipt", {
        "deliveryId": delivery_id,
        "editorSessionId": session.editor_session_id,
        "outcome": "autoplay_accepted",
        "schemaVersion": 1,
    })
    editor_lifecycle_bridge.on_editor_lifecycle_message((False, None), exact, editor)
    assert session.pending_editor_intent is None
    editor_lifecycle_bridge.on_editor_lifecycle_message((False, None), exact, editor)
    assert session.pending_editor_intent is None


def test_recorder_commands_dispatch_for_typed_target_without_focused_field(monkeypatch) -> None:
    editor, session = _editor_and_session()
    editor.currentField = None
    session.field_index = None
    start = MagicMock()
    stop = MagicMock()
    cancel = MagicMock()
    monkeypatch.setattr(editor_lifecycle_bridge.editor_callbacks, "record_learner_voice", start)
    monkeypatch.setattr(editor_lifecycle_bridge.editor_callbacks, "stop_learner_recording", stop)
    monkeypatch.setattr(editor_lifecycle_bridge.editor_callbacks, "cancel_learner_recording", cancel)
    active_attempt = SimpleNamespace(
        attempt_id=7,
        target=SimpleNamespace(editor_session_id=session.editor_session_id, field_index=0),
    )
    monkeypatch.setattr(
        editor_lifecycle_bridge.editor_runtime,
        "RECORDER_SERVICE",
        SimpleNamespace(active_attempt=active_attempt),
    )

    editor_lifecycle_bridge.on_editor_lifecycle_message(
        (False, None),
        _envelope("editor.recorder-command", {
            "fieldOrd": 0,
            "graphSettings": {"smoothness": "balanced"},
            "kind": "start",
            "schemaVersion": 1,
            "startCursorMs": 125,
        }),
        editor,
    )
    start.assert_called_once_with(
        editor,
        field_index=0,
        graph_settings={"smoothness": "balanced"},
        start_cursor_ms=125,
    )

    editor_lifecycle_bridge.on_editor_lifecycle_message(
        (False, None),
        _envelope("editor.recorder-command", {
            "fieldOrd": 1,
            "kind": "stop",
            "schemaVersion": 1,
        }),
        editor,
    )
    stop.assert_not_called()

    editor_lifecycle_bridge.on_editor_lifecycle_message(
        (False, None),
        _envelope("editor.recorder-command", {
            "fieldOrd": 0,
            "kind": "cancel",
            "reason": "user",
            "schemaVersion": 1,
        }),
        editor,
    )
    cancel.assert_called_once_with(editor, reason="user")


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("schemaVersion",), 2),
        (("target", "backendMediaGeneration"), 4),
        (("target", "editorSessionId"), 999),
        (("target", "fieldOrd"), 1),
        (("target", "noteId"), 12),
        (("target", "sourceFilename"), "other.m4a"),
    ],
)
def test_source_mutation_rejects_every_stale_backend_target(
    monkeypatch,
    path: tuple[str, ...],
    value: object,
) -> None:
    editor, session = _editor_and_session()
    convert = MagicMock()
    monkeypatch.setattr(editor_lifecycle_bridge.editor_callbacks, "convert_async", convert)
    payload = _source_mutation_payload(session)
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    editor_lifecycle_bridge.on_editor_lifecycle_message(
        (False, None),
        _envelope("editor.source-mutation", payload),
        editor,
    )

    convert.assert_not_called()


def test_source_mutation_accepts_current_same_filename_generation_once(monkeypatch) -> None:
    editor, session = _editor_and_session()
    convert = MagicMock()
    monkeypatch.setattr(editor_lifecycle_bridge.editor_callbacks, "convert_async", convert)

    editor_lifecycle_bridge.on_editor_lifecycle_message(
        (False, None),
        _envelope("editor.source-mutation", _source_mutation_payload(session)),
        editor,
    )

    convert.assert_called_once()
    command = convert.call_args.args[1]
    assert command.source_filename == "clip.m4a"
    assert command.overrides.target_format == "mp3"


def test_source_mutation_accepts_target_without_rebinding_edit_history(monkeypatch) -> None:
    editor, session = _editor_and_session()
    payload = _source_mutation_payload(session)
    session.field_index = None
    session.current_filename = None
    convert = MagicMock()
    monkeypatch.setattr(editor_lifecycle_bridge.editor_callbacks, "convert_async", convert)

    editor_lifecycle_bridge.on_editor_lifecycle_message(
        (False, None),
        _envelope("editor.source-mutation", payload),
        editor,
    )

    convert.assert_called_once()


def test_source_mutation_rejects_same_filename_after_bytes_change(monkeypatch) -> None:
    editor, session = _editor_and_session()
    convert = MagicMock()
    monkeypatch.setattr(editor_lifecycle_bridge.editor_callbacks, "convert_async", convert)
    payload = _source_mutation_payload(session)
    media_path: Path = editor._media_path
    previous_mtime = media_path.stat().st_mtime_ns
    media_path.write_bytes(b"replacement")
    os.utime(media_path, ns=(previous_mtime + 1_000_000, previous_mtime + 1_000_000))

    editor_lifecycle_bridge.on_editor_lifecycle_message(
        (False, None),
        _envelope("editor.source-mutation", payload),
        editor,
    )

    convert.assert_not_called()
    assert session.backend_media_target(0, "clip.m4a").generation > payload["target"]["backendMediaGeneration"]


def test_source_mutation_is_rejected_while_application_recorder_is_busy(monkeypatch) -> None:
    editor, session = _editor_and_session()
    convert = MagicMock()
    monkeypatch.setattr(editor_lifecycle_bridge.editor_callbacks, "convert_async", convert)
    monkeypatch.setattr(
        editor_lifecycle_bridge.editor_runtime,
        "RECORDER_SERVICE",
        SimpleNamespace(is_busy=True),
    )

    editor_lifecycle_bridge.on_editor_lifecycle_message(
        (False, None),
        _envelope("editor.source-mutation", _source_mutation_payload(session)),
        editor,
    )

    convert.assert_not_called()


def test_malformed_and_unrelated_messages_do_not_escape_the_boundary() -> None:
    editor, _session = _editor_and_session()
    assert editor_lifecycle_bridge.on_editor_lifecycle_message(
        (False, "prior"),
        "bridge:not-json",
        editor,
    ) == (False, "prior")
    assert editor_lifecycle_bridge.on_editor_lifecycle_message(
        (False, None),
        _envelope("editor.recorder-command", {"kind": "start"}),
        editor,
    ) == (True, None)
    assert editor_lifecycle_bridge.on_editor_lifecycle_message(
        (False, None),
        _envelope("unrelated.command", {}),
        editor,
    ) == (False, None)


def _editor_and_session() -> tuple[object, EditorSession]:
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.m4a]"])
    editor._media_directory = Path(mkdtemp(prefix="aqe-lifecycle-test-"))
    editor._media_path = editor._media_directory / "clip.m4a"
    editor._media_path.write_bytes(b"source")
    editor.mw = SimpleNamespace(
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(editor._media_directory))),
    )
    session = EditorSession(
        note_id=11,
        field_index=0,
        current_filename="clip.m4a",
        backend_media_generation=2,
    )
    session.bind_backend_media_target(0, "clip.m4a", editor._media_path.stat().st_mtime_ns)
    SESSIONS[editor] = session
    return editor, session


def _source_mutation_payload(session: EditorSession) -> dict[str, object]:
    return deepcopy({
        "failure": {
            "attemptId": "none",
            "failureId": "failure-7",
            "fieldInstanceId": "field-2",
            "runtimeId": "runtime-1",
            "sourceInstanceId": "source-6",
        },
        "kind": "convert_to_mp3",
        "schemaVersion": 1,
        "target": {
            "backendMediaGeneration": session.backend_media_generation,
            "editorSessionId": session.editor_session_id,
            "fieldOrd": 0,
            "noteId": session.note_id,
            "sourceFilename": session.current_filename,
        },
    })


def _envelope(command: str, payload: object) -> str:
    return "bridge:" + json.dumps({"command": command, "payload": payload})
