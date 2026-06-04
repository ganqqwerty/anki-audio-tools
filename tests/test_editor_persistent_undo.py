"""Tests for editor-facing persistent undo behavior."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.editor_persistent_undo import (
    can_persistent_undo,
    collection_id_for_editor,
    history_db_path_for_editor,
    record_standard_persistent_undo,
    restore_persistent_undo,
)
from anki_audio_quick_editor.editor_processing import replace_current_field_after_render
from anki_audio_quick_editor.editor_session import EditorSession
from anki_audio_quick_editor.persistent_history import (
    PersistentHistoryAppend,
    PersistentHistoryRepository,
    audio_edit_state_to_json,
    media_fingerprint,
)


def test_history_db_path_uses_addon_user_files(tmp_path: Path) -> None:
    editor = _editor(tmp_path / "media", note_id=1001, field_html="[sound:clip.mp3]")

    db_path = history_db_path_for_editor(editor)

    assert db_path == tmp_path / "addon" / "user_files" / "persistent_undo.sqlite3"


def test_can_persistent_undo_requires_matching_old_media(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    new_media = media_dir / "clip__aqe_1.mp3"
    old_media.write_bytes(b"old")
    new_media.write_bytes(b"new")
    db_path = tmp_path / "history.sqlite3"
    editor = _editor(media_dir, note_id=1001, field_html=f"[sound:{new_media.name}]")
    _append_operation(db_path, editor, old_filename=old_media.name, new_filename=new_media.name)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )

    assert can_persistent_undo(editor, 0) is True

    old_media.write_bytes(b"changed")

    assert can_persistent_undo(editor, 0) is False


def test_restore_persistent_undo_restores_old_field_html(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    new_media = media_dir / "clip__aqe_1.mp3"
    old_media.write_bytes(b"old")
    new_media.write_bytes(b"new")
    db_path = tmp_path / "history.sqlite3"
    editor = _editor(media_dir, note_id=1001, field_html=f"Prompt [sound:{new_media.name}]")
    _append_operation(
        db_path,
        editor,
        old_filename=old_media.name,
        new_filename=new_media.name,
        old_field_html=f"Prompt [sound:{old_media.name}]",
        new_field_html=f"Prompt [sound:{new_media.name}]",
    )
    session = EditorSession()
    deps = _deps()
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )

    restored = restore_persistent_undo(editor, session, deps)

    assert restored is True
    assert editor.note.fields == [f"Prompt [sound:{old_media.name}]"]
    assert session.state == AudioEditState(old_media.name)
    assert session.current_filename == old_media.name
    assert editor.loadNote.call_args.kwargs == {"focusTo": 0}
    assert deps.request_playback_after_edit.call_args.args[:2] == (editor, 0)


def test_restore_persistent_undo_replaces_matching_current_reference(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    new_media = media_dir / "clip__aqe_1.mp3"
    old_media.write_bytes(b"old")
    new_media.write_bytes(b"new")
    db_path = tmp_path / "history.sqlite3"
    editor = _editor(
        media_dir,
        note_id=1001,
        field_html=f"Manually kept text [sound:{new_media.name}]",
    )
    _append_operation(
        db_path,
        editor,
        old_filename=old_media.name,
        new_filename=new_media.name,
        old_field_html=f"Prompt [sound:{old_media.name}]",
        new_field_html=f"Prompt [sound:{new_media.name}]",
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )

    restored = restore_persistent_undo(editor, EditorSession(), _deps())

    assert restored is True
    assert editor.note.fields == [f"Manually kept text [sound:{old_media.name}]"]


def test_restore_persistent_undo_refuses_unrelated_field(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    new_media = media_dir / "clip__aqe_1.mp3"
    other_media = media_dir / "other.mp3"
    old_media.write_bytes(b"old")
    new_media.write_bytes(b"new")
    other_media.write_bytes(b"other")
    db_path = tmp_path / "history.sqlite3"
    editor = _editor(media_dir, note_id=1001, field_html=f"[sound:{other_media.name}]")
    _append_operation(db_path, editor, old_filename=old_media.name, new_filename=new_media.name)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )

    restored = restore_persistent_undo(editor, EditorSession(), _deps())

    assert restored is False
    assert editor.note.fields == [f"[sound:{other_media.name}]"]


def test_restore_persistent_undo_refuses_missing_old_media(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    new_media = media_dir / "clip__aqe_1.mp3"
    old_media.write_bytes(b"old")
    new_media.write_bytes(b"new")
    db_path = tmp_path / "history.sqlite3"
    editor = _editor(media_dir, note_id=1001, field_html=f"[sound:{new_media.name}]")
    _append_operation(db_path, editor, old_filename=old_media.name, new_filename=new_media.name)
    old_media.unlink()
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )

    restored = restore_persistent_undo(editor, EditorSession(), _deps())

    assert restored is False
    assert editor.note.fields == [f"[sound:{new_media.name}]"]


def test_standard_render_commit_records_persistent_undo(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    old_media.write_bytes(b"old")
    output_path = tmp_path / "rendered.mp3"
    output_path.write_bytes(b"new")
    db_path = tmp_path / "history.sqlite3"
    editor = _editor(media_dir, note_id=1001, field_html="Prompt [sound:clip.mp3]")
    session = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        next_status_summary="Increased speed to x1.5.",
    )
    deps = SimpleNamespace(
        current_field_audio_missing="Missing audio",
        current_field_index=lambda _editor: 0,
        dispose_editor_frontend_controls=MagicMock(),
        eval_history_availability=MagicMock(),
        eval_playback_state=MagicMock(),
        record_standard_persistent_undo=record_standard_persistent_undo,
        request_history_availability_after_edit=MagicMock(),
        request_playback_after_edit=MagicMock(),
        request_graph_redraw=MagicMock(),
        sessions={editor: session},
        set_busy=MagicMock(),
        write_generated_media=_write_generated_media,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )

    replace_current_field_after_render(
        editor,
        AudioEditState("clip.mp3", speed=1.5),
        "clip__aqe_1.mp3",
        deps,
        output_path=output_path,
    )

    latest = PersistentHistoryRepository(db_path).latest_undoable(collection_id_for_editor(editor), 1001, 0)
    assert latest is not None
    assert latest.old_field_html == "Prompt [sound:clip.mp3]"
    assert latest.new_field_html == "Prompt [sound:clip__aqe_1.mp3]"
    assert latest.old_filename == "clip.mp3"
    assert latest.new_filename == "clip__aqe_1.mp3"
    assert latest.status_summary == "Increased speed to x1.5."
    assert audio_edit_state_to_json(AudioEditState("clip.mp3", speed=1.5)) == latest.new_state_json
    assert session.current_filename == "clip__aqe_1.mp3"


def _editor(media_dir: Path, *, note_id: int, field_html: str):
    media_dir.mkdir(parents=True, exist_ok=True)

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


def _write_generated_media(editor, desired_name: str, output_path: Path) -> str:
    media_path = Path(editor.mw.col.media.dir()) / desired_name
    media_path.write_bytes(output_path.read_bytes())
    return desired_name


def _deps() -> SimpleNamespace:
    return SimpleNamespace(
        current_field_index=lambda _editor: 0,
        dispose_editor_frontend_controls=MagicMock(),
        eval_playback_state=MagicMock(),
        request_history_availability_after_edit=MagicMock(),
        request_playback_after_edit=MagicMock(),
        stop_session_playback=MagicMock(),
    )


def _append_operation(
    db_path: Path,
    editor,
    *,
    old_filename: str,
    new_filename: str,
    old_field_html: str | None = None,
    new_field_html: str | None = None,
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
            old_field_html=old_field_html or f"[sound:{old_filename}]",
            new_field_html=new_field_html or f"[sound:{new_filename}]",
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
