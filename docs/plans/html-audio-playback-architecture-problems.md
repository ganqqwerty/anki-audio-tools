# HTML Audio Playback Architecture Problems

Branch: `codex/review-htmlonly-playback-plan`

This document describes architecture and clarity problems in the HTML audio
playback system. The codebase is in a **transitional state** between two
playback architectures: a legacy `playback-controller` system and a new
`html-audio-session-machine` state machine. Both run simultaneously.

Playback observability requirements are maintained in
[`../architecture/html-audio-observability.md`](../architecture/html-audio-observability.md).
Do not duplicate the logging, invariant, or e2e-observation checklist here.

---

## 1. Two Parallel Playback Systems

The most significant problem. Two completely separate playback control systems
coexist and both write to the same stores:

**System A (Legacy):** `playback-controller.ts` + `playback-controller-pass.ts` +
`playback-controller-state.ts` + `playback-controller-frame.ts` +
`playback-controller-audio.ts` + `audio-clock.ts`

- Manages `requestAnimationFrame` loops via `paintProgressFromClock`
- Directly reads `HTMLAudioElement.currentTime`
- Directly writes to `field-state-store`
- Manages `PlaybackPass`, `PlaybackProgressPlan`

**System B (Session Machine):** `html-audio-session-controller.ts` +
`html-audio-session-machine.ts` + supporting files

- Manages its own `requestAnimationFrame` loop via `startProgressFrame`
- Directly reads `HTMLAudioElement.currentTime` via `audioProgressMsForOrd`
- Directly writes to `field-state-store` via `html-audio-session-field-effects.ts`
- Has its own progress computation in `html-audio-session-progress.ts`

Both systems are active because `playback-actions.ts` calls both
`startProgressClock` (System A) and dispatches session events (System B) in
`handleHtmlPlaybackCommand`. Both modify `field-state-store` independently.

---

## 2. State Machine Is NOT the Source of Truth

The session machine is **intended** to be the single source of truth but state
leaks in multiple ways:

### Leak 1: `field-state-store` is a parallel authority

`field-state-store` stores `playback.state` ("playing" | "paused" | "stopped"),
`playback.clockMode`, `playback.engine`, cursor positions. Both the old
playback-controller and the new session machine write to it independently. The
old system reads it to determine its own behavior, creating circular dependency
on store state.

### Leak 2: `visualizer-runtime-state` stores playback runtime data

`setPlaybackClockRuntime`, `setPlaybackPassRuntime`,
`readRepeatPauseSecondsRuntime`, etc. are written by the old playback-controller
but read by `source-playback-controller.ts`. Not managed by the session machine.

### Leak 3: `playback-controller-pass.ts` stores `PlaybackPass` independently

The old system computes and stores `PlaybackPass` in both `field-state-store` and
`visualizer-runtime-state`. The session machine has its own `HtmlAudioStartRequest`
with equivalent fields (`cursorMs`, `endMs`, `loop`, `regionMode`,
`resetCursorMs`). These two representations can diverge.

### Leak 4: Two independent frame loops

`paintProgressFromClock` in `playback-controller.ts` runs its own
`requestAnimationFrame` loop. The session machine's `startProgressFrame` in the
controller also runs a frame loop. Both can be active simultaneously.

### Leak 5: Old system drives new system via boundary bridge

`source-playback-controller.ts::handleSourcePlaybackBoundary` is called FROM the
old system's frame loop when it detects a boundary. It dispatches
`BoundaryReached` into the new session machine and may synthesize
`SourceConfigured` + `MetadataLoaded` event sequences, recreating the session
mid-boundary.

---

## 3. `playback-engine-decision.ts` Is Dead Code

Every code path returns `engine: "html"`. The file has 12 selection reasons and
complex input gathering, but the result is always the same. It exists as a
vestige of a removed multi-engine system. All the branching logic is dead.

---

## 4. Two Separate `HTMLAudioElement` Management APIs

- `audio-clock.ts` manages audio via `visualizer.querySelector(".aqe-audio-clock")`
- `html-audio-session-audio-element.ts` manages audio via
  `document.querySelector('[data-testid="aqe-audio-clock-${ord}"]')`

Both manipulate the same DOM element. Both set `src`, call `load()`, `play()`,
`pause()`, set `currentTime`. A fix in one path may not propagate to the other.

---

## 5. `playback-actions.ts` Is a Coordination Mess

A 346-line file that re-exports functions from `playback-controller.ts` with
renamed imports:

```typescript
import {
  completePlayback as completePlaybackFromController,
  currentProgressMs as currentProgressMsFromController,
  handlePlaybackBoundary as handlePlaybackBoundaryFromController,
  ...
} from "./playback-controller.js";
```

Then wraps each one with `playbackControllerDependencies()`. This is pure
ceremony -- the DI pattern was designed for testability, but the wrapper hardcodes
the dependency call every time, making the abstraction pointless. The file also
contains significant business logic (`playAfterEdit`, `handleHtmlPlaybackCommand`,
`sendPlaybackRequest`) that is not just delegation.

---

## 6. Module Naming Confusion

### "Controller" proliferation

| File | What it actually controls |
|------|--------------------------|
| `playback-controller.ts` | Old visual progress rendering + clock management |
| `source-playback-controller.ts` | Bridges PlaybackRequest to HtmlAudioStartRequest |
| `html-audio-session-controller.ts` | Owns session state maps, dispatches events, executes effects |

Three files with "controller" in the name doing fundamentally different things.

### "Effects" naming collision

In the session machine, "effects" means commands returned by state transitions
(`HtmlAudioSessionEffect`). But `html-audio-session-field-effects.ts` and
`html-audio-session-learner-effects.ts` are *executors* of some of those effects,
not the effects themselves. They also source new events. The naming suggests
Redux/Elm-style effects but they are imperative side-effect handlers.

### `playback-actions.ts` vs `playback-controller.ts`

"Actions" is the public API, "controller" is the implementation. But "actions"
also contains significant logic that is not just delegation. The boundary is
unclear.

---

## 7. Duplicate Functions Across Systems

### `completePlayback` exists in three places

1. `playback-controller-state.ts::completePlayback` -- old system, uses DI deps
2. `html-audio-session-field-effects.ts::completePlayback` -- new system, direct
3. `playback-actions.ts::completePlayback` -- re-export of old system

### Boundary handling exists in four places

1. `playback-controller.ts::handlePlaybackBoundary` -- old system
2. `html-audio-session-machine.ts` `BoundaryReached` handler -- new system
3. `source-playback-controller.ts::handleSourcePlaybackBoundary` -- bridge
4. `playback-actions.ts::handlePlaybackBoundary` -- re-export of old system

### Backend playback request sending exists in two places

1. `playback-actions.ts::sendPlaybackRequest` -- via `focusAndSendCommand`
2. `html-audio-session-backend-queue.ts::queueBackendPlayback` -- also via
   `focusAndSendCommand`, same pattern

### Progress computation exists in three places

1. `playback-controller-audio.ts::currentProgressMs` -- reads from store/clock
2. `html-audio-session-progress.ts::htmlAudioProgressMs` -- clock + audio time
3. `playback-controller-audio.ts::manualProgressMs` -- PlaybackClockRuntime

---

## 8. Global Prototype Monkey-Patch

`html-audio-session-learner-effects.ts:93-94` patches
`EventTarget.prototype.dispatchEvent` globally. It holds closure references to
`latestReadState` and `latestDispatchEvent` in module-level variables.

- Global mutable state persists across all ord values
- Affects all event dispatching in the page, not just the audio element
- Exists because the audio element's `ended`/`error` events may fire when the
  session machine is in an unexpected state

---

## 9. Behavioral Circularity

No import cycles exist, but there is behavioral circularity:

1. `playback-actions.ts::handleHtmlPlaybackCommand` calls `pauseProgressClock`
   (old system) AND dispatches `PauseRequested` (new system)
2. `source-playback-controller.ts::handleSourcePlaybackBoundary` is called FROM
   the old system's frame loop and dispatches INTO the new system
3. The new system's `PublishPlaybackState` writes to `field-state-store`
4. The old system's frame loop reads from `field-state-store` to determine
   playback state

Both systems write to the same store, and each system's behavior can be affected
by writes from the other.

---

## Recommended Path Forward

1. **Delete `playback-engine-decision.ts`** -- dead code, always returns "html"
2. **Delete `audio-clock.ts`** -- consolidate all audio element management into
   `html-audio-session-audio-element.ts`
3. **Delete `playback-controller.ts` and its sub-modules** -- move all progress
   rendering into the session machine's frame loop
4. **Eliminate the boundary bridge** -- the session machine should own boundary
   detection directly, not receive it from the old system
5. **Make `field-state-store` a read-only projection** -- only the session machine
   should write playback state; other modules should read but never write
6. **Rename files for clarity** -- "controller" should be reserved for the
   session controller; bridge/adapter modules should say so in their names
7. **Remove the `EventTarget.prototype` monkey-patch** -- use a local event
   listener pattern instead of global mutation
