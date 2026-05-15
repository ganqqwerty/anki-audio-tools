"""Tests for the thin Anki editor bridge layer."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
from anki_audio_quick_editor.editor_integration import (
    _ANALYSIS_CACHE,
    _SESSIONS,
    BRIDGE_COMMANDS,
    EditorSession,
    UndoHistory,
    _analyze_prosody_cached,
    _audio_field_indices,
    _prosody_cache_key,
    _reveal_file,
    _set_busy,
    register_editor_hooks,
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

    assert aqt.gui_hooks.main_window_did_init.append.call_count == 5


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


def test_prosody_cache_key_uses_path_size_and_mtime(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"one")
    first_key = _prosody_cache_key(source)
    source.write_bytes(b"one-two")
    second_key = _prosody_cache_key(source)

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

    monkeypatch.setattr("anki_audio_quick_editor.editor_integration.analyze_prosody", fake_analyze)
    _ANALYSIS_CACHE.clear()

    assert _analyze_prosody_cached(source, AudioProcessingConfig()) is track
    assert _analyze_prosody_cached(source, AudioProcessingConfig()) is track
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


def test_reveal_file_selects_file_on_macos(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.editor_integration.platform.system", lambda: "Darwin")
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration._run_detached",
        lambda command: commands.append(command),
    )

    _reveal_file(source)

    assert commands == [("open", "-R", str(source.resolve()))]


def test_reveal_file_selects_file_on_windows(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.editor_integration.platform.system", lambda: "Windows")
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration._run_detached",
        lambda command: commands.append(command),
    )

    _reveal_file(source)

    assert commands == [("explorer", f"/select,{source.resolve()}")]


def test_reveal_file_opens_parent_folder_elsewhere(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    folders: list[Path] = []

    monkeypatch.setattr("anki_audio_quick_editor.editor_integration.platform.system", lambda: "Linux")
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_integration._open_parent_folder",
        lambda folder: folders.append(folder),
    )

    _reveal_file(source)

    assert folders == [source.resolve().parent]
