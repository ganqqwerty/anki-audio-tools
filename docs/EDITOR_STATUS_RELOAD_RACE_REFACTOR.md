# Editor Status Reload Race Refactor Note

## Problem

Editor operations that replace media often need to reload the Anki editor note and then restore a final user-facing status such as:

- `Increased volume by 15 dB.`
- `Undid: Original audio.`
- `Closed settings.`

The current implementation uses `EditorSession.pending_status` to pass that status through the next webview injection as `initialStatusByField`. The race appears when backend code does this:

```python
session.pending_status = PendingEditorStatus(field_index, message=status)
editor.loadNote(focusTo=field_index)
session.pending_status = None
```

`editor.loadNote(...)` schedules/rebuilds frontend state, but it does not prove that the injected frontend bundle has consumed `pending_status`. Clearing immediately after `loadNote(...)` can therefore remove the status before `editor_webview_injection._initial_status_by_field()` serializes it.

The race becomes more visible when a reload also triggers:

- default graph auto-analysis across multiple fields,
- post-edit playback readiness retries,
- graph redraw for the generated/restored audio,
- playback completion callbacks that clear or restore status,
- controller reuse instead of full Svelte remount.

The user-visible symptom is a blank final status:

```js
{ kind: "info", text: "", title: "" }
```

where a completion status should be visible.

## Current Partial Fix

The last commit fixed the failing standard processing and undo/redo e2e paths by:

- not clearing `session.pending_status` immediately after `loadNote(...)` in standard processing and history restore,
- initializing the Svelte status node from `initialStatusByField`,
- applying initial status when an existing field controller is reused,
- making playback completion restore stable status instead of blindly clearing it.

This made `python3 scripts/dev.py check` and `python3 scripts/dev.py test-e2e` pass, but it is not fully systematic.

## Remaining Regression Risks

The same immediate-clear pattern still exists in other reload paths:

- settings save reload in `editor_settings_actions.py`,
- region delete reload in `editor_region_delete.py`,
- special/noise-reduction transform reload in `editor_special_transforms.py`.

These paths can regress in the same way: the operation succeeds, the note reloads, but the final status disappears.

Other likely future regressions:

- A new editor operation reloads the note and copies the old `pending_status` pattern.
- A graph redraw or default graph queue clears visible status after an edit status has been restored.
- Playback completion clears an edit/undo status because playback status and edit status are not explicitly modeled as separate status owners.
- Svelte/controller lifecycle changes reintroduce duplicate consumers of `initialStatusByField`.
- Settings reload status appears reliable in unit tests but flakes in e2e because the injected frontend config is not synchronized with backend `pending_status` lifetime.

## Refactor Proposal

Make pending reload status a backend lifecycle concept instead of a per-callsite convention.

Introduce one backend helper for editor reloads that need a post-reload status:

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
    if session is not None and message:
        session.pending_status = PendingEditorStatus(field_index, message=message, kind=kind)
    deps.dispose_editor_frontend_controls(editor)
    editor.loadNote(focusTo=field_index)
```

Use this helper for:

- standard processing replacement,
- undo/redo restore,
- region delete,
- special/noise-reduction transforms,
- settings save reload.

Do not clear `pending_status` immediately after `loadNote(...)`. Clear it only when the session is no longer relevant:

- note changes,
- field/source media changes outside an active generated edit session,
- processing failure or stale guard cleanup,
- explicit "prepare for new note" lifecycle.

On the frontend, give status state explicit ownership:

- `edit`: completion statuses from processing, undo/redo, settings reload, region delete.
- `graph`: graph analysis progress/errors.
- `playback`: transient playback status.
- `error`: user-facing error status.

Playback completion should only clear playback-owned status. It should never erase an edit-owned stable status that was installed after an operation completed.

Also choose a single owner for `initialStatusByField` consumption. Preferred shape:

- `field-controller.ts` reads and deletes `initialStatusByField[ord]`,
- `EditorControls.svelte` receives `initialStatus` as a prop,
- `control-actions.ts` applies later imperative status updates only.

Avoid having both Svelte component initialization and imperative controller code read/delete the same global config.

## Acceptance Criteria

- No callsite clears `session.pending_status` immediately after `editor.loadNote(...)`.
- All editor reload-with-status paths use the shared helper.
- Playback completion cannot clear a stable edit/undo/settings status.
- `initialStatusByField` is consumed in exactly one frontend place.
- e2e status assertions remain stable with graph default enabled and post-edit playback enabled.

## Test Plan

Add or update focused tests before relying on e2e:

- Python unit tests for the shared reload helper preserving `pending_status` through `loadNote(...)`.
- Python tests for standard processing, undo/redo, region delete, special transform, and settings save setting the expected pending status.
- Svelte test proving `initialStatusByField` is consumed once and does not render back to blank after deletion.
- Svelte playback test proving playback completion preserves edit-owned status but clears playback-owned transient status.
- E2e coverage for graph-default processing undo/redo, region delete after graph redraw, and settings save reload status.

Full validation after refactor:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```
