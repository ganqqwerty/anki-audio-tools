# Race Condition Mitigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make async editor, batch, cache, and frontend bridge workflows reject stale work and avoid unsafe cross-thread state/media mutations.

**Architecture:** Use the generation-guard pattern already present in graph analysis, playback, and learner recording. Worker threads may render or analyze, but note/media/UI mutations must run through a current-generation main-thread completion path. Batch runs gain duplicate-start protection and optimistic field-conflict checks.

**Tech Stack:** Python 3.13, Anki task manager/main-thread callbacks, Pytest, Svelte 5/TypeScript, Vitest, `python3 scripts/dev.py`.

---

## Background

This add-on has several workflows where a user action starts work that finishes later: audio renders, denoise/voice-only transforms, region deletion, graph analysis, playback segment rendering, learner recording analysis, settings diagnostics, and Browser batch jobs. A race condition can happen when the callback that completes later assumes the editor, note, field, media file, or frontend pending request is still the same one that existed when the work started.

The code already handles some of these cases well. Graph analysis stores a per-field generation and ignores stale callbacks. Playback segment rendering stores a playback generation and deletes stale temp output. Learner recording stores a generation, field index, and source filename before accepting callbacks. The mitigation plan extends that same pattern to the remaining workflows that can mutate note fields or media.

### Scenario 1: Stale Editor Render Replaces the Wrong Note or Field

1. The user clicks an inline edit command such as faster, volume up, pause removal, or conversion.
2. `render_and_replace_async()` captures the current source path and starts a worker thread.
3. Before ffmpeg finishes, the user moves to another note, switches fields, or Anki reloads the editor.
4. The worker finishes and schedules `replace_current_field_after_render()`.
5. Without a guard, the completion path can inspect the current editor state and replace the current field, even though the render belongs to an older note or field.

The same shape exists for special transforms such as denoise, RNNoise, voice-only, pitch hum, and selected-region operations. These operations are more dangerous than stale status updates because they write generated media and then mutate note HTML.

The fix is a processing guard that records operation generation, note id, field index, and source filename at the moment the operation is accepted. Completion must re-check the guard before writing media or mutating the note. Note loads and new processing operations must invalidate older guards.

### Scenario 2: Worker Threads Write Anki Media Outside the Main Boundary

1. A render worker produces a temp audio file.
2. The worker calls `col.media.write_data()` directly.
3. Meanwhile, Anki or another add-on may be performing collection/media work on the main thread or Anki task manager boundary.
4. Even if the later UI replacement is stale and ignored, the media write has already happened.

Rendering and analysis are suitable for background threads. Anki collection/media mutations should happen after the stale guard is checked, and should run on the main-thread completion path. This plan moves media persistence into guarded replacement functions.

### Scenario 3: Duplicate Browser Batch Starts Share One Dialog and Cancel Event

1. The Batch dialog frontend sends `batch.start`.
2. `_handle_batch_start()` marks the dialog running and starts `_run_batch_in_background()`.
3. A double click, delayed bridge retry, or frontend bug sends another `batch.start` before the first run finishes.
4. A second background job starts with the same dialog callbacks, same log UI, and same `cancel_event`.
5. Progress, logs, cancel, finish, and undo publication can interleave.

The fix is simple: once the dialog is running, later start commands are accepted as handled but do not start another job.

### Scenario 4: Browser Batch Clobbers User Edits Made During Processing

1. A batch job snapshots note fields and starts processing one note.
2. While analysis or rendering runs, the user edits the same note field in Anki or another process changes it.
3. `_apply_result()` refetches the note, assigns `note[target_field] = result.target_html`, and calls `update_note()`.
4. The user's newer field content is overwritten by HTML computed from an older snapshot.

The fix is an optimistic conflict check. Each written `BatchNoteResult` carries the original target field HTML used to compute `target_html`. `_apply_result()` must compare the current field value with that original value immediately before writing. If it changed, the batch records a failed row and leaves the note untouched.

### Scenario 5: Prosody Cache Is Shared Across Background Threads

1. Editor graph analysis, learner recording analysis, and Browser batch graph generation all call `analyze_prosody_cached()`.
2. Two background workers can miss the same cache key at the same time.
3. Both run expensive analysis, then both mutate the global dict and eviction order.
4. In CPython this may often appear harmless, but it is still unsynchronized shared state and can duplicate work or behave unpredictably under concurrent eviction.

The conservative fix is to guard cache lookup, analysis, insertion, and eviction with one re-entrant lock. This serializes prosody analysis through the cache path and preserves correctness.

### Scenario 6: Frontend Pending Bridge Payloads Can Be Overwritten

1. The frontend stores a pending graph analysis, region delete, or split-default save request in a module-level variable.
2. It sends a bridge command telling Python to pop that pending payload.
3. Before Python evaluates the pop expression, another request of the same kind is stored.
4. The newer request overwrites the older one, so Python processes only the latest payload and the earlier user action disappears.

The fix is to replace each single pending slot with a FIFO queue. Python's existing pop calls can keep the same public API, but they should shift the oldest request instead of returning the only stored request.

## File Structure

- Modify `addon/anki_audio_quick_editor/editor_session.py`: add a reusable editor processing guard.
- Modify `addon/anki_audio_quick_editor/editor_processing.py`: guard standard render completions and persist generated media on the main thread.
- Modify `addon/anki_audio_quick_editor/editor_special_transforms.py`: apply the same guard and main-thread persistence to special transforms.
- Modify `addon/anki_audio_quick_editor/editor_region_delete.py`: apply the same guard and main-thread persistence to region operations.
- Modify `addon/anki_audio_quick_editor/browser_dialog.py`: reject duplicate batch starts while a batch is already running.
- Modify `addon/anki_audio_quick_editor/batch_operations.py`: include original field HTML in written batch results.
- Modify `addon/anki_audio_quick_editor/browser_integration.py`: refuse to apply a batch result if the target field changed after the worker snapshot.
- Modify `addon/anki_audio_quick_editor/prosody_cache.py`: serialize cache access and analysis through a lock.
- Modify `settings_ui/src/editor-inline/bridge.ts`: replace single pending bridge payload slots with FIFO queues.
- Add or extend focused tests under `tests/` and `settings_ui/tests/`.

## Task 1: Add Editor Processing Guards

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_session.py`
- Test: `tests/test_editor_processing_guard.py`

- [ ] **Step 1: Write failing guard tests**

Create `tests/test_editor_processing_guard.py`:

```python
from __future__ import annotations

from anki_audio_quick_editor.editor_session import (
    EditorSession,
    begin_processing_guard,
    invalidate_processing_guard,
    is_current_processing_guard,
    reset_for_note_load,
)


def test_processing_guard_matches_only_current_generation_note_field_and_source() -> None:
    session = EditorSession(note_id=10, field_index=1, current_filename="clip.mp3")

    guard = begin_processing_guard(session, field_index=1, source_filename="clip.mp3")

    assert is_current_processing_guard(session, guard)
    session.field_index = 2
    assert not is_current_processing_guard(session, guard)
    session.field_index = 1
    session.current_filename = "other.mp3"
    assert not is_current_processing_guard(session, guard)


def test_processing_guard_is_invalidated_by_note_load() -> None:
    session = EditorSession(note_id=10, field_index=0, current_filename="clip.mp3")
    guard = begin_processing_guard(session, field_index=0, source_filename="clip.mp3")

    reset_for_note_load(session, note_id=11)

    assert not is_current_processing_guard(session, guard)


def test_processing_guard_can_be_invalidated_without_note_change() -> None:
    session = EditorSession(note_id=10, field_index=0, current_filename="clip.mp3")
    guard = begin_processing_guard(session, field_index=0, source_filename="clip.mp3")

    invalidate_processing_guard(session)

    assert not is_current_processing_guard(session, guard)
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```bash
python3 -m pytest tests/test_editor_processing_guard.py -q
```

Expected: FAIL with import errors for `begin_processing_guard`, `invalidate_processing_guard`, and `is_current_processing_guard`.

- [ ] **Step 3: Implement the guard helpers**

In `addon/anki_audio_quick_editor/editor_session.py`, add the dataclass near the other session dataclasses and add `processing_generation` to `EditorSession`:

```python
@dataclass(frozen=True)
class EditorProcessingGuard:
    """Identity for one async editor operation that may later mutate the note."""

    generation: int
    note_id: int | None
    field_index: int
    source_filename: str
```

```python
processing_generation: int = 0
```

Add helpers near `reset_for_note_load()`:

```python
def begin_processing_guard(
    session: EditorSession,
    *,
    field_index: int,
    source_filename: str,
) -> EditorProcessingGuard:
    """Start a guarded editor mutation generation."""
    session.processing_generation += 1
    return EditorProcessingGuard(
        generation=session.processing_generation,
        note_id=session.note_id,
        field_index=int(field_index),
        source_filename=source_filename,
    )


def invalidate_processing_guard(session: EditorSession) -> None:
    """Invalidate pending editor processing completions."""
    session.processing_generation += 1


def is_current_processing_guard(session: EditorSession, guard: EditorProcessingGuard) -> bool:
    """Return whether an async processing completion still targets the same editor state."""
    return (
        session.processing_generation == guard.generation
        and session.note_id == guard.note_id
        and session.field_index == guard.field_index
        and session.current_filename == guard.source_filename
    )
```

In `reset_for_note_load()`, increment `processing_generation` before clearing `processing`:

```python
session.processing_generation += 1
session.processing = False
```

- [ ] **Step 4: Run the guard tests**

Run:

```bash
python3 -m pytest tests/test_editor_processing_guard.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add addon/anki_audio_quick_editor/editor_session.py tests/test_editor_processing_guard.py
git commit -m "test: add editor processing generation guards"
```

## Task 2: Guard Standard Render Completion and Move Media Write to Main Thread

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_processing.py`
- Modify: `addon/anki_audio_quick_editor/editor_session.py` only if Task 1 needs import exports adjusted
- Test: `tests/test_editor_post_edit_playback.py`

- [ ] **Step 1: Add stale and main-thread persistence tests**

Append these tests to `tests/test_editor_post_edit_playback.py`:

```python
def test_standard_render_replacement_ignores_stale_processing_guard(tmp_path: Path) -> None:
    from anki_audio_quick_editor.editor_session import begin_processing_guard, reset_for_note_load

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"source")
    rendered = tmp_path / "rendered.mp3"
    rendered.write_bytes(b"rendered")

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=lambda: str(media_dir),
                write_data=MagicMock(return_value="clip__aqe.mp3"),
            )
        )
    )
    session = EditorSession(
        note_id=1,
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
    )
    _SESSIONS[editor] = session
    guard = begin_processing_guard(session, field_index=0, source_filename="clip.mp3")
    reset_for_note_load(session, note_id=2)

    _replace_current_field_after_render(
        editor,
        AudioEditState("clip.mp3", volume_db=3.0),
        "clip__aqe.mp3",
        guard=guard,
        output_path=rendered,
    )

    assert editor.note.fields == ["[sound:clip.mp3]"]
    editor.mw.col.media.write_data.assert_not_called()
    editor.loadNote.assert_not_called()


def test_standard_render_replacement_writes_generated_media_after_guard(tmp_path: Path) -> None:
    from anki_audio_quick_editor.editor_session import begin_processing_guard

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"source")
    rendered = tmp_path / "rendered.mp3"
    rendered.write_bytes(b"rendered")

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=lambda: str(media_dir),
                write_data=MagicMock(return_value="clip__aqe_saved.mp3"),
            )
        )
    )
    session = EditorSession(
        note_id=1,
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
    )
    _SESSIONS[editor] = session
    guard = begin_processing_guard(session, field_index=0, source_filename="clip.mp3")

    _replace_current_field_after_render(
        editor,
        AudioEditState("clip.mp3", volume_db=3.0),
        "clip__aqe.mp3",
        guard=guard,
        output_path=rendered,
    )

    editor.mw.col.media.write_data.assert_called_once_with("clip__aqe.mp3", b"rendered")
    assert editor.note.fields == ["[sound:clip__aqe_saved.mp3]"]
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run:

```bash
python3 -m pytest tests/test_editor_post_edit_playback.py -q
```

Expected: FAIL because `_replace_current_field_after_render()` does not accept `guard` and `output_path`.

- [ ] **Step 3: Implement guarded replacement and main-thread persistence**

In `addon/anki_audio_quick_editor/editor_processing.py`, import the guard helpers:

```python
from .editor_session import (
    EditorProcessingGuard,
    PendingEditorStatus,
    begin_processing_guard,
    is_current_processing_guard,
)
```

In `render_and_replace_async()`, create a guard after determining the target field:

```python
field_index = session.field_index if session.field_index is not None else deps.current_field_index(editor)
guard = begin_processing_guard(session, field_index=int(field_index), source_filename=source_path.name)
```

Replace the worker completion with a main-thread finish callback:

```python
def _finish() -> None:
    try:
        deps.replace_current_field_after_render(
            editor,
            updated_state,
            desired_name,
            guard=guard,
            output_path=output_path,
        )
    finally:
        shutil.rmtree(output_path.parent, ignore_errors=True)

deps.main(editor, _finish)
```

Remove the off-thread call to `deps.write_generated_media()` from `_run()`.

Change `replace_current_field_after_render()` to accept guarded persistence:

```python
def replace_current_field_after_render(
    editor: Any,
    updated_state: AudioEditState,
    saved_name: str,
    deps: Any,
    *,
    guard: EditorProcessingGuard | None = None,
    output_path: Path | None = None,
) -> None:
    """Replace the current field after a successful standard render."""
    session = deps.sessions.get(editor)
    if guard is not None and (session is None or not is_current_processing_guard(session, guard)):
        return
    if output_path is not None:
        saved_name = deps.write_generated_media(editor, saved_name, output_path)
```

Keep the existing field replacement body after those checks.

- [ ] **Step 4: Run standard render tests**

Run:

```bash
python3 -m pytest tests/test_editor_post_edit_playback.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add addon/anki_audio_quick_editor/editor_processing.py tests/test_editor_post_edit_playback.py
git commit -m "fix: ignore stale standard render completions"
```

## Task 3: Guard Special Transforms and Region Deletes

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_special_transforms.py`
- Modify: `addon/anki_audio_quick_editor/editor_region_delete.py`
- Test: `tests/test_editor_noise_reduction_callbacks.py`
- Test: `tests/test_editor_region_delete_integration.py`

- [ ] **Step 1: Add a stale special-transform replacement test**

Append to `tests/test_editor_noise_reduction_callbacks.py`:

```python
def test_noise_removal_replacement_ignores_stale_processing_guard(tmp_path: Path) -> None:
    from anki_audio_quick_editor.editor_integration import _replace_current_field_after_noise_removal
    from anki_audio_quick_editor.editor_session import begin_processing_guard, reset_for_note_load

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "clip.mp3").write_bytes(b"source")
    rendered = tmp_path / "rendered.mp3"
    rendered.write_bytes(b"rendered")

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=lambda: str(media_dir),
                write_data=MagicMock(return_value="clip__aqe_noise.mp3"),
            )
        )
    )
    session = EditorSession(
        note_id=1,
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
    )
    _SESSIONS[editor] = session
    guard = begin_processing_guard(session, field_index=0, source_filename="clip.mp3")
    reset_for_note_load(session, note_id=2)

    _replace_current_field_after_noise_removal(
        editor,
        "clip__aqe_noise.mp3",
        guard=guard,
        output_path=rendered,
    )

    assert editor.note.fields == ["[sound:clip.mp3]"]
    editor.mw.col.media.write_data.assert_not_called()
    editor.loadNote.assert_not_called()
```

- [ ] **Step 2: Add a stale region-delete replacement test**

Append to `tests/test_editor_region_delete_integration.py`:

```python
def test_region_delete_replacement_ignores_stale_processing_guard(tmp_path: Path) -> None:
    from anki_audio_quick_editor.editor_session import begin_processing_guard, reset_for_note_load

    media_dir = tmp_path / "media"
    media_dir.mkdir()
    current = media_dir / "clip.mp3"
    current.write_bytes(b"current")
    rendered = tmp_path / "rendered.mp3"
    rendered.write_bytes(b"rendered")

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.note = SimpleNamespace(fields=["[sound:clip.mp3]"])
    editor.web = MagicMock()
    editor.loadNote = MagicMock()
    editor.mw = SimpleNamespace(
        col=SimpleNamespace(
            media=SimpleNamespace(
                dir=lambda: str(media_dir),
                write_data=MagicMock(return_value="clip__aqe_cut.mp3"),
            )
        )
    )
    session = EditorSession(
        note_id=1,
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        source_mtime_ns=current.stat().st_mtime_ns,
    )
    _SESSIONS[editor] = session
    guard = begin_processing_guard(session, field_index=0, source_filename="clip.mp3")
    reset_for_note_load(session, note_id=2)
    request = _parse_region_delete_request(
        {
            "ord": 0,
            "sourceFilename": "clip.mp3",
            "selectionStartMs": 100,
            "selectionEndMs": 300,
            "cursorMs": 100,
            "durationMs": 1000,
            "trigger": "button",
        }
    )
    assert request is not None

    _replace_current_field_after_region_delete(
        editor,
        request,
        "clip__aqe_cut.mp3",
        800,
        0.0,
        guard=guard,
        output_path=rendered,
    )

    assert editor.note.fields == ["[sound:clip.mp3]"]
    editor.mw.col.media.write_data.assert_not_called()
    editor.loadNote.assert_not_called()
```

- [ ] **Step 3: Run focused tests and verify they fail**

Run:

```bash
python3 -m pytest tests/test_editor_noise_reduction_callbacks.py tests/test_editor_region_delete_integration.py -q
```

Expected: FAIL because replacement functions do not accept `guard` and `output_path`.

- [ ] **Step 4: Apply guarded main-thread persistence to special transforms**

In `addon/anki_audio_quick_editor/editor_special_transforms.py`, import `begin_processing_guard` and `is_current_processing_guard`. After `session.processing = True`, create:

```python
guard = begin_processing_guard(
    session,
    field_index=int(session.field_index if session.field_index is not None else getattr(editor, "currentField", 0)),
    source_filename=current_path.name,
)
```

Replace the worker completion with:

```python
def _finish() -> None:
    try:
        deps.replace_current_field_after_noise_removal(
            editor,
            desired_name,
            guard=guard,
            output_path=output_path,
        )
    finally:
        shutil.rmtree(output_path.parent, ignore_errors=True)

deps.main(editor, _finish)
```

Remove the worker-thread media write.

Change `replace_current_field_after_noise_removal()`:

```python
def replace_current_field_after_noise_removal(
    editor: Any,
    saved_name: str,
    deps: Any,
    *,
    guard: EditorProcessingGuard | None = None,
    output_path: Path | None = None,
) -> None:
    session = deps.sessions.get(editor)
    if guard is not None and (session is None or not is_current_processing_guard(session, guard)):
        return
    if output_path is not None:
        saved_name = deps.write_generated_media(editor, saved_name, output_path)
```

Keep the existing replacement body after those checks.

- [ ] **Step 5: Apply guarded main-thread persistence to region delete**

In `addon/anki_audio_quick_editor/editor_region_delete.py`, import the same helpers. In `delete_selection_async()`, create a guard after setting `session.processing = True`:

```python
guard = begin_processing_guard(
    session,
    field_index=request.field_index,
    source_filename=request.source_filename,
)
```

Replace the worker-thread `editor.mw.col.media.write_data()` and completion with:

```python
def _finish() -> None:
    try:
        deps.replace_current_field_after_region_delete(
            editor,
            request,
            desired_name,
            result.duration_ms,
            started_at,
            guard=guard,
            output_path=output_path,
        )
    finally:
        shutil.rmtree(output_path.parent, ignore_errors=True)

deps.main(editor, _finish)
```

Change `replace_current_field_after_region_delete()`:

```python
def replace_current_field_after_region_delete(
    editor: Any,
    request: RegionDeleteRequest,
    saved_name: str,
    output_duration_ms: int | None,
    started_at: float,
    deps: Any,
    *,
    guard: EditorProcessingGuard | None = None,
    output_path: Path | None = None,
) -> None:
    session = deps.sessions.get(editor)
    if guard is not None and (session is None or not is_current_processing_guard(session, guard)):
        return
    if output_path is not None:
        with output_path.open("rb") as file:
            saved_name = editor.mw.col.media.write_data(saved_name, file.read())
```

Keep the existing try/body after those checks.

- [ ] **Step 6: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_editor_noise_reduction_callbacks.py tests/test_editor_region_delete_integration.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add addon/anki_audio_quick_editor/editor_special_transforms.py addon/anki_audio_quick_editor/editor_region_delete.py tests/test_editor_noise_reduction_callbacks.py tests/test_editor_region_delete_integration.py
git commit -m "fix: guard stale editor transform completions"
```

## Task 4: Protect Batch Runs from Duplicate Starts and Field Clobbering

**Files:**
- Modify: `addon/anki_audio_quick_editor/browser_dialog.py`
- Modify: `addon/anki_audio_quick_editor/batch_operations.py`
- Modify: `addon/anki_audio_quick_editor/browser_integration.py`
- Test: `tests/test_browser_dialog.py`
- Test: `tests/test_browser_integration.py`

- [ ] **Step 1: Add duplicate-start dialog test**

Append to `tests/test_browser_dialog.py`:

```python
def test_batch_dialog_ignores_duplicate_start_while_running(monkeypatch, request) -> None:
    dialog_module = _reload_browser_dialog_with_fake_qt(request)
    run_calls = []
    monkeypatch.setattr(dialog_module, "request_from_batch_start_payload", lambda _payload: "request")

    dialog = dialog_module.BatchOperationsDialog(
        browser=object(),
        note_ids=[1, 2],
        groups=(),
        config=AudioProcessingConfig(),
        run_batch_in_background=lambda *args: run_calls.append(args),
    )
    command = "bridge:" + json.dumps({"command": "batch.start", "payload": {"operation": "graph"}})

    assert dialog._webview.bridge(command) is True
    assert dialog._webview.bridge(command) is True

    assert len(run_calls) == 1
```

- [ ] **Step 2: Add batch field-conflict test**

Add `__getitem__()` to `_FakeNote` in `tests/test_browser_integration.py`:

```python
def __getitem__(self, key: str) -> str:
    return self.fields[key]
```

Append this test:

```python
def test_run_batch_does_not_overwrite_field_changed_after_snapshot(monkeypatch, tmp_path: Path) -> None:
    col = _FakeCol()

    def fake_process(*_args, **_kwargs) -> BatchNoteResult:
        col.notes[1].fields["Image"] = "user edit"
        return BatchNoteResult(
            note_id=1,
            status="written",
            message="appended viz.svg",
            target_field="Image",
            target_html='<img src="viz.svg">',
            audio_filename="clip.mp3",
            image_filename="viz.svg",
            written_filename="viz.svg",
            original_target_html="",
        )

    monkeypatch.setattr("anki_audio_quick_editor.browser_integration._process_note", fake_process)

    report = _run_batch(
        col,
        [1],
        BatchRunRequest(operation=OP_GRAPH, source_field="Audio", target_field="Image"),
        tmp_path,
        AudioProcessingConfig(),
        threading.Event(),
        lambda _line: None,
        lambda *_args: None,
    )

    assert report.written == 0
    assert report.failures == 1
    assert col.notes[1].fields["Image"] == "user edit"
    assert col.updated == []
```

- [ ] **Step 3: Run focused tests and verify they fail**

Run:

```bash
python3 -m pytest tests/test_browser_dialog.py tests/test_browser_integration.py -q
```

Expected: FAIL because duplicate starts are accepted and `BatchNoteResult` lacks `original_target_html`.

- [ ] **Step 4: Reject duplicate batch starts**

In `BatchOperationsDialog._handle_batch_start()`, add this at the top:

```python
if self._running:
    return True
```

Do not emit another start/progress event here. The frontend is already in the running state; the important invariant is that no second background task starts.

- [ ] **Step 5: Add optimistic field checks to batch results**

In `BatchNoteResult`, add:

```python
original_target_html: str | None = None
```

In `_process_graph_operation()`, include the target field snapshot:

```python
original_target_html=note.fields[target_field],
```

In `_process_transform_operation()`, include the source field snapshot:

```python
original_target_html=source_html,
```

In `browser_integration.py`, add a helper near `_apply_result()`:

```python
def _note_field_value(note: Any, field_name: str) -> str:
    try:
        return str(note[field_name])
    except (KeyError, TypeError, AttributeError):
        fields = getattr(note, "fields", None)
        if isinstance(fields, dict):
            return str(fields[field_name])
        raise
```

Then check before writing:

```python
if result.original_target_html is not None:
    current_html = _note_field_value(note, result.target_field)
    if current_html != result.original_target_html:
        report.failures += 1
        return BatchNoteResult(
            note_id=result.note_id,
            status="failed",
            message=f"target field {result.target_field!r} changed during batch run",
            target_field=result.target_field,
            target_html=result.target_html,
            audio_filename=result.audio_filename,
            image_filename=result.image_filename,
            written_filename=result.written_filename,
            original_target_html=result.original_target_html,
        )
```

- [ ] **Step 6: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_browser_dialog.py tests/test_browser_integration.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add addon/anki_audio_quick_editor/browser_dialog.py addon/anki_audio_quick_editor/batch_operations.py addon/anki_audio_quick_editor/browser_integration.py tests/test_browser_dialog.py tests/test_browser_integration.py
git commit -m "fix: prevent duplicate and stale batch writes"
```

## Task 5: Serialize Prosody Cache Access

**Files:**
- Modify: `addon/anki_audio_quick_editor/prosody_cache.py`
- Test: `tests/test_prosody_cache.py`

- [ ] **Step 1: Add concurrent cache test**

Append to `tests/test_prosody_cache.py`:

```python
def test_prosody_cache_serializes_concurrent_same_file_analysis(tmp_path: Path, monkeypatch) -> None:
    import threading

    source = tmp_path / "clip.mp3"
    source.write_bytes(b"audio")
    track = ProsodyTrack(
        duration_ms=1000,
        points=(ProsodyPoint(0, 220.0, -20.0, 0.5, True),),
        pitch_min_hz=220.0,
        pitch_max_hz=220.0,
        source_filename="clip.mp3",
        analyzer_name="test",
    )
    calls: list[Path] = []

    def fake_analyze(path: Path, _config: AudioProcessingConfig) -> ProsodyTrack:
        calls.append(path)
        return track

    monkeypatch.setattr("anki_audio_quick_editor.prosody_cache.analyze_prosody", fake_analyze)
    _ANALYSIS_CACHE.clear()

    results: list[ProsodyTrack] = []
    threads = [
        threading.Thread(target=lambda: results.append(analyze_prosody_cached(source, AudioProcessingConfig())))
        for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results == [track, track]
    assert calls == [source]
```

- [ ] **Step 2: Run the cache test and verify it fails**

Run:

```bash
python3 -m pytest tests/test_prosody_cache.py -q
```

Expected: FAIL intermittently or consistently with duplicate analysis calls. If it passes once due thread timing, run it five times:

```bash
for i in 1 2 3 4 5; do python3 -m pytest tests/test_prosody_cache.py::test_prosody_cache_serializes_concurrent_same_file_analysis -q || exit 1; done
```

- [ ] **Step 3: Add a cache lock**

In `addon/anki_audio_quick_editor/prosody_cache.py`:

```python
import threading
```

Add:

```python
_ANALYSIS_CACHE_LOCK = threading.RLock()
```

Wrap the entire body of `analyze_prosody_cached()`:

```python
def analyze_prosody_cached(path: Path, config: AudioProcessingConfig) -> ProsodyTrack:
    """Analyze ``path`` and reuse results while the file identity is unchanged."""
    key = prosody_cache_key(path, config)
    with _ANALYSIS_CACHE_LOCK:
        cached = _ANALYSIS_CACHE.get(key)
        if cached is not None:
            return cached
        track = analyze_prosody(path, config)
        _ANALYSIS_CACHE[key] = track
        while len(_ANALYSIS_CACHE) > _ANALYSIS_CACHE_MAX:
            _ANALYSIS_CACHE.pop(next(iter(_ANALYSIS_CACHE)))
        return track
```

This serializes prosody analysis globally. That is conservative but acceptable because analysis is already user-visible background work, and correctness matters more than parallel throughput here.

- [ ] **Step 4: Run cache tests repeatedly**

Run:

```bash
for i in 1 2 3 4 5; do python3 -m pytest tests/test_prosody_cache.py -q || exit 1; done
```

Expected: PASS on all five runs.

- [ ] **Step 5: Commit**

```bash
git add addon/anki_audio_quick_editor/prosody_cache.py tests/test_prosody_cache.py
git commit -m "fix: serialize prosody cache access"
```

## Task 6: Queue Frontend Pending Bridge Requests

**Files:**
- Modify: `settings_ui/src/editor-inline/bridge.ts`
- Test: `settings_ui/tests/editor-inline.bridge.test.ts`

- [ ] **Step 1: Add FIFO bridge queue tests**

Create `settings_ui/tests/editor-inline.bridge.test.ts`:

```typescript
import { beforeEach, describe, expect, it, vi } from "vitest";

describe("editor inline bridge pending requests", () => {
  beforeEach(() => {
    vi.resetModules();
    Reflect.deleteProperty(globalThis, "pycmd");
  });

  it("queues graph analysis requests instead of overwriting the previous one", async () => {
    const bridge = await import("../src/editor-inline/bridge.js");

    bridge.sendGraphAnalysisRequest({ ord: 0, filename: "first.mp3", graphSettings: null });
    bridge.sendGraphAnalysisRequest({ ord: 1, filename: "second.mp3", graphSettings: null });

    expect(bridge.popPendingGraphAnalysisRequest()?.filename).toBe("first.mp3");
    expect(bridge.popPendingGraphAnalysisRequest()?.filename).toBe("second.mp3");
    expect(bridge.popPendingGraphAnalysisRequest()).toBeNull();
  });

  it("queues region delete requests instead of overwriting the previous one", async () => {
    const bridge = await import("../src/editor-inline/bridge.js");

    bridge.setPendingRegionDeleteRequest({
      ord: 0,
      sourceFilename: "first.mp3",
      selectionStartMs: 10,
      selectionEndMs: 20,
      cursorMs: 10,
      durationMs: 100,
      trigger: "button",
      playbackActive: false,
      operation: "delete-selection",
    });
    bridge.setPendingRegionDeleteRequest({
      ord: 1,
      sourceFilename: "second.mp3",
      selectionStartMs: 30,
      selectionEndMs: 40,
      cursorMs: 30,
      durationMs: 100,
      trigger: "button",
      playbackActive: false,
      operation: "delete-selection",
    });

    expect(bridge.popPendingRegionDeleteRequest()?.sourceFilename).toBe("first.mp3");
    expect(bridge.popPendingRegionDeleteRequest()?.sourceFilename).toBe("second.mp3");
    expect(bridge.popPendingRegionDeleteRequest()).toBeNull();
  });
});
```

- [ ] **Step 2: Run bridge tests and verify they fail**

Run:

```bash
cd settings_ui && npm test -- editor-inline.bridge.test.ts --run
```

Expected: FAIL because `pendingGraphAnalysisRequest` and `pendingRegionDeleteRequest` only store one request.

- [ ] **Step 3: Replace single slots with queues**

In `settings_ui/src/editor-inline/bridge.ts`, replace the pending request declarations:

```typescript
const pendingGraphAnalysisRequests: GraphAnalysisRequest[] = [];
const pendingRegionDeleteRequests: RegionDeleteRequest[] = [];
const pendingSplitDefaultSaveRequests: SplitDefaultSaveRequest[] = [];
```

Update request producers:

```typescript
export function sendGraphAnalysisRequest(request: GraphAnalysisRequest): void {
  pendingGraphAnalysisRequests.push(request);
  sendBridgeCommand("aqe:analyze-field");
}

export function sendSplitDefaultSaveRequest(request: SplitDefaultSaveRequest): void {
  pendingSplitDefaultSaveRequests.push(request);
  sendBridgeCommand("aqe:save-split-defaults");
}

export function setPendingRegionDeleteRequest(request: RegionDeleteRequest): void {
  pendingRegionDeleteRequests.push(request);
}
```

Update poppers:

```typescript
export function popPendingGraphAnalysisRequest(): GraphAnalysisRequest | null {
  return pendingGraphAnalysisRequests.shift() ?? null;
}

export function popPendingRegionDeleteRequest(): RegionDeleteRequest | null {
  return pendingRegionDeleteRequests.shift() ?? null;
}

export function popPendingSplitDefaultSaveRequest(): SplitDefaultSaveRequest | null {
  return pendingSplitDefaultSaveRequests.shift() ?? null;
}
```

- [ ] **Step 4: Run frontend bridge tests**

Run:

```bash
cd settings_ui && npm test -- editor-inline.bridge.test.ts --run
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add settings_ui/src/editor-inline/bridge.ts settings_ui/tests/editor-inline.bridge.test.ts
git commit -m "fix: queue editor bridge payloads"
```

## Task 7: Add Regression Coverage to the Existing Quality Gate

**Files:**
- Modify only test files touched by previous tasks if imports or timing need adjustment.

- [ ] **Step 1: Run targeted race-condition suites**

Run:

```bash
python3 -m pytest \
  tests/test_editor_processing_guard.py \
  tests/test_editor_post_edit_playback.py \
  tests/test_editor_noise_reduction_callbacks.py \
  tests/test_editor_region_delete_integration.py \
  tests/test_browser_dialog.py \
  tests/test_browser_integration.py \
  tests/test_prosody_cache.py \
  -q
```

Expected: PASS.

- [ ] **Step 2: Run frontend tests for bridge behavior**

Run:

```bash
cd settings_ui && npm test -- editor-inline.bridge.test.ts --run
```

Expected: PASS.

- [ ] **Step 3: Run repository QC**

Run:

```bash
python3 scripts/dev.py check
```

Expected: PASS.

- [ ] **Step 4: Run required E2E suite**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS.

- [ ] **Step 5: Commit any test-only fixups**

If Step 1 through Step 4 required small test import or timing adjustments, commit them:

```bash
git add tests settings_ui/tests settings_ui/src addon/anki_audio_quick_editor
git commit -m "test: cover async race regressions"
```

If there were no additional changes after the earlier commits, skip this commit.

## Self-Review

- Spec coverage: The plan covers stale editor completions, unsafe worker media writes, duplicate batch starts, batch field clobbering, prosody cache concurrency, and frontend pending-payload overwrites.
- Marker scan: No incomplete markers or unspecified "add tests" steps remain.
- Type consistency: Guard helpers use `EditorProcessingGuard`, `processing_generation`, `begin_processing_guard()`, `invalidate_processing_guard()`, and `is_current_processing_guard()` consistently across tasks.
- Execution risk: Task 3 depends on Task 1 and Task 2. Task 4, Task 5, and Task 6 are independent and can be handled by separate workers after Task 1 lands.
