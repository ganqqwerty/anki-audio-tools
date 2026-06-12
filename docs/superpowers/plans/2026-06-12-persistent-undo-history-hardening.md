# Persistent Undo History Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make SQLite-backed editor undo history easier to reason about, less race-prone, and better covered by tests, while preserving strict contiguous undo-stack semantics.

**Architecture:** Move persistent undo chain planning into a pure module that owns executable-chain rules, make snapshot generation derive availability from one planned item list, and keep editor mutation in the existing restore path. Extend tests so SQLite row state, stale-chain behavior, and region-delete persistence are explicit rather than inferred from mocked editor objects.

**Tech Stack:** Python 3.13 Anki add-on code, SQLite, pytest integration tests, Anki/Qt e2e tests, `scripts/dev.py` quality commands.

---

## File Structure

- Create `addon/anki_audio_quick_editor/persistent_undo_chain.py`: pure chain planner and frontend item shaping helpers for persistent undo rows.
- Modify `addon/anki_audio_quick_editor/editor_persistent_undo.py`: delegate chain selection to the new planner, keep editor/session mutation and repository lookup here.
- Modify `addon/anki_audio_quick_editor/editor_history_snapshot.py`: remove the double-read availability gate when `persistent_undo_items` is available.
- Modify `addon/anki_audio_quick_editor/persistent_history.py`: clamp repository query limits to the supported history cap.
- Modify `addon/anki_audio_quick_editor/editor_region_delete.py`: record persistent undo rows for successful region-delete replacements.
- Modify `addon/anki_audio_quick_editor/editor_dependencies.py`: pass the persistent recorder dependency into region-delete deps.
- Modify `addon/anki_audio_quick_editor/editor_deps_protocols.py`: declare the region-delete persistent recorder dependency.
- Test `tests/test_persistent_undo_chain.py`: pure chain planner tests for contiguous chains, stale newest rows, missing old media, and fallback labels.
- Modify `tests/test_editor_history_snapshot.py`: prove persistent snapshots no longer call `can_persistent_undo` when item-provider data is available.
- Modify `tests/test_persistent_history.py`: prove query limits are clamped.
- Modify `tests/test_editor_persistent_undo_integration.py`: keep bridge/injection coverage, but add stale-chain and SQLite row-state assertions around the extracted planner behavior.
- Modify `tests/test_editor_region_delete_integration.py`: prove region delete records a persistent undo row.
- Modify `e2e/test_editor_persistent_history_workflow.py`: assert SQLite rows directly before and after persistent depth restore.
- Modify `e2e/test_editor_region_delete_workflow.py`: assert region-delete history survives editor reopen.

## Task 1: Extract Pure Persistent Undo Chain Planning

**Files:**
- Create: `addon/anki_audio_quick_editor/persistent_undo_chain.py`
- Modify: `addon/anki_audio_quick_editor/editor_persistent_undo.py`
- Test: `tests/test_persistent_undo_chain.py`

- [ ] **Step 1: Write the failing planner tests**

Create `tests/test_persistent_undo_chain.py`:

```python
from __future__ import annotations

from dataclasses import replace

from anki_audio_quick_editor.persistent_history import PersistentHistoryOperation
from anki_audio_quick_editor.persistent_undo_chain import (
    PersistentUndoChainResult,
    build_persistent_undo_chain,
    persistent_undo_menu_items,
)


def test_builds_contiguous_chain_newest_first() -> None:
    first = _operation(1, "a.mp3", "b.mp3", "First edit")
    second = _operation(2, "b.mp3", "c.mp3", "Second edit")
    third = _operation(3, "c.mp3", "d.mp3", "Third edit")

    result = build_persistent_undo_chain(
        current_field_html="[sound:d.mp3]",
        operations=[third, second, first],
        old_media_available=lambda operation: operation.old_filename != "missing.mp3",
    )

    assert result == PersistentUndoChainResult(
        operations=[third, second, first],
        break_reason=None,
        break_operation_id=None,
    )


def test_stops_at_stale_newest_row_to_preserve_undo_stack_semantics() -> None:
    older = _operation(1, "a.mp3", "b.mp3", "Older edit")
    stale_newest = _operation(2, "b.mp3", "c.mp3", "Stale newest edit")

    result = build_persistent_undo_chain(
        current_field_html="[sound:b.mp3]",
        operations=[stale_newest, older],
        old_media_available=lambda _operation: True,
    )

    assert result.operations == []
    assert result.break_reason == "current_field_not_applicable"
    assert result.break_operation_id == stale_newest.id


def test_stops_at_first_missing_old_media() -> None:
    first = _operation(1, "a.mp3", "b.mp3", "First edit")
    second = _operation(2, "b.mp3", "c.mp3", "Second edit")

    result = build_persistent_undo_chain(
        current_field_html="[sound:c.mp3]",
        operations=[second, first],
        old_media_available=lambda operation: operation.id != second.id,
    )

    assert result.operations == []
    assert result.break_reason == "old_media_unavailable"
    assert result.break_operation_id == second.id


def test_menu_items_use_operation_labels_and_fallback() -> None:
    labeled = _operation(1, "a.mp3", "b.mp3", "Clean label")
    unlabeled = replace(_operation(2, "b.mp3", "c.mp3", "  "), status_summary="  ")

    assert persistent_undo_menu_items([unlabeled, labeled], empty_label="Undo generated audio") == [
        {"id": "persistent:2", "label": "Undo generated audio"},
        {"id": "persistent:1", "label": "Clean label"},
    ]


def _operation(operation_id: int, old_filename: str, new_filename: str, status: str) -> PersistentHistoryOperation:
    return PersistentHistoryOperation(
        id=operation_id,
        collection_id="collection",
        note_id=1001,
        field_index=0,
        operation_type="standard-render",
        old_field_html=f"[sound:{old_filename}]",
        new_field_html=f"[sound:{new_filename}]",
        old_filename=old_filename,
        new_filename=new_filename,
        old_state_json=None,
        new_state_json=None,
        old_media_sha256="old-sha",
        old_media_size=10,
        new_media_sha256="new-sha",
        new_media_size=20,
        status_summary=status,
        created_at_ms=operation_id,
        undone_at_ms=None,
        expired_at_ms=None,
    )
```

- [ ] **Step 2: Run the planner tests to verify failure**

Run:

```bash
python3 -m pytest tests/test_persistent_undo_chain.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'anki_audio_quick_editor.persistent_undo_chain'`.

- [ ] **Step 3: Implement the pure planner**

Create `addon/anki_audio_quick_editor/persistent_undo_chain.py`:

```python
"""Pure helpers for building executable persistent undo chains."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .errors import AudioQuickEditorError
from .media_paths import media_filenames_match
from .persistent_history import PersistentHistoryOperation
from .sound_refs import replace_sound_reference, select_first_sound_reference


@dataclass(frozen=True)
class PersistentUndoChainResult:
    operations: list[PersistentHistoryOperation]
    break_reason: str | None
    break_operation_id: int | None


def build_persistent_undo_chain(
    *,
    current_field_html: str,
    operations: Iterable[PersistentHistoryOperation],
    old_media_available: Callable[[PersistentHistoryOperation], bool],
) -> PersistentUndoChainResult:
    """Return the contiguous executable undo chain from the current field state."""
    chain: list[PersistentHistoryOperation] = []
    current_html = current_field_html
    for operation in operations:
        if not old_media_available(operation):
            return PersistentUndoChainResult(chain, "old_media_unavailable", operation.id)
        restored_html = restored_field_html(current_html, operation)
        if restored_html is None:
            return PersistentUndoChainResult(chain, "current_field_not_applicable", operation.id)
        chain.append(operation)
        current_html = restored_html
    return PersistentUndoChainResult(chain, None, None)


def persistent_undo_menu_items(
    operations: Iterable[PersistentHistoryOperation],
    *,
    empty_label: str,
) -> list[dict[str, str]]:
    """Return frontend menu items for persistent undo operations."""
    return [
        {
            "id": f"persistent:{operation.id}",
            "label": operation.status_summary.strip() or empty_label,
        }
        for operation in operations
    ]


def restored_field_html(field_html: str, operation: PersistentHistoryOperation) -> str | None:
    """Return field HTML after applying one persistent undo row, if applicable."""
    if field_html == operation.new_field_html:
        return operation.old_field_html
    try:
        selection = select_first_sound_reference(field_html)
    except AudioQuickEditorError:
        return None
    if selection.selected is not None and media_filenames_match(selection.selected.filename, operation.new_filename):
        return replace_sound_reference(field_html, selection.selected, operation.old_filename)
    return None
```

- [ ] **Step 4: Delegate existing editor code to the planner**

In `addon/anki_audio_quick_editor/editor_persistent_undo.py`, add imports:

```python
from .persistent_undo_chain import (
    build_persistent_undo_chain,
    persistent_undo_menu_items,
    restored_field_html,
)
```

Remove these imports because the new pure module owns them:

```python
from .errors import AudioQuickEditorError
from .media_paths import media_filenames_match
from .sound_refs import replace_sound_reference, select_first_sound_reference
```

Replace the body of `persistent_undo_items(...)` with:

```python
    try:
        operations = _undo_chain_for_field(editor, field_index, history_size)
    except PersistentHistoryUnavailableError:
        return []
    return persistent_undo_menu_items(
        operations,
        empty_label=t("editor.history.undo_empty_label"),
    )
```

Replace `_undo_chain_for_field(...)` with:

```python
def _undo_chain_for_field(
    editor: Any,
    field_index: int | None,
    history_size: object,
) -> list[PersistentHistoryOperation]:
    if field_index is None:
        return []
    try:
        field_html = editor.note.fields[int(field_index)]
    except (AttributeError, IndexError, TypeError, ValueError):
        return []
    result = build_persistent_undo_chain(
        current_field_html=field_html,
        operations=_recent_for_field(editor, field_index, history_size),
        old_media_available=lambda operation: _old_media_available(editor, operation),
    )
    if result.break_reason is not None:
        logger.debug(
            "persistent undo chain stopped reason=%s field_index=%s operation_id=%s",
            result.break_reason,
            field_index,
            result.break_operation_id,
        )
    return result.operations
```

Replace calls to `_restored_field_html(...)` with `restored_field_html(...)`, then delete `_restored_field_html(...)`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_persistent_undo_chain.py tests/test_editor_persistent_undo_integration.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add addon/anki_audio_quick_editor/persistent_undo_chain.py addon/anki_audio_quick_editor/editor_persistent_undo.py tests/test_persistent_undo_chain.py
git commit -m "Clarify persistent undo chain planning

Extract chain construction into a pure helper so editor side effects no longer
own stack semantics. This keeps newest-first contiguous undo behavior explicit
and makes stale-row and media-availability failures directly testable."
```

## Task 2: Make Snapshot Generation Single-Source-Of-Truth

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_history_snapshot.py`
- Modify: `tests/test_editor_history_snapshot.py`

- [ ] **Step 1: Add a failing test for avoiding the double persistence read**

Add this test to `tests/test_editor_history_snapshot.py`:

```python
def test_snapshot_uses_persistent_item_provider_without_availability_probe() -> None:
    calls: list[str] = []

    snapshot = history_snapshot_for_field(
        object(),
        field_index=0,
        session=None,
        history_size=100,
        can_persistent_undo=lambda _editor, _field_index: calls.append("can") or False,
        latest_persistent_undo_item=lambda _editor, _field_index: None,
        persistent_undo_items=lambda _editor, _field_index, _limit: calls.append("items") or [
            {"id": "persistent:9", "label": "Third edit"}
        ],
    )

    assert calls == ["items"]
    assert snapshot == {
        "canUndo": True,
        "canRedo": False,
        "undoItems": [{"id": "persistent:9", "label": "Third edit"}],
        "redoItems": [],
    }
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
python3 -m pytest tests/test_editor_history_snapshot.py::test_snapshot_uses_persistent_item_provider_without_availability_probe -q
```

Expected: FAIL because `can_persistent_undo` is called and prevents item generation.

- [ ] **Step 3: Replace the double-read branch**

In `addon/anki_audio_quick_editor/editor_history_snapshot.py`, replace:

```python
    if field_index is not None and not undo_items and can_persistent_undo(editor, field_index):
        if persistent_undo_items is not None:
            undo_items.extend(persistent_undo_items(editor, field_index, limit))
        else:
            item = latest_persistent_undo_item(editor, field_index)
            if item is not None:
                undo_items.append(item)
```

with:

```python
    if field_index is not None and not undo_items:
        if persistent_undo_items is not None:
            undo_items.extend(persistent_undo_items(editor, field_index, limit))
        elif can_persistent_undo(editor, field_index):
            item = latest_persistent_undo_item(editor, field_index)
            if item is not None:
                undo_items.append(item)
```

- [ ] **Step 4: Run snapshot tests**

Run:

```bash
python3 -m pytest tests/test_editor_history_snapshot.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add addon/anki_audio_quick_editor/editor_history_snapshot.py tests/test_editor_history_snapshot.py
git commit -m "Avoid double reads for persistent history snapshots

Persistent undo snapshots should be derived from one executable item provider
when that provider exists. This removes a race-prone availability probe and
makes canUndo a consequence of the returned menu items."
```

## Task 3: Clamp Persistent Repository Query Limits

**Files:**
- Modify: `addon/anki_audio_quick_editor/persistent_history.py`
- Modify: `tests/test_persistent_history.py`

- [ ] **Step 1: Add failing query-limit tests**

Add this test to `tests/test_persistent_history.py`:

```python
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
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
python3 -m pytest tests/test_persistent_history.py::test_repository_clamps_recent_undoable_limit -q
```

Expected: FAIL because `limit=500` returns 105 rows.

- [ ] **Step 3: Add repository-local query cap**

In `addon/anki_audio_quick_editor/persistent_history.py`, add near the top-level constants:

```python
MAX_RECENT_UNDOABLE_LIMIT = 100
```

In `PersistentHistoryRepository.recent_undoable(...)`, before the SQL call, add:

```python
        bounded_limit = min(MAX_RECENT_UNDOABLE_LIMIT, max(0, int(limit)))
```

Then replace the SQL parameters:

```python
                (collection_id, note_id, field_index, max(0, int(limit))),
```

with:

```python
                (collection_id, note_id, field_index, bounded_limit),
```

Update the debug argument from `limit` to `bounded_limit`:

```python
            bounded_limit,
```

- [ ] **Step 4: Run persistence repository tests**

Run:

```bash
python3 -m pytest tests/test_persistent_history.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add addon/anki_audio_quick_editor/persistent_history.py tests/test_persistent_history.py
git commit -m "Bound persistent history repository queries

The SQLite repository now enforces the same 100-item history ceiling as the
editor UI. This keeps accidental broad queries from bypassing the user-facing
history contract."
```

## Task 4: Assert SQLite State In E2E Persistent History Coverage

**Files:**
- Modify: `e2e/test_editor_persistent_history_workflow.py`

- [ ] **Step 1: Add SQLite helpers and failing row-state assertions**

Add imports near the top of `e2e/test_editor_persistent_history_workflow.py`:

```python
import sqlite3
```

Add this helper below `_history_labels_js(...)`:

```python
def _persistent_history_rows(editor) -> list[dict[str, object]]:
    from anki_audio_quick_editor.editor_persistent_undo import history_db_path_for_editor

    db_path = history_db_path_for_editor(editor)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            select id, status_summary, undone_at_ms, expired_at_ms
            from persistent_undo_operations
            order by id
            """
        ).fetchall()
    return [dict(row) for row in rows]
```

After the first editor close block and before reopening, add:

```python
    rows_after_render = _persistent_history_rows(editor)
    assert [row["status_summary"] for row in rows_after_render[-3:]] == [
        "Increased speed to x1.5.",
        "Increased volume by 15 dB.",
        "Decreased speed to x1.5.",
    ]
    assert [row["undone_at_ms"] for row in rows_after_render[-3:]] == [None, None, None]
```

After the depth-2 undo wait at line 103, add:

```python
        rows_after_depth_restore = _persistent_history_rows(reopened)
        assert [row["undone_at_ms"] is not None for row in rows_after_depth_restore[-3:]] == [
            False,
            True,
            True,
        ]
```

- [ ] **Step 2: Run the e2e test**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_persistent_history_workflow.py
```

Expected: PASS. If it fails because `editor` was closed before row lookup, move `rows_after_render = _persistent_history_rows(editor)` before `editor.set_note(None)` in the `finally` block by storing it in an outer variable:

```python
    rows_after_render: list[dict[str, object]] = []
```

and assigning it before closing:

```python
        rows_after_render = _persistent_history_rows(editor)
```

- [ ] **Step 3: Commit**

```bash
git add e2e/test_editor_persistent_history_workflow.py
git commit -m "Verify persistent undo SQLite state in e2e

The reopen workflow now checks the durable journal directly, so UI behavior is
tied to row creation and row consumption instead of only menu labels."
```

## Task 5: Persist Region Delete Undo Rows

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_region_delete.py`
- Modify: `addon/anki_audio_quick_editor/editor_dependencies.py`
- Modify: `addon/anki_audio_quick_editor/editor_deps_protocols.py`
- Test: `tests/test_editor_region_delete_integration.py`
- Test: `e2e/test_editor_region_delete_workflow.py`

- [ ] **Step 1: Add a failing region-delete persistence test**

In `tests/test_editor_region_delete_integration.py`, add this monkeypatch before calling `_replace_current_field_after_region_delete(...)` in `test_region_delete_replacement_updates_only_requested_field_and_history`:

```python
    persistent_recorder = MagicMock()
    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_callbacks._record_standard_persistent_undo",
        persistent_recorder,
    )
```

Add these assertions after the existing history assertions:

```python
    persistent_recorder.assert_called_once()
    call = persistent_recorder.call_args.kwargs
    assert call["field_index"] == 1
    assert call["old_field_html"] == "<b>Prompt</b> [sound:clip.mp3] extra"
    assert call["new_field_html"] == "<b>Prompt</b> [sound:clip__aqe_cut.mp3] extra"
    assert call["old_filename"] == current.name
    assert call["new_filename"] == saved_name
    assert call["status_summary"] == session.status_summary
```

- [ ] **Step 2: Run the failing region-delete test**

Run:

```bash
python3 -m pytest tests/test_editor_region_delete_integration.py::test_region_delete_replacement_updates_only_requested_field_and_history -q
```

Expected: FAIL because `record_standard_persistent_undo` is not called.

- [ ] **Step 3: Add the dependency to the region-delete protocol and deps**

In `addon/anki_audio_quick_editor/editor_deps_protocols.py`, add to `RegionDeleteDeps`:

```python
    record_standard_persistent_undo: Callable[..., Any]
```

In `addon/anki_audio_quick_editor/editor_dependencies.py`, add to `region_delete_deps(...)`:

```python
        record_standard_persistent_undo=callbacks.record_standard_persistent_undo,
```

- [ ] **Step 4: Record the persistent row from region delete**

In `addon/anki_audio_quick_editor/editor_region_delete.py`, change:

```python
        replace_first_sound_reference_in_field(
            editor,
            field_index=field_index,
            saved_name=saved_name,
            missing_message=deps.current_field_audio_missing,
            expected_filename=request.source_filename,
            mismatch_message=t("editor.status.graph_audio_mismatch"),
        )
        should_redraw_graph = _replace_region_delete_session_state(editor, session, field_index, saved_name, request)
```

to:

```python
        old_field_html, new_field_html, old_filename = replace_first_sound_reference_in_field(
            editor,
            field_index=field_index,
            saved_name=saved_name,
            missing_message=deps.current_field_audio_missing,
            expected_filename=request.source_filename,
            mismatch_message=t("editor.status.graph_audio_mismatch"),
        )
        old_state = session.state if session is not None else None
        should_redraw_graph = _replace_region_delete_session_state(editor, session, field_index, saved_name, request)
        try:
            deps.record_standard_persistent_undo(
                editor,
                field_index=field_index,
                old_field_html=old_field_html,
                new_field_html=new_field_html,
                old_filename=old_filename,
                new_filename=saved_name,
                old_state=old_state,
                new_state=session.state if session is not None else AudioEditState(source_file=saved_name),
                status_summary=session.status_summary if session is not None else region_operation_status_summary(request),
            )
        except Exception:
            logger.debug(
                "Could not record persistent undo operation for region delete field_index=%s old=%s new=%s.",
                field_index,
                old_filename,
                saved_name,
                exc_info=True,
            )
```

- [ ] **Step 5: Run region-delete Python tests**

Run:

```bash
python3 -m pytest tests/test_editor_region_delete_integration.py tests/test_architecture/test_rule29_editor_dependency_protocols.py -q
```

Expected: PASS.

- [ ] **Step 6: Add e2e reopen coverage for region delete history**

In `e2e/test_editor_region_delete_workflow.py`, extend the main successful region-delete workflow after closing and reopening the editor:

```python
        click_selector(reopened.web, '[data-testid="aqe-split-0-undo-menu"]', timeout=5.0)
        wait_for_selector(reopened.web, '[data-testid="aqe-history-0-undo-1"]', timeout=5.0)
```

Then click the first undo history item and assert the note field returns to the source filename:

```python
        click_selector(reopened.web, '[data-testid="aqe-history-0-undo-1"]', timeout=5.0)
        wait_for_condition(
            lambda: source.name in note.fields[0],
            timeout=5.0,
            message="Persistent region-delete undo did not restore the original source reference",
        )
```

- [ ] **Step 7: Run region-delete e2e**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_region_delete_workflow.py
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add addon/anki_audio_quick_editor/editor_region_delete.py addon/anki_audio_quick_editor/editor_dependencies.py addon/anki_audio_quick_editor/editor_deps_protocols.py tests e2e/test_editor_region_delete_workflow.py
git commit -m "Persist region delete editor undo history

Region delete now records the same durable undo journal as standard editor
renders. This removes an operation-coverage gap where generated files could be
undone in-memory but disappeared from history after reopening the editor."
```

## Task 6: Final Verification And Documentation Check

**Files:**
- Modify docs only if verification reveals stale claims in `WEBVIEW_AND_TEMPLATES.md`, `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`, or `ARCHITECTURE.md`.

- [ ] **Step 1: Run focused persistence checks**

Run:

```bash
python3 scripts/dev.py test tests/test_persistent_history.py tests/test_persistent_undo_chain.py tests/test_editor_persistent_undo.py tests/test_editor_persistent_undo_integration.py tests/test_editor_history_snapshot.py
```

Expected: PASS.

- [ ] **Step 2: Run focused e2e checks**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_persistent_history_workflow.py e2e/test_editor_region_delete_workflow.py
```

Expected: PASS.

- [ ] **Step 3: Run full quality gate**

Run:

```bash
python3 scripts/dev.py check
```

Expected: PASS.

- [ ] **Step 4: Run full e2e suite**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS.

- [ ] **Step 5: Commit verification documentation changes if any were needed**

If docs changed, run:

```bash
git add WEBVIEW_AND_TEMPLATES.md EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md ARCHITECTURE.md
git commit -m "Document durable editor history behavior

The documentation now matches the hardened persistent undo architecture and
explains which editor operations survive reopen through SQLite-backed history."
```

If no docs changed, do not create an empty commit.

## Self-Review Checklist

- Spec coverage: The plan addresses snapshot double reads, chain-planner SRP, strict stale-row semantics, repository query bounds, SQLite e2e assertions, restart-adjacent reopen behavior, and region-delete operation coverage.
- Test design: Pure planner tests cover rules without mocks; integration tests keep fake editor seams for bridge/session behavior; e2e tests exercise real Anki editor reopen and direct SQLite row state.
- SOLID: Chain planning moves behind a pure interface, repository bounds stay in the repository, snapshot generation derives state from one provider, and editor mutation remains in editor-specific restore code.
- Known boundary: Durable redo persistence is still out of scope because the current SQLite model is an undo journal. This plan does not introduce redo rows or redo-stack semantics.
