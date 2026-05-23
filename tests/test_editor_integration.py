"""Core editor integration tests."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    BRIDGE_COMMANDS,
    EditorSession,
    UndoHistory,
    _audio_field_indices,
    _handle_bridge_command,
    _initial_status_by_field,
    _parse_region_delete_request,
    _replace_current_field_after_region_delete,
    _set_busy,
    register_editor_hooks,
)


def test_register_editor_hooks() -> None:
    hooks = SimpleNamespace(editor_did_init=MagicMock(), editor_will_load_note=MagicMock())

    register_editor_hooks(hooks)

    hooks.editor_did_init.append.assert_called_once()
    hooks.editor_will_load_note.append.assert_called_once()


def test_entrypoint_registers_editor_startup_hook() -> None:
    import aqt

    import anki_audio_quick_editor

    importlib.reload(anki_audio_quick_editor)

    assert aqt.gui_hooks.main_window_did_init.append.call_count == 7


def test_editor_init_registers_all_bridge_commands(tmp_path: Path) -> None:
    from anki_audio_quick_editor.editor_integration import _on_editor_did_init

    editor = SimpleNamespace(_links={}, mw=MagicMock(), web=MagicMock(), currentField=0)
    editor.mw.col.media.dir.return_value = str(tmp_path)

    _on_editor_did_init(editor)

    assert set(BRIDGE_COMMANDS) <= set(editor._links)


def test_audio_field_indices_are_detected_from_note_fields() -> None:
    note = SimpleNamespace(fields=["plain", "<b>[sound:first.mp3]</b>", "[sound:movie.mp4]"])

    assert _audio_field_indices(note) == [1]


def test_undo_history_restores_last_audio_modification_only() -> None:
    history = UndoHistory()
    original = AudioEditState("source.wav")
    trimmed = original.trim_left(100)

    history.push(original, "source.wav")
    history.push(trimmed, "source__aqe_first.mp3")

    assert history.pop().filename == "source__aqe_first.mp3"
    assert history.pop().filename == "source.wav"
    assert history.pop() is None


def test_editor_undo_and_redo_restore_audio_references_without_processing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    original = media_dir / "clip.mp3"
    generated = media_dir / "clip__aqe_first.mp3"
    original.write_bytes(b"original")
    generated.write_bytes(b"generated")
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip__aqe_first.mp3]"])
    editor.web = MagicMock()
    reload_statuses: list[dict[int, dict[str, str]]] = []
    editor.loadNote = MagicMock(side_effect=lambda **_kwargs: reload_statuses.append(_initial_status_by_field(session)))
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    generated_state = AudioEditState("clip.mp3", speed=1.1)
    session = EditorSession(
        state=generated_state,
        field_index=0,
        current_filename="clip__aqe_first.mp3",
        status_summary="Increased speed to x1.10.",
        source_mtime_ns=generated.stat().st_mtime_ns,
    )
    session.undo_history.push(AudioEditState("clip.mp3"), "clip.mp3", status_summary="Original audio.")
    _SESSIONS[editor] = session

    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    _handle_bridge_command(editor, "aqe:undo")

    assert editor.note.fields == ["[sound:clip.mp3]"]
    assert session.state == AudioEditState("clip.mp3")
    assert session.current_filename == "clip.mp3"
    assert session.redo_history.pop().filename == "clip__aqe_first.mp3"
    assert reload_statuses[0] == {0: {"kind": "info", "message": "Undid: Original audio."}}

    session.redo_history.push(
        generated_state,
        "clip__aqe_first.mp3",
        status_summary="Increased speed to x1.10.",
    )
    _handle_bridge_command(editor, "aqe:redo")

    assert editor.note.fields == ["[sound:clip__aqe_first.mp3]"]
    assert session.state == generated_state
    assert session.current_filename == "clip__aqe_first.mp3"
    assert session.undo_history.pop().filename == "clip.mp3"
    assert editor.loadNote.call_count == 2
    assert reload_statuses[1] == {0: {"kind": "info", "message": "Redid: Increased speed to x1.10."}}
    evals = [call.args[0] for call in editor.web.eval.call_args_list]
    assert any("window.__aqeSetHistoryAvailability && window.__aqeSetHistoryAvailability(0, false, true)" in call for call in evals)
    assert any("window.__aqeSetHistoryAvailability && window.__aqeSetHistoryAvailability(0, true, false)" in call for call in evals)
    assert sum("__aqePlayAfterEdit" in call.args[0] for call in editor.web.evalWithCallback.call_args_list) == 2


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

        deps = SimpleNamespace(
            render_audio_region_deleted=deleted_renderer,
            render_audio_region_kept=kept_renderer,
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
    assert "__aqePlayAfterEdit(1)" in editor.web.evalWithCallback.call_args.args[0]


def test_editor_settings_command_opens_settings_and_refreshes_after_save(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"audio")
    callbacks: list[object] = []
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    reload_statuses: list[dict[int, dict[str, str]]] = []
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        analysis_busy=True,
        playback_active=True,
        playback_paused=True,
        playback_preparing=True,
    )
    editor.loadNote = MagicMock(side_effect=lambda **_kwargs: reload_statuses.append(_initial_status_by_field(session)))
    _SESSIONS[editor] = session

    def fake_settings_opener(callback):
        callbacks.append(callback)

    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.SETTINGS_OPENER", fake_settings_opener)
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)

    _handle_bridge_command(editor, "aqe:settings")

    assert len(callbacks) == 1
    assert any("Opened settings." in call.args[0] for call in editor.web.eval.call_args_list)

    callbacks[0].on_saved()

    assert session.analysis_generation == 1
    assert session.processing is False
    assert session.analysis_busy is False
    assert session.playback_active is False
    assert session.playback_paused is False
    assert session.playback_preparing is False
    assert reload_statuses == [{0: {"kind": "info", "message": "Closed settings."}}]
    assert editor.loadNote.call_args.args == ()
    assert editor.loadNote.call_args.kwargs == {"focusTo": 0}
    assert any("window.__aqeEditorDispose" in call.args[0] for call in editor.web.eval.call_args_list)


def test_editor_settings_command_reports_closed_settings_without_refresh_on_close(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"audio")
    callbacks: list[object] = []

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    _SESSIONS[editor] = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
    )

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_runtime.SETTINGS_OPENER",
        lambda callback: callbacks.append(callback),
    )

    _handle_bridge_command(editor, "aqe:settings")
    callbacks[0].on_closed()

    assert any("Opened settings." in call.args[0] for call in editor.web.eval.call_args_list)
    assert any("Closed settings." in call.args[0] for call in editor.web.eval.call_args_list)
    editor.loadNote.assert_not_called()


def test_set_busy_falls_back_to_session_field_index() -> None:
    class Editor:
        pass

    editor = Editor()
    editor.currentField = None
    editor.web = MagicMock()
    _SESSIONS[editor] = EditorSession(field_index=2)

    _set_busy(editor, False)

    assert "window.__aqeSetBusy" in editor.web.eval.call_args.args[0]
    assert "(2, false" in editor.web.eval.call_args.args[0]
