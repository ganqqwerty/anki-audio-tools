"""Integration tests for persistent undo editor wiring."""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_integration import (
    _SESSIONS,
    _handle_bridge_command,
    editor_injection_script,
)
from anki_audio_quick_editor.editor_persistent_undo import collection_id_for_editor
from anki_audio_quick_editor.persistent_history import (
    PersistentHistoryAppend,
    PersistentHistoryRepository,
    audio_edit_state_to_json,
    media_fingerprint,
)


def test_persistent_undo_restores_after_session_history_is_empty(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _SESSIONS.clear()
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    new_media = media_dir / "clip__aqe_1.mp3"
    old_media.write_bytes(b"old")
    new_media.write_bytes(b"new")
    db_path = tmp_path / "persistent_undo.sqlite3"
    editor = _persistent_undo_editor(
        media_dir,
        note_id=1001,
        field_html=f"[sound:{new_media.name}]",
    )
    _append_persistent_operation(
        db_path,
        editor,
        old_filename=old_media.name,
        new_filename=new_media.name,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    _handle_bridge_command(editor, "aqe:undo")

    session = _SESSIONS[editor]
    assert editor.note.fields == [f"[sound:{old_media.name}]"]
    assert session.current_filename == old_media.name
    assert session.state == AudioEditState(old_media.name)


def test_persistent_undo_refuses_when_old_media_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _SESSIONS.clear()
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    new_media = media_dir / "clip__aqe_1.mp3"
    old_media.write_bytes(b"old")
    new_media.write_bytes(b"new")
    db_path = tmp_path / "persistent_undo.sqlite3"
    editor = _persistent_undo_editor(
        media_dir,
        note_id=1001,
        field_html=f"[sound:{new_media.name}]",
    )
    _append_persistent_operation(
        db_path,
        editor,
        old_filename=old_media.name,
        new_filename=new_media.name,
    )
    old_media.unlink()
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )

    _handle_bridge_command(editor, "aqe:undo")

    assert editor.note.fields == [f"[sound:{new_media.name}]"]
    assert any("Nothing to undo" in call.args[0] for call in editor.web.eval.call_args_list)


def test_persistent_undo_refuses_when_field_changed_after_edit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _SESSIONS.clear()
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    new_media = media_dir / "clip__aqe_1.mp3"
    unrelated_media = media_dir / "other.mp3"
    old_media.write_bytes(b"old")
    new_media.write_bytes(b"new")
    unrelated_media.write_bytes(b"other")
    db_path = tmp_path / "persistent_undo.sqlite3"
    editor = _persistent_undo_editor(
        media_dir,
        note_id=1001,
        field_html=f"[sound:{unrelated_media.name}]",
    )
    _append_persistent_operation(
        db_path,
        editor,
        old_filename=old_media.name,
        new_filename=new_media.name,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )

    _handle_bridge_command(editor, "aqe:undo")

    assert editor.note.fields == [f"[sound:{unrelated_media.name}]"]


def test_editor_injection_embeds_persistent_undo_availability(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _SESSIONS.clear()
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    new_media = media_dir / "clip__aqe_1.mp3"
    old_media.write_bytes(b"old")
    new_media.write_bytes(b"new")
    db_path = tmp_path / "persistent_undo.sqlite3"
    editor = _persistent_undo_editor(
        media_dir,
        note_id=1001,
        field_html=f"[sound:{new_media.name}]",
    )
    _append_persistent_operation(
        db_path,
        editor,
        old_filename=old_media.name,
        new_filename=new_media.name,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )

    script = editor_injection_script(editor, editor.note)

    match = re.search(r"window\.__AQE_EDITOR_CONFIG__ = (?P<config>\{.*?\});", script)
    assert match is not None
    config = json.loads(match.group("config"))
    assert config["initialHistoryAvailabilityByField"] == {
        "0": {"canUndo": True, "canRedo": False}
    }


def _persistent_undo_editor(media_dir: Path, *, note_id: int, field_html: str):
    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(id=note_id, fields=[field_html])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        col=SimpleNamespace(media=SimpleNamespace(dir=lambda: str(media_dir))),
        addonManager=SimpleNamespace(
            addonFromModule=lambda _module: "addon",
            addonsFolder=lambda _addon: str(media_dir.parent / "addon"),
            getConfig=lambda _addon: {},
        ),
    )
    return editor


def _append_persistent_operation(
    db_path: Path,
    editor,
    *,
    old_filename: str,
    new_filename: str,
) -> None:
    media_dir = Path(editor.mw.col.media.dir())
    old_fingerprint = media_fingerprint(media_dir / old_filename)
    new_fingerprint = media_fingerprint(media_dir / new_filename)
    PersistentHistoryRepository(db_path).append_operation(
        PersistentHistoryAppend(
            collection_id=collection_id_for_editor(editor),
            note_id=int(editor.note.id),
            field_index=0,
            operation_type="standard-render",
            old_field_html=f"[sound:{old_filename}]",
            new_field_html=f"[sound:{new_filename}]",
            old_filename=old_filename,
            new_filename=new_filename,
            old_state_json=audio_edit_state_to_json(AudioEditState(old_filename)),
            new_state_json=audio_edit_state_to_json(AudioEditState(old_filename, speed=1.5)),
            old_media_sha256=old_fingerprint.sha256,
            old_media_size=old_fingerprint.size,
            new_media_sha256=new_fingerprint.sha256,
            new_media_size=new_fingerprint.size,
            status_summary="Increased speed to x1.5.",
            created_at_ms=1234,
        )
    )
