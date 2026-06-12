"""Tests for SQLite-backed persistent undo history."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_state import AudioEditState
from anki_audio_quick_editor.persistent_history import (
    PersistentHistoryAppend,
    PersistentHistoryRepository,
    PersistentHistoryUnavailableError,
    audio_edit_state_from_json,
    audio_edit_state_to_json,
    media_fingerprint,
    sqlite_available,
)


def test_repository_migrates_and_appends_operation(tmp_path: Path) -> None:
    db_path = tmp_path / "history.sqlite3"
    repo = PersistentHistoryRepository(db_path)
    media = tmp_path / "clip.mp3"
    media.write_bytes(b"before")
    fingerprint = media_fingerprint(media)

    operation_id = repo.append_operation(
        PersistentHistoryAppend(
            collection_id="collection",
            note_id=1001,
            field_index=0,
            operation_type="standard-render",
            old_field_html="Prompt [sound:clip.mp3]",
            new_field_html="Prompt [sound:clip__aqe_1.mp3]",
            old_filename="clip.mp3",
            new_filename="clip__aqe_1.mp3",
            old_state_json=audio_edit_state_to_json(AudioEditState("clip.mp3")),
            new_state_json=audio_edit_state_to_json(AudioEditState("clip.mp3", speed=1.5)),
            old_media_sha256=fingerprint.sha256,
            old_media_size=fingerprint.size,
            new_media_sha256="new-sha",
            new_media_size=12,
            status_summary="Increased speed to x1.5.",
            created_at_ms=1234,
        )
    )

    latest = repo.latest_undoable("collection", 1001, 0)

    assert operation_id > 0
    assert latest is not None
    assert latest.id == operation_id
    assert latest.old_filename == "clip.mp3"
    assert latest.new_filename == "clip__aqe_1.mp3"
    assert audio_edit_state_from_json(latest.new_state_json) == AudioEditState(
        "clip.mp3",
        speed=1.5,
    )


def test_repository_returns_latest_not_undone_operation(tmp_path: Path) -> None:
    repo = PersistentHistoryRepository(tmp_path / "history.sqlite3")
    first = _append_operation(repo, old_filename="a.mp3", new_filename="b.mp3", created_at_ms=1)
    second = _append_operation(repo, old_filename="b.mp3", new_filename="c.mp3", created_at_ms=2)

    repo.mark_undone(second, undone_at_ms=3)

    latest = repo.latest_undoable("collection", 1001, 0)

    assert latest is not None
    assert latest.id == first


def test_repository_returns_recent_undoable_operations_newest_first_with_limit(tmp_path: Path) -> None:
    repo = PersistentHistoryRepository(tmp_path / "history.sqlite3")
    first = _append_operation(repo, old_filename="a.mp3", new_filename="b.mp3", created_at_ms=1)
    second = _append_operation(repo, old_filename="b.mp3", new_filename="c.mp3", created_at_ms=2)
    third = _append_operation(repo, old_filename="c.mp3", new_filename="d.mp3", created_at_ms=3)

    recent = repo.recent_undoable("collection", 1001, 0, limit=2)

    assert [operation.id for operation in repo.recent_undoable("collection", 1001, 0, limit=10)] == [
        third,
        second,
        first,
    ]
    assert [operation.id for operation in recent] == [third, second]


def test_repository_clamps_recent_undoable_limit(tmp_path: Path) -> None:
    repo = PersistentHistoryRepository(tmp_path / "history.sqlite3")
    for index in range(105):
        _append_operation(
            repo,
            old_filename=f"{index}.mp3",
            new_filename=f"{index + 1}.mp3",
            created_at_ms=index,
        )

    assert repo.recent_undoable("collection", 1001, 0, limit=-1) == []
    assert len(repo.recent_undoable("collection", 1001, 0, limit=500)) == 100


def test_repository_ignores_expired_operations(tmp_path: Path) -> None:
    repo = PersistentHistoryRepository(tmp_path / "history.sqlite3")
    operation_id = _append_operation(
        repo,
        old_filename="a.mp3",
        new_filename="b.mp3",
        created_at_ms=1,
    )

    repo.mark_expired(operation_id, expired_at_ms=2)

    assert repo.latest_undoable("collection", 1001, 0) is None


def test_repository_logs_debug_history_lifecycle(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    repo = PersistentHistoryRepository(tmp_path / "history.sqlite3")
    caplog.set_level(logging.DEBUG, logger="anki_audio_quick_editor.persistent_history")

    operation_id = _append_operation(repo, old_filename="a.mp3", new_filename="b.mp3", created_at_ms=1)
    latest = repo.latest_undoable("collection", 1001, 0)
    repo.mark_undone(operation_id, undone_at_ms=2)

    assert latest is not None
    assert any("persistent undo stored row" in record.message for record in caplog.records)
    assert any("persistent undo latest query hit" in record.message for record in caplog.records)
    assert any(f"operation_id={operation_id}" in record.message for record in caplog.records)
    assert any("persistent undo marked undone" in record.message for record in caplog.records)


def test_repository_reports_missing_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.persistent_history._sqlite3", None)
    repo = PersistentHistoryRepository(tmp_path / "history.sqlite3")

    assert sqlite_available() is False
    with pytest.raises(PersistentHistoryUnavailableError):
        repo.latest_undoable("collection", 1001, 0)


def test_media_fingerprint_detects_size_and_hash(tmp_path: Path) -> None:
    media = tmp_path / "clip.wav"
    media.write_bytes(b"audio")

    fingerprint = media_fingerprint(media)

    assert fingerprint.size == 5
    assert fingerprint.sha256 == hashlib.sha256(b"audio").hexdigest()


def test_audio_edit_state_json_round_trips_none_and_state() -> None:
    state = AudioEditState("clip.mp3", left_trim_ms=20, speed=1.25, volume_db=3.0)

    assert audio_edit_state_from_json(audio_edit_state_to_json(None)) is None
    assert audio_edit_state_from_json(audio_edit_state_to_json(state)) == state


def _append_operation(
    repo: PersistentHistoryRepository,
    *,
    old_filename: str,
    new_filename: str,
    created_at_ms: int,
) -> int:
    return repo.append_operation(
        PersistentHistoryAppend(
            collection_id="collection",
            note_id=1001,
            field_index=0,
            operation_type="standard-render",
            old_field_html=f"Prompt [sound:{old_filename}]",
            new_field_html=f"Prompt [sound:{new_filename}]",
            old_filename=old_filename,
            new_filename=new_filename,
            old_state_json=audio_edit_state_to_json(AudioEditState(old_filename)),
            new_state_json=audio_edit_state_to_json(AudioEditState(old_filename, speed=1.5)),
            old_media_sha256=f"old-{old_filename}",
            old_media_size=100,
            new_media_sha256=f"new-{new_filename}",
            new_media_size=200,
            status_summary="Increased speed to x1.5.",
            created_at_ms=created_at_ms,
        )
    )
