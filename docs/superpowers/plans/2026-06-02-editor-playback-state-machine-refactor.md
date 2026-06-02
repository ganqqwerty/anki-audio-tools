# Editor Playback State Machine Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement task-by-task.

**Goal:** Make inline editor playback deterministic and extensible before adding complex playback schemes.

**Architecture:** Extract playback decisions into a pure TypeScript model. DOM `dataset` remains the storage adapter for now, but it must only read/write snapshots and planned results; it must not own playback semantics. Viewport logic remains separate and continues to only project/follow absolute audio time.

**Tech Stack:** Svelte 5, TypeScript, Vitest, Python Anki e2e.

---

## Summary

Refactor current playback behavior without changing user-visible behavior.

Key invariant: playback state transitions are decided by pure functions from an immutable snapshot. The controller applies those decisions to DOM/audio clocks.

Default policy: playback uses a snapshotted pass once started. If selection/cursor changes while playback is active, existing gesture paths must stop/restart and create a new pass explicitly.

---

## Key Changes

- Add `settings_ui/src/editor-inline/playback-model.ts`.
- Keep the existing Python bridge `PlaybackRequest` shape unchanged.
- Move request decisions out of ad hoc `dataset` branching:
  - play while stopped
  - pause while playing
  - resume paused playback
  - restart paused playback after cursor/selection change
  - selected vs full-cover selected vs full playback
  - repeat boundary and completion reset cursor
- Keep viewport follow in `viewport-actions.ts`; do not mix viewport state into playback planning.
- Keep `playback-state.ts` as a compatibility facade initially, delegating to the new pure model.

### New Internal Types

```ts
export interface PlaybackSnapshot {
  anchorMs: number;
  cursorMs: number;
  currentProgressMs: number | null;
  durationMs: number;
  engine: PlaybackEngine;
  ord: number;
  playbackState: PlaybackState;
  region: PlaybackRegion;
  repeat: boolean;
  resumeRequiresRestart: boolean;
}

export interface PlaybackPass {
  startMs: number;
  endMs: number;
  regionMode: PlaybackRegionMode;
  loop: boolean;
  resetCursorMs: number;
}

export type PlaybackBoundaryPlan =
  | { kind: "continue" }
  | { kind: "loop"; pass: PlaybackPass; repeatPauseMs: number }
  | { kind: "complete"; resetCursorMs: number };
```

### Pure Functions

```ts
export function planPlaybackRequest(snapshot: PlaybackSnapshot): PlaybackRequest;
export function planPlaybackPass(snapshot: PlaybackSnapshot, startMs: number): PlaybackPass;
export function planPlaybackBoundary(input: {
  nextMs: number;
  pass: PlaybackPass;
  repeat: boolean;
  repeatPauseMs: number;
}): PlaybackBoundaryPlan;
export function playbackCompletionCursor(pass: Pick<PlaybackPass, "regionMode" | "resetCursorMs">): number;
```

---

## Implementation Tasks

### Task 1: Add Pure Model Tests

- [ ] Create `settings_ui/tests/playback-model.test.ts`.
- [ ] Cover stopped full playback, stopped selection playback, full-cover selection playback, pause, resume, paused restart, out-of-selection resume, boundary continue, boundary repeat, selected completion reset, and full completion reset.
- [ ] Run `npm --prefix settings_ui test -- playback-model.test.ts`.
- [ ] Confirm the first run fails before implementation because `playback-model.ts` does not exist.

### Task 2: Implement `playback-model.ts`

- [ ] Create `settings_ui/src/editor-inline/playback-model.ts`.
- [ ] Move request decision logic from `buildPlaybackRequestForPython` into `planPlaybackRequest`.
- [ ] Implement `planPlaybackPass`, `planPlaybackBoundary`, and `playbackCompletionCursor`.
- [ ] Run `npm --prefix settings_ui test -- playback-model.test.ts`.

### Task 3: Keep `playback-state.ts` as a Compatibility Adapter

- [ ] Modify `settings_ui/src/editor-inline/playback-state.ts`.
- [ ] Keep `buildPlaybackRequestForPython(state)` signature unchanged.
- [ ] Delegate request planning to `planPlaybackRequest(state)`.
- [ ] Preserve `clampMsToRegion` compatibility.
- [ ] Run `npm --prefix settings_ui test -- playback-state.test.ts playback-model.test.ts`.

### Task 4: Snapshot Playback Passes in the Controller

- [ ] Modify `settings_ui/src/editor-inline/playback-controller.ts`.
- [ ] Store `playbackStartMs`, `playbackEndMs`, and `playbackRegionMode` from a planned pass.
- [ ] Make boundary handling read the active pass from stored playback fields.
- [ ] Make repeat restart reuse the active pass until gesture code explicitly restarts playback.
- [ ] Make completion reset use the pass reset cursor.
- [ ] Run `npm --prefix settings_ui test -- editor-inline.playback.integration.test.ts editor-inline.playback-zoom.integration.test.ts editor-inline.cursor-selection-playback.integration.test.ts`.

### Task 5: Centralize DOM Snapshot Reading

- [ ] Modify `settings_ui/src/editor-inline/playback-actions.ts`.
- [ ] Add `playbackSnapshotFor(visualizer, ord): PlaybackSnapshot`.
- [ ] Make `playbackRequest(ord)` call `planPlaybackRequest(playbackSnapshotFor(...))`.
- [ ] Run `npm --prefix settings_ui test -- editor-inline.actions.test.ts editor-inline.actions.progress.test.ts playback-model.test.ts`.

### Task 6: Preserve Gesture Restart Semantics

- [ ] Inspect `settings_ui/src/editor-inline/selection-gestures.ts`.
- [ ] Keep active playback cursor/selection gesture paths creating a new playback pass through existing restart helpers.
- [ ] Run `npm --prefix settings_ui test -- editor-inline.selection-creation.integration.test.ts editor-inline.selection-resize.integration.test.ts editor-inline.cursor-selection-playback.integration.test.ts`.

### Task 7: E2E Regression Gate

- [ ] Run `python3 scripts/dev.py test-e2e e2e/test_editor_cursor_selection_playback_workflow.py`.
- [ ] Run `python3 scripts/dev.py test-e2e e2e/test_editor_region_loop_playback_workflow.py`.
- [ ] Run `python3 scripts/dev.py test-e2e e2e/test_editor_graph_zoom_workflow.py`.
- [ ] Run `python3 scripts/dev.py check`.
- [ ] Run `python3 scripts/dev.py test-e2e`.

---

## Test Plan

- Pure unit tests prove transition decisions without DOM/audio clocks.
- Integration tests prove DOM adapters still emit the same requests and update graph state correctly.
- E2E tests prove Anki WebView behavior for zoom, cursor, repeat, selection, pause/reposition, and transformation interruption.
- Existing behavior must not change unless a test currently encodes a known bug.

---

## Assumptions

- `PlaybackRequest` bridge shape remains unchanged.
- No new public UI behavior is introduced in this refactor.
- Playback pass is snapshotted at start; selection/cursor changes during active playback must restart explicitly.
- Viewport follow remains a rendering concern, not part of playback planning.
- Repeat remains boolean plus optional pause duration for this refactor; multi-segment schemes come later.
