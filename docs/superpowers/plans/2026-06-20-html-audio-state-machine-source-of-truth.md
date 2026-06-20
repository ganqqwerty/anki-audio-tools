# HTML Audio State Machine Source Of Truth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current split HTML playback coordination with one authoritative, typed per-field playback session state so source audio, post-edit autoplay, repeat, and learner recording playback are driven by explicit transitions rather than implicit controller contracts.

**Architecture:** Introduce a shared HTML audio session model that owns source configuration, metadata readiness, play/pause lifecycle, failure state, progress clock ownership, repeat waiting, and post-edit autoplay readiness. Source playback and learner recording playback become thin domain adapters over this shared model. Python continues to create media files and publish explicit playback intent metadata, but it no longer relies on filename heuristics or frontend graph state as hidden playback contracts.

**Tech Stack:** Svelte 5, TypeScript, Vitest, Python Anki/Qt e2e, existing `scripts/dev.py` quality gates.

---

## Context

The current branch successfully removes native editor playback and fixes the speed/volume post-edit browser-audio failure, but the design is not yet as simple or as explicit as intended.

The original expectation was roughly 400-500 lines for the HTML audio state machine. The current runtime implementation grew because it contains:

- `settings_ui/src/editor-inline/source-playback-machine.ts`
- `settings_ui/src/editor-inline/source-playback-controller.ts`
- `settings_ui/src/editor-inline/source-playback-repeat-loop.ts`
- `settings_ui/src/editor-inline/learner-recording-playback-machine.ts`
- `settings_ui/src/editor-inline/learner-recording-playback.ts`
- `settings_ui/src/editor-inline/post-edit-playback.ts`
- additional readiness and clock behavior in `settings_ui/src/editor-inline/playback-controller.ts`

This is operationally correct after the latest checks, but conceptually it has too many owners.

## Problems To Fix

### Problem 1: Source Playback Machine Is Not The Sole Source Of Truth

`source-playback-machine.ts` defines clear states and events, but `source-playback-controller.ts` currently reconstructs a state from field/runtime data for a transition, then lets truth continue in field state, visualizer runtime properties, DOM audio state, graph state, and callbacks.

This means the reducer is testable, but it is not the authoritative runtime state.

**Design target:** source playback must have a stored per-field `HtmlAudioSessionState`. Runtime code dispatches events into that state and executes returned effects. It must not reconstruct state ad hoc from scattered DOM/runtime facts for the core transition.

### Problem 2: Post-Edit Autoplay Is A Separate Implicit Protocol

`post-edit-playback.ts` currently owns pending request checks, graph readiness checks, metadata timers, rendered-graph fallback, duplicate dispatch suppression, and bridge notification dispatch.

This created the speed/volume fix, but the protocol is implicit:

- pending post-edit request must match field ordinal, generation, and source filename
- graph readiness may stand in for metadata readiness
- generated source is partly inferred from `__aqe_` filename
- duplicate readiness is suppressed by module-level sets
- metadata timeout retries readiness instead of becoming a state transition

**Design target:** post-edit autoplay should be a session state/event pair:

- `PostEditAutoplayRequested`
- `GeneratedSourceConfigured`
- `GraphRenderedForSource`
- `MetadataLoaded`
- `AutoplayReadyDispatched`
- `AutoplayConsumed`
- `AutoplayFailed`

Duplicate suppression should fall out of the state: once the session has `readyDispatched: true` or is `playing`, additional ready events for the same generation are ignored by transition rules.

### Problem 3: Browser Audio Readiness Lives Outside The Playback Machine

`audio-readiness.ts` classifies readiness from DOM audio state and visualizer failure flags. That classification is useful, but playback behavior still depends on callers interpreting readiness correctly.

Examples:

- `allowLoadingAudio` means "post-edit zero-ms generated source may call `audio.play()` before metadata".
- `audio_metadata_loading` can be blocking for user seek playback but playable for graph-backed post-edit autoplay.
- `metadata_timeout` is handled differently in post-edit autoplay than in normal user playback.

**Design target:** readiness classification remains a low-level adapter, but the playback session machine decides what each readiness event means for the current intent.

### Problem 4: Graph State Is Used As A Playback Readiness Proxy

The speed/volume bug fix uses rendered graph state to provide duration/source confidence before the hidden audio element fires metadata. This was necessary to pull in generated files, but graph state should not be the primary playback readiness authority.

**Design target:** graph rendered events may provide known duration for post-edit autoplay, but the playback session state should record that as explicit session data. Code should not repeatedly query graph state as a hidden readiness source.

### Problem 5: Filename Heuristic Encodes Backend Knowledge In The Frontend

The current post-edit graph request logic treats filenames containing `__aqe_` as generated files. That matches current output names, but it is an implicit backend/frontend contract.

**Design target:** Python should publish explicit post-edit intent metadata:

```ts
export interface PendingPostEditPlayback {
  fieldOrd: number;
  generation: number;
  sourceFilename: string;
  sourceKind: "generated_edit" | "existing_media";
  requireGraphRedraw: boolean;
  expectedDurationMs?: number;
}
```

### Problem 6: Source And Learner Playback Duplicate HTML Audio Lifecycle

Source playback and learner recording playback both implement:

- source URL setup
- metadata readiness
- seek
- `audio.play()`
- play rejection handling
- pause/stop
- progress frame
- ended/error events

The domain states differ, but the audio element lifecycle is the same.

**Design target:** create one shared HTML audio session model and use source/learner wrappers for domain-specific commands, labels, and cursor projection.

### Problem 7: Some Reducer Effects Are Not Actually Owned By The Executor

`SourcePlaybackEffect` includes metadata effects such as `ProbeAudioMetadata`, `StartMetadataTimer`, and `ClearMetadataTimer`, but the current source playback executor has no-op branches for some of them.

**Design target:** every effect emitted by a reducer must be implemented by the owning executor, or the effect must be removed from the reducer. A reducer must not describe a lifecycle the runtime does not actually own.

### Problem 8: Playback Leak Checks Are Not A Suite-Level Contract

The branch added and used checks for unexpected native playback and lingering mpv playback, but this is still mostly targeted validation.

**Design target:** playback leak assertions should be available as a reusable e2e fixture/helper and applied to transform/post-edit/repeat workflows that can accidentally keep audio playing.

### Problem 9: Commit History Does Not Explain Why

The branch commits have useful subjects, but no bodies. The repo instructions require commit messages to explain intent, behavior, system impact, and whether full check/e2e ran.

**Design target:** before merge, split or amend commits so each commit explains why the change exists and what it protects.

---

## Target Architecture

### Ownership Rules

One stored per-field playback session state is the source of truth for source audio playback:

```ts
type HtmlAudioSessionState =
  | { kind: "empty"; ord: number; cursorMs: number }
  | { kind: "loading"; ord: number; source: HtmlAudioSource; cursorMs: number; pendingStart: HtmlAudioStartRequest | null; metadataDeadlineMs: number | null }
  | { kind: "ready"; ord: number; source: HtmlAudioSource; durationMs: number; cursorMs: number }
  | { kind: "starting"; ord: number; source: HtmlAudioSource; request: HtmlAudioStartRequest; durationMs: number }
  | { kind: "playing"; ord: number; source: HtmlAudioSource; request: HtmlAudioStartRequest; durationMs: number; startedAtMs: number }
  | { kind: "paused"; ord: number; source: HtmlAudioSource; request: HtmlAudioStartRequest; durationMs: number; pausedAtMs: number }
  | { kind: "repeat_waiting"; ord: number; source: HtmlAudioSource; request: HtmlAudioStartRequest; durationMs: number; resumeAtMs: number }
  | { kind: "post_edit_waiting"; ord: number; source: HtmlAudioSource; postEdit: PostEditAutoplayIntent; cursorMs: number; graphDurationMs: number | null }
  | { kind: "failed"; ord: number; source: HtmlAudioSource | null; cursorMs: number; reason: HtmlAudioFailureReason };
```

The session state may read low-level adapter observations as events, but it must not leave core state split across hidden audio fields, graph state, visualizer properties, and module-level sets.

### Low-Level Adapter Boundary

Create a low-level adapter with this responsibility only:

```ts
export interface HtmlAudioElementAdapter {
  configureSource(sourceFilename: string): void;
  clearSource(): void;
  currentTimeMs(): number;
  durationMs(): number | null;
  pause(): void;
  play(): Promise<void>;
  seek(cursorMs: number): boolean;
}
```

This adapter wraps actual DOM audio operations. It should not decide playback transitions.

### Session Events

All meaningful state changes should be events:

```ts
type HtmlAudioSessionEvent =
  | { type: "SourceConfigured"; source: HtmlAudioSource; cursorMs: number; expectedDurationMs?: number }
  | { type: "SourceCleared" }
  | { type: "MetadataLoaded"; durationMs: number }
  | { type: "MetadataTimedOut" }
  | { type: "StartRequested"; request: HtmlAudioStartRequest }
  | { type: "PostEditAutoplayRequested"; intent: PostEditAutoplayIntent; request: HtmlAudioStartRequest }
  | { type: "GraphRenderedForSource"; sourceFilename: string; durationMs: number }
  | { type: "PlayResolved"; nowMs: number }
  | { type: "PlayRejected"; reason: "audio_play_rejected" }
  | { type: "PauseRequested"; cursorMs: number }
  | { type: "ResumeRequested" }
  | { type: "StopRequested"; cursorMs: number }
  | { type: "BoundaryReached"; cursorMs: number }
  | { type: "RepeatDelayElapsed" }
  | { type: "AudioError"; reason: "audio_error"; cursorMs: number }
  | { type: "RuntimeDisposed" };
```

### Effects

Every effect must be implemented by the session executor:

```ts
type HtmlAudioSessionEffect =
  | { type: "ConfigureAudioSource"; sourceFilename: string }
  | { type: "ClearAudioSource" }
  | { type: "SeekAudio"; cursorMs: number }
  | { type: "PlayAudio" }
  | { type: "PauseAudio" }
  | { type: "StartProgressFrame"; cursorMs: number; endMs: number }
  | { type: "ClearProgressFrame" }
  | { type: "StartMetadataTimer"; timeoutMs: number }
  | { type: "ClearMetadataTimer" }
  | { type: "StartRepeatTimer"; pauseMs: number }
  | { type: "ClearRepeatTimer" }
  | { type: "RequestGraphForSource"; ord: number; sourceFilename: string }
  | { type: "DispatchPostEditReady"; ord: number; generation: number; sourceFilename: string }
  | { type: "PublishPlaybackState"; status: "stopped" | "playing" | "paused"; cursorMs?: number }
  | { type: "ShowPlaybackWarning"; statusKey: string }
  | { type: "LogTelemetry"; event: string; data: Record<string, unknown> };
```

### Domain Wrappers

Source playback wrapper:

- converts existing `PlaybackRequest` into `HtmlAudioStartRequest`
- maps playback state into field-state projection
- keeps source graph cursor rendering
- handles source-region and repeat semantics

Learner recording wrapper:

- converts recording publication state into `HtmlAudioSource`
- maps session cursor into learner recording cursor offset
- keeps learner-specific status strings and controls

Post-edit wrapper:

- creates `PostEditAutoplayIntent` from Python config
- dispatches `PostEditAutoplayRequested`
- consumes `DispatchPostEditReady` effect through the existing bridge
- does not own timers or duplicate-suppression sets

---

## File Structure

### New Files

- `settings_ui/src/editor-inline/html-audio-session-machine.ts`
  - Pure reducer and typed states/events/effects.

- `settings_ui/src/editor-inline/html-audio-session-controller.ts`
  - Stored per-field session map, DOM audio adapter wiring, timers, effect execution.

- `settings_ui/tests/html-audio-session-machine.test.ts`
  - Exhaustive transition tests for source, post-edit, repeat, metadata, and failures.

- `settings_ui/tests/editor-inline.html-audio-session.integration.test.ts`
  - Integration tests proving source playback and post-edit playback use the stored session state.

### Modified Files

- `settings_ui/src/editor-inline/source-playback-controller.ts`
  - Convert into a source-domain adapter around the shared session controller.

- `settings_ui/src/editor-inline/source-playback-machine.ts`
  - Delete after the shared session machine covers the same states, or reduce to source-domain request planning only.

- `settings_ui/src/editor-inline/source-playback-repeat-loop.ts`
  - Fold repeat waiting into the shared session controller, then delete this file if no source-specific logic remains.

- `settings_ui/src/editor-inline/learner-recording-playback.ts`
  - Use shared session controller instead of directly owning audio elements and progress frames.

- `settings_ui/src/editor-inline/learner-recording-playback-machine.ts`
  - Reduce to learner-domain availability mapping, or delete if the shared session plus recording state covers it.

- `settings_ui/src/editor-inline/post-edit-playback.ts`
  - Reduce to bridge-intent ingestion and remove graph request / timer / duplicate-set ownership.

- `settings_ui/src/editor-inline/playback-controller.ts`
  - Remove `allowLoadingAudio` special case after it becomes an explicit session transition.

- `settings_ui/src/editor-inline/audio-readiness.ts`
  - Keep readiness classifier as an adapter helper; remove policy decisions from callers.

- `addon/anki_audio_quick_editor/editor_playback.py`
  - Publish explicit post-edit metadata: `sourceKind`, `expectedDurationMs` where available, and `requireGraphRedraw`.

- `settings_ui/src/editor-inline/editor-runtime-config.ts`
  - Extend `PendingPostEditPlayback` type with explicit metadata.

- `settings_ui/tests/editor-inline.post-edit-playback.integration.test.ts`
  - Update to assert state-machine events/effects rather than module-level duplicate sets.

- `e2e/test_editor_post_edit_playback_workflow.py`
  - Keep speed/volume generated playback reproduction; assert exact browser `play()` count remains one.

- `e2e/editor_playback_helpers.py`
  - Add suite-level reusable playback leak guard.

---

## Implementation Tasks

### Current Status As Of 2026-06-20

- [x] Tasks 1-4 are implemented: the shared reducer, stored controller, source session tests, and post-edit readiness reducer tests exist and pass.
- [x] Task 5 Step 1 is implemented: `startSourceHtmlPlayback()` routes through `html-audio-session-controller.ts`.
- [x] Task 5 Step 2 is implemented for source playback: `source-playback-machine.ts`, `source-playback-repeat-loop.ts`, and `source-playback-machine.test.ts` were removed after the session reducer took over source lifecycle and repeat boundary handling.
- [x] Task 6 is implemented: post-edit readiness and duplicate dispatch suppression are session-controller effects instead of `post-edit-playback.ts` module-level state.
- [x] Task 7 is implemented: explicit post-edit metadata is used and `rg -n "__aqe_" settings_ui/src/editor-inline` returns no playback-readiness heuristic.
- [x] Additional cleanup completed: session types, backend queueing, post-edit ready dispatch, and learner projection helpers were split out so `html-audio-session-machine.ts` and `html-audio-session-controller.ts` stay under the existing frontend architecture line budget.
- [x] Latest focused verification: `npm --prefix settings_ui test -- frontend-architecture.test.ts html-audio-session-machine.test.ts editor-inline.html-audio-session.integration.test.ts editor-inline.actions.playback.test.ts editor-inline.playback.integration.test.ts editor-inline.post-edit-playback.integration.test.ts editor-inline.selection-repeat-pause.integration.test.ts editor-inline.selection-playback.integration.test.ts && npm --prefix settings_ui run typecheck` passes.
- [x] Task 8 is implemented: learner playback runs through the shared HTML audio session, stale `aqe-learner-audio-0` selectors were moved to the shared field audio clock, and `learner-recording-playback-machine.ts` plus its standalone lifecycle tests were removed.
- [x] Task 8 verification: `npm --prefix settings_ui test -- editor-inline.learner-recording-playback.test.ts editor-inline.recording.integration.test.ts html-audio-session-machine.test.ts && npm --prefix settings_ui run typecheck` passes; `python3 scripts/dev.py test-e2e-parallel e2e/test_editor_voice_recording_comparison_workflow.py` passes.
- [x] Latest Task 9/11 hardening completed: pause/resume commands now dispatch into the HTML session machine, start requests carry an explicit reset cursor, zoomed playback follows progress on every HTML tick, and full-source loop restarts reload browser media before replaying real OGG sources.
- [x] Latest full verification: `python3 scripts/dev.py check` passes.
- [x] Latest full e2e verification: `python3 scripts/dev.py test-e2e-parallel` passes.
- [ ] Next task: review remaining soft size warnings and decide whether to split the session reducer/controller further for readability. Current verified coverage includes post-edit speed/volume generated-audio playback, selected-region repeat/one-shot behavior, full-source repeat resume, zoomed playback follow, and bounded real-media repeat without native fallback.

### Task 1: Add Failing Tests For The Desired Single Source Of Truth

**Files:**

- Create: `settings_ui/tests/html-audio-session-machine.test.ts`

- [ ] **Step 1: Create transition tests for source metadata and normal play**

Add tests that prove a configured source moves through loading, ready, starting, playing, paused, and stopped without consulting field state or DOM state.

```ts
import { describe, expect, it } from "vitest";

import {
  initialHtmlAudioSessionState,
  transitionHtmlAudioSession,
  type HtmlAudioSessionState,
} from "../src/editor-inline/html-audio-session-machine.js";

const source = {
  kind: "source" as const,
  sourceFilename: "clip one.mp3",
};

const request = {
  cursorMs: 0,
  endMs: 1000,
  loop: false,
  ord: 0,
  regionMode: "full" as const,
  source: "user" as const,
};

describe("html audio session machine", () => {
  it("owns source playback transitions from configured source to playing", () => {
    let state: HtmlAudioSessionState = initialHtmlAudioSessionState(0);

    let transition = transitionHtmlAudioSession(state, {
      cursorMs: 0,
      source,
      type: "SourceConfigured",
    });
    expect(transition.state).toMatchObject({
      kind: "loading",
      ord: 0,
      source,
    });
    expect(transition.effects).toContainEqual({
      sourceFilename: "clip one.mp3",
      type: "ConfigureAudioSource",
    });
    state = transition.state;

    transition = transitionHtmlAudioSession(state, {
      durationMs: 1000,
      type: "MetadataLoaded",
    });
    expect(transition.state).toMatchObject({
      durationMs: 1000,
      kind: "ready",
      source,
    });
    state = transition.state;

    transition = transitionHtmlAudioSession(state, {
      request,
      type: "StartRequested",
    });
    expect(transition.state).toMatchObject({
      durationMs: 1000,
      kind: "starting",
      request,
      source,
    });
    expect(transition.effects).toEqual([
      { cursorMs: 0, type: "SeekAudio" },
      { type: "PlayAudio" },
      { cursorMs: 0, endMs: 1000, type: "StartProgressFrame" },
      { status: "playing", type: "PublishPlaybackState" },
    ]);

    transition = transitionHtmlAudioSession(transition.state, {
      nowMs: 120,
      type: "PlayResolved",
    });
    expect(transition.state).toMatchObject({
      kind: "playing",
      startedAtMs: 120,
    });
  });
});
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:

```bash
npm --prefix settings_ui test -- html-audio-session-machine.test.ts
```

Expected: fail because `html-audio-session-machine.ts` does not exist.

### Task 2: Implement The Shared Session Reducer

**Files:**

- Create: `settings_ui/src/editor-inline/html-audio-session-machine.ts`
- Test: `settings_ui/tests/html-audio-session-machine.test.ts`

- [ ] **Step 1: Add the shared reducer types and source transitions**

Create `html-audio-session-machine.ts` with these exported names:

```ts
export type HtmlAudioSource =
  | { kind: "source"; sourceFilename: string }
  | { kind: "learner_recording"; sourceFilename: string; startCursorMs: number; generation: number };

export type HtmlAudioFailureReason =
  | "metadata_timeout"
  | "audio_play_rejected"
  | "audio_error"
  | "audio_seek_failed";

export interface HtmlAudioStartRequest {
  cursorMs: number;
  endMs: number;
  loop: boolean;
  ord: number;
  regionMode: "full" | "selection";
  source: "user" | "post_edit" | "chorusing" | "learner_recording";
}

export interface PostEditAutoplayIntent {
  fieldOrd: number;
  generation: number;
  sourceFilename: string;
  requireGraphRedraw: boolean;
  sourceKind: "generated_edit" | "existing_media";
  expectedDurationMs?: number;
}

export type HtmlAudioSessionState =
  | { kind: "empty"; ord: number; cursorMs: number }
  | { kind: "loading"; ord: number; source: HtmlAudioSource; cursorMs: number; pendingStart: HtmlAudioStartRequest | null; metadataDeadlineMs: number | null }
  | { kind: "ready"; ord: number; source: HtmlAudioSource; durationMs: number; cursorMs: number }
  | { kind: "starting"; ord: number; source: HtmlAudioSource; request: HtmlAudioStartRequest; durationMs: number }
  | { kind: "playing"; ord: number; source: HtmlAudioSource; request: HtmlAudioStartRequest; durationMs: number; startedAtMs: number }
  | { kind: "paused"; ord: number; source: HtmlAudioSource; request: HtmlAudioStartRequest; durationMs: number; pausedAtMs: number }
  | { kind: "repeat_waiting"; ord: number; source: HtmlAudioSource; request: HtmlAudioStartRequest; durationMs: number; resumeAtMs: number }
  | { kind: "post_edit_waiting"; ord: number; source: HtmlAudioSource; postEdit: PostEditAutoplayIntent; cursorMs: number; graphDurationMs: number | null }
  | { kind: "failed"; ord: number; source: HtmlAudioSource | null; cursorMs: number; reason: HtmlAudioFailureReason };
```

Implement `initialHtmlAudioSessionState(ord)` and `transitionHtmlAudioSession(state, event)` so the Task 1 test passes.

- [ ] **Step 2: Run the focused reducer test**

Run:

```bash
npm --prefix settings_ui test -- html-audio-session-machine.test.ts
```

Expected: pass.

### Task 3: Move Post-Edit Readiness Into The Session Reducer

**Files:**

- Modify: `settings_ui/src/editor-inline/html-audio-session-machine.ts`
- Modify: `settings_ui/tests/html-audio-session-machine.test.ts`

- [ ] **Step 1: Add failing tests for generated post-edit autoplay before metadata**

Append this test:

```ts
it("dispatches post-edit ready once when a generated source has a rendered graph before metadata", () => {
  const intent = {
    fieldOrd: 0,
    generation: 7,
    requireGraphRedraw: true,
    sourceFilename: "clip__aqe_123.mp3",
    sourceKind: "generated_edit" as const,
  };
  const request = {
    cursorMs: 0,
    endMs: 1333,
    loop: false,
    ord: 0,
    regionMode: "full" as const,
    source: "post_edit" as const,
  };
  let state = initialHtmlAudioSessionState(0);

  let transition = transitionHtmlAudioSession(state, {
    cursorMs: 0,
    source: { kind: "source", sourceFilename: "clip__aqe_123.mp3" },
    type: "SourceConfigured",
  });
  state = transition.state;

  transition = transitionHtmlAudioSession(state, {
    intent,
    request,
    type: "PostEditAutoplayRequested",
  });
  expect(transition.state).toMatchObject({
    kind: "post_edit_waiting",
    postEdit: intent,
  });
  state = transition.state;

  transition = transitionHtmlAudioSession(state, {
    durationMs: 1333,
    sourceFilename: "clip__aqe_123.mp3",
    type: "GraphRenderedForSource",
  });
  expect(transition.effects).toContainEqual({
    fieldOrd: 0,
    generation: 7,
    sourceFilename: "clip__aqe_123.mp3",
    type: "DispatchPostEditReady",
  });

  const duplicate = transitionHtmlAudioSession(transition.state, {
    durationMs: 1333,
    sourceFilename: "clip__aqe_123.mp3",
    type: "GraphRenderedForSource",
  });
  expect(duplicate.effects).not.toContainEqual({
    fieldOrd: 0,
    generation: 7,
    sourceFilename: "clip__aqe_123.mp3",
    type: "DispatchPostEditReady",
  });
});
```

- [ ] **Step 2: Implement post-edit states and events**

Add these events:

```ts
| { type: "PostEditAutoplayRequested"; intent: PostEditAutoplayIntent; request: HtmlAudioStartRequest }
| { type: "GraphRenderedForSource"; sourceFilename: string; durationMs: number }
| { type: "PostEditReadyConsumed"; generation: number; sourceFilename: string }
```

Represent duplicate suppression in state with:

```ts
readyDispatched: boolean
```

inside the `post_edit_waiting` state.

- [ ] **Step 3: Run reducer tests**

Run:

```bash
npm --prefix settings_ui test -- html-audio-session-machine.test.ts
```

Expected: pass.

### Task 4: Add The Stored Session Controller

**Files:**

- Create: `settings_ui/src/editor-inline/html-audio-session-controller.ts`
- Create: `settings_ui/tests/editor-inline.html-audio-session.integration.test.ts`

- [ ] **Step 1: Add controller integration test for persisted session state**

Create an integration test that initializes the runtime, configures source audio, starts playback, and asserts the second event observes the stored state rather than reconstructing `ready`.

```ts
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { dispatchHtmlAudioSessionEvent, readHtmlAudioSessionState } from "../src/editor-inline/html-audio-session-controller.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import { prepareHtmlAudio, renderFields } from "./editor-inline.integration.helpers.js";

describe("editor inline html audio session controller", () => {
  beforeEach(() => {
    renderFields();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
  });

  afterEach(() => {
    disposeEditorRuntime();
    vi.restoreAllMocks();
  });

  it("stores source playback session state between events", async () => {
    const audio = prepareHtmlAudio(0);
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());

    dispatchHtmlAudioSessionEvent(0, {
      cursorMs: 0,
      source: { kind: "source", sourceFilename: "clip one.mp3" },
      type: "SourceConfigured",
    });
    dispatchHtmlAudioSessionEvent(0, {
      durationMs: 1000,
      type: "MetadataLoaded",
    });
    dispatchHtmlAudioSessionEvent(0, {
      request: {
        cursorMs: 0,
        endMs: 1000,
        loop: false,
        ord: 0,
        regionMode: "full",
        source: "user",
      },
      type: "StartRequested",
    });
    await Promise.resolve();

    expect(readHtmlAudioSessionState(0)).toMatchObject({
      kind: "playing",
      ord: 0,
      source: { sourceFilename: "clip one.mp3" },
    });
    expect(audio.play).toHaveBeenCalledTimes(1);
  });
});
```

- [ ] **Step 2: Implement controller session map and effect execution**

Create:

```ts
const sessionStates = new Map<number, HtmlAudioSessionState>();
```

Export:

```ts
export function readHtmlAudioSessionState(ord: number): HtmlAudioSessionState;
export function dispatchHtmlAudioSessionEvent(ord: number, event: HtmlAudioSessionEvent): void;
export function clearHtmlAudioSession(ord: number): void;
export function clearAllHtmlAudioSessions(): void;
```

Effect execution must implement every `HtmlAudioSessionEffect`. Use `exhaustive(effect)` for the default branch so no effect can silently become a no-op.

- [ ] **Step 3: Run integration test**

Run:

```bash
npm --prefix settings_ui test -- editor-inline.html-audio-session.integration.test.ts html-audio-session-machine.test.ts
```

Expected: pass.

### Task 5: Replace Source Playback Controller Internals

**Files:**

- Modify: `settings_ui/src/editor-inline/source-playback-controller.ts`
- Modify: `settings_ui/src/editor-inline/playback-actions.ts`
- Modify: `settings_ui/tests/editor-inline.playback.integration.test.ts`
- Modify: `settings_ui/tests/editor-inline.post-edit-playback.integration.test.ts`

- [ ] **Step 1: Route `startSourceHtmlPlayback` into the stored session**

Change `startSourceHtmlPlayback` so it dispatches `StartRequested` or `PostEditAutoplayRequested` into `html-audio-session-controller.ts` instead of calling `transitionSourcePlayback` directly.

The function must keep this public behavior:

```ts
export function startSourceHtmlPlayback(
  visualizer: VisualizerElement,
  request: PlaybackRequest,
  runtime: SourcePlaybackRuntime,
): boolean
```

but the implementation should:

- derive `HtmlAudioStartRequest`
- read pending post-edit intent when `request.source === "post_edit"`
- dispatch a session event
- return `true` only when the dispatch produced a start/defer path, not when source is missing

- [ ] **Step 2: Delete or shrink `source-playback-machine.ts`**

If all tests pass using `html-audio-session-machine.ts`, delete `source-playback-machine.ts` and update imports. If source-specific request planning still needs a helper, reduce the file to request conversion only and rename it to `source-playback-request.ts`.

- [ ] **Step 3: Run focused frontend tests**

Run:

```bash
npm --prefix settings_ui test -- editor-inline.playback.integration.test.ts editor-inline.post-edit-playback.integration.test.ts html-audio-session-machine.test.ts editor-inline.html-audio-session.integration.test.ts
```

Expected: pass.

### Task 6: Move Post-Edit Glue To Session Events

**Files:**

- Modify: `settings_ui/src/editor-inline/post-edit-playback.ts`
- Modify: `settings_ui/src/editor-inline/html-audio-session-controller.ts`
- Modify: `settings_ui/tests/editor-inline.post-edit-playback.integration.test.ts`

- [ ] **Step 1: Remove module-level duplicate and graph request sets**

Remove:

```ts
const postEditGraphRequests: Set<string> = new Set();
const postEditReadyDispatches: Set<string> = new Set();
```

from `post-edit-playback.ts`.

- [ ] **Step 2: Convert readiness handlers to session events**

`notifyPostEditPlaybackReady()` should only validate the pending config and dispatch:

```ts
dispatchHtmlAudioSessionEvent(ord, {
  intent,
  request,
  type: "PostEditAutoplayRequested",
});
```

Graph rendered notifications should dispatch:

```ts
dispatchHtmlAudioSessionEvent(ord, {
  durationMs,
  sourceFilename,
  type: "GraphRenderedForSource",
});
```

- [ ] **Step 3: Keep the speed/volume generated-file regression**

Run:

```bash
python3 scripts/dev.py test-e2e-parallel e2e/test_editor_post_edit_playback_workflow.py
```

Expected: pass, including both `aqe:faster` and `aqe:volume-up` cases with exactly one browser `play()` call.

### Task 7: Publish Explicit Backend Post-Edit Metadata

**Files:**

- Modify: `addon/anki_audio_quick_editor/editor_playback.py`
- Modify: `settings_ui/src/editor-inline/editor-runtime-config.ts`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `settings_ui/tests/editor-inline.post-edit-playback.integration.test.ts`

- [ ] **Step 1: Extend pending post-edit payload type**

Add:

```ts
sourceKind: "generated_edit" | "existing_media";
expectedDurationMs?: number;
```

to the TypeScript pending post-edit config type.

- [ ] **Step 2: Set explicit metadata in Python**

When Python records a generated post-edit playback request after an edit, include:

```python
"sourceKind": "generated_edit",
"requireGraphRedraw": True,
```

When Python records a non-generated existing-media playback request, include:

```python
"sourceKind": "existing_media",
```

- [ ] **Step 3: Remove `__aqe_` heuristic**

Search:

```bash
rg -n "__aqe_" settings_ui/src/editor-inline
```

Expected after implementation: no playback-readiness logic depends on `sourceFilename.includes("__aqe_")`.

- [ ] **Step 4: Run type and frontend tests**

Run:

```bash
npm --prefix settings_ui test -- editor-inline.post-edit-playback.integration.test.ts html-audio-session-machine.test.ts
npm --prefix settings_ui run typecheck
```

Expected: pass.

### Task 8: Move Learner Recording Playback Onto The Shared Session

**Files:**

- Modify: `settings_ui/src/editor-inline/learner-recording-playback.ts`
- Modify: `settings_ui/src/editor-inline/learner-recording-playback-machine.ts`
- Modify: `settings_ui/tests/editor-inline.learner-recording-playback.test.ts`
- Modify: `settings_ui/tests/learner-recording-playback-machine.test.ts`

- [ ] **Step 1: Add failing test for learner playback through shared session**

Update learner integration tests so `toggleLearnerRecordingHtmlPlayback(0)` produces a shared session state:

```ts
expect(readHtmlAudioSessionState(0)).toMatchObject({
  kind: "playing",
  source: {
    kind: "learner_recording",
    sourceFilename: "learner.wav",
  },
});
```

- [ ] **Step 2: Replace learner-owned audio maps**

Remove learner-specific ownership of:

```ts
const audioByOrd = new Map<number, HTMLAudioElement>();
const frameByOrd = new Map<number, number>();
```

from `learner-recording-playback.ts`.

Use `dispatchHtmlAudioSessionEvent()` for configure, play, pause, stop, ended, and error behavior.

- [ ] **Step 3: Reduce or delete learner reducer**

If learner recording still needs a pure domain reducer, keep only availability mapping:

```ts
recording publication state -> learner HtmlAudioSource | unavailable reason
```

Do not keep a second full ready/starting/playing/paused/failed audio lifecycle.

- [ ] **Step 4: Run learner tests and e2e**

Run:

```bash
npm --prefix settings_ui test -- editor-inline.learner-recording-playback.test.ts learner-recording-playback-machine.test.ts html-audio-session-machine.test.ts
python3 scripts/dev.py test-e2e-parallel e2e/test_editor_voice_recording_comparison_workflow.py
```

Expected: pass.

### Task 9: Add Reusable E2E Playback Leak Guard

**Files:**

- Modify: `e2e/editor_playback_helpers.py`
- Modify: `e2e/test_editor_post_edit_playback_workflow.py`
- Modify: `e2e/test_editor_region_loop_graph_repeat_workflow.py`
- Modify: `e2e/test_editor_region_loop_playback_one_shot_workflow.py`

- [ ] **Step 1: Add helper that asserts no extra browser play calls**

Add a helper that installs a browser audio driver with counters:

```python
def _install_counting_html_audio_driver(editor, ord_: int = 0) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          window.__aqeHtmlPlayCounts = window.__aqeHtmlPlayCounts || {{}};
          window.__aqeHtmlPlayCounts[{ord_}] = 0;
          const audio = document.querySelector('[data-testid="aqe-audio-clock-{ord_}"]');
          if (!audio) return false;
          audio.play = () => {{
            window.__aqeHtmlPlayCounts[{ord_}] += 1;
            return Promise.resolve();
          }};
          audio.pause = () => undefined;
          return true;
        }})()
        """,
    )
```

- [ ] **Step 2: Add helper that reads play count**

```python
def _html_audio_play_count(editor, ord_: int = 0) -> int:
    return int(run_js(
        editor.web,
        f"window.__aqeHtmlPlayCounts?.[{ord_}] || 0",
    ))
```

- [ ] **Step 3: Apply to post-edit transform tests**

For speed and volume post-edit tests, assert:

```python
assert _html_audio_play_count(editor) == 1
```

after the expected playback starts.

- [ ] **Step 4: Run focused e2e**

Run:

```bash
python3 scripts/dev.py test-e2e-parallel e2e/test_editor_post_edit_playback_workflow.py e2e/test_editor_region_loop_graph_repeat_workflow.py e2e/test_editor_region_loop_playback_one_shot_workflow.py
```

Expected: pass.

### Task 10: Remove Old No-Op Effects And Dead Files

**Files:**

- Modify or delete: `settings_ui/src/editor-inline/source-playback-machine.ts`
- Modify or delete: `settings_ui/src/editor-inline/source-playback-repeat-loop.ts`
- Modify or delete: `settings_ui/src/editor-inline/learner-recording-playback-machine.ts`
- Modify: `settings_ui/tests/frontend-architecture.test.ts`

- [ ] **Step 1: Search for no-op effect branches**

Run:

```bash
rg -n "case \"(ProbeAudioMetadata|StartMetadataTimer|ClearMetadataTimer|SeekAudio)\"|return;" settings_ui/src/editor-inline/source-playback-controller.ts settings_ui/src/editor-inline/learner-recording-playback.ts
```

Expected: no reducer effect that is intentionally emitted remains unimplemented.

- [ ] **Step 2: Add architecture assertion for session ownership**

Extend frontend architecture tests to require playback lifecycle transitions to be imported from:

```text
settings_ui/src/editor-inline/html-audio-session-machine.ts
settings_ui/src/editor-inline/html-audio-session-controller.ts
```

and forbid source/learner playback modules from creating their own `HTMLAudioElement` maps.

- [ ] **Step 3: Run architecture and frontend tests**

Run:

```bash
npm --prefix settings_ui test -- frontend-architecture.test.ts html-audio-session-machine.test.ts
python3 scripts/dev.py test tests/test_architecture/test_rule38_frontend_playback_state_machine_ownership.py
```

Expected: pass.

### Task 11: Full Verification Gate

**Files:**

- No source files should be changed in this task.

- [ ] **Step 1: Run full check**

Run:

```bash
python3 scripts/dev.py check
```

Expected: exit code 0.

- [ ] **Step 2: Run full parallel e2e**

Run:

```bash
python3 scripts/dev.py test-e2e-parallel
```

Expected: exit code 0.

- [ ] **Step 3: Scan for playback leaks**

Run:

```bash
ps -ef | rg -i "anki_audio/mpv|forvo_Vertrag|pytest-|ffplay|mpv|test-e2e|pytest|scripts/dev.py" || true
printf '{"command":["get_property","idle-active"]}\n{"command":["get_property","path"]}\n{"command":["get_property","filename"]}\n{"command":["get_property","playlist-count"]}\n' | nc -U -w 1 /var/folders/sd/kz30sp1d7l3f99k1nk6l8xnw0000gn/T/mpv.gk613h0e || true
```

Expected:

- no pytest/e2e process remains
- no test media path is actively playing
- mpv reports idle or no active path
- playlist count is `0` or otherwise known idle state for the user’s long-lived Anki process

### Task 12: Commit Hygiene Before Merge

**Files:**

- Git history only.

- [ ] **Step 1: Split or amend commits**

Suggested final commit groups:

1. Architecture guards for no native editor playback.
2. Shared HTML audio session machine and tests.
3. Source playback adapter migration.
4. Post-edit generated playback readiness migration.
5. Learner recording playback adapter migration.
6. E2E leak and playback-count hardening.
7. Dead code removal and docs.

- [ ] **Step 2: Use explanatory commit bodies**

Each commit body must include:

```text
Why:
<explain the problem or risk>

Impact:
<explain behavior and module boundary changes>

Verification:
<commands run, or explicitly say if full check/e2e were not run>
```

---

## Acceptance Criteria

- There is one stored per-field HTML audio session state for source playback.
- Post-edit autoplay readiness is represented as session state, not module-level sets and timers.
- Duplicate post-edit ready dispatch is impossible by state transition, not by external guard.
- `__aqe_` filename detection is not used to decide playback behavior.
- Graph rendered data can feed duration into the session, but graph state is not a hidden playback-readiness owner.
- Learner playback no longer owns a separate audio-element lifecycle when the shared session can handle it.
- Every reducer effect has an executor implementation.
- Speed and volume generated-file e2e tests assert exactly one browser `play()` call and no native fallback.
- Full `python3 scripts/dev.py check` passes.
- Full `python3 scripts/dev.py test-e2e-parallel` passes.
- Post-run playback leak scan is clean.

## Risks

- This refactor touches central playback flow, so broad e2e is mandatory after each major task.
- Removing the current post-edit glue too early can reintroduce “Browser audio is unavailable” after transforms.
- Over-generalizing the shared session can make source and learner behavior harder to read. Keep domain adapters thin and concrete.
- Some browser audio behavior differs between test stubs and Qt WebEngine; do not rely only on Vitest.

## Recommended Execution Order

1. Build the shared reducer with tests while old runtime remains intact.
2. Add the stored controller behind existing public functions.
3. Migrate source playback.
4. Migrate post-edit autoplay.
5. Publish explicit backend metadata and remove filename heuristics.
6. Migrate learner playback.
7. Add leak-count guards.
8. Delete old machines/no-op effects.
9. Run full verification.
10. Clean commit history.
