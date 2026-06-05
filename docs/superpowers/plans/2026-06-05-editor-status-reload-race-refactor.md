# Editor Status Reload Race Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make editor reload completion statuses survive Anki note reloads, graph redraws, playback completion, and controller reuse.

**Architecture:** Treat reload status as an `EditorSession` lifecycle concern: one backend helper sets `PendingEditorStatus`, disposes stale frontend controls, and calls `editor.loadNote(...)` without clearing the pending status. On the frontend, consume `initialStatusByField` in `field-controller.ts` only and make status ownership explicit so graph and playback transients cannot erase stable edit/error statuses.

**Tech Stack:** Python 3.13 Anki add-on runtime, Svelte 5, TypeScript, Vitest, pytest, Anki e2e through `scripts/dev.py`.

---

## File Structure

- Modify `addon/anki_audio_quick_editor/editor_session.py`
  Add `reload_editor_with_pending_status(...)` beside `PendingEditorStatus` and existing lifecycle reset helpers.

- Modify `addon/anki_audio_quick_editor/editor_processing.py`
  Use the shared helper for standard render replacement and stop constructing `PendingEditorStatus` inside `_replace_standard_render_session_state(...)`.

- Modify `addon/anki_audio_quick_editor/editor_history.py`
  Use the shared helper for undo/redo reloads and keep the pending undo/redo status alive after reload.

- Modify `addon/anki_audio_quick_editor/editor_region_delete.py`
  Use the shared helper for region delete reloads and remove the immediate `session.pending_status = None` clear.

- Modify `addon/anki_audio_quick_editor/editor_special_transforms.py`
  Use the shared helper for denoise, DPDFNet, voice-only, pitch-hum, convert, and size-reduction reloads and remove the immediate clear.

- Modify `addon/anki_audio_quick_editor/editor_settings_actions.py`
  Use the shared helper for settings-save reloads and remove the immediate clear.

- Create `tests/test_editor_pending_reload_status.py`
  Add focused unit coverage for the shared helper preserving pending status through `loadNote(...)`.

- Modify `tests/test_editor_post_edit_playback.py`
  Assert standard render replacement preserves the expected pending status.

- Modify `tests/test_editor_integration.py`
  Assert undo/redo and settings-save reloads preserve pending status after `loadNote(...)`.

- Modify `tests/test_editor_region_delete_integration.py`
  Assert region delete preserves the expected pending status after reload.

- Modify `tests/test_editor_noise_reduction_callbacks.py` and `tests/test_editor_pitch_hum_callbacks.py`
  Assert special/noise-reduction transform reloads preserve expected pending statuses.

- Modify `settings_ui/src/editor-inline/control-actions.ts`
  Add explicit status ownership, one-shot initial status consumption, and playback-owned transient clearing.

- Modify `settings_ui/src/editor-inline/field-controller.ts`
  Make this the only `initialStatusByField` consumer; pass initial status into new Svelte mounts and apply it imperatively only when a controller is reused.

- Modify `settings_ui/src/editor-inline/EditorControls.svelte`
  Remove direct reads of `window.__AQE_EDITOR_CONFIG__.initialStatusByField`; receive `initialStatus` as a prop and render initial stable status attributes from that prop.

- Modify `settings_ui/src/editor-inline/graph-actions.ts`
  Mark graph progress, graph warnings, and graph errors as graph-owned statuses.

- Modify `settings_ui/src/editor-inline/playback-actions.ts`
  Mark playback-only warnings as playback-owned statuses.

- Modify `settings_ui/src/editor-inline/actions.ts`
  Wire playback controller dependencies to the new playback-only clear function.

- Modify frontend tests:
  `settings_ui/tests/editor-inline.integration.test.ts`,
  `settings_ui/tests/editor-inline.actions.test.ts`,
  and `settings_ui/tests/editor-inline.playback.integration.test.ts`.

- Modify e2e tests:
  `e2e/test_editor_processing_graph_default_workflow.py`,
  `e2e/test_editor_region_delete_workflow.py`,
  and `e2e/test_editor_integration.py`.

---

### Task 1: Add Failing Backend Helper Tests

**Files:**
- Create: `tests/test_editor_pending_reload_status.py`
- Test: `tests/test_editor_pending_reload_status.py`

- [ ] **Step 1: Create focused helper tests**

Create `tests/test_editor_pending_reload_status.py` with this content:

```python
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from anki_audio_quick_editor.editor_session import (
    EditorSession,
    PendingEditorStatus,
    reload_editor_with_pending_status,
)


def test_reload_editor_with_pending_status_preserves_status_through_load() -> None:
    session = EditorSession()
    load_observed: list[PendingEditorStatus | None] = []

    editor = SimpleNamespace()
    editor.loadNote = MagicMock(side_effect=lambda **_kwargs: load_observed.append(session.pending_status))
    deps = SimpleNamespace(dispose_editor_frontend_controls=MagicMock())

    reload_editor_with_pending_status(
        editor,
        session,
        2,
        message="Closed settings.",
        kind="info",
        deps=deps,
    )

    expected = PendingEditorStatus(2, kind="info", message="Closed settings.")
    assert load_observed == [expected]
    assert session.pending_status == expected
    deps.dispose_editor_frontend_controls.assert_called_once_with(editor)
    editor.loadNote.assert_called_once_with(focusTo=2)


def test_reload_editor_with_pending_status_supports_missing_session() -> None:
    editor = SimpleNamespace(loadNote=MagicMock())
    deps = SimpleNamespace(dispose_editor_frontend_controls=MagicMock())

    reload_editor_with_pending_status(
        editor,
        None,
        1,
        message="Deleted selection 500-1250 ms.",
        deps=deps,
    )

    deps.dispose_editor_frontend_controls.assert_called_once_with(editor)
    editor.loadNote.assert_called_once_with(focusTo=1)
```

- [ ] **Step 2: Run the new tests and confirm they fail**

Run:

```bash
python3 scripts/dev.py test -- tests/test_editor_pending_reload_status.py -q
```

Expected: FAIL with an import error because `reload_editor_with_pending_status` does not exist yet.

---

### Task 2: Implement The Shared Backend Reload Helper

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_session.py`
- Test: `tests/test_editor_pending_reload_status.py`

- [ ] **Step 1: Add the helper to `editor_session.py`**

Insert this function immediately after `PendingEditorStatus`:

```python
def reload_editor_with_pending_status(
    editor: Any,
    session: EditorSession | None,
    field_index: int,
    *,
    message: str = "",
    kind: str = "info",
    deps: Any,
) -> None:
    """Reload editor controls while preserving one status for frontend injection."""
    if session is not None and message:
        session.pending_status = PendingEditorStatus(field_index, kind=kind, message=message)
    deps.dispose_editor_frontend_controls(editor)
    editor.loadNote(focusTo=field_index)
```

Keep `Any` imported from `typing`; it is already present in this file.

- [ ] **Step 2: Run the helper tests**

Run:

```bash
python3 scripts/dev.py test -- tests/test_editor_pending_reload_status.py -q
```

Expected: PASS.

- [ ] **Step 3: Commit the helper and tests**

Run:

```bash
git add addon/anki_audio_quick_editor/editor_session.py tests/test_editor_pending_reload_status.py
git commit -m "Introduce reload status lifecycle helper" -m "The editor reload path needs one backend owner for pending completion status because loadNote schedules frontend injection asynchronously. This helper preserves PendingEditorStatus through the reload and centralizes frontend disposal so future reload-with-status paths do not copy the race-prone clear-after-load pattern. Verified with the focused helper pytest; full check and e2e routines not yet run."
```

---

### Task 3: Migrate Backend Reload Call Sites

**Files:**
- Modify: `addon/anki_audio_quick_editor/editor_processing.py`
- Modify: `addon/anki_audio_quick_editor/editor_history.py`
- Modify: `addon/anki_audio_quick_editor/editor_region_delete.py`
- Modify: `addon/anki_audio_quick_editor/editor_special_transforms.py`
- Modify: `addon/anki_audio_quick_editor/editor_settings_actions.py`
- Test: `tests/test_editor_post_edit_playback.py`
- Test: `tests/test_editor_integration.py`
- Test: `tests/test_editor_region_delete_integration.py`
- Test: `tests/test_editor_noise_reduction_callbacks.py`
- Test: `tests/test_editor_pitch_hum_callbacks.py`

- [ ] **Step 1: Add failing assertions for standard render pending status**

In `tests/test_editor_post_edit_playback.py`, add this import:

```python
from anki_audio_quick_editor.editor_session import PendingEditorStatus
```

In `test_standard_render_replacement_records_pending_post_edit_playback`, change the session setup to seed the status summary that the bridge command normally sets before async rendering:

```python
    _SESSIONS[editor] = EditorSession(
        state=AudioEditState("clip.mp3"),
        field_index=0,
        current_filename="clip.mp3",
        next_status_summary="Increased volume by 15 dB.",
    )
```

Add this assertion after `session = _SESSIONS[editor]`:

```python
    assert session.pending_status == PendingEditorStatus(
        0,
        message="Increased volume by 15 dB.",
    )
```

Run:

```bash
python3 scripts/dev.py test -- tests/test_editor_post_edit_playback.py::test_standard_render_replacement_records_pending_post_edit_playback -q
```

Expected before call-site migration: this documents the already-fixed standard path and should PASS.

- [ ] **Step 2: Add failing assertions for settings, undo, and redo**

In `tests/test_editor_integration.py`, add this import:

```python
from anki_audio_quick_editor.editor_session import PendingEditorStatus
```

In `test_editor_undo_and_redo_restore_audio_references_without_processing`, add after the first reload status assertion:

```python
    assert session.pending_status == PendingEditorStatus(
        0,
        message="Undid: Original audio.",
    )
```

After the redo reload status assertion, add:

```python
    assert session.pending_status == PendingEditorStatus(
        0,
        message="Redid: Increased speed to x1.5.",
    )
```

In `test_editor_settings_command_opens_settings_and_refreshes_after_save`, add after `assert reload_statuses == ...`:

```python
    assert session.pending_status == PendingEditorStatus(
        0,
        message="Closed settings.",
    )
```

Run:

```bash
python3 scripts/dev.py test -- tests/test_editor_integration.py::test_editor_undo_and_redo_restore_audio_references_without_processing tests/test_editor_integration.py::test_editor_settings_command_opens_settings_and_refreshes_after_save -q
```

Expected: undo/redo assertions PASS; settings assertion FAIL because `refresh_editor_after_settings_save(...)` clears `session.pending_status` after `loadNote(...)`.

- [ ] **Step 3: Add failing assertion for region delete**

In `tests/test_editor_region_delete_integration.py`, add this import:

```python
from anki_audio_quick_editor.editor_session import PendingEditorStatus
```

In `test_region_delete_replacement_updates_only_requested_field_and_history`, add after `session = _SESSIONS[editor]` or before post-edit playback assertions:

```python
    assert session.pending_status == PendingEditorStatus(
        1,
        message="Deleted selection 250-750 ms.",
    )
```

Run:

```bash
python3 scripts/dev.py test -- tests/test_editor_region_delete_integration.py::test_region_delete_replacement_updates_only_requested_field_and_history -q
```

Expected: FAIL because `replace_current_field_after_region_delete(...)` clears `session.pending_status` after `loadNote(...)`.

- [ ] **Step 4: Add failing assertions for special/noise-reduction transforms**

In `tests/test_editor_noise_reduction_callbacks.py`, add this import:

```python
from anki_audio_quick_editor.editor_session import PendingEditorStatus
```

In `test_standard_denoise_replaces_current_media_and_resets_state`, add after `session = _SESSIONS[editor]`:

```python
    assert session.pending_status == PendingEditorStatus(
        0,
        message="Cleaned audio with Standard.",
    )
```

In `tests/test_editor_pitch_hum_callbacks.py`, add this import:

```python
from anki_audio_quick_editor.editor_session import PendingEditorStatus
```

In `test_pitch_hum_replaces_current_media_and_resets_state`, add after `session = _SESSIONS[editor]`:

```python
    assert session.pending_status == PendingEditorStatus(
        0,
        message="Rendered pitch hum with Direct mode.",
    )
```

Run:

```bash
python3 scripts/dev.py test -- tests/test_editor_noise_reduction_callbacks.py::test_standard_denoise_replaces_current_media_and_resets_state tests/test_editor_pitch_hum_callbacks.py::test_pitch_hum_replaces_current_media_and_resets_state -q
```

Expected: FAIL because special transform reloads clear `session.pending_status` after `loadNote(...)`.

- [ ] **Step 5: Migrate standard processing**

In `addon/anki_audio_quick_editor/editor_processing.py`, change the import block from `editor_session` to include `reload_editor_with_pending_status` and remove `PendingEditorStatus` if it is no longer used:

```python
from .editor_session import (
    EditorProcessingGuard,
    EditorSession,
    begin_processing_guard,
    clear_processing_for_stale_guard,
    is_current_processing_guard,
    processing_guard_matches_editor,
    reload_editor_with_pending_status,
)
```

In `replace_current_field_after_render(...)`, remove:

```python
    deps.dispose_editor_frontend_controls(editor)
```

Replace:

```python
    editor.loadNote(focusTo=field_index)
```

with:

```python
    reload_editor_with_pending_status(
        editor,
        session,
        field_index,
        message=session.status_summary if session is not None else "",
        deps=deps,
    )
```

In `_replace_standard_render_session_state(...)`, remove:

```python
    session.pending_status = PendingEditorStatus(field_index, message=session.status_summary)
```

- [ ] **Step 6: Migrate undo/redo history restore**

In `addon/anki_audio_quick_editor/editor_history.py`, change the import:

```python
from .editor_session import EditorSession, UndoEntry, reload_editor_with_pending_status
```

Remove:

```python
    deps.dispose_editor_frontend_controls(editor)
```

Remove:

```python
    session.pending_status = PendingEditorStatus(field_index, message=status)
```

Replace:

```python
    editor.loadNote(focusTo=field_index)
```

with:

```python
    reload_editor_with_pending_status(
        editor,
        session,
        field_index,
        message=status,
        deps=deps,
    )
```

- [ ] **Step 7: Migrate region delete**

In `addon/anki_audio_quick_editor/editor_region_delete.py`, add `reload_editor_with_pending_status` to the `editor_session` import and remove `PendingEditorStatus` if unused.

Remove:

```python
        deps.dispose_editor_frontend_controls(editor)
```

Replace:

```python
        editor.loadNote(focusTo=field_index)
        if session:
            session.pending_status = None
```

with:

```python
        reload_editor_with_pending_status(
            editor,
            session,
            field_index,
            message=session.status_summary if session is not None else "",
            deps=deps,
        )
```

In `_replace_region_delete_session_state(...)`, remove:

```python
    session.pending_status = PendingEditorStatus(field_index, message=session.status_summary)
```

- [ ] **Step 8: Migrate special transforms**

In `addon/anki_audio_quick_editor/editor_special_transforms.py`, add `reload_editor_with_pending_status` to the `editor_session` import and remove `PendingEditorStatus` if unused.

Remove:

```python
    deps.dispose_editor_frontend_controls(editor)
```

Replace:

```python
    editor.loadNote(focusTo=field_index)
    if session:
        session.pending_status = None
```

with:

```python
    reload_editor_with_pending_status(
        editor,
        session,
        field_index,
        message=session.status_summary if session is not None else "",
        deps=deps,
    )
```

In `_replace_noise_reduction_session_state(...)`, remove:

```python
    session.pending_status = PendingEditorStatus(field_index, message=session.status_summary)
```

- [ ] **Step 9: Migrate settings save reload**

In `addon/anki_audio_quick_editor/editor_settings_actions.py`, change the import:

```python
from .editor_session import ready_learner_recording_media_path, reload_editor_with_pending_status
```

Remove:

```python
        if status_after_reload:
            session.pending_status = PendingEditorStatus(field_index, message=status_after_reload)
    deps.dispose_editor_frontend_controls(editor)
    editor.loadNote(focusTo=field_index)
    if session is not None:
        session.pending_status = None
```

Replace it with:

```python
    reload_editor_with_pending_status(
        editor,
        session,
        field_index,
        message=status_after_reload,
        deps=deps,
    )
```

- [ ] **Step 10: Run backend targeted tests**

Run:

```bash
python3 scripts/dev.py test -- tests/test_editor_pending_reload_status.py tests/test_editor_post_edit_playback.py::test_standard_render_replacement_records_pending_post_edit_playback tests/test_editor_integration.py::test_editor_undo_and_redo_restore_audio_references_without_processing tests/test_editor_integration.py::test_editor_settings_command_opens_settings_and_refreshes_after_save tests/test_editor_region_delete_integration.py::test_region_delete_replacement_updates_only_requested_field_and_history tests/test_editor_noise_reduction_callbacks.py::test_standard_denoise_replaces_current_media_and_resets_state tests/test_editor_pitch_hum_callbacks.py::test_pitch_hum_replaces_current_media_and_resets_state -q
```

Expected: PASS.

- [ ] **Step 11: Check no reload callsite clears pending status immediately**

Run:

```bash
rg -n "loadNote\\(|pending_status = None|PendingEditorStatus" addon/anki_audio_quick_editor/editor_processing.py addon/anki_audio_quick_editor/editor_history.py addon/anki_audio_quick_editor/editor_region_delete.py addon/anki_audio_quick_editor/editor_special_transforms.py addon/anki_audio_quick_editor/editor_settings_actions.py addon/anki_audio_quick_editor/editor_session.py
```

Expected:
- `PendingEditorStatus` construction appears in `editor_session.py`.
- Target reload paths call `reload_editor_with_pending_status(...)`.
- `pending_status = None` remains only in legitimate lifecycle cleanup functions such as `reset_for_note_load`, `reset_session_for_media`, stale guard cleanup, and failure cleanup, not immediately after `loadNote(...)`.

- [ ] **Step 12: Commit backend call-site migration**

Run:

```bash
git add addon/anki_audio_quick_editor/editor_session.py addon/anki_audio_quick_editor/editor_processing.py addon/anki_audio_quick_editor/editor_history.py addon/anki_audio_quick_editor/editor_region_delete.py addon/anki_audio_quick_editor/editor_special_transforms.py addon/anki_audio_quick_editor/editor_settings_actions.py tests/test_editor_pending_reload_status.py tests/test_editor_post_edit_playback.py tests/test_editor_integration.py tests/test_editor_region_delete_integration.py tests/test_editor_noise_reduction_callbacks.py tests/test_editor_pitch_hum_callbacks.py
git commit -m "Route editor reload statuses through one lifecycle helper" -m "Reload completion status was previously a per-callsite convention, which let some paths clear PendingEditorStatus before the injected editor bundle could serialize it. Routing standard processing, history restore, settings save, region delete, and special transforms through the helper keeps the status alive until a real session lifecycle reset. Verified with focused backend pytest targets and a literal callsite scan; full check and e2e routines not yet run."
```

---

### Task 4: Make Initial Status Consumption Single-Owner

**Files:**
- Modify: `settings_ui/src/editor-inline/control-actions.ts`
- Modify: `settings_ui/src/editor-inline/field-controller.ts`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/tests/editor-inline.integration.test.ts`

- [ ] **Step 1: Add a failing integration test for one-shot consumption**

In `settings_ui/tests/editor-inline.integration.test.ts`, add this test after `renders one canonical status element after the visualizer`:

```ts
  it("consumes initial status once in the field controller", () => {
    const config = {
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Closed settings." },
      },
    };
    initializeEditorRuntime(config);
    scan(config);

    const status = document.querySelector<HTMLElement>('[data-testid="aqe-status-0"]')!;
    expect(status).toHaveTextContent("Closed settings.");
    expect(window.__AQE_EDITOR_CONFIG__?.initialStatusByField?.[0]).toBeUndefined();

    status.textContent = "";
    scan(config);

    expect(status).toHaveTextContent("");
    expect(window.__AQE_EDITOR_CONFIG__?.initialStatusByField?.[0]).toBeUndefined();
  });
```

Run:

```bash
cd settings_ui
npm test -- --run tests/editor-inline.integration.test.ts
```

Expected before implementation: FAIL because `EditorControls.svelte` still reads `initialStatusByField` directly during mount, and consumption ownership is split.

- [ ] **Step 2: Add typed one-shot consumption helpers**

In `settings_ui/src/editor-inline/control-actions.ts`, add this exported interface near `EditorStatusMessage`:

```ts
export interface InitialEditorStatus {
  kind?: string;
  message: string;
}
```

Replace `applyInitialStatusForOrd(...)` with:

```ts
export function consumeInitialStatusForOrd(ord: number): InitialEditorStatus | null {
  const initialStatuses = window.__AQE_EDITOR_CONFIG__?.initialStatusByField;
  const initialStatus = initialStatuses?.[ord];
  if (initialStatuses) {
    delete initialStatuses[ord];
  }
  return initialStatus?.message ? initialStatus : null;
}

export function applyInitialStatusForOrd(ord: number, initialStatus: InitialEditorStatus | null): void {
  if (!initialStatus?.message) return;
  setStatusForOrd(ord, initialStatus.message, initialStatus.kind || "info");
}
```

- [ ] **Step 3: Move global consumption into `field-controller.ts`**

In `settings_ui/src/editor-inline/field-controller.ts`, replace the import:

```ts
import { applyInitialStatusForOrd, consumeInitialStatusForOrd } from "./control-actions.js";
```

At the top of `mountController(target: FieldTarget)`, add:

```ts
  const initialStatus = consumeInitialStatusForOrd(target.ord);
```

Replace every reuse call:

```ts
      applyInitialStatusForOrd(target.ord);
```

with:

```ts
      applyInitialStatusForOrd(target.ord, initialStatus);
```

Replace the mount props:

```ts
    props: { target },
```

with:

```ts
    props: { initialStatus, target },
```

Remove the post-mount call:

```ts
  applyInitialStatusForOrd(target.ord);
```

- [ ] **Step 4: Remove direct global reads from `EditorControls.svelte`**

In `settings_ui/src/editor-inline/EditorControls.svelte`, add the type import:

```ts
  import type { InitialEditorStatus } from "./control-actions.js";
```

Replace:

```ts
  const { target }: { target: FieldTarget } = $props();
```

with:

```ts
  const {
    initialStatus = null,
    target,
  }: { initialStatus?: InitialEditorStatus | null; target: FieldTarget } = $props();
```

Remove:

```ts
  const initialStatus = (() => window.__AQE_EDITOR_CONFIG__?.initialStatusByField?.[target.ord])();
```

Keep:

```ts
  const initialStatusKind = initialStatus?.kind || "info";
  const initialStatusMessage = initialStatus?.message || "";
```

- [ ] **Step 5: Run the focused frontend integration test**

Run:

```bash
cd settings_ui
npm test -- --run tests/editor-inline.integration.test.ts
```

Expected: PASS.

- [ ] **Step 6: Commit single-owner initial status consumption**

Run:

```bash
git add settings_ui/src/editor-inline/control-actions.ts settings_ui/src/editor-inline/field-controller.ts settings_ui/src/editor-inline/EditorControls.svelte settings_ui/tests/editor-inline.integration.test.ts
git commit -m "Consume editor reload status in the field controller" -m "Initial status injection needs one frontend owner because duplicate readers can delete or reapply the same global config in different lifecycle paths. Moving consumption to the field controller gives reused controllers and fresh Svelte mounts the same one-shot source of truth. Verified with focused Vitest integration coverage; full check and e2e routines not yet run."
```

---

### Task 5: Add Explicit Frontend Status Ownership

**Files:**
- Modify: `settings_ui/src/editor-inline/control-actions.ts`
- Modify: `settings_ui/src/editor-inline/actions.ts`
- Modify: `settings_ui/src/editor-inline/graph-actions.ts`
- Modify: `settings_ui/src/editor-inline/playback-actions.ts`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/tests/editor-inline.actions.test.ts`
- Modify: `settings_ui/tests/editor-inline.playback.integration.test.ts`

- [ ] **Step 1: Add failing ownership tests**

In `settings_ui/tests/editor-inline.actions.test.ts`, add this test after `restores a stable operation status after a graph fallback warning`:

```ts
  it("keeps graph-owned statuses transient and restores edit-owned status", async () => {
    vi.useFakeTimers();
    const visualizer = await mountTrack(0);
    setControlsBusy(0, false, "Increased volume by 15 dB.", "");

    setVisualizerStatusFromPython(0, "Analyzing...", "processing");
    const status = visualizer.closest<HTMLElement>(".aqe-controls")?.querySelector<HTMLElement>(".aqe-status")!;
    expect(status).toHaveTextContent("Analyzing...");
    expect(status.dataset.statusOwner).toBe("graph");

    window.__aqeSetVisualizer?.(0, track, 0);

    expect(status).toHaveTextContent("Increased volume by 15 dB.");
    expect(status.dataset.statusOwner).toBe("edit");
  });
```

In `settings_ui/tests/editor-inline.playback.integration.test.ts`, add this test after `restores the stable status after post-edit playback completes`:

```ts
  it("clears playback-owned warning without erasing edit-owned status", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Closed settings." },
      },
    });
    scan({
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Closed settings." },
      },
    });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 400);

    const status = document.querySelector<HTMLElement>('[data-testid="aqe-status-0"]')!;
    const visualizer = document.querySelector('[data-testid="aqe-graph-0"]') as Parameters<typeof completePlayback>[0] | null;
    expect(visualizer).not.toBeNull();

    window.__aqeSetStatus?.("Selected repeat playback needs browser audio.", "warning", "playback");
    expect(status).toHaveTextContent("Selected repeat playback needs browser audio.");
    expect(status.dataset.statusOwner).toBe("playback");

    completePlayback(visualizer!);

    expect(status).toHaveTextContent("Closed settings.");
    expect(status.dataset.statusOwner).toBe("edit");
  });
```

Run:

```bash
cd settings_ui
npm test -- --run tests/editor-inline.actions.test.ts tests/editor-inline.playback.integration.test.ts
```

Expected before implementation: FAIL because `data-status-owner` does not exist and `window.__aqeSetStatus` does not accept an owner argument.

- [ ] **Step 2: Add owner types and stable-owner rules**

In `settings_ui/src/editor-inline/control-actions.ts`, add:

```ts
export type StatusOwner = "edit" | "error" | "graph" | "playback";
```

Add these helpers near `statusText(...)`:

```ts
function defaultStatusOwner(kind: string): StatusOwner {
  if (kind === "error") return "error";
  if (kind === "processing") return "graph";
  return "edit";
}

function storesStableStatus(owner: StatusOwner): boolean {
  return owner === "edit" || owner === "error";
}
```

- [ ] **Step 3: Extend status setters with owner arguments**

In `control-actions.ts`, change:

```ts
export function setStatus(message: EditorStatusMessage, kind = "info"): void {
  const ord = Number(window.__aqeActiveField ?? 0);
  setStatusForOrd(ord, message, kind);
}
```

to:

```ts
export function setStatus(message: EditorStatusMessage, kind = "info", owner: StatusOwner = defaultStatusOwner(kind)): void {
  const ord = Number(window.__aqeActiveField ?? 0);
  setStatusForOrd(ord, message, kind, "", owner);
}
```

Change `setStatusForOrd(...)` to:

```ts
export function setStatusForOrd(
  ord: number,
  message: EditorStatusMessage,
  kind = "info",
  command = "",
  owner: StatusOwner = defaultStatusOwner(kind),
): void {
  const status = statusForOrd(ord);
  if (!status) return;
  if (storesStableStatus(owner)) {
    status.dataset.stableMessage = statusText(message || "");
    if (isUserFacingError(message)) {
      status.dataset.stableUserError = JSON.stringify(message);
    } else {
      delete status.dataset.stableUserError;
    }
    status.dataset.stableKind = kind || "info";
    status.dataset.stableCommand = command || "";
    status.dataset.stableOwner = owner;
  }
  renderStatus(status, message || "", kind || "info", command || "", owner);
}
```

Change `setTransientStatusForOrd(...)` to:

```ts
export function setTransientStatusForOrd(
  ord: number,
  message: EditorStatusMessage,
  kind = "info",
  owner: StatusOwner = "graph",
): void {
  const status = statusForOrd(ord);
  if (!status) return;
  renderStatus(status, message || "", kind || "info", "", owner);
}
```

- [ ] **Step 4: Add playback-only clearing**

Replace `clearTransientStatusForOrd(...)` with:

```ts
export function clearTransientStatusForOrd(ord: number): void {
  const status = statusForOrd(ord);
  if (!status) return;
  restoreStableStatus(status);
}

export function clearPlaybackStatusForOrd(ord: number): void {
  const status = statusForOrd(ord);
  if (!status || status.dataset.statusOwner !== "playback") return;
  restoreStableStatus(status);
}
```

Change `renderStatus(...)` to accept and store owner:

```ts
function renderStatus(
  status: HTMLElement,
  message: EditorStatusMessage,
  kind: string,
  command: string,
  owner: StatusOwner,
): void {
  renderStatusContent(status, message);
  status.dataset.kind = kind;
  status.dataset.statusOwner = owner;
  setTooltipContent(status, command);
  const spinner = status.closest<HTMLElement>(".aqe-status-row")?.querySelector<HTMLElement>(".aqe-spinner");
  if (spinner) spinner.hidden = kind !== "processing";
}
```

Change `restoreStableStatus(...)` to pass the stable owner:

```ts
  renderStatus(
    status,
    message,
    status.dataset.stableKind || "info",
    status.dataset.stableCommand || "",
    (status.dataset.stableOwner as StatusOwner | undefined) || "edit",
  );
```

Change `clearStatus(...)` so it clears the stored owner:

```ts
  status.dataset.stableOwner = "edit";
  renderStatus(status, "", "info", "", "edit");
```

- [ ] **Step 5: Render owner attributes in Svelte**

In `EditorControls.svelte`, add this status attribute:

```svelte
            data-status-owner="edit"
            data-stable-owner="edit"
```

Keep the existing `data-kind`, `data-stable-kind`, and `data-stable-message` attributes.

- [ ] **Step 6: Wire playback dependency to playback-only clearing**

In `settings_ui/src/editor-inline/actions.ts`, replace the import:

```ts
  clearTransientStatusForOrd,
```

with:

```ts
  clearPlaybackStatusForOrd,
```

In `playbackControllerDependencies()`, replace:

```ts
    clearStatus: clearTransientStatusForOrd,
```

with:

```ts
    clearStatus: clearPlaybackStatusForOrd,
```

- [ ] **Step 7: Mark graph statuses as graph-owned**

In `settings_ui/src/editor-inline/graph-actions.ts`, change:

```ts
  setStatusForOrd(ord, message, kind);
```

to:

```ts
  setStatusForOrd(ord, message, kind, "", "graph");
```

Change:

```ts
    setTransientStatusForOrd(ord, rawTrack.analysisWarning, "warning");
```

to:

```ts
    setTransientStatusForOrd(ord, rawTrack.analysisWarning, "warning", "graph");
```

- [ ] **Step 8: Mark playback-only warnings as playback-owned**

In `settings_ui/src/editor-inline/playback-actions.ts`, change:

```ts
        setStatus(t("editor.status.selected_repeat_browser_audio"), "warning");
```

to:

```ts
        setStatus(t("editor.status.selected_repeat_browser_audio"), "warning", "playback");
```

- [ ] **Step 9: Update global contract type declarations if needed**

If TypeScript reports that `window.__aqeSetStatus` accepts only two arguments, update the declaration in `settings_ui/src/editor-inline/globals.d.ts` from:

```ts
  __aqeSetStatus?: (message: string | UserFacingError, kind?: string) => void;
```

to:

```ts
  __aqeSetStatus?: (message: string | UserFacingError, kind?: string, owner?: StatusOwner) => void;
```

Add the import at the top of `globals.d.ts`:

```ts
import type { StatusOwner } from "./control-actions.js";
```

- [ ] **Step 10: Run focused frontend ownership tests**

Run:

```bash
cd settings_ui
npm test -- --run tests/editor-inline.actions.test.ts tests/editor-inline.playback.integration.test.ts
npm run typecheck
```

Expected: PASS.

- [ ] **Step 11: Commit frontend status ownership**

Run:

```bash
git add settings_ui/src/editor-inline/control-actions.ts settings_ui/src/editor-inline/actions.ts settings_ui/src/editor-inline/graph-actions.ts settings_ui/src/editor-inline/playback-actions.ts settings_ui/src/editor-inline/EditorControls.svelte settings_ui/src/editor-inline/globals.d.ts settings_ui/tests/editor-inline.actions.test.ts settings_ui/tests/editor-inline.playback.integration.test.ts
git commit -m "Separate edit graph and playback status ownership" -m "Playback and graph callbacks can arrive after an edit reload status is restored, so status updates need explicit ownership instead of treating every clear as a stable-status clear. Edit and error statuses remain stable, graph/playback statuses stay transient, and playback completion only clears playback-owned messages. Verified with focused Vitest and TypeScript checks; full check and e2e routines not yet run."
```

---

### Task 6: Harden E2E Reload Status Coverage

**Files:**
- Modify: `e2e/test_editor_processing_graph_default_workflow.py`
- Modify: `e2e/test_editor_region_delete_workflow.py`
- Modify: `e2e/test_editor_integration.py`

- [ ] **Step 1: Strengthen graph-default processing workflow**

In `e2e/test_editor_processing_graph_default_workflow.py`, keep the existing processing, undo, and redo status checks. After each final status wait, add a graph-state wait that proves the graph can finish without blanking the status.

Use this helper near the existing helper functions:

```python
def _wait_for_status_text(editor, expected: str) -> None:
    _wait_for_status_flow(
        editor,
        lambda status: status["text"] == expected,
        timeout=10.0,
    )
```

After each `_wait_for_status_flow(... expected status ...)`, add:

```python
        _wait_for_status_text(editor, _expected_processing_status(command))
```

For undo:

```python
        _wait_for_status_text(editor, "Undid: Original audio.")
```

For redo:

```python
        _wait_for_status_text(editor, f"Redid: {_expected_processing_status(command)}")
```

- [ ] **Step 2: Strengthen region delete status after redraw**

In `e2e/test_editor_region_delete_workflow.py`, after each `_wait_for_visualizer_track(...)` call, add a second status wait.

For delete-selection:

```python
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Deleted selection 500-1250 ms.",
            timeout=10.0,
        )
```

For delete-rest:

```python
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Kept only selection 500-1250 ms.",
            timeout=10.0,
        )
```

- [ ] **Step 3: Run settings save reload with default graph enabled**

In `e2e/test_editor_integration.py`, in `test_editor_settings_save_refreshes_current_editor_button_modes(...)`, add `show_graph_by_default=True` to the `_configure_ffmpeg(...)` call:

```python
        show_graph_by_default=True,
```

After the final button-mode wait, add:

```python
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Closed settings.",
            timeout=10.0,
        )
```

- [ ] **Step 4: Run focused e2e tests**

Run:

```bash
python3 scripts/dev.py test-e2e -- e2e/test_editor_processing_graph_default_workflow.py e2e/test_editor_region_delete_workflow.py e2e/test_editor_integration.py
```

Expected: PASS.

- [ ] **Step 5: Commit e2e hardening**

Run:

```bash
git add e2e/test_editor_processing_graph_default_workflow.py e2e/test_editor_region_delete_workflow.py e2e/test_editor_integration.py
git commit -m "Harden reload status e2e coverage" -m "The race appears only when reload, graph redraw, and playback readiness callbacks interleave, so e2e needs to assert final status after those callbacks settle. These checks cover graph-default processing undo/redo, region delete redraw, and settings reload with default graph enabled. Verified with focused e2e targets; full check and complete e2e routines not yet run."
```

---

### Task 7: Full Validation And Cleanup

**Files:**
- Review all files modified in Tasks 1-6.
- Test: full repository quality and e2e gates.

- [ ] **Step 1: Run backend and frontend quality gate**

Run:

```bash
python3 scripts/dev.py check
```

Expected: PASS.

- [ ] **Step 2: Run full e2e gate**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS.

- [ ] **Step 3: Re-run callsite scan**

Run:

```bash
rg -n "pending_status = None|PendingEditorStatus|loadNote\\(" addon/anki_audio_quick_editor
```

Expected:
- No `session.pending_status = None` immediately follows any `editor.loadNote(...)`.
- `PendingEditorStatus` construction is centralized in `editor_session.py`.
- Remaining `pending_status = None` uses are lifecycle cleanup paths: note/media reset, stale guard cleanup, and failure cleanup.

- [ ] **Step 4: Review status ownership scan**

Run:

```bash
rg -n "initialStatusByField|statusOwner|stableOwner|setStatusForOrd|setTransientStatusForOrd|clearPlaybackStatusForOrd" settings_ui/src/editor-inline settings_ui/tests
```

Expected:
- `initialStatusByField` is read and deleted only in `field-controller.ts` through `consumeInitialStatusForOrd(...)`.
- `EditorControls.svelte` receives `initialStatus` as a prop and does not read the global editor config status map.
- Playback completion uses `clearPlaybackStatusForOrd(...)`.
- Graph actions pass owner `"graph"` and playback warnings pass owner `"playback"`.

- [ ] **Step 5: Commit final cleanup if needed**

If the full gates required small fixes, commit them:

```bash
git add addon/anki_audio_quick_editor/editor_session.py addon/anki_audio_quick_editor/editor_processing.py addon/anki_audio_quick_editor/editor_history.py addon/anki_audio_quick_editor/editor_region_delete.py addon/anki_audio_quick_editor/editor_special_transforms.py addon/anki_audio_quick_editor/editor_settings_actions.py tests/test_editor_pending_reload_status.py tests/test_editor_post_edit_playback.py tests/test_editor_integration.py tests/test_editor_region_delete_integration.py tests/test_editor_noise_reduction_callbacks.py tests/test_editor_pitch_hum_callbacks.py settings_ui/src/editor-inline/control-actions.ts settings_ui/src/editor-inline/actions.ts settings_ui/src/editor-inline/field-controller.ts settings_ui/src/editor-inline/EditorControls.svelte settings_ui/src/editor-inline/graph-actions.ts settings_ui/src/editor-inline/playback-actions.ts settings_ui/src/editor-inline/globals.d.ts settings_ui/tests/editor-inline.integration.test.ts settings_ui/tests/editor-inline.actions.test.ts settings_ui/tests/editor-inline.playback.integration.test.ts e2e/test_editor_processing_graph_default_workflow.py e2e/test_editor_region_delete_workflow.py e2e/test_editor_integration.py
git commit -m "Stabilize editor reload status refactor" -m "Final validation surfaced small integration issues after the lifecycle and ownership changes, and these fixes keep the refactor aligned with the full quality gates. Verified with python3 scripts/dev.py check and python3 scripts/dev.py test-e2e."
```

If no fixes were needed after the previous commits, skip this commit.

---

## Self-Review

- Spec coverage:
  - Shared backend helper: Tasks 1-3.
  - All reload-with-status paths: Task 3 covers standard processing, undo/redo, region delete, special/noise transforms, and settings save.
  - No immediate clear after `loadNote(...)`: Task 3 scan and Task 7 scan.
  - Single frontend `initialStatusByField` consumer: Task 4.
  - Playback completion cannot clear stable edit status: Task 5.
  - Graph/default redraw and post-edit playback e2e stability: Task 6 and Task 7.

- Placeholder scan:
  - The plan avoids placeholder markers, open-ended "add tests", and unspecified implementation steps. Commands and expected outcomes are concrete.

- Type consistency:
  - Backend helper signature is used consistently as `reload_editor_with_pending_status(editor, session, field_index, message=..., deps=...)`.
  - Frontend owner type is consistently `StatusOwner = "edit" | "error" | "graph" | "playback"`.
  - Initial status shape is consistently `InitialEditorStatus`.
