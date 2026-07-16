"""Editor region-delete integration tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_callbacks import (
    _parse_region_delete_request,
    _replace_current_field_after_region_delete,
)
from anki_audio_quick_editor.editor_region_delete import delete_selection_with_request
from anki_audio_quick_editor.editor_runtime import SESSIONS
from anki_audio_quick_editor.editor_session import EditorSession


def _region_request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "operation": "delete-selection",
        "ord": 0,
        "sourceFilename": "clip.wav",
        "selectionStartMs": 250,
        "selectionEndMs": 750,
        "cursorMs": 300,
        "durationMs": 1000,
        "trigger": "button",
        "playbackActive": False,
    }
    request.update(overrides)
    return request


def _public_region_delete_deps(tmp_path: Path, **overrides: object) -> SimpleNamespace:
    statuses: list[tuple[str, Any]] = []
    busy: list[tuple[int | None, bool]] = []
    session = SimpleNamespace()
    values: dict[str, object] = {
        "sessions": {},
        "is_busy": lambda _session: False,
        "still_processing_message": "Still processing. Please wait.",
        "current_field_index": lambda _editor: 0,
        "resolve_requested_field_media": lambda *_args: object(),
        "current_media_path": lambda _editor: (session, tmp_path / "clip.wav"),
        "set_busy": lambda _editor, value: busy.append((None, value)),
        "set_busy_for_field": lambda _editor, field, value, *_args: busy.append((field, value)),
        "eval_status": lambda _editor, message, *, kind: statuses.append((kind, message)),
        "statuses": statuses,
        "busy_calls": busy,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_public_region_delete_rejects_malformed_request_and_releases_busy(tmp_path: Path) -> None:
    deps = _public_region_delete_deps(tmp_path)

    delete_selection_with_request(object(), {"operation": "invalid"}, deps)

    assert deps.busy_calls == [(None, False)]
    assert deps.statuses[0][0] == "error"
    assert deps.statuses[0][1]["code"] == "AQE-AUDIO-001"


def test_public_region_delete_rejects_busy_session_without_starting_work(tmp_path: Path) -> None:
    editor = object()
    existing = object()
    deps = _public_region_delete_deps(
        tmp_path,
        sessions={editor: existing},
        is_busy=lambda session: session is existing,
    )

    delete_selection_with_request(editor, _region_request(), deps)

    assert deps.busy_calls == []
    assert deps.statuses == [("processing", "Still processing. Please wait.")]


def test_public_region_delete_rejects_inactive_field(tmp_path: Path) -> None:
    deps = _public_region_delete_deps(tmp_path, current_field_index=lambda _editor: 1)

    delete_selection_with_request(object(), _region_request(), deps)

    assert deps.busy_calls == [(0, False)]
    assert deps.statuses[0][0] == "error"
    assert deps.statuses[0][1]["code"] == "AQE-GRAPH-001"


def test_public_region_delete_rejects_unresolved_or_changed_media(tmp_path: Path) -> None:
    unresolved = _public_region_delete_deps(tmp_path, resolve_requested_field_media=lambda *_args: None)
    delete_selection_with_request(object(), _region_request(), unresolved)
    assert unresolved.busy_calls == [(0, False)]
    assert unresolved.statuses[0][1]["code"] == "AQE-GRAPH-001"

    changed = _public_region_delete_deps(
        tmp_path,
        current_media_path=lambda _editor: (SimpleNamespace(), tmp_path / "changed.wav"),
    )
    delete_selection_with_request(object(), _region_request(), changed)
    assert changed.busy_calls == [(0, False)]
    assert changed.statuses[0][1]["code"] == "AQE-GRAPH-001"


def test_public_region_delete_rejects_whole_clip(tmp_path: Path) -> None:
    deps = _public_region_delete_deps(tmp_path)

    delete_selection_with_request(
        object(),
        _region_request(selectionStartMs=0, selectionEndMs=1000),
        deps,
    )

    assert deps.busy_calls == [(0, False)]
    assert deps.statuses[0][0] == "warning"


def test_region_delete_request_parser_normalizes_payload() -> None:
    request = _parse_region_delete_request(
        {
            "ord": "2",
            "sourceFilename": "../clip.wav",
            "selectionStartMs": 1200.2,
            "selectionEndMs": 300.7,
            "cursorMs": 9999,
            "durationMs": 2000,
            "trigger": "backspace",
            "playbackActive": True,
        }
    )
    assert request is not None
    assert request.field_index == 2
    assert request.source_filename == "clip.wav"
    assert request.selection_start_ms == 301
    assert request.selection_end_ms == 1200
    assert request.cursor_ms == 2000
    assert request.trigger == "backspace"
    assert request.playback_active is True
    assert request.operation == "delete-selection"


def test_region_delete_request_parser_accepts_delete_rest_operation() -> None:
    request = _parse_region_delete_request(
        {
            "operation": "delete-rest",
            "ord": 0,
            "sourceFilename": "clip.wav",
            "selectionStartMs": 250,
            "selectionEndMs": 750,
            "cursorMs": 300,
            "durationMs": 1000,
            "trigger": "button",
            "playbackActive": False,
        }
    )
    assert request is not None
    assert request.operation == "delete-rest"
    assert request.selection_start_ms == 250
    assert request.selection_end_ms == 750


def test_delete_rest_removed_duration_counts_outside_selection() -> None:
    request = _parse_region_delete_request(
        {
            "operation": "delete-rest",
            "ord": 0,
            "sourceFilename": "clip.wav",
            "selectionStartMs": 250,
            "selectionEndMs": 700,
            "cursorMs": 300,
            "durationMs": 1000,
            "trigger": "button",
        }
    )
    assert request is not None
    assert request.selected_duration_ms == 450
    assert request.removed_duration_ms == 550


def test_region_delete_request_parser_rejects_unknown_operation() -> None:
    request = _parse_region_delete_request(
        {
            "operation": "replace-with-silence",
            "ord": 0,
            "sourceFilename": "clip.wav",
            "selectionStartMs": 250,
            "selectionEndMs": 750,
            "cursorMs": 300,
            "durationMs": 1000,
            "trigger": "button",
        }
    )
    assert request is None


def test_region_delete_request_parser_rejects_explicit_malformed_operations() -> None:
    for operation in ("", False, 0):
        request = _parse_region_delete_request(
            {
                "operation": operation,
                "ord": 0,
                "sourceFilename": "clip.wav",
                "selectionStartMs": 250,
                "selectionEndMs": 750,
                "cursorMs": 300,
                "durationMs": 1000,
                "trigger": "button",
            }
        )
        assert request is None


def test_region_operation_renderer_routes_delete_rest_to_keep_renderer(tmp_path: Path) -> None:
    from anki_audio_quick_editor.editor_region_delete import render_region_operation

    calls: list[tuple[str, int, int]] = []
    request = _parse_region_delete_request(
        {
            "operation": "delete-rest",
            "ord": 0,
            "sourceFilename": "clip.wav",
            "selectionStartMs": 250,
            "selectionEndMs": 750,
            "cursorMs": 300,
            "durationMs": 1000,
            "trigger": "button",
        }
    )
    assert request is not None
    expected = object()
    deps = SimpleNamespace(
        render_audio_region_deleted=lambda *_args, **_kwargs: calls.append(("delete", _args[1], _args[2])),
        render_audio_region_kept=lambda *_args, **_kwargs: calls.append(("keep", _args[1], _args[2])) or expected,
    )

    result = render_region_operation(
        deps,
        tmp_path / "clip.wav",
        request,
        AudioProcessingConfig(),
        output_path=tmp_path / "out.mp3",
        on_command=None,
    )
    assert result is expected
    assert calls == [("keep", 250, 750)]


def test_region_operation_renderer_routes_delete_selection_to_delete_renderer(tmp_path: Path) -> None:
    from anki_audio_quick_editor.editor_region_delete import render_region_operation

    for payload in ({}, {"operation": "delete-selection"}):
        calls: list[tuple[str, int, int]] = []
        request = _parse_region_delete_request(
            {
                **payload,
                "ord": 0,
                "sourceFilename": "clip.wav",
                "selectionStartMs": 250,
                "selectionEndMs": 750,
                "cursorMs": 300,
                "durationMs": 1000,
                "trigger": "button",
            }
        )
        assert request is not None
        expected = object()

        def deleted_renderer(
            _source_path: Path,
            start_ms: int,
            end_ms: int,
            *_args: object,
            _calls: list[tuple[str, int, int]] = calls,
            _expected: object = expected,
            **_kwargs: object,
        ) -> object:
            _calls.append(("delete", start_ms, end_ms))
            return _expected

        def kept_renderer(
            _source_path: Path,
            start_ms: int,
            end_ms: int,
            *_args: object,
            _calls: list[tuple[str, int, int]] = calls,
            **_kwargs: object,
        ) -> object:
            _calls.append(("keep", start_ms, end_ms))
            return object()

        deps = SimpleNamespace(render_audio_region_deleted=deleted_renderer, render_audio_region_kept=kept_renderer)
        result = render_region_operation(
            deps,
            tmp_path / "clip.wav",
            request,
            AudioProcessingConfig(),
            output_path=tmp_path / "out.mp3",
            on_command=None,
        )
        assert result is expected
        assert calls == [("delete", 250, 750)]


def test_region_delete_replacement_updates_only_requested_field_and_history(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    current = media_dir / "clip.mp3"
    generated = media_dir / "clip__aqe_cut.mp3"
    current.write_bytes(b"current")
    generated.write_bytes(b"generated")

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 1
    editor.note = SimpleNamespace(fields=["[sound:other.mp3]", "<b>Prompt</b> [sound:clip.mp3] extra"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=1,
        current_filename="clip.mp3",
        source_mtime_ns=current.stat().st_mtime_ns,
    )
    SESSIONS[editor] = session
    request = _parse_region_delete_request(
        {
            "ord": 1,
            "sourceFilename": "clip.mp3",
            "selectionStartMs": 250,
            "selectionEndMs": 750,
            "cursorMs": 300,
            "durationMs": 1000,
            "trigger": "button",
        }
    )
    assert request is not None
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())
    persistent_recorder = MagicMock()
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._record_standard_persistent_undo",
        persistent_recorder,
    )

    _replace_current_field_after_region_delete(editor, request, generated.name, 500, 0.0)

    assert editor.note.fields == ["[sound:other.mp3]", "<b>Prompt</b> [sound:clip__aqe_cut.mp3] extra"]
    assert session.current_filename == "clip__aqe_cut.mp3"
    assert session.state == AudioEditState("clip__aqe_cut.mp3")
    assert session.cursor_ms == 0
    assert session.redo_history.pop() is None
    assert session.undo_history.pop().filename == "clip.mp3"
    assert session.pending_status is not None
    assert session.pending_status.field_index == 1
    assert session.pending_status.kind == "info"
    assert session.pending_status.message == "Deleted selection 250-750 ms."
    assert editor.loadNote.call_args.kwargs == {"focusTo": 1}
    assert any(
        "__aqeSetHistoryAvailability(1, true, false)" in call.args[0]
        for call in editor.web.evalWithCallback.call_args_list
    )
    assert session.post_edit_playback.pending_field_index == 1
    assert session.post_edit_playback.pending_generation == session.post_edit_playback.generation
    assert session.post_edit_playback.pending_source_filename == "clip__aqe_cut.mp3"
    persistent_recorder.assert_called_once()
    call = persistent_recorder.call_args.kwargs
    assert call["field_index"] == 1
    assert call["old_field_html"] == "<b>Prompt</b> [sound:clip.mp3] extra"
    assert call["new_field_html"] == "<b>Prompt</b> [sound:clip__aqe_cut.mp3] extra"
    assert call["old_filename"] == current.name
    assert call["new_filename"] == generated.name
    assert call["status_summary"] == session.status_summary
