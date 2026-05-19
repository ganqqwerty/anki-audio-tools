"""Core editor integration tests."""

from __future__ import annotations

import importlib
from collections.abc import Callable
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
    _parse_region_delete_request,
    _replace_current_field_after_region_delete,
    _set_busy,
    register_editor_hooks,
)
from anki_audio_quick_editor.prosody_cache import (
    _ANALYSIS_CACHE,
    analyze_prosody_cached,
    prosody_cache_key,
)
from anki_audio_quick_editor.prosody_types import ProsodyPoint, ProsodyTrack


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
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))))
    generated_state = AudioEditState("clip.mp3", speed=1.1)
    session = EditorSession(
        state=generated_state,
        field_index=0,
        current_filename="clip__aqe_first.mp3",
        source_mtime_ns=generated.stat().st_mtime_ns,
    )
    session.undo_history.push(AudioEditState("clip.mp3"), "clip.mp3")
    _SESSIONS[editor] = session

    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)

    _handle_bridge_command(editor, "aqe:undo")

    assert editor.note.fields == ["[sound:clip.mp3]"]
    assert session.state == AudioEditState("clip.mp3")
    assert session.current_filename == "clip.mp3"
    assert session.redo_history.pop().filename == "clip__aqe_first.mp3"

    session.redo_history.push(generated_state, "clip__aqe_first.mp3")
    _handle_bridge_command(editor, "aqe:redo")

    assert editor.note.fields == ["[sound:clip__aqe_first.mp3]"]
    assert session.state == generated_state
    assert session.current_filename == "clip__aqe_first.mp3"
    assert session.undo_history.pop().filename == "clip.mp3"
    assert editor.loadNote.call_count == 2


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


def test_region_delete_replacement_updates_only_requested_field_and_history(tmp_path: Path) -> None:
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

    _replace_current_field_after_region_delete(editor, request, generated.name, 500, 0.0)

    assert editor.note.fields == ["[sound:other.mp3]", "<b>Prompt</b> [sound:clip__aqe_cut.mp3] extra"]
    assert session.current_filename == "clip__aqe_cut.mp3"
    assert session.state == AudioEditState("clip__aqe_cut.mp3")
    assert session.cursor_ms == 0
    assert session.redo_history.pop() is None
    assert session.undo_history.pop().filename == "clip.mp3"
    assert editor.loadNote.call_args.kwargs == {"focusTo": 1}


def test_editor_settings_command_opens_settings_and_refreshes_after_save(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"audio")
    callbacks: list[Callable[[], None]] = []
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
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
    _SESSIONS[editor] = session

    def fake_settings_opener(callback):
        callbacks.append(callback)

    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.SETTINGS_OPENER", fake_settings_opener)
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)

    _handle_bridge_command(editor, "aqe:settings")

    assert len(callbacks) == 1
    assert any("Opened settings." in call.args[0] for call in editor.web.eval.call_args_list)

    callbacks[0]()

    assert session.analysis_generation == 1
    assert session.processing is False
    assert session.analysis_busy is False
    assert session.playback_active is False
    assert session.playback_paused is False
    assert session.playback_preparing is False
    assert editor.loadNote.call_args.args == ()
    assert editor.loadNote.call_args.kwargs == {"focusTo": 0}
    assert any("window.__aqeEditorDispose" in call.args[0] for call in editor.web.eval.call_args_list)


def test_prosody_cache_key_uses_path_size_and_mtime(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"one")
    first_key = prosody_cache_key(source)
    source.write_bytes(b"one-two")
    second_key = prosody_cache_key(source)

    assert first_key[0] == str(source)
    assert second_key[0] == str(source)
    assert first_key[1] != second_key[1]
    assert isinstance(first_key[2], int)


def test_prosody_cache_reuses_matching_file_identity(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    track = ProsodyTrack(
        duration_ms=1000,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename=source.name,
        analyzer_name="test",
    )
    calls: list[Path] = []

    def fake_analyze(path: Path, _config: AudioProcessingConfig) -> ProsodyTrack:
        calls.append(path)
        return track

    monkeypatch.setattr("anki_audio_quick_editor.prosody_cache.analyze_prosody", fake_analyze)
    _ANALYSIS_CACHE.clear()

    assert analyze_prosody_cached(source, AudioProcessingConfig()) is track
    assert analyze_prosody_cached(source, AudioProcessingConfig()) is track
    assert calls == [source]


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
