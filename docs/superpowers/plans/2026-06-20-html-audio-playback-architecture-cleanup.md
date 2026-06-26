# HTML Audio Playback Architecture Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the remaining legacy/source playback coupling so HTML audio session state is the source of truth for source and learner playback, while keeping manual visual progress and chorusing behavior intact until they have explicit replacement coverage.

**Architecture:** Treat `html-audio-session-machine.ts`, `html-audio-session-machine-helpers.ts`, `html-audio-session-progress.ts`, and `html-audio-session-types.ts` as the pure model layer. Treat `html-audio-session-controller.ts` as the only owner of source/learner session state and effect dispatch. Keep `field-state-store` as the UI projection, but add guardrails so source playback lifecycle writes flow through session effects rather than the legacy progress controller.

**Observability:** Use [`../../architecture/html-audio-observability.md`](../../architecture/html-audio-observability.md)
as the single source of truth for playback logs, suspicious invariants, and e2e
observation requirements. Do not duplicate that checklist in this plan.

**Tech Stack:** Svelte 5 editor webview, TypeScript, Vitest, Python `scripts/dev.py`, Anki/Qt e2e tests.

---

## Problem Audit

The source document at `docs/plans/html-audio-playback-architecture-problems.md` is useful, but several recommendations are too broad for the current branch.

| Problem | Verdict | Notes |
|---|---|---|
| Two parallel playback systems | Legit, but scoped | The old progress controller still exists and can still dispatch source boundaries through `source-playback-controller.ts`. It also supports manual visual progress, selection gestures, and chorusing, so deleting it all at once is unsafe. |
| State machine not sole source of truth | Legit | `field-state-store` is a projection, but old modules still write playback lifecycle state. `visualizer-runtime-state` still stores pass/repeat facts used outside the session. |
| `playback-engine-decision.ts` dead code | Mostly legit | The selected engine is always `"html"`. The reason strings still feed telemetry, so collapse it into a reason/readiness helper instead of deleting telemetry blindly. |
| Two audio element APIs | Legit | `audio-clock.ts` and `html-audio-session-audio-element.ts` both manipulate the same `.aqe-audio-clock` element. Consolidation should preserve graph metadata/readiness handling. |
| `playback-actions.ts` coordination mess | Legit | It is both facade and business logic. Split after source session ownership is cleaner. |
| Naming confusion | Legit but lower priority | Rename after behavior boundaries are simpler so names reflect real ownership. |
| Duplicate functions | Legit | Some duplicates are harmless facade exports; the risky duplicates are source boundary/progress/completion ownership. |
| Global `EventTarget.prototype.dispatchEvent` patch | Legit and high priority | This should be removed early. Local audio event handlers already cover normal synthetic `audio.dispatchEvent(new Event("ended"))` tests. |
| Behavioral circularity | Legit | Old frame loop can dispatch into the session, and both paths write playback projection state. |

Unsafe recommendations from the source document:

- Do not delete `audio-clock.ts` in one step. It also owns readiness, source configuration from graph rendering, metadata publication, and seek support for cursor/selection behavior.
- Do not delete `playback-controller.ts` in one step. Manual progress and chorusing tests still depend on it.
- Do not make all of `field-state-store` read-only. It is the editor UI projection store; the realistic goal is to centralize source playback lifecycle writes behind session effects.

## File Structure

- `settings_ui/src/editor-inline/html-audio-session-machine.ts`
  - Pure reducer for source and learner playback lifecycle.
- `settings_ui/src/editor-inline/html-audio-session-progress.ts`
  - Pure progress and boundary decision helper.
- `settings_ui/src/editor-inline/html-audio-session-controller.ts`
  - Session maps, event dispatch, and effect runner.
- `settings_ui/src/editor-inline/html-audio-session-audio-element.ts`
  - Audio element operations for the session effect runner.
- `settings_ui/src/editor-inline/html-audio-session-field-effects.ts`
  - Projection from session effects into field state and toolbar state.
- `settings_ui/src/editor-inline/html-audio-session-learner-effects.ts`
  - Learner recording projection and audio event handlers. This should lose its global prototype patch.
- `settings_ui/src/editor-inline/source-playback-controller.ts`
  - Temporary adapter from existing `PlaybackRequest` to `HtmlAudioStartRequest`. This should shrink to start-request adaptation only.
- `settings_ui/src/editor-inline/playback-controller.ts`
  - Legacy manual/chorusing visual progress controller after this cleanup. It should stop owning source playback boundaries.
- `settings_ui/src/editor-inline/playback-actions.ts`
  - Current facade plus business logic. It should be split after source session ownership is isolated.
- `settings_ui/src/editor-inline/audio-clock.ts`
  - Current shared audio element helper/readiness layer. It should stop duplicating source playback mutation once session audio operations own that path.
- `settings_ui/tests/frontend-architecture.test.ts`
  - Add source-ownership guardrails.

---

### Task 1: Add Guardrails For Source Playback Ownership

**Files:**

- Modify: `settings_ui/tests/frontend-architecture.test.ts`

- [ ] **Step 1: Add a failing architecture test for source boundary ownership**

Add this test after the existing `keeps HTML audio session model files pure` test:

```typescript
  it("keeps source playback boundaries out of the legacy progress controller", () => {
    const forbiddenPatterns = [
      {
        relPath: "src/editor-inline/actions-playback.ts",
        patterns: [/handleSourcePlaybackBoundary/, /source-playback-controller/],
      },
      {
        relPath: "src/editor-inline/playback-controller.ts",
        patterns: [/handleSourceLoopBoundary/],
      },
      {
        relPath: "src/editor-inline/actions-audio-clock.ts",
        patterns: [/handlePlaybackBoundary/, /handleSourceAudioError/],
      },
    ];
    const offenders = forbiddenPatterns.flatMap(({ relPath, patterns }) => {
      const source = withoutComments(readFileSync(join(projectRoot, relPath), "utf-8"));
      return patterns
        .filter((pattern) => pattern.test(source))
        .map((pattern) => `${relPath}: ${pattern.source}`);
    });

    expect(offenders).toEqual([]);
  });
```

- [ ] **Step 2: Run the architecture test and verify it fails**

Run:

```bash
npm --prefix settings_ui test -- frontend-architecture.test.ts
```

Expected: FAIL with offenders for `actions-playback.ts`, `playback-controller.ts`, and `actions-audio-clock.ts`.

- [ ] **Step 3: Commit the failing guard**

```bash
git add settings_ui/tests/frontend-architecture.test.ts
git commit -m "Guard source playback ownership in architecture tests" -m "Source playback should be owned by the HTML audio session, but legacy progress modules still dispatch source boundaries. Add a failing guard first so the cleanup has a concrete target and future regressions cannot reintroduce this coupling."
```

---

### Task 2: Remove The Legacy Source Boundary Bridge

**Files:**

- Modify: `settings_ui/src/editor-inline/playback-controller.ts`
- Modify: `settings_ui/src/editor-inline/actions-playback.ts`
- Modify: `settings_ui/src/editor-inline/actions-audio-clock.ts`
- Modify: `settings_ui/src/editor-inline/playback-actions.ts`
- Modify: `settings_ui/src/editor-inline/source-playback-controller.ts`
- Test: `settings_ui/tests/frontend-architecture.test.ts`
- Test: `settings_ui/tests/editor-inline.actions.progress.test.ts`
- Test: `settings_ui/tests/editor-inline.chorusing.integration.test.ts`
- Test: `settings_ui/tests/editor-inline.html-audio-session.integration.test.ts`
- Test: `settings_ui/tests/editor-inline.selection-playback.integration.test.ts`

- [ ] **Step 1: Make legacy progress loops handle only legacy/manual loop boundaries**

In `settings_ui/src/editor-inline/playback-controller.ts`, remove `handleSourceLoopBoundary` from `PlaybackControllerDependencies`:

```typescript
export interface PlaybackControllerDependencies {
  clearStatus: (ord: number) => void;
  effectivePlaybackRegion: (visualizer: VisualizerElement) => PlaybackRegion;
  focusAndSendCommand: (ord: number, command: string) => void;
  handleLoopBoundary?: (visualizer: VisualizerElement, pass: PlaybackPass) => boolean;
  playbackEngineFor: (visualizer: VisualizerElement | null) => "html";
  repeatEnabledFor: (visualizer: VisualizerElement) => boolean;
  restoreStatus: (ord: number) => void;
  setCursor: (
    visualizer: VisualizerElement,
    ms: number,
    notifyPython: boolean,
    options?: {
      engine?: "html" | "";
      previousPlaybackState?: PlaybackState;
      restartPlayback?: boolean;
      updateAnchor?: boolean;
    },
  ) => void;
  setPlaybackButtonLabel: (visualizer: VisualizerElement, label: string) => void;
  stopOtherPlayback: (activeVisualizer: VisualizerElement) => void;
}
```

Then update the loop branch in `handlePlaybackBoundary()`:

```typescript
  if (boundary.kind === "loop") {
    if (deps.handleLoopBoundary?.(visualizer, boundary.pass) === true) {
      return true;
    }
    startManualPlaybackPass(visualizer, boundary.pass, deps, boundary.pass.startMs);
    return true;
  }
```

This preserves manual repeat behavior without dispatching source session events from the old frame loop.

- [ ] **Step 2: Remove source boundary dependency wiring**

In `settings_ui/src/editor-inline/actions-playback.ts`, remove:

```typescript
import { handleSourcePlaybackBoundary } from "./source-playback-controller.js";
```

Then remove the `handleSourceLoopBoundary` property from `playbackControllerDependencies()`.

- [ ] **Step 3: Route audio clock ended/error callbacks directly to the session**

In `settings_ui/src/editor-inline/actions-audio-clock.ts`, replace the `playback-actions` import:

```typescript
import { completePlayback, playbackStateFor, stopProgressClock } from "./playback-actions.js";
```

Add:

```typescript
import {
  dispatchHtmlAudioSessionEvent,
  readHtmlAudioSessionState,
} from "./html-audio-session-controller.js";
```

Replace the audio clock callbacks inside `installAudioClockHandlers()`:

```typescript
    onErrorDuringPlayback(cursorMs) {
      const ord = fieldOrd(visualizer);
      logger.warn("audio clock failed during playback", { ord });
      dispatchHtmlAudioSessionEvent(ord, {
        cursorMs,
        reason: "audio_error",
        type: "AudioError",
      });
    },
    onEndedDuringPlayback(durationMs) {
      const ord = fieldOrd(visualizer);
      const session = readHtmlAudioSessionState(ord);
      if (session.kind !== "starting" && session.kind !== "playing") return;
      if (session.source.kind !== "source") return;
      const field = readFieldState(ord);
      dispatchHtmlAudioSessionEvent(ord, {
        cursorMs: durationMs,
        repeatEnabled: field.playback.repeat,
        repeatPauseMs: readRepeatPauseSecondsRuntime(visualizer) * 1000,
        resetCursorMs: session.request.resetCursorMs ?? session.request.cursorMs,
        restartAudio: true,
        type: "BoundaryReached",
      });
    },
```

- [ ] **Step 4: Shrink `source-playback-controller.ts` to start adaptation**

In `settings_ui/src/editor-inline/source-playback-controller.ts`, remove:

- `SourcePlaybackRuntime`
- `SourcePlaybackEvent`
- `dispatchSourcePlaybackEvent()`
- `handleSourcePlaybackBoundary()`
- `ensureHtmlAudioSessionForBoundary()`
- `ProgressClockOptions` import
- `PlaybackPass` import

Change `startSourceHtmlPlayback()` signature to:

```typescript
export function startSourceHtmlPlayback(
  visualizer: VisualizerElement,
  request: PlaybackRequest,
): boolean {
```

- [ ] **Step 5: Update `playback-actions.ts` call sites**

Change `startSourcePlayback()`:

```typescript
export function startSourcePlayback(visualizer: VisualizerElement, request: PlaybackRequest): boolean {
  setPreserveStatusOnPlaybackEndRuntime(visualizer, request.source === "post_edit");
  return startSourceHtmlPlayback(visualizer, { ...request, engine: "html" });
}
```

Remove `dispatchSourcePlaybackEvent`, `handleSourceAudioError()`, and `sourcePlaybackRuntime()` from `playback-actions.ts`.

- [ ] **Step 6: Run focused tests**

Run:

```bash
npm --prefix settings_ui test -- frontend-architecture.test.ts editor-inline.actions.progress.test.ts editor-inline.chorusing.integration.test.ts editor-inline.html-audio-session.integration.test.ts editor-inline.selection-playback.integration.test.ts editor-inline.playback.integration.test.ts
```

Expected: PASS.

- [ ] **Step 7: Run full phase verification**

Run:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e-parallel
```

Expected: both exit 0. The known unrelated warning for `e2e/test_editor_playback_workflow.py:405` may remain.

- [ ] **Step 8: Commit**

```bash
git add settings_ui/src/editor-inline/playback-controller.ts settings_ui/src/editor-inline/actions-playback.ts settings_ui/src/editor-inline/actions-audio-clock.ts settings_ui/src/editor-inline/playback-actions.ts settings_ui/src/editor-inline/source-playback-controller.ts settings_ui/tests/frontend-architecture.test.ts
git commit -m "Route source boundaries through HTML sessions" -m "The HTML session reducer should own source playback boundaries. Remove the old progress-controller source boundary bridge while preserving manual repeat and chorusing behavior, then enforce that source boundary ownership with an architecture test."
```

---

### Task 3: Remove The Learner Playback Global Prototype Patch

**Files:**

- Modify: `settings_ui/src/editor-inline/html-audio-session-learner-effects.ts`
- Modify: `settings_ui/tests/editor-inline.learner-recording-playback.test.ts`

- [ ] **Step 1: Add a regression test that forbids global dispatch patching**

In `settings_ui/tests/editor-inline.learner-recording-playback.test.ts`, add this test after `resets learner playback state when audio ends`:

```typescript
  it("does not patch EventTarget dispatch globally for learner playback", async () => {
    const dispatchEvent = EventTarget.prototype.dispatchEvent;
    mockMediaPlayback();
    initAndScan(recordingConfig());
    await setupAudioTrack();
    publishReadyRecording({ recordingDurationMs: 600, startCursorMs: 200 });

    playRecordingButton().click();
    await flushMicrotasks();

    expect(EventTarget.prototype.dispatchEvent).toBe(dispatchEvent);
    learnerAudio().dispatchEvent(new Event("ended"));
    expect(window.__aqeGraphStateForTest?.(0)?.learnerPlaybackStatus).toBe("stopped");
  });
```

- [ ] **Step 2: Run the learner test and verify it fails**

Run:

```bash
npm --prefix settings_ui test -- editor-inline.learner-recording-playback.test.ts
```

Expected: FAIL because `EventTarget.prototype.dispatchEvent` changes after playback starts.

- [ ] **Step 3: Remove the prototype patch**

In `settings_ui/src/editor-inline/html-audio-session-learner-effects.ts`, delete:

- `learnerSyntheticBridgeInstalled`
- `latestReadState`
- `latestDispatchEvent`
- `installLearnerSyntheticDispatchBridge()`
- the `installLearnerSyntheticDispatchBridge(readState, dispatchEvent);` call
- the `document.addEventListener("ended", ...)` and `document.addEventListener("error", ...)` blocks inside `installLearnerAudioHandlers()`

Keep the local `audio.addEventListener()`, `audio.onended`, and `audio.onerror` assignments.

- [ ] **Step 4: Run focused tests**

Run:

```bash
npm --prefix settings_ui test -- editor-inline.learner-recording-playback.test.ts editor-inline.recording.integration.test.ts html-audio-session-machine.test.ts html-audio-session-progress.test.ts
```

Expected: PASS.

- [ ] **Step 5: Run full phase verification**

Run:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e-parallel
```

Expected: both exit 0.

- [ ] **Step 6: Commit**

```bash
git add settings_ui/src/editor-inline/html-audio-session-learner-effects.ts settings_ui/tests/editor-inline.learner-recording-playback.test.ts
git commit -m "Remove learner playback global event patch" -m "Learner recording playback should use local audio element handlers, not a global EventTarget prototype patch. This removes page-wide mutable behavior while preserving ended/error dispatch into the HTML audio session."
```

---

### Task 4: Collapse Engine Selection Into Readiness Reason Telemetry

**Files:**

- Modify: `settings_ui/src/editor-inline/playback-engine-decision.ts`
- Modify: `settings_ui/src/editor-inline/playback-telemetry.ts`
- Modify: `settings_ui/src/editor-inline/playback-actions.ts`
- Modify: `settings_ui/tests/playback-engine-decision.test.ts`

- [ ] **Step 1: Rename the model to describe what it now does**

In `settings_ui/src/editor-inline/playback-engine-decision.ts`, keep the filename for this task to minimize churn, but rename exported types:

```typescript
export interface PlaybackReadinessDecisionInput {
  audioClockReady: boolean;
  graphHasTrack: boolean;
  htmlAudioReadinessFailed: boolean;
  htmlAudioReadinessTransient: boolean;
  playbackState: PlaybackState;
  regionMode: PlaybackRegionMode;
  repeat: boolean;
  visualizerPresent: boolean;
}

export interface PlaybackReadinessDecision {
  engine: "html";
  reason: PlaybackEngineSelectionReason;
}
```

Then rename `choosePlaybackEngine()` to:

```typescript
export function describeHtmlPlaybackReadiness(input: PlaybackReadinessDecisionInput): PlaybackReadinessDecision {
```

Remove unused input fields from the implementation:

- `activeEngine`
- `graphDurationMs`
- `htmlAudioReadinessReason`
- `htmlAudioReadinessState`

- [ ] **Step 2: Update telemetry imports and call sites**

In `settings_ui/src/editor-inline/playback-telemetry.ts`, import the renamed function and types:

```typescript
import {
  describeHtmlPlaybackReadiness,
  type PlaybackReadinessDecision,
} from "./playback-engine-decision.js";
```

Rename `playbackEngineDecisionFor()` only if all call sites stay readable in one pass. If not, keep the old function name as a public compatibility wrapper but change its internals to call `describeHtmlPlaybackReadiness()`.

- [ ] **Step 3: Update unit tests**

In `settings_ui/tests/playback-engine-decision.test.ts`, replace `choosePlaybackEngine` imports and expectations with `describeHtmlPlaybackReadiness`. Keep the same reason expectations.

- [ ] **Step 4: Run focused tests**

Run:

```bash
npm --prefix settings_ui test -- playback-engine-decision.test.ts editor-inline.playback.integration.test.ts editor-inline.post-edit-playback.integration.test.ts
```

Expected: PASS.

- [ ] **Step 5: Run full phase verification**

Run:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e-parallel
```

Expected: both exit 0.

- [ ] **Step 6: Commit**

```bash
git add settings_ui/src/editor-inline/playback-engine-decision.ts settings_ui/src/editor-inline/playback-telemetry.ts settings_ui/src/editor-inline/playback-actions.ts settings_ui/tests/playback-engine-decision.test.ts
git commit -m "Clarify HTML playback readiness decisions" -m "Playback no longer chooses between native and HTML engines, so the remaining decision logic is readiness telemetry. Rename and trim the model to reduce dead multi-engine vocabulary while preserving logged reason detail."
```

---

### Task 5: Consolidate Audio Element Ownership Incrementally

**Files:**

- Modify: `settings_ui/src/editor-inline/audio-clock.ts`
- Modify: `settings_ui/src/editor-inline/html-audio-session-audio-element.ts`
- Modify: `settings_ui/src/editor-inline/actions-audio-clock.ts`
- Modify: `settings_ui/tests/frontend-architecture.test.ts`
- Test: `settings_ui/tests/editor-inline.actions.playback.test.ts`
- Test: `settings_ui/tests/editor-inline.html-audio-session.integration.test.ts`

- [ ] **Step 1: Add an architecture guard against duplicate source mutation APIs**

In `settings_ui/tests/frontend-architecture.test.ts`, add:

```typescript
  it("keeps source audio element mutation in the HTML audio session operations", () => {
    const source = withoutComments(readFileSync(join(projectRoot, "src/editor-inline/audio-clock.ts"), "utf-8"));
    const forbiddenExports = Array.from(
      source.matchAll(/export function (pauseAudioClock|clearAudioClockSource|reloadAudioClockSource|configureAudioClock|setAudioClockLoop)\b/g),
      (match) => match[1],
    );

    expect(forbiddenExports).toEqual([]);
  });
```

- [ ] **Step 2: Run the architecture test and verify it fails**

Run:

```bash
npm --prefix settings_ui test -- frontend-architecture.test.ts
```

Expected: FAIL with the listed `audio-clock.ts` mutation exports.

- [ ] **Step 3: Move source mutation exports into session audio operations or graph adapters**

Keep `audioClockFor()`, `mediaUrlForFilename()`, `audioClockReady()`, and metadata/readiness helpers available. Move source mutation responsibilities as follows:

- `configureAudioClock()` call sites that configure the source file after graph rendering should dispatch `SourceConfigured` through the session controller.
- `clearAudioClockSource()` call sites for graph removal should dispatch `SourceCleared` through the session controller, then clear readiness projection.
- `pauseAudioClock()` and `setAudioClockLoop()` should no longer be public source playback controls; source playback pause/loop is represented by session effects.
- `seekAudioClock()` should remain only if selection/cursor gestures need immediate audio seek without changing playback state. If it remains, rename it to `seekAudioElementForCursorPreview()` in this task and update imports.

- [ ] **Step 4: Run focused tests**

Run:

```bash
npm --prefix settings_ui test -- frontend-architecture.test.ts editor-inline.actions.playback.test.ts editor-inline.html-audio-session.integration.test.ts editor-inline.selection-playback.integration.test.ts editor-inline.playback.integration.test.ts
```

Expected: PASS.

- [ ] **Step 5: Run full phase verification**

Run:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e-parallel
```

Expected: both exit 0.

- [ ] **Step 6: Commit**

```bash
git add settings_ui/src/editor-inline/audio-clock.ts settings_ui/src/editor-inline/html-audio-session-audio-element.ts settings_ui/src/editor-inline/actions-audio-clock.ts settings_ui/tests/frontend-architecture.test.ts
git commit -m "Consolidate source audio element mutation" -m "The same audio element was mutated through both audio-clock helpers and HTML session operations. Move source playback mutation behind the session effect runner while preserving readiness and cursor-preview behavior."
```

---

### Task 6: Split `playback-actions.ts` Into Facade And Source Session Adapter

**Files:**

- Create: `settings_ui/src/editor-inline/playback-request-planning.ts`
- Create: `settings_ui/src/editor-inline/post-edit-playback-actions.ts`
- Modify: `settings_ui/src/editor-inline/playback-actions.ts`
- Modify: `settings_ui/src/editor-inline/window-contract.ts`
- Modify: `settings_ui/src/editor-inline/command-actions.ts`
- Test: `settings_ui/tests/editor-inline.playback.integration.test.ts`
- Test: `settings_ui/tests/editor-inline.post-edit-playback.integration.test.ts`

- [ ] **Step 1: Move request construction into `playback-request-planning.ts`**

Create `settings_ui/src/editor-inline/playback-request-planning.ts` with:

```typescript
import { readFieldState } from "./field-state-store.js";
import { currentProgressMs } from "./playback-controller.js";
import { planPlaybackRequest, type PlaybackSnapshot } from "./playback-model.js";
import { effectivePlaybackRegion, repeatEnabledFor } from "./actions.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
import type { PlaybackEngineDecision } from "./playback-engine-decision.js";
import type { PlaybackRequest, VisualizerElement } from "./types.js";

function fieldOrd(visualizer: VisualizerElement): number {
  return Number(visualizer.dataset.aqeFieldOrd || "0");
}

export function playbackRequestFromSnapshot(
  visualizer: VisualizerElement,
  ord: number,
  decision: PlaybackEngineDecision,
): PlaybackRequest {
  return planPlaybackRequest(playbackSnapshotForRequest(visualizer, ord, decision));
}

function playbackSnapshotForRequest(
  visualizer: VisualizerElement,
  ord: number,
  decision: PlaybackEngineDecision,
): PlaybackSnapshot {
  const state = readFieldState(fieldOrd(visualizer));
  return {
    anchorMs: state.cursor.anchorMs,
    currentProgressMs: currentProgressMs(visualizer),
    cursorMs: state.cursor.ms,
    durationMs: readVisualizerTargetDurationMs(visualizer),
    engine: decision.engine,
    ord,
    playbackState: state.playback.state,
    region: effectivePlaybackRegion(visualizer),
    repeat: repeatEnabledFor(visualizer),
    resumeRequiresRestart: state.playback.resumeRequiresRestart,
  };
}
```

- [ ] **Step 2: Move post-edit start logic into `post-edit-playback-actions.ts`**

Move `playAfterEdit()` and its private context/readiness helpers out of `playback-actions.ts`. Keep the exported `playAfterEdit` name re-exported from `playback-actions.ts` during this task to avoid touching Python/window command wiring more than necessary.

- [ ] **Step 3: Keep `playback-actions.ts` as a facade**

After this task, `playback-actions.ts` should primarily export:

- `manualProgressMs`
- `audioProgressMs`
- `currentProgressMs`
- `handlePlaybackBoundary`
- `completePlayback`
- `paintProgressFromClock`
- `startManualProgressClock`
- `startAudioProgressClock`
- `startProgressClock`
- `pauseProgressClock`
- `stopProgressClock`
- `playbackRequest`
- `playAfterEdit`
- `playbackEngineFor`
- `sendPlaybackRequest`
- `startSourcePlayback`
- `handleHtmlPlaybackCommand`
- `setPlaybackState`
- `getPlaybackRequest`
- `stopEditorPlayback`
- `getCursorMs`
- `getCursorIntent`

The logic inside that file should shrink below 250 lines.

- [ ] **Step 4: Run focused tests**

Run:

```bash
npm --prefix settings_ui test -- editor-inline.playback.integration.test.ts editor-inline.post-edit-playback.integration.test.ts editor-inline.actions.playback.test.ts playback-model.test.ts
```

Expected: PASS.

- [ ] **Step 5: Run full phase verification**

Run:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e-parallel
```

Expected: both exit 0.

- [ ] **Step 6: Commit**

```bash
git add settings_ui/src/editor-inline/playback-actions.ts settings_ui/src/editor-inline/playback-request-planning.ts settings_ui/src/editor-inline/post-edit-playback-actions.ts settings_ui/src/editor-inline/window-contract.ts settings_ui/src/editor-inline/command-actions.ts
git commit -m "Split playback action orchestration" -m "Playback actions mixed public facade exports with request planning and post-edit business logic. Split those responsibilities so the remaining facade is easier to audit while preserving existing command wiring."
```

---

### Task 7: Rename Effect Executor Modules After Behavior Cleanup

**Files:**

- Rename: `settings_ui/src/editor-inline/html-audio-session-field-effects.ts` to `settings_ui/src/editor-inline/html-audio-session-field-projection.ts`
- Rename: `settings_ui/src/editor-inline/html-audio-session-learner-effects.ts` to `settings_ui/src/editor-inline/html-audio-session-learner-projection.ts`
- Modify imports in `settings_ui/src/editor-inline/html-audio-session-controller.ts`
- Modify imports in `settings_ui/src/editor-inline/html-audio-session-audio-element.ts`
- Modify imports in tests if any direct imports exist

- [ ] **Step 1: Rename files using `git mv`**

Run:

```bash
git mv settings_ui/src/editor-inline/html-audio-session-field-effects.ts settings_ui/src/editor-inline/html-audio-session-field-projection.ts
git mv settings_ui/src/editor-inline/html-audio-session-learner-effects.ts settings_ui/src/editor-inline/html-audio-session-learner-projection.ts
```

- [ ] **Step 2: Update imports**

Replace:

```typescript
from "./html-audio-session-field-effects.js"
from "./html-audio-session-learner-effects.js"
```

with:

```typescript
from "./html-audio-session-field-projection.js"
from "./html-audio-session-learner-projection.js"
```

- [ ] **Step 3: Run focused tests**

Run:

```bash
npm --prefix settings_ui test -- frontend-architecture.test.ts html-audio-session-machine.test.ts html-audio-session-progress.test.ts editor-inline.html-audio-session.integration.test.ts editor-inline.learner-recording-playback.test.ts
```

Expected: PASS.

- [ ] **Step 4: Run full phase verification**

Run:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e-parallel
```

Expected: both exit 0.

- [ ] **Step 5: Commit**

```bash
git add settings_ui/src/editor-inline/html-audio-session-field-projection.ts settings_ui/src/editor-inline/html-audio-session-learner-projection.ts settings_ui/src/editor-inline/html-audio-session-controller.ts settings_ui/src/editor-inline/html-audio-session-audio-element.ts
git commit -m "Name HTML session projection modules explicitly" -m "The session reducer returns effects as data, while these modules execute UI projections. Rename them to projection modules so file names describe their role and avoid confusing them with reducer effects."
```

---

## Final Verification

After all tasks are complete, run:

```bash
npm --prefix settings_ui test -- frontend-architecture.test.ts html-audio-session-machine.test.ts html-audio-session-progress.test.ts editor-inline.html-audio-session.integration.test.ts editor-inline.learner-recording-playback.test.ts editor-inline.selection-playback.integration.test.ts editor-inline.playback.integration.test.ts editor-inline.post-edit-playback.integration.test.ts editor-inline.chorusing.integration.test.ts editor-inline.actions.progress.test.ts
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e-parallel
```

Expected: all commands exit 0. If the known unrelated `e2e/test_editor_playback_workflow.py:405` line-count warning remains, report it separately and do not treat it as part of this cleanup.

## Execution Notes

- Commit after each task. Each commit message must explain why the boundary changed and what behavior is preserved.
- Do not remove manual progress or chorusing behavior until tests prove those workflows are no longer using the legacy controller.
- Do not remove readiness telemetry just because engine selection is fixed to HTML. Keep reason logging unless product behavior no longer needs it.
- Run full `python3 scripts/dev.py check` and `python3 scripts/dev.py test-e2e-parallel` after each task, not only at the end.
