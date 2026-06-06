# Persistent Undo Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship SQLite-only persistent undo for standard editor audio edits, so the user can return to a note later and undo the last standard edit when the previous media file still exists in Anki media.

**Architecture:** Add a small add-on-owned SQLite operation journal under add-on `user_files`, then bridge it into the existing standard render commit path and undo path. Keep the current in-memory `UndoHistory` as the active-session fast path; persistent undo is a fallback when the session undo stack is empty. Phase 1 does not archive media, does not implement persistent redo, and does not cover special transforms or region delete.

**Tech Stack:** Python 3.13, stdlib `sqlite3`, Anki editor hooks, existing Svelte editor bundle, pytest/e2e via `python3 scripts/dev.py`.

---

## Success Criteria

- Standard render commands handled by `editor_processing.update_state_and_render` create persistent history rows:
  - `aqe:slower`
  - `aqe:faster`
  - `aqe:volume-down`
  - `aqe:volume-up`
  - `aqe:remove-pauses`
- After the editor session is gone, reopening the note enables Undo when the old media file still exists.
- Persistent undo restores the previous audio reference without running ffmpeg.
- If the old media file is missing, Undo is unavailable or refuses without changing the note.
- If the field changed after the recorded edit, Undo refuses without changing the note.
- Existing session undo/redo behavior remains unchanged.

## File Structure

- Create `addon/anki_audio_quick_editor/persistent_history.py`
  - Owns SQLite schema, migrations, operation dataclasses, media fingerprinting, and `AudioEditState` JSON serialization.
  - Import-safe core module. It may import `audio_state`.

- Create `addon/anki_audio_quick_editor/editor_persistent_undo.py`
  - Owns editor-specific use of persistent history: DB path resolution, collection identity, operation recording, availability checks, and persistent undo restoration.
  - Import-safe enough for editor adapters, but it reads Anki-like editor objects passed by callers.

- Modify `addon/anki_audio_quick_editor/editor_processing.py`
  - Capture old/new field HTML and record persistent history only for standard render commit.

- Modify `addon/anki_audio_quick_editor/editor_history.py`
  - Keep session undo first.
  - Fall back to persistent undo when session undo is empty.
  - Include persistent undo in history availability.

- Modify `addon/anki_audio_quick_editor/editor_dependencies.py`
  - Expose persistent history helpers through existing dependency namespaces.

- Modify `addon/anki_audio_quick_editor/editor_callbacks.py`
  - Export persistent history wrappers for dependency injection.

- Modify `addon/anki_audio_quick_editor/editor_integration.py`
  - Compute initial persistent undo availability during editor injection.

- Modify `addon/anki_audio_quick_editor/editor_ui.py`
  - Add `initialHistoryAvailabilityByField` to the editor runtime config.

- Modify Svelte editor runtime files:
  - `settings_ui/src/editor-inline/types.ts`
  - `settings_ui/src/editor-inline/control-actions.ts`
  - `settings_ui/src/editor-inline/field-controller.ts`

- Modify generated editor templates:
  - `addon/anki_audio_quick_editor/templates/editor/editor_bundle.js`
  - `addon/anki_audio_quick_editor/templates/editor/editor_bundle.css` only if the build updates it.

- Modify locale catalogs only if new status keys are added:
  - `addon/anki_audio_quick_editor/locales/*.json`

- Modify architecture contracts:
  - `tests/test_architecture/contract_core.py`
  - `tests/test_architecture/contract_editor/operations.py`
  - `tests/test_architecture/contract_editor/processing.py`
  - `tests/test_architecture/contract_editor/integration.py` if new imports require it.

- Add tests:
  - `tests/test_persistent_history.py`
  - `tests/test_editor_persistent_undo.py`
  - Extend `tests/test_editor_integration.py`
  - Extend `tests/test_editor_frontend.py` or add focused frontend tests if existing coverage fits.
  - Add `e2e/test_editor_persistent_undo_workflow.py`

## Shared Implementation Decisions

- Store the Phase 1 DB at:

```python
user_files_dir(addon_dir) / "persistent_undo.sqlite3"
```

- Resolve `addon_dir` from:

```python
Path(editor.mw.addonManager.addonsFolder(addon_id))
```

- Use collection identity:

```python
sha256(str(Path(editor.mw.col.media.dir()).resolve()).encode("utf-8")).hexdigest()
```

This avoids direct collection DB access and is stable enough for Phase 1 because history is scoped to the profile/add-on user files plus collection media directory.

- Persistent undo validates applicability in this order:
  - exact field HTML match against `new_field_html`,
  - otherwise first supported sound reference filename match against `new_filename`,
  - otherwise refuse.

- Persistent undo requires the old media file to exist and match recorded hash/size.

- Do not mark missing-media operations expired in Phase 1. The file may reappear. Availability is computed dynamically from SQLite plus current media existence.

- SQLite failures during operation recording should not block the audio edit. Record the exception through existing diagnostics logging and keep session undo functional.

---

### Task 1: Add Persistent History Storage

**Files:**
- Create: `addon/anki_audio_quick_editor/persistent_history.py`
- Test: `tests/test_persistent_history.py`
- Modify: `tests/test_architecture/contract_core.py`

- [ ] **Step 1: Write failing storage tests**

Add `tests/test_persistent_history.py` with tests for schema creation, append/query, dynamic undoability, marking undone, media fingerprinting, and state JSON round-trip.

Use these test names:

```python
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
    assert audio_edit_state_from_json(latest.new_state_json) == AudioEditState("clip.mp3", speed=1.5)
```

```python
def test_repository_returns_latest_not_undone_operation(tmp_path: Path) -> None:
    repo = PersistentHistoryRepository(tmp_path / "history.sqlite3")
    first = _append_operation(repo, old_filename="a.mp3", new_filename="b.mp3", created_at_ms=1)
    second = _append_operation(repo, old_filename="b.mp3", new_filename="c.mp3", created_at_ms=2)

    repo.mark_undone(second, undone_at_ms=3)

    latest = repo.latest_undoable("collection", 1001, 0)

    assert latest is not None
    assert latest.id == first
```

```python
def test_media_fingerprint_detects_size_and_hash(tmp_path: Path) -> None:
    media = tmp_path / "clip.wav"
    media.write_bytes(b"audio")

    fingerprint = media_fingerprint(media)

    assert fingerprint.size == 5
    assert fingerprint.sha256 == hashlib.sha256(b"audio").hexdigest()
```

The helper `_append_operation` in this test file should construct a complete `PersistentHistoryAppend` with deterministic values, not partial dictionaries.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_persistent_history.py
```

Expected: import errors for `PersistentHistoryRepository`, `PersistentHistoryAppend`, and helper functions.

- [ ] **Step 3: Implement storage module**

Create `addon/anki_audio_quick_editor/persistent_history.py` with:

```python
"""SQLite-backed persistent undo history."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from .audio_state import AudioEditState

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class MediaFingerprint:
    sha256: str
    size: int


@dataclass(frozen=True)
class PersistentHistoryAppend:
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
    id: int
    undone_at_ms: int | None
    expired_at_ms: int | None


class PersistentHistoryRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def append_operation(self, operation: PersistentHistoryAppend) -> int:
        self._migrate()
        with self._connect() as db:
            cursor = db.execute(
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
            return int(cursor.lastrowid)

    def latest_undoable(
        self,
        collection_id: str,
        note_id: int,
        field_index: int,
    ) -> PersistentHistoryOperation | None:
        self._migrate()
        with self._connect() as db:
            row = db.execute(
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
        self._migrate()
        with self._connect() as db:
            db.execute(
                """
                update persistent_undo_operations
                set undone_at_ms = ?
                where id = ?
                """,
                (undone_at_ms, operation_id),
            )

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self._db_path)
        db.row_factory = sqlite3.Row
        return db

    def _migrate(self) -> None:
        with self._connect() as db:
            db.execute(
                """
                create table if not exists persistent_undo_meta (
                    key text primary key,
                    value text not null
                )
                """
            )
            db.execute(
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
            db.execute(
                """
                create index if not exists persistent_undo_latest_idx
                on persistent_undo_operations (
                    collection_id, note_id, field_index, expired_at_ms, undone_at_ms, id
                )
                """
            )
            db.execute(
                """
                insert into persistent_undo_meta (key, value)
                values ('schema_version', ?)
                on conflict(key) do update set value = excluded.value
                """,
                (str(SCHEMA_VERSION),),
            )


def media_fingerprint(path: Path) -> MediaFingerprint:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return MediaFingerprint(sha256=digest.hexdigest(), size=size)


def audio_edit_state_to_json(state: AudioEditState | None) -> str:
    if state is None:
        return "{}"
    return json.dumps(asdict(state), sort_keys=True, separators=(",", ":"))


def audio_edit_state_from_json(raw: str) -> AudioEditState | None:
    if raw == "{}":
        return None
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        return None
    return AudioEditState(**payload)


def _operation_from_row(row: sqlite3.Row) -> PersistentHistoryOperation:
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
        undone_at_ms=row["undone_at_ms"],
        expired_at_ms=row["expired_at_ms"],
    )
```

- [ ] **Step 4: Register architecture contract**

In `tests/test_architecture/contract_core.py`, add:

```python
"persistent_history": contract(
    "persistent_history",
    layer=Layer.IMPORT_SAFE_CORE,
    allowed_addon_deps=("audio_state",),
    allowed_side_effects=(SideEffect.DB_ACCESS,),
    notes="Add-on-owned SQLite journal for persistent audio undo history.",
),
```

- [ ] **Step 5: Run storage and architecture tests**

Run:

```bash
python3 scripts/dev.py test tests/test_persistent_history.py
python3 scripts/dev.py test tests/test_architecture/test_rule15_all_modules_have_contracts.py
python3 scripts/dev.py test tests/test_architecture/test_rule5_all_modules_classified.py
```

Expected: all pass.

---

### Task 2: Add Editor Persistent Undo Service

**Files:**
- Create: `addon/anki_audio_quick_editor/editor_persistent_undo.py`
- Test: `tests/test_editor_persistent_undo.py`
- Modify: `tests/test_architecture/contract_editor/operations.py`

- [ ] **Step 1: Write failing editor service tests**

Add `tests/test_editor_persistent_undo.py` with tests for:

- `history_db_path_for_editor` uses add-on `user_files`.
- `can_persistent_undo` returns true only when old media exists and matches hash/size.
- `restore_persistent_undo` restores exact old field HTML when current field equals `new_field_html`.
- `restore_persistent_undo` refuses when the current field no longer contains `new_filename`.
- `restore_persistent_undo` refuses when old media is missing.

Use this core test shape:

```python
def test_restore_persistent_undo_restores_old_field_html(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    new_media = media_dir / "clip__aqe_1.mp3"
    old_media.write_bytes(b"old")
    new_media.write_bytes(b"new")
    db_path = tmp_path / "history.sqlite3"
    repo = PersistentHistoryRepository(db_path)
    old_fingerprint = media_fingerprint(old_media)
    new_fingerprint = media_fingerprint(new_media)
    repo.append_operation(
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
            old_media_sha256=old_fingerprint.sha256,
            old_media_size=old_fingerprint.size,
            new_media_sha256=new_fingerprint.sha256,
            new_media_size=new_fingerprint.size,
            status_summary="Increased speed to x1.5.",
            created_at_ms=1234,
        )
    )
    editor = _editor(media_dir, note_id=1001, field_html="Prompt [sound:clip__aqe_1.mp3]")
    session = EditorSession()
    deps = SimpleNamespace(
        current_field_index=lambda _editor: 0,
        eval_playback_state=lambda *_args: None,
        request_history_availability_after_edit=lambda *_args: None,
        request_playback_after_edit=lambda *_args, **_kwargs: None,
        stop_session_playback=lambda _session: None,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.repository_for_editor",
        lambda _editor: repo,
    )
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.collection_id_for_editor",
        lambda _editor: "collection",
    )

    restored = restore_persistent_undo(editor, session, deps)

    assert restored is True
    assert editor.note.fields == ["Prompt [sound:clip.mp3]"]
    assert session.state == AudioEditState("clip.mp3")
    assert session.current_filename == "clip.mp3"
```

The `_editor` helper should create a `SimpleNamespace` with `note.id`, `note.fields`, `mw.col.media.dir`, `mw.addonManager.addonFromModule`, and `mw.addonManager.addonsFolder`.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_persistent_undo.py
```

Expected: import errors for `editor_persistent_undo`.

- [ ] **Step 3: Implement editor service**

Create `addon/anki_audio_quick_editor/editor_persistent_undo.py` with these public functions:

```python
def history_db_path_for_editor(editor: Any) -> Path:
    addon_id = editor.mw.addonManager.addonFromModule(__name__)
    addon_dir = Path(editor.mw.addonManager.addonsFolder(addon_id))
    return user_files_dir(addon_dir) / "persistent_undo.sqlite3"
```

```python
def repository_for_editor(editor: Any) -> PersistentHistoryRepository:
    return PersistentHistoryRepository(history_db_path_for_editor(editor))
```

```python
def collection_id_for_editor(editor: Any) -> str:
    media_dir = Path(editor.mw.col.media.dir()).resolve()
    return hashlib.sha256(str(media_dir).encode("utf-8")).hexdigest()
```

```python
def can_persistent_undo(editor: Any, field_index: int | None) -> bool:
    if field_index is None or getattr(getattr(editor, "note", None), "id", None) is None:
        return False
    operation = repository_for_editor(editor).latest_undoable(
        collection_id_for_editor(editor),
        int(editor.note.id),
        int(field_index),
    )
    if operation is None:
        return False
    return _old_media_available(editor, operation)
```

```python
def restore_persistent_undo(editor: Any, session: EditorSession, deps: Any) -> bool:
    field_index = int(deps.current_field_index(editor))
    note_id = getattr(getattr(editor, "note", None), "id", None)
    if note_id is None:
        return False
    repo = repository_for_editor(editor)
    operation = repo.latest_undoable(collection_id_for_editor(editor), int(note_id), field_index)
    if operation is None:
        return False
    if not _old_media_available(editor, operation):
        return False
    field_html = editor.note.fields[field_index]
    selection = select_first_sound_reference(field_html)
    if field_html == operation.new_field_html:
        restored_field_html = operation.old_field_html
    elif selection.selected is not None and media_filenames_match(selection.selected.filename, operation.new_filename):
        restored_field_html = replace_sound_reference(field_html, selection.selected, operation.old_filename)
    else:
        return False
    deps.stop_session_playback(session)
    session.post_edit_playback_generation += 1
    deps.dispose_editor_frontend_controls(editor)
    editor.note.fields[field_index] = restored_field_html
    session.state = audio_edit_state_from_json(operation.old_state_json) or AudioEditState(operation.old_filename)
    session.current_filename = operation.old_filename
    session.field_index = field_index
    session.status_summary = restored_status_summary(UndoEntry(session.state, operation.old_filename, operation.status_summary))
    session.pending_status = PendingEditorStatus(
        field_index,
        message=undo_status_message(UndoEntry(session.state, operation.old_filename, operation.status_summary)),
    )
    session.cursor_ms = 0
    session.playback_active = False
    session.playback_paused = False
    repo.mark_undone(operation.id, undone_at_ms=_now_ms())
    deps.request_playback_after_edit(
        editor,
        field_index,
        require_graph_redraw=field_index in session.graph_active_fields,
    )
    editor.loadNote(focusTo=field_index)
    session.pending_status = None
    deps.eval_playback_state(editor, field_index, "stopped", 0)
    return True
```

Include private helpers:

- `_old_media_available(editor, operation)`
- `_media_matches(path, sha256, size)`
- `_now_ms()`

The implementation should import:

```python
from .runtime_paths import user_files_dir
from .persistent_history import (
    PersistentHistoryAppend,
    PersistentHistoryOperation,
    PersistentHistoryRepository,
    audio_edit_state_from_json,
    audio_edit_state_to_json,
    media_fingerprint,
)
from .media_paths import existing_media_file_path, media_filenames_match
from .sound_refs import replace_sound_reference, select_first_sound_reference
from .editor_session import EditorSession, PendingEditorStatus, UndoEntry
from .editor_status import restored_status_summary, undo_status_message
```

- [ ] **Step 4: Register architecture contract**

In `tests/test_architecture/contract_editor/operations.py`, add an `editor_persistent_undo` contract in the operations/editor section:

```python
"editor_persistent_undo": contract(
    "editor_persistent_undo",
    layer=Layer.IMPORT_SAFE_CORE,
    allowed_addon_deps=(
        "audio_state",
        "editor_session",
        "editor_status",
        "media_paths",
        "persistent_history",
        "runtime_paths",
        "sound_refs",
    ),
    allowed_side_effects=(SideEffect.DB_ACCESS,),
),
```

- [ ] **Step 5: Run service tests**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_persistent_undo.py
python3 scripts/dev.py test tests/test_architecture
```

Expected: all pass.

---

### Task 3: Record Standard Render Operations

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_processing.py`
- Modify: `addon/anki_audio_quick_editor/editor_dependencies.py`
- Modify: `addon/anki_audio_quick_editor/editor_callbacks.py`
- Modify: `tests/test_architecture/contract_editor/processing.py`
- Test: `tests/test_editor_integration.py` or `tests/test_editor_async_race_guards.py`

- [ ] **Step 1: Add failing integration test for recording**

In `tests/test_editor_integration.py`, add a test that calls `_handle_bridge_command(editor, "aqe:faster")` with patched immediate rendering and asserts one persistent operation is recorded.

The test should:

- create `clip.mp3`,
- render `clip__aqe_*.mp3`,
- verify `old_field_html == "[sound:clip.mp3]"`,
- verify `new_field_html` references the saved generated filename,
- verify `old_state_json` and `new_state_json` are populated,
- verify `old_media_sha256` matches `clip.mp3`.

Use monkeypatching:

```python
monkeypatch.setattr(
    "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
    lambda _editor: tmp_path / "persistent_undo.sqlite3",
)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_integration.py
```

Expected: assertion failure because standard render does not append a persistent operation yet.

- [ ] **Step 3: Add callback exports**

In `addon/anki_audio_quick_editor/editor_callbacks.py`, import `editor_persistent_undo` and export wrappers:

```python
from . import editor_persistent_undo
```

```python
_record_standard_persistent_undo = editor_persistent_undo.record_standard_persistent_undo
_can_persistent_undo = editor_persistent_undo.can_persistent_undo
_restore_persistent_undo = _with_deps(editor_persistent_undo.restore_persistent_undo, _history_deps)
```

Use the dependency wrapper only for restore because it needs history deps. Keep `record_standard_persistent_undo` direct if its signature receives all values and resolves repository internally.

In `tests/test_architecture/contract_editor/processing.py`, add `editor_persistent_undo` to the `editor_callbacks` `allowed_addon_deps` tuple.

- [ ] **Step 4: Add dependency seams**

In `editor_dependencies.processing_deps`, add:

```python
record_standard_persistent_undo=callbacks.record_standard_persistent_undo,
```

In `editor_dependencies.history_deps`, add:

```python
can_persistent_undo=callbacks.can_persistent_undo,
restore_persistent_undo=callbacks.restore_persistent_undo,
```

- [ ] **Step 5: Implement record helper**

In `editor_persistent_undo.py`, add:

```python
def record_standard_persistent_undo(
    editor: Any,
    *,
    field_index: int,
    old_field_html: str,
    new_field_html: str,
    old_filename: str,
    new_filename: str,
    old_state: AudioEditState | None,
    new_state: AudioEditState,
    status_summary: str,
) -> None:
    media_dir = Path(editor.mw.col.media.dir())
    old_path = existing_media_file_path(media_dir, old_filename)
    new_path = existing_media_file_path(media_dir, new_filename)
    note_id = getattr(getattr(editor, "note", None), "id", None)
    if old_path is None or new_path is None or note_id is None:
        return
    old_fingerprint = media_fingerprint(old_path)
    new_fingerprint = media_fingerprint(new_path)
    repository_for_editor(editor).append_operation(
        PersistentHistoryAppend(
            collection_id=collection_id_for_editor(editor),
            note_id=int(note_id),
            field_index=int(field_index),
            operation_type="standard-render",
            old_field_html=old_field_html,
            new_field_html=new_field_html,
            old_filename=old_filename,
            new_filename=new_filename,
            old_state_json=audio_edit_state_to_json(old_state),
            new_state_json=audio_edit_state_to_json(new_state),
            old_media_sha256=old_fingerprint.sha256,
            old_media_size=old_fingerprint.size,
            new_media_sha256=new_fingerprint.sha256,
            new_media_size=new_fingerprint.size,
            status_summary=status_summary,
            created_at_ms=_now_ms(),
        )
    )
```

- [ ] **Step 6: Record in standard render commit path**

In `replace_current_field_after_render`, capture old values before replacing the field:

```python
old_field_html = field_html
old_filename = selection.selected.filename
old_state = session.state if session else None
```

After replacing the field and after the new media has been written:

```python
new_field_html = editor.note.fields[field_index]
try:
    deps.record_standard_persistent_undo(
        editor,
        field_index=field_index,
        old_field_html=old_field_html,
        new_field_html=new_field_html,
        old_filename=old_filename,
        new_filename=saved_name,
        old_state=old_state,
        new_state=updated_state,
        status_summary=session.next_status_summary if session else "",
    )
except Exception:
    logger.debug("Could not record persistent undo operation.", exc_info=True)
```

This write should happen before `_replace_standard_render_session_state`, because that function clears `session.next_status_summary`.

- [ ] **Step 7: Run recording tests**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_integration.py
python3 scripts/dev.py test tests/test_editor_async_race_guards.py
```

Expected: all pass and stale async render tests confirm no persistent row is recorded for rejected stale completions.

---

### Task 4: Add Persistent Undo Fallback And Availability

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_history.py`
- Modify: `addon/anki_audio_quick_editor/editor_integration.py`
- Modify: `addon/anki_audio_quick_editor/editor_ui.py`
- Test: `tests/test_editor_integration.py`
- Test: `tests/test_editor_frontend.py`

- [ ] **Step 1: Add failing backend tests**

In `tests/test_editor_integration.py`, add tests:

```python
def test_persistent_undo_restores_after_session_history_is_empty(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    new_media = media_dir / "clip__aqe_1.mp3"
    old_media.write_bytes(b"old")
    new_media.write_bytes(b"new")
    db_path = tmp_path / "persistent_undo.sqlite3"
    _append_persistent_operation(
        db_path,
        media_dir,
        note_id=1001,
        old_filename=old_media.name,
        new_filename=new_media.name,
    )
    editor = _persistent_undo_editor(
        media_dir,
        note_id=1001,
        field_html=f"[sound:{new_media.name}]",
    )
    session = EditorSession(
        state=AudioEditState(old_media.name, speed=1.5),
        field_index=0,
        current_filename=new_media.name,
    )
    _SESSIONS[editor] = session
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )
    monkeypatch.setattr("anki_audio_quick_editor.editor_runtime.stop_audio_playback", lambda: None)
    monkeypatch.setattr("aqt.qt.QTimer.singleShot", lambda _delay, callback: callback())

    _handle_bridge_command(editor, "aqe:undo")

    assert editor.note.fields == [f"[sound:{old_media.name}]"]
    assert session.current_filename == old_media.name
    assert session.state == AudioEditState(old_media.name)
```

```python
def test_persistent_undo_refuses_when_old_media_is_missing(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    new_media = media_dir / "clip__aqe_1.mp3"
    old_media.write_bytes(b"old")
    new_media.write_bytes(b"new")
    db_path = tmp_path / "persistent_undo.sqlite3"
    _append_persistent_operation(
        db_path,
        media_dir,
        note_id=1001,
        old_filename=old_media.name,
        new_filename=new_media.name,
    )
    old_media.unlink()
    editor = _persistent_undo_editor(
        media_dir,
        note_id=1001,
        field_html=f"[sound:{new_media.name}]",
    )
    _SESSIONS[editor] = EditorSession(field_index=0, current_filename=new_media.name)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )

    _handle_bridge_command(editor, "aqe:undo")

    assert editor.note.fields == [f"[sound:{new_media.name}]"]
    assert any("Nothing to undo" in call.args[0] for call in editor.web.eval.call_args_list)
```

```python
def test_persistent_undo_refuses_when_field_changed_after_edit(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    new_media = media_dir / "clip__aqe_1.mp3"
    unrelated_media = media_dir / "other.mp3"
    old_media.write_bytes(b"old")
    new_media.write_bytes(b"new")
    unrelated_media.write_bytes(b"other")
    db_path = tmp_path / "persistent_undo.sqlite3"
    _append_persistent_operation(
        db_path,
        media_dir,
        note_id=1001,
        old_filename=old_media.name,
        new_filename=new_media.name,
    )
    editor = _persistent_undo_editor(
        media_dir,
        note_id=1001,
        field_html=f"[sound:{unrelated_media.name}]",
    )
    _SESSIONS[editor] = EditorSession(field_index=0, current_filename=unrelated_media.name)
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_persistent_undo.history_db_path_for_editor",
        lambda _editor: db_path,
    )

    _handle_bridge_command(editor, "aqe:undo")

    assert editor.note.fields == [f"[sound:{unrelated_media.name}]"]
```

The first test should:

- record a persistent row manually through `PersistentHistoryRepository`,
- set editor field to the new filename,
- set `EditorSession` with empty `undo_history`,
- call `_handle_bridge_command(editor, "aqe:undo")`,
- assert field is restored to old filename.

The missing-media test should delete the old file and assert the field remains on the new filename.

The changed-field test should change the field to another sound reference and assert the field remains unchanged.

Add these helpers near the new persistent undo integration tests:

```python
from anki_audio_quick_editor.editor_persistent_undo import collection_id_for_editor
from anki_audio_quick_editor.persistent_history import (
    PersistentHistoryAppend,
    PersistentHistoryRepository,
    audio_edit_state_to_json,
    media_fingerprint,
)


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
    media_dir: Path,
    *,
    note_id: int,
    old_filename: str,
    new_filename: str,
) -> None:
    old_fingerprint = media_fingerprint(media_dir / old_filename)
    new_fingerprint = media_fingerprint(media_dir / new_filename)
    PersistentHistoryRepository(db_path).append_operation(
        PersistentHistoryAppend(
            collection_id=collection_id_for_editor(
                _persistent_undo_editor(
                    media_dir,
                    note_id=note_id,
                    field_html=f"[sound:{new_filename}]",
                )
            ),
            note_id=note_id,
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
```

- [ ] **Step 2: Add failing injection availability test**

In `tests/test_editor_integration.py`, add:

```python
def test_editor_injection_embeds_persistent_undo_availability(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    old_media = media_dir / "clip.mp3"
    new_media = media_dir / "clip__aqe_1.mp3"
    old_media.write_bytes(b"old")
    new_media.write_bytes(b"new")
    db_path = tmp_path / "persistent_undo.sqlite3"
    _append_persistent_operation(
        db_path,
        media_dir,
        note_id=1001,
        old_filename=old_media.name,
        new_filename=new_media.name,
    )
    editor = _persistent_undo_editor(
        media_dir,
        note_id=1001,
        field_html=f"[sound:{new_media.name}]",
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
```

Assert the injected config contains:

```python
"initialHistoryAvailabilityByField": {"0": {"canUndo": True, "canRedo": False}}
```

Use the existing regex style from `test_editor_injection_script_embeds_source_audio_metadata`.

- [ ] **Step 3: Run tests to verify failures**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_integration.py
```

Expected: failures because `editor_history.undo` still reports nothing to undo and injection has no initial history availability.

- [ ] **Step 4: Modify history availability**

In `editor_history.sync_history_availability`, compute:

```python
can_undo = bool(session.undo_history.entries) or bool(deps.can_persistent_undo(editor, session.field_index))
can_redo = bool(session.redo_history.entries)
```

Use the same logic in `request_history_availability_after_edit`.

- [ ] **Step 5: Modify undo fallback**

In `editor_history.undo`, after `previous is None`, call:

```python
if deps.restore_persistent_undo(editor, session):
    sync_history_availability(editor, session, deps)
    request_history_availability_after_edit(editor, session, deps)
    return
deps.eval_status(editor, t("editor.status.nothing_to_undo"))
```

Do not call persistent undo while a session undo entry exists.

- [ ] **Step 6: Add initial history availability to Python injection config**

In `editor_ui.injection_script`, add an optional parameter:

```python
initial_history_availability_by_field: dict[int, dict[str, bool]] | None = None,
```

Add to config:

```python
"initialHistoryAvailabilityByField": initial_history_availability_by_field or {},
```

In `editor_integration.editor_injection_script`, pass:

```python
initial_history_availability_by_field=_initial_history_availability_by_field(editor, note, _SESSIONS.get(editor)),
```

Add helper:

```python
def _initial_history_availability_by_field(
    editor: Any,
    note: Any,
    session: EditorSession | None,
) -> dict[int, dict[str, bool]]:
    result: dict[int, dict[str, bool]] = {}
    for field_index in _audio_field_indices(note):
        session_can_undo = (
            session is not None
            and session.field_index == field_index
            and bool(session.undo_history.entries)
        )
        session_can_redo = (
            session is not None
            and session.field_index == field_index
            and bool(session.redo_history.entries)
        )
        persistent_can_undo = editor_persistent_undo.can_persistent_undo(editor, field_index)
        result[int(field_index)] = {
            "canUndo": bool(session_can_undo or persistent_can_undo),
            "canRedo": bool(session_can_redo),
        }
    return result
```

Add `editor_persistent_undo` to `editor_integration` imports and update its architecture contract allowed deps.

In `tests/test_architecture/contract_editor/integration.py`, add `editor_persistent_undo` to the `editor_integration` `allowed_addon_deps` tuple.

- [ ] **Step 7: Run backend tests**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_integration.py
python3 scripts/dev.py test tests/test_editor_frontend.py
```

Expected: backend tests pass. Frontend tests may still fail until Task 5 applies the initial availability config.

---

### Task 5: Apply Initial History Availability In Frontend

**Files:**
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `settings_ui/src/editor-inline/control-actions.ts`
- Modify: `settings_ui/src/editor-inline/field-controller.ts`
- Generated by build: `addon/anki_audio_quick_editor/templates/editor/editor_bundle.js`
- Generated by build if changed: `addon/anki_audio_quick_editor/templates/editor/editor_bundle.css`
- Test: `tests/test_editor_frontend.py`

- [ ] **Step 1: Add failing frontend unit test**

In `tests/test_editor_frontend.py`, add or extend an existing test around `injection_script` to assert the generated config contains `initialHistoryAvailabilityByField`.

Expected JSON fragment:

```json
{
  "initialHistoryAvailabilityByField": {
    "0": {
      "canUndo": true,
      "canRedo": false
    }
  }
}
```

- [ ] **Step 2: Add frontend config type**

In `settings_ui/src/editor-inline/types.ts`, add:

```typescript
initialHistoryAvailabilityByField?: Record<number, { canRedo: boolean; canUndo: boolean }>;
```

- [ ] **Step 3: Apply initial availability on mount**

In `settings_ui/src/editor-inline/control-actions.ts`, add:

```typescript
export function applyInitialHistoryAvailabilityForOrd(ord: number): void {
  const initialAvailability = window.__AQE_EDITOR_CONFIG__?.initialHistoryAvailabilityByField;
  const availability = initialAvailability?.[ord];
  if (!availability) return;
  setHistoryAvailability(ord, availability.canUndo, availability.canRedo);
  delete initialAvailability[ord];
}
```

In `settings_ui/src/editor-inline/field-controller.ts`, import it:

```typescript
import {
  applyInitialHistoryAvailabilityForOrd,
  applyInitialStatusForOrd,
} from "./control-actions.js";
```

Call it immediately after `applyInitialStatusForOrd(target.ord)`:

```typescript
applyInitialHistoryAvailabilityForOrd(target.ord);
```

- [ ] **Step 4: Build editor bundle**

Run:

```bash
python3 scripts/dev.py build-ui
```

Expected: editor template bundle updates.

- [ ] **Step 5: Run frontend validation**

Run:

```bash
python3 scripts/dev.py test-svelte
python3 scripts/dev.py test tests/test_editor_frontend.py
```

Expected: all pass.

---

### Task 6: Add Phase 1 E2E Coverage

**Files:**
- Create: `e2e/test_editor_persistent_undo_workflow.py`

- [ ] **Step 1: Write e2e test for persistent undo after session reset**

Create `e2e/test_editor_persistent_undo_workflow.py` with:

```python
"""E2E tests for SQLite-only persistent editor undo."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _click_and_wait_for_new_file,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
)
from e2e.helpers import click_selector, generate_tone, wait_for_condition, wait_for_js_condition, wait_for_selector


def test_persistent_undo_survives_editor_session_reset(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_persistent_undo_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        generated = _click_and_wait_for_new_file(editor, note, media_dir, "aqe:faster", source.name)
    finally:
        editor.set_note(None)
        parent.close()

    reopened_editor, reopened_parent = _open_editor(anki_mw, note)
    try:
        wait_for_js_condition(
            reopened_editor.web,
            """
            (() => {
              const undo = document.querySelector('[data-aqe-command="aqe:undo"]');
              return undo !== null && undo.disabled === false;
            })()
            """,
            lambda value: value is True,
            timeout=10.0,
        )
        click_selector(reopened_editor.web, _button_selector("aqe:undo"), timeout=5.0)
        wait_for_condition(
            lambda: _sound_filename(note.fields[0]) == source.name,
            timeout=5.0,
            message="Persistent undo did not restore the original media reference",
        )
        assert (media_dir / generated).is_file()
    finally:
        reopened_editor.set_note(None)
        reopened_parent.close()
```

- [ ] **Step 2: Write e2e missing-media test**

Add:

```python
def test_persistent_undo_is_unavailable_when_old_media_is_missing(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_persistent_undo_missing_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:faster"), timeout=10.0)
        generated = _click_and_wait_for_new_file(editor, note, media_dir, "aqe:faster", source.name)
    finally:
        editor.set_note(None)
        parent.close()

    source.unlink()

    reopened_editor, reopened_parent = _open_editor(anki_mw, note)
    try:
        wait_for_js_condition(
            reopened_editor.web,
            """
            (() => {
              const undo = document.querySelector('[data-aqe-command="aqe:undo"]');
              return undo !== null && undo.disabled === true;
            })()
            """,
            lambda value: value is True,
            timeout=10.0,
        )
        assert _sound_filename(note.fields[0]) == generated
    finally:
        reopened_editor.set_note(None)
        reopened_parent.close()
```

- [ ] **Step 3: Run e2e tests**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_persistent_undo_workflow.py
```

Expected: both tests pass.

---

### Task 7: Verification And Release Gate

**Files:**
- No new files unless verification exposes required fixes.

- [ ] **Step 1: Run targeted unit and architecture suite**

Run:

```bash
python3 scripts/dev.py test tests/test_persistent_history.py
python3 scripts/dev.py test tests/test_editor_persistent_undo.py
python3 scripts/dev.py test tests/test_editor_integration.py
python3 scripts/dev.py test tests/test_editor_frontend.py
python3 scripts/dev.py test tests/test_architecture
```

Expected: all pass.

- [ ] **Step 2: Run frontend validation**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected: Svelte check, ESLint, TypeScript, and frontend tests pass.

- [ ] **Step 3: Run Phase 1 e2e**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_persistent_undo_workflow.py
```

Expected: all pass.

- [ ] **Step 4: Run reusable QC gate**

Run:

```bash
python3 scripts/dev.py check
```

Expected: all configured checks pass.

- [ ] **Step 5: Run full e2e before release**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: full e2e suite passes.

## Phase 1 Release Notes

User-facing release summary:

> Undo for standard editor audio edits now survives reopening the note or restarting Anki, as long as the previous media file still exists in Anki media. Media-cleanup-proof undo will come in the archive phase.

Known limitation to document:

> If Anki media cleanup removes the previous audio file before you undo, Phase 1 cannot restore it. The add-on will keep the note unchanged and leave Undo disabled or report that there is nothing available to undo.

## Self-Review Checklist

- Phase 1 does not implement archive behavior.
- Phase 1 does not implement persistent redo.
- Phase 1 does not record special transforms or region delete.
- Persistent undo is unavailable when the old media file is missing.
- Persistent undo refuses field conflicts.
- Existing in-memory undo remains the first choice.
- Tests cover unit, editor integration, architecture, frontend bundle behavior, and e2e.
