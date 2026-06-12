"""Integration tests for persistent undo editor wiring."""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_callbacks import _handle_bridge_command
from anki_audio_quick_editor.editor_persistent_undo import collection_id_for_editor
from anki_audio_quick_editor.editor_runtime import SESSIONS
from anki_audio_quick_editor.editor_webview_injection import editor_injection_script
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
    SESSIONS.clear()
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

    session = SESSIONS[editor]
    assert editor.note.fields == [f"[sound:{old_media.name}]"]
    assert session.current_filename == old_media.name
    assert session.state == AudioEditState(old_media.name)


def test_persistent_undo_refuses_when_old_media_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    SESSIONS.clear()
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
    SESSIONS.clear()
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
    SESSIONS.clear()
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

    config = _embedded_config(script)
    assert config["initialHistoryAvailabilityByField"] == {
        "0": {"canUndo": True, "canRedo": False}
    }
    assert config["initialHistorySnapshotsByField"] == {
        "0": {
            "canUndo": True,
            "canRedo": False,
            "undoItems": [{"id": "persistent:1", "label": "Increased speed to x1.5."}],
            "redoItems": [],
        }
    }


def test_editor_injection_embeds_persistent_undo_chain(
    tmp_path: Path,
    monkeypatch,
) -> None:
    SESSIONS.clear()
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    for name in ("clip0.mp3", "clip1.mp3", "clip2.mp3", "clip3.mp3"):
        (media_dir / name).write_bytes(name.encode("utf-8"))
    db_path = tmp_path / "persistent_undo.sqlite3"
    editor = _persistent_undo_editor(
        media_dir,
        note_id=1001,
        field_html="[sound:clip3.mp3]",
        config={"editor_history_size": 2},
    )
    _append_persistent_operation(db_path, editor, old_filename="clip0.mp3", new_filename="clip1.mp3", status="First edit")
    _append_persistent_operation(db_path, editor, old_filename="clip1.mp3", new_filename="clip2.mp3", status="Second edit")
    _append_persistent_operation(db_path, editor, old_filename="clip2.mp3", new_filename="clip3.mp3", status="Third edit")
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )

    script = editor_injection_script(editor, editor.note)

    config = _embedded_config(script)
    assert config["initialHistorySnapshotsByField"]["0"]["undoItems"] == [
        {"id": "persistent:3", "label": "Third edit"},
        {"id": "persistent:2", "label": "Second edit"},
    ]


def test_editor_injection_disables_persistent_undo_for_unrelated_current_field(
    tmp_path: Path,
    monkeypatch,
) -> None:
    SESSIONS.clear()
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

    script = editor_injection_script(editor, editor.note)

    config = _embedded_config(script)
    assert config["initialHistoryAvailabilityByField"] == {
        "0": {"canUndo": False, "canRedo": False}
    }
    assert config["initialHistorySnapshotsByField"] == {
        "0": {"canUndo": False, "canRedo": False, "undoItems": [], "redoItems": []}
    }


def test_persistent_history_jump_restores_selected_depth_and_marks_rows(
    tmp_path: Path,
    monkeypatch,
) -> None:
    SESSIONS.clear()
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    for name in ("clip0.mp3", "clip1.mp3", "clip2.mp3", "clip3.mp3"):
        (media_dir / name).write_bytes(name.encode("utf-8"))
    db_path = tmp_path / "persistent_undo.sqlite3"
    editor = _persistent_undo_editor(
        media_dir,
        note_id=1001,
        field_html="[sound:clip3.mp3]",
    )
    first = _append_persistent_operation(db_path, editor, old_filename="clip0.mp3", new_filename="clip1.mp3", status="First edit")
    second = _append_persistent_operation(db_path, editor, old_filename="clip1.mp3", new_filename="clip2.mp3", status="Second edit")
    third = _append_persistent_operation(db_path, editor, old_filename="clip2.mp3", new_filename="clip3.mp3", status="Third edit")
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    _handle_bridge_command(editor, '{"command":"aqe:history-jump","fieldOrd":0,"direction":"undo","steps":2}')

    rows = PersistentHistoryRepository(db_path).recent_undoable(collection_id_for_editor(editor), 1001, 0, limit=10)
    session = SESSIONS[editor]
    assert editor.note.fields == ["[sound:clip1.mp3]"]
    assert session.current_filename == "clip1.mp3"
    assert [row.id for row in rows] == [first]
    assert PersistentHistoryRepository(db_path).latest_undoable(collection_id_for_editor(editor), 1001, 0).id == first
    assert {second, third}.isdisjoint({row.id for row in rows})


def _embedded_config(script: str) -> dict[str, object]:
    match = re.search(r"window\.__AQE_EDITOR_CONFIG__ = (?P<config>\{.*?\});", script)
    assert match is not None
    return json.loads(match.group("config"))


def _persistent_undo_editor(
    media_dir: Path,
    *,
    note_id: int,
    field_html: str,
    config: dict[str, object] | None = None,
):
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
            getConfig=lambda _addon: config or {},
        ),
    )
    return editor


def _append_persistent_operation(
    db_path: Path,
    editor,
    *,
    old_filename: str,
    new_filename: str,
    status: str = "Increased speed to x1.5.",
) -> int:
    return _append_persistent_operation_with_fields(
        db_path,
        editor,
        old_filename=old_filename,
        new_filename=new_filename,
        old_field_html=f"[sound:{old_filename}]",
        new_field_html=f"[sound:{new_filename}]",
        status=status,
    )


def _append_persistent_operation_with_fields(
    db_path: Path,
    editor,
    *,
    old_filename: str,
    new_filename: str,
    old_field_html: str,
    new_field_html: str,
    status: str,
) -> int:
    media_dir = Path(editor.mw.col.media.dir())
    old_fingerprint = media_fingerprint(media_dir / old_filename)
    new_fingerprint = media_fingerprint(media_dir / new_filename)
    return PersistentHistoryRepository(db_path).append_operation(
        PersistentHistoryAppend(
            collection_id=collection_id_for_editor(editor),
            note_id=int(editor.note.id),
            field_index=0,
            operation_type="standard-render",
            old_field_html=old_field_html,
            new_field_html=new_field_html,
            old_filename=old_filename,
            new_filename=new_filename,
            old_state_json=audio_edit_state_to_json(AudioEditState(old_filename)),
            new_state_json=audio_edit_state_to_json(AudioEditState(old_filename, speed=1.5)),
            old_media_sha256=old_fingerprint.sha256,
            old_media_size=old_fingerprint.size,
            new_media_sha256=new_fingerprint.sha256,
            new_media_size=new_fingerprint.size,
            status_summary=status,
            created_at_ms=1234,
        )
    )
