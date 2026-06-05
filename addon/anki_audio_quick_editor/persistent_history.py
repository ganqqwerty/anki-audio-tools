"""SQLite-backed persistent undo history."""

from __future__ import annotations

import hashlib
import json
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .audio_state import AudioEditState

_sqlite3: Any
try:
    import sqlite3 as _sqlite3
except ImportError:
    _sqlite3 = None

SCHEMA_VERSION = 1


class PersistentHistoryUnavailableError(RuntimeError):
    """Raised when SQLite support is unavailable."""


@dataclass(frozen=True)
class MediaFingerprint:
    """Hash and size metadata for a media file."""

    sha256: str
    size: int


@dataclass(frozen=True)
class PersistentHistoryAppend:
    """One persistent undo operation to append to the SQLite journal."""

    collection_id: str
    note_id: int
    field_index: int
    operation_type: str
    old_field_html: str
    new_field_html: str
    old_filename: str
    new_filename: str
    old_state_json: str
    new_state_json: str
    old_media_sha256: str
    old_media_size: int
    new_media_sha256: str
    new_media_size: int
    status_summary: str
    created_at_ms: int


@dataclass(frozen=True)
class PersistentHistoryOperation(PersistentHistoryAppend):
    """One persistent undo operation read from the SQLite journal."""

    id: int
    undone_at_ms: int | None
    expired_at_ms: int | None


class PersistentHistoryRepository:
    """Repository for persistent audio undo operations."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def append_operation(self, operation: PersistentHistoryAppend) -> int:
        """Append an operation and return its row id."""
        self._migrate()
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                """
                    insert into persistent_undo_operations (
                        collection_id, note_id, field_index, operation_type,
                        old_field_html, new_field_html, old_filename, new_filename,
                        old_state_json, new_state_json,
                        old_media_sha256, old_media_size,
                        new_media_sha256, new_media_size,
                        status_summary, created_at_ms
                    ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                (
                    operation.collection_id,
                    operation.note_id,
                    operation.field_index,
                    operation.operation_type,
                    operation.old_field_html,
                    operation.new_field_html,
                    operation.old_filename,
                    operation.new_filename,
                    operation.old_state_json,
                    operation.new_state_json,
                    operation.old_media_sha256,
                    operation.old_media_size,
                    operation.new_media_sha256,
                    operation.new_media_size,
                    operation.status_summary,
                    operation.created_at_ms,
                ),
            )
            row_id = cursor.lastrowid
            if row_id is None:
                raise RuntimeError("SQLite did not return an id for the persistent undo row.")
            return int(row_id)

    def latest_undoable(
        self,
        collection_id: str,
        note_id: int,
        field_index: int,
    ) -> PersistentHistoryOperation | None:
        """Return the latest non-expired operation that has not been undone."""
        self._migrate()
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                select * from persistent_undo_operations
                where collection_id = ?
                  and note_id = ?
                  and field_index = ?
                  and undone_at_ms is null
                  and expired_at_ms is null
                order by id desc
                limit 1
                """,
                (collection_id, note_id, field_index),
            ).fetchone()
        return _operation_from_row(row) if row is not None else None

    def mark_undone(self, operation_id: int, *, undone_at_ms: int) -> None:
        """Mark an operation as undone."""
        self._migrate()
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                    update persistent_undo_operations
                    set undone_at_ms = ?
                    where id = ?
                    """,
                (undone_at_ms, operation_id),
            )

    def mark_expired(self, operation_id: int, *, expired_at_ms: int) -> None:
        """Mark an operation as unavailable due to retention pruning."""
        self._migrate()
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                    update persistent_undo_operations
                    set expired_at_ms = ?
                    where id = ?
                    """,
                (expired_at_ms, operation_id),
            )

    def _connect(self) -> Any:
        sqlite = _require_sqlite()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite.connect(self._db_path)
        connection.row_factory = sqlite.Row
        return connection

    def _migrate(self) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                create table if not exists persistent_undo_meta (
                    key text primary key,
                    value text not null
                )
                """
            )
            connection.execute(
                """
                create table if not exists persistent_undo_operations (
                    id integer primary key autoincrement,
                    collection_id text not null,
                    note_id integer not null,
                    field_index integer not null,
                    operation_type text not null,
                    old_field_html text not null,
                    new_field_html text not null,
                    old_filename text not null,
                    new_filename text not null,
                    old_state_json text not null,
                    new_state_json text not null,
                    old_media_sha256 text not null,
                    old_media_size integer not null,
                    new_media_sha256 text not null,
                    new_media_size integer not null,
                    status_summary text not null,
                    created_at_ms integer not null,
                    undone_at_ms integer,
                    expired_at_ms integer
                )
                """
            )
            connection.execute(
                """
                create index if not exists persistent_undo_latest_idx
                on persistent_undo_operations (
                    collection_id, note_id, field_index, expired_at_ms, undone_at_ms, id
                )
                """
            )
            connection.execute(
                """
                insert into persistent_undo_meta (key, value)
                values ('schema_version', ?)
                on conflict(key) do update set value = excluded.value
                """,
                (str(SCHEMA_VERSION),),
            )


def media_fingerprint(path: Path) -> MediaFingerprint:
    """Return a SHA-256 hash and byte size for a media file."""
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return MediaFingerprint(sha256=digest.hexdigest(), size=size)


def audio_edit_state_to_json(state: AudioEditState | None) -> str:
    """Serialize an optional edit state for persistent history."""
    if state is None:
        return "{}"
    return json.dumps(asdict(state), sort_keys=True, separators=(",", ":"))


def audio_edit_state_from_json(raw: str) -> AudioEditState | None:
    """Deserialize an edit state from persistent history."""
    if raw == "{}":
        return None
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        return None
    return AudioEditState(**payload)


def sqlite_available() -> bool:
    """Return whether the active Python runtime provides SQLite."""
    return _sqlite3 is not None


def _require_sqlite() -> Any:
    if _sqlite3 is None:
        raise PersistentHistoryUnavailableError("SQLite support is not available in this Python runtime.")
    return _sqlite3


def _operation_from_row(row: Any) -> PersistentHistoryOperation:
    return PersistentHistoryOperation(
        id=int(row["id"]),
        collection_id=str(row["collection_id"]),
        note_id=int(row["note_id"]),
        field_index=int(row["field_index"]),
        operation_type=str(row["operation_type"]),
        old_field_html=str(row["old_field_html"]),
        new_field_html=str(row["new_field_html"]),
        old_filename=str(row["old_filename"]),
        new_filename=str(row["new_filename"]),
        old_state_json=str(row["old_state_json"]),
        new_state_json=str(row["new_state_json"]),
        old_media_sha256=str(row["old_media_sha256"]),
        old_media_size=int(row["old_media_size"]),
        new_media_sha256=str(row["new_media_sha256"]),
        new_media_size=int(row["new_media_size"]),
        status_summary=str(row["status_summary"]),
        created_at_ms=int(row["created_at_ms"]),
        undone_at_ms=_optional_int(row["undone_at_ms"]),
        expired_at_ms=_optional_int(row["expired_at_ms"]),
    )


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise TypeError("Expected an integer SQLite value.")
