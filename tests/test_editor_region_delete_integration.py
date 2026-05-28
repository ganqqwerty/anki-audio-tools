"""Editor region-delete integration tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    EditorSession,
    _parse_region_delete_request,
    _replace_current_field_after_region_delete,
)


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
    _SESSIONS[editor] = session
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

    _replace_current_field_after_region_delete(editor, request, generated.name, 500, 0.0)

    assert editor.note.fields == ["[sound:other.mp3]", "<b>Prompt</b> [sound:clip__aqe_cut.mp3] extra"]
    assert session.current_filename == "clip__aqe_cut.mp3"
    assert session.state == AudioEditState("clip__aqe_cut.mp3")
    assert session.cursor_ms == 0
    assert session.redo_history.pop() is None
    assert session.undo_history.pop().filename == "clip.mp3"
    assert editor.loadNote.call_args.kwargs == {"focusTo": 1}
    assert any(
        "__aqeSetHistoryAvailability(1, true, false)" in call.args[0]
        for call in editor.web.evalWithCallback.call_args_list
    )
    assert session.pending_post_edit_playback_field_index == 1
    assert session.pending_post_edit_playback_generation == session.post_edit_playback_generation
    assert session.pending_post_edit_playback_source_filename == "clip__aqe_cut.mp3"
