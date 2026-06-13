# Plan: Migrate Inline Editor from DOM-as-State to Typed Runtime State

## Problem

The inline editor frontend stores its source of truth in DOM `dataset` attributes.
Playback, selection, graph, cursor, viewport, and busy state are all encoded as
strings on `HTMLElement.dataset`. The `EditorFieldState` type and its pure
transition functions exist in `field-state.ts` but are **never used at runtime** —
they are tested only in isolation.

### Scope

23+ `dataset` attributes on `.aqe-visualizer`, plus attributes on
`.aqe-controls`, `.aqe-status`, `.aqe-button`, and `document.body`. These
represent the runtime state machine for every mounted audio field.

### Consequences

- State is stringly typed (`"true"` / `"false"`, `Number()` coercions everywhere).
- State transitions are implicit — any module can write any dataset attr at any time.
- Pure state logic (`field-state.ts`, `selection-state.ts`) cannot be tested without jsdom
  because the runtime code never calls these functions.
- Cross-module invariants are unenforced (nothing prevents `playbackState="playing"`
  while `durationMs="0"`).
- 37 files read/write dataset attrs; the blast radius of a wrong write is unbounded.

### Current Dataset Surface (by category)

| Category | Attributes | Read files | Write files | Both |
|----------|-----------|-----------|-------------|------|
| Graph/Track | `graphActive`, `graphBusy`, `hasTrack`, `durationMs`, `targetDurationMs`, `sourceFilename`, `analyzerName`, `statusMessage` | 18 | 4 | `graph-actions.ts`, `visualizer-renderer.ts` |
| Playback | `playbackState`, `playbackEngine`, `playStartMs`, `playbackStartMs`, `playbackEndMs`, `playbackRegionMode`, `playbackResetCursorMs`, `playbackLoop`, `resumeRequiresRestart`, `preserveStatusOnPlaybackEnd`, `playStartedAt`, `progressClockMode` | 12 | 5 | `playback-controller.ts`, `playback-controller-pass.ts`, `playback-actions.ts` |
| Cursor | `cursorMs`, `progressMs`, `anchorMs` | 9 | 5 | `actions-playback.ts`, `recording-actions-state.ts` |
| Selection | `selectionActive`, `selectionStartMs`, `selectionEndMs`, `selectionDraftActive`, `selectionDraftStartMs`, `selectionDraftEndMs` | 4 | 1 | `visualizer-state.ts` |
| Selection overlay | `selectionOverlayReady`, `selectionShiftHideInner`, `selectionStartEdgeVisible`, `selectionEndEdgeVisible` | 1 | 1 | `visualizer-selection-renderer.ts` |
| Viewport | `viewportStartMs`, `viewportEndMs` | 1 | 1 | `visualizer-state.ts` |
| Repeat | `repeatEnabled`, `repeatPauseSeconds`, `repeatPauseWaiting` | 7 | 3 | `actions-audio-clock.ts`, `playback-controller.ts` |
| Chorusing | `chorusingState`, `chorusingBaseStartMs`, `chorusingBaseEndMs`, `chorusingMarkersMs`, `chorusingActiveMarkerIndex` | 0 | 1 | `chorusing-dom.ts` (written for CSS/MutationObserver, never read as `dataset.*`) |
| Learner recording | `learnerRecordingStatus`, `learnerPlaybackStatus`, `learnerStartCursorMs`, `learnerDurationMs`, `learnerRecordingGeneration`, `learnerRecordingMediaFilename`, `learnerRecordingFailureMessage` | 2 | 2 | `recording-actions-state.ts` |
| Controls | `busy`, `aqeCanUndo`, `aqeCanRedo`, `aqeSourceFilename` | 6 | 3 | `control-actions.ts`, `field-controller.ts` |
| Status | `stableMessage`, `stableUserError`, `stableKind`, `stableCommand`, `kind`, `statusOwner` | 2 | 1 | `control-actions.ts` |
| Buttons | `aqeButtonState`, `aqeEnabledTitle`, `aqeDisabledTitle`, `aqeRecordingDisabled` | 6 | 3 | `control-actions.ts`, `recording-actions-sync.ts` |
| Global busy | `aqeBusy` on `document.body` | 10 | 2 | `control-actions.ts` |

### Python ↔ JS Bridge (writes into dataset)

Python calls `window.__aqeSet*` functions via `web.eval()`. Each writes directly to dataset:

| Python file | JS function | Dataset targets |
|-------------|------------|----------------|
| `editor_analysis.py` | `__aqeSetVisualizer` | Visualizer: `graphActive`, `graphBusy`, `hasTrack`, `durationMs`, `targetDurationMs`, `sourceFilename`, `analyzerName`, `anchorMs`, `cursorMs` |
| `editor_frontend/playback.py` | `__aqeSetPlaybackState` | Visualizer: `resumeRequiresRestart` |
| `editor_frontend/busy.py` | `__aqeSetBusy` | Body: `aqeBusy`, Controls: `busy`, Status: `kind`, `statusOwner` |
| `editor_frontend/status.py` | `__aqeSetStatus` | Status: `stableMessage`, `stableUserError`, `stableKind`, `stableCommand`, `kind`, `statusOwner` |
| `editor_frontend/status.py` | `__aqeSetVisualizerStatus` | Visualizer: `graphActive`, `hasTrack`, `graphBusy`, `statusMessage`, Status |
| `editor_frontend/refresh.py` | `__aqeSetHistoryAvailability` | Controls: `aqeCanUndo`, `aqeCanRedo` |
| `editor_recording_frontend.py` | `__aqeSetLearnerRecordingState` | Controls + Visualizer: ~10 attrs |
| `editor_recording_frontend.py` | `__aqeSetLearnerVisualizer` | Visualizer: `learnerDurationMs` |
| `editor_frontend/status.py` | `__aqeEditorDispose` | Body, all Controls, all Visualizers: ~25 attrs cleared |

### Existing Test Coverage

| Test file | Dataset usage | Type |
|-----------|--------------|------|
| `settings_ui/tests/visualizer-state.test.ts` (11 refs) | Writes + asserts dataset | Unit (DOM facade) |
| `settings_ui/tests/field-state.test.ts` (0 refs) | Pure state transitions | Unit |
| `settings_ui/tests/selection-state.test.ts` (0 refs) | Pure state transitions | Unit |
| `settings_ui/tests/editor-inline.actions.playback.test.ts` (19 refs) | Writes + asserts dataset | Integration |
| `settings_ui/tests/editor-inline.actions.selection.test.ts` (4 refs) | Writes + asserts dataset | Integration |
| `settings_ui/tests/editor-inline.actions.progress.test.ts` (10 refs) | Writes + asserts dataset | Integration |
| `settings_ui/tests/editor-inline.actions.status.test.ts` (6 refs) | Asserts dataset | Integration |
| `settings_ui/tests/editor-inline.integration.*.ts` (12 refs across 7 files) | Various | Integration |
| `settings_ui/tests/editor-inline.recording.integration.test.ts` (4 refs) | Asserts dataset | Integration |
| `e2e/editor_graph_helpers.py` (26 refs) | Reads dataset in JS eval | E2E |
| `e2e/test_editor_*workflow.py` (21 refs across 7 files) | Reads/writes dataset | E2E |
| `tests/` (0 refs) | None | Python unit |

---

## Solution Design

### Core Idea

Make `EditorFieldState` (from `field-state.ts`) the **single runtime source of truth**
per mounted field. The DOM dataset becomes a **write-only CSS projection layer** —
never read for logic decisions.

```text
Before:   every module reads/writes dataset.* directly
After:    every module reads/writes EditorFieldState → sync layer → dataset projection
```

### State Store: `field-state-store.ts`

A thin module holding the live state per field ordinal:

```ts
// field-state-store.ts (new file)
import type { EditorFieldState } from "./field-state.js";
import {
  readVisualizerCursorMs,
  // ... other visualizer-state readers
} from "./visualizer-state.js";

// Runtime source of truth — keyed by field ordinal
const _fieldStates: Map<number, EditorFieldState> = new Map();

// Initialize state for a newly mounted field (called from field-controller.ts)
export function initFieldState(ord: number, state: EditorFieldState): EditorFieldState {
  _fieldStates.set(ord, state);
  return state;
}

// Read current state. Falls back to reconstructing from DOM on first access
// (for bootstrapping before migration is complete).
export function readFieldState(ord: number): EditorFieldState {
  const stored = _fieldStates.get(ord);
  if (stored) return stored;
  return rebuildFieldStateFromDom(ord);
}

// Write state — updates the store AND syncs to DOM dataset
export function writeFieldState(ord: number, state: EditorFieldState): void {
  _fieldStates.set(ord, state);
  syncFieldStateToDom(ord, state);
}

// Apply a pure transition function
export function updateFieldState(
  ord: number,
  reducer: (state: EditorFieldState) => EditorFieldState,
): EditorFieldState {
  const next = reducer(readFieldState(ord));
  writeFieldState(ord, next);
  return next;
}

// Remove state for a disposed field
export function removeFieldState(ord: number): void {
  _fieldStates.delete(ord);
}

// Bootstrap: reconstruct state from existing DOM dataset (for backward compat)
function rebuildFieldStateFromDom(ord: number): EditorFieldState;
```

### Dataset Sync: `field-state-dom-sync.ts`

One centralized module that projects `EditorFieldState` onto DOM dataset attributes.
This is the **only place** that writes to dataset:

```ts
// field-state-dom-sync.ts (new file)
import type { EditorFieldState } from "./field-state.js";

export function syncFieldStateToDom(ord: number, state: EditorFieldState): void {
  const visualizer = getVisualizerForOrd(ord);
  if (!visualizer) return;

  // Graph / track
  visualizer.dataset.graphActive = String(state.graph.active);
  visualizer.dataset.graphBusy = String(state.graph.busy);
  visualizer.dataset.hasTrack = String(state.graph.hasTrack);
  visualizer.dataset.durationMs = String(state.graph.durationMs);
  visualizer.dataset.sourceFilename = state.sourceFilename;

  // Cursor
  visualizer.dataset.cursorMs = String(Math.round(state.cursor.ms));
  visualizer.dataset.progressMs = String(Math.round(state.cursor.progressMs));
  visualizer.dataset.anchorMs = String(Math.round(state.cursor.anchorMs));

  // Playback
  visualizer.dataset.playbackState = state.playback.state;
  visualizer.dataset.playbackEngine = state.playback.engine;
  visualizer.dataset.playbackStartMs = String(Math.round(state.playback.startMs));
  visualizer.dataset.playbackEndMs = String(Math.round(state.playback.endMs));
  visualizer.dataset.playbackRegionMode = state.playback.regionMode;
  // ... resumeRequiresRestart, repeat, etc.

  // Selection
  visualizer.dataset.selectionActive = String(state.selection.active);
  // ... selectionStartMs, selectionEndMs, draft attrs
}
```

### Migration Strategy

#### Phase 1: Create the store + sync (zero behavior change)

1. Create `field-state-store.ts` with `initFieldState`, `readFieldState`, `writeFieldState`, `updateFieldState`, `removeFieldState`.
2. Create `field-state-dom-sync.ts` with `syncFieldStateToDom()` that mirrors the current dataset writes from `visualizer-renderer.ts`, `graph-actions.ts`, `playback-controller.ts`, and `playback-controller-pass.ts`.
3. Wire `initFieldState()` into `field-controller.ts` when a new field is mounted.
4. Wire `removeFieldState()` into the dispose path.
5. Run `python3 scripts/dev.py test-e2e` — must pass identically since no reads have changed yet.

#### Phase 2: Migrate all dataset reads → store reads

Replace every `visualizer.dataset.foo` read with `readFieldState(ord).foo`:

1. **Layer 1 — visualizer-state.ts**: Convert all readers to delegate to `readFieldState()`.
   - `readVisualizerCursorMs` → `readFieldState(ord).cursor.ms`
   - `readVisualizerSelectionState` → `readFieldState(ord).selection`
   - `readVisualizerRepeatEnabled` → `readFieldState(ord).playback.repeat`
   - `readVisualizerDurationMs` → `readFieldState(ord).graph.durationMs`
   - etc.
   - This is the highest-leverage change because most downstream modules already go through `visualizer-state.ts` readers.

2. **Layer 2 — playback-controller.ts**: Replace internal dataset reads.
   - `visualizer.dataset.playbackState` → `readFieldState(ord).playback.state`
   - `visualizer.dataset.durationMs` → `readFieldState(ord).graph.durationMs`
   - `visualizer.dataset.cursorMs` → `readFieldState(ord).cursor.ms`
   - etc.

3. **Layer 3 — playback-controller-pass.ts**: Same migration.

4. **Layer 4 — playback-actions.ts**: Replace `playbackSnapshotFor()` dataset reads.

5. **Layer 5 — control-actions.ts**: Replace direct dataset reads.
   - `anyBusy()` can stay on `document.body.dataset.aqeBusy` (it's a global, not per-field state).
   - Button/label reads stay on DOM (they are DOM element state, not audio field state).

6. **Layer 6 — graph-actions.ts**: Replace dataset reads.

7. **Layer 7 — remaining modules** in dependency order.

8. **E2E helpers**: Update `e2e/editor_graph_helpers.py` to read from `window.__aqeFieldStates` (expose the store on `window` for e2e) instead of dataset.

#### Phase 3: Make all writes go through store

Replace direct dataset writes with `writeFieldState()`:

1. **graph-actions.ts**: `prepareForNewNote()` → calls `writeFieldState(ord, initialFieldState(...))` instead of writing 25 dataset attrs directly.
2. **visualizer-renderer.ts**: `renderVisualizerTrack()` → calls state transitions on the store instead of direct DOM writes.
3. **playback-controller.ts**: All `visualizer.dataset.* = ...` → `updateFieldState(ord, ...)`.
4. **playback-controller-pass.ts**: Same.
5. **playback-plan-state.ts**: Progress updates → `updateFieldState(ord, ...)`.
6. **playback-actions.ts**: `playAfterEdit()` dataset writes → `updateFieldState(ord, ...)`.
7. **control-actions.ts**: `setControlsBusy()` dataset writes for status → store.
8. **recording-actions-state.ts**: Recording state → store.
9. **actions-audio-clock.ts**: Audio clock state → store.

Each migration step should be individually testable. Run `python3 scripts/dev.py test-e2e` after each module.

#### Phase 4: Remove the sync projection for attrs not needed by CSS

After Phase 3, most dataset attributes are dead — written by the sync layer but never read.
Audit CSS rules in `settings_ui/src/editor-inline/styles/` for which `data-*` selectors exist
and keep only those attributes in the sync layer. Remove the rest.

Likely CSS-needed attributes:
- `[data-aqe-busy]` (on body + controls — disables buttons)
- `[data-has-track]` (shows/hides visualizer elements)
- `[data-playback-state]` (play/pause button styling)
- `[data-aqe-button-state]` (play vs pause icon)
- `[data-selection-active]` (selection overlay visibility)
- `[data-selection-draft-active]` (draft selection rendering)

Likely removable attributes:
- `anchorMs`, `progressMs`, `playStartedAt`, `playStartMs` (internal timing)
- `playbackResetCursorMs`, `playbackLoop`, `resumeRequiresRestart` (internal state)
- `analyzerName`, `statusMessage` (no CSS selector)
- `targetDurationMs` (no CSS selector, used for logic)

#### Phase 5: Update tests

1. **field-state.test.ts** — Already pure, no changes needed. These become the canonical
   state transition tests.
2. **visualizer-state.test.ts** — Refactor to test `field-state-store.ts` instead of DOM.
   Tests that assert dataset values move to `field-state-dom-sync.test.ts`.
3. **playback/selection/status action tests** — Replace dataset assertions with
   `readFieldState(ord)` assertions.
4. **E2E helpers** — Read from `window.__aqeFieldStates` instead of dataset. Add a
   `window.__aqeTestFieldState(ord): EditorFieldState` helper exposed only in e2e mode.
5. **New tests** — Add tests for `field-state-store.ts` (init, read, write, update, remove),
   and `field-state-dom-sync.ts` (correct projection from typed state to DOM attrs).

---

## Implementation Order

| Step | Task | Files changed | Verification |
|------|------|--------------|-------------|
| 1 | Create `field-state-store.ts` | 1 new file | Unit test |
| 2 | Create `field-state-dom-sync.ts` | 1 new file | Unit test |
| 3 | Wire init/dispose into `field-controller.ts` | 1 file | E2E passes unchanged |
| 4 | Migrate `visualizer-state.ts` readers → store | 1 file | Integration tests |
| 5 | Migrate `playback-controller.ts` reads | 1 file | Playback E2E |
| 6 | Migrate `playback-controller-pass.ts` reads | 1 file | Playback E2E |
| 7 | Migrate `playback-actions.ts` reads | 1 file | Playback E2E |
| 8 | Migrate `graph-actions.ts` reads | 1 file | Graph E2E |
| 9 | Migrate remaining readers | ~10 files | E2E |
| 10 | Migrate `graph-actions.ts` writes → store | 1 file | Graph E2E |
| 11 | Migrate `visualizer-renderer.ts` writes → store | 1 file | Graph E2E |
| 12 | Migrate `playback-controller.ts` writes → store | 1 file | Playback E2E |
| 13 | Migrate `playback-plan-state.ts` writes → store | 1 file | Playback E2E |
| 14 | Migrate remaining writers | ~10 files | E2E |
| 15 | Audit CSS selectors, trim sync layer | ~5 files | Visual regression |
| 16 | Update unit/integration tests | ~15 test files | `test-svelte` |
| 17 | Update E2E helpers | ~3 e2e files | `test-e2e` |
| 18 | Add architecture test for no-direct-dataset reads | 1 test | `arch` |

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| E2E test breakage during migration | Migrate one module at a time; run E2E after each step |
| CSS breakage from removed dataset attrs | Phase 4 explicitly audits CSS before removal |
| Race between Python callback writes and store | All Python callbacks go through the same `writeFieldState()` path; no change to timing |
| Performance regression from extra allocation | `EditorFieldState` objects are shallow; one allocation per state change is negligible vs the existing string coercion and DOM writes |
| Chorusing state (purely CSS-driven) | Leave chorusing dataset writes as-is; they are never read as `dataset.*` by JS |
| Learner recording state (bridges two elements) | Keep learner-recording-specific dataset attrs on `.aqe-controls` as-is; only migrate the data mirrored on `.aqe-visualizer` |
| Button/status DOM state is DOM-native | Keep button/status dataset attrs as-is; they represent DOM element state, not audio field state |

## What Does NOT Change

- **Split-button state** (`window.__aqeSplitButtonStates`) — already a typed JS object, not DOM dataset. No change needed.
- **Bridge protocol** — `window.__aqeSet*` callbacks keep the same signatures. Only internal implementation changes.
- **Python code** — no Python changes needed. The JS functions exported on `window` keep identical signatures.
- **CSS** — dataset attributes needed for styling remain projected by the sync layer.
- **Svelte components** — they bind to split-button state and DOM-observed attributes. No component rearchitecture.
