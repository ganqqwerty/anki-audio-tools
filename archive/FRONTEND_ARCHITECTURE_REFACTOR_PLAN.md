# Frontend Architecture Refactor Plan

## Purpose

This document records the current shape of the Svelte/TypeScript frontend, the architecture problems identified in the inline editor bundle, and a staged plan for refactoring it without losing behavior. It is intended to guide a large refactor, not to describe the final architecture as if it already exists.

The main conclusion is that the frontend does not need a third-party state management library yet. The immediate problem is mixed responsibilities: one module owns state transitions, DOM reads and writes, audio timers, bridge dispatch, SVG rendering coordination, and test-only window helpers. A small typed state/controller layer should address that directly while keeping the injected Anki editor runtime simple.

## Current Frontend Structure

The frontend source lives under `settings_ui/` and produces two committed WebView bundles:

- settings dialog bundle: `settings_ui/src/App.svelte`, `settings_ui/src/main.ts`, and `settings_ui/src/lib/`
- inline editor bundle: `settings_ui/src/editor-inline/`
- settings output: `addon/anki_audio_quick_editor/templates/settings/settings_bundle.{js,css}`
- editor output: `addon/anki_audio_quick_editor/templates/editor/editor_bundle.{js,css}`

The inline editor bundle is built as an IIFE from `settings_ui/src/editor-inline/main.ts` through `settings_ui/vite.editor.config.ts`, then injected by `addon/anki_audio_quick_editor/editor_ui.py`. Python registers `aqe:*` bridge commands in `addon/anki_audio_quick_editor/editor_integration.py` and calls the frontend through the `window.__aqe*` contract.

### Size Inventory

Current frontend production and test file sizes:

| File | Lines | Notes |
|------|-------|-------|
| `settings_ui/src/editor-inline/actions.ts` | 1414 | Central inline editor behavior module. Largest risk. |
| `settings_ui/tests/editor-inline.integration.test.ts` | 736 | Broad jsdom integration coverage for injected editor behavior. |
| `settings_ui/src/App.svelte` | 517 | Settings UI state, markup, and CSS in one component. |
| `settings_ui/tests/editor-inline.actions.test.ts` | 360 | Focused tests for `actions.ts` workflows. |
| `settings_ui/src/editor-inline/EditorControls.svelte` | 315 | Inline controls markup, visualizer markup, CSS, and mount initialization. |
| `settings_ui/tests/app.test.ts` | 240 | Settings UI tests. |
| `settings_ui/src/editor-inline/runtime.ts` | 182 | Runtime mount/dispose/scan/window-contract installer. |
| `settings_ui/src/editor-inline/types.ts` | 163 | Editor command, state-like, test-state, and DOM extension types. |
| `settings_ui/src/lib/async-jobs.ts` | 162 | Settings async operation promise registry. |
| `settings_ui/src/editor-inline/plot.ts` | 145 | Plot geometry and SVG drawing helpers. |
| `settings_ui/src/lib/generated/contracts.ts` | 139 | Generated communication contracts. |
| `settings_ui/src/lib/logger.ts` | 119 | Shared logger and generated `FrontendLogPayload` adapter. |
| `settings_ui/src/lib/bridge.ts` | 70 | Settings bridge. |
| `settings_ui/src/editor-inline/commands.ts` | 63 | Inline editor command metadata. |
| `settings_ui/src/editor-inline/bridge.ts` | 40 | Inline editor bridge queue and `pycmd` wrapper. |
| `settings_ui/src/lib/utils.ts` | 28 | Currently unused helper residue. |

`actions.ts` exports 69 symbols. This is a strong signal that it is not a cohesive module, even though many individual functions are named reasonably.

### Current Inline Editor Runtime Flow

1. Python appends the editor bundle to the Anki editor load JavaScript through `injection_script(...)`.
2. The injected script writes `window.__AQE_EDITOR_CONFIG__`, disposes any previous editor runtime, injects CSS, and executes the editor bundle.
3. `settings_ui/src/editor-inline/main.ts` calls `initializeEditorRuntime()`.
4. `runtime.ts` installs the `window.__aqe*` contract, calls `prepareForNewNote()`, and schedules several scans.
5. `scan(...)` finds audio fields or uses explicit Python-provided audio field indices.
6. `mountNear(...)` mounts `EditorControls.svelte` beside each field.
7. `EditorControls.svelte` renders buttons, repeat checkbox, SVG visualizer shell, hidden audio element, status text, and calls setup functions from `actions.ts` on mount.
8. Button clicks call `send(...)` in `actions.ts`.
9. `send(...)` decides whether the click is graph analysis, HTML playback, a processing command, or a direct bridge command.
10. Python handles the command in `_handle_bridge_command(...)` and may later call frontend callbacks such as `window.__aqeSetBusy`, `window.__aqeSetVisualizer`, `window.__aqeSetPlaybackState`, or `window.__aqeSetVisualizerStatus`.

### Current Python/Frontend Contract

Python-to-frontend window functions currently include:

- `__aqeScan`
- `__aqeSetBusy`
- `__aqeSetStatus`
- `__aqeSetVisualizer`
- `__aqeSetVisualizerStatus`
- `__aqeResetGraphAfterEdit`
- `__aqeSetPlaybackState`
- `__aqeGetPlaybackRequest`
- `__aqeStopEditorPlayback`
- `__aqeGetCursorMs`
- `__aqeGetCursorIntent`
- `__aqePrepareForNewNote`
- `__aqePopFrontendLog`

Test-oriented functions are also installed on `window`:

- `__aqeGraphStateForTest`
- `__aqeInstallAudioPlaybackTestDriverForTest`
- `__aqeSetCursorForTest`
- `__aqeSetCursorByClientXForTest`

The test helpers are valuable, but their production placement makes the runtime contract look broader than it really is.

### Current Test Gate

`python3 scripts/dev.py test-svelte` currently passes. It runs:

- `svelte-check --tsconfig ./tsconfig.json`
- `eslint .`
- `tsc --noEmit`
- `vitest run --coverage`

Most recent observed result:

- 8 frontend test files passed
- 74 Vitest tests passed
- 92.07% overall statement/line coverage
- `settings_ui/src/editor-inline`: 93.14% statements/lines, 95.23% functions, 71.66% branches
- `settings_ui/src/editor-inline/actions.ts`: 90.9% statements/lines, 93.69% functions, 65.84% branches
- `settings_ui/src/lib/utils.ts`: 0% coverage and no current imports

The coverage is strong enough to refactor safely, but it is not yet shaped around clean state transitions. Many tests observe behavior through the DOM and the test window contract, which is useful, but the pure business rules are not isolated.

## GitNexus Findings

GitNexus was used to inspect the connected execution flows and impact of key editor symbols.

### Central Hub

GitNexus query and Cypher inspection both show `settings_ui/src/editor-inline/actions.ts` as the hub for editor-inline behavior. Notable internal connections include:

- `send(...)` reaches graph analysis, HTML playback command handling, processing busy state, and bridge dispatch.
- `setVisualizer(...)` reaches graph DOM rendering, audio clock configuration, cursor state, selection reset, busy state, and logging.
- `startSelectionGesture(...)` reaches selection draft state, committed selection state, playback interruption/resume, current progress, and HTML playback restart.
- `startProgressClock(...)` reaches playback state, cursor state, other visualizer stoppage, audio/manual clock choice, timer setup, and audio fallback.
- `playbackRequest(...)` derives Python bridge payloads from current DOM/dataset state and current playback progress.

### Impact Analysis

GitNexus impact analysis showed:

- `startProgressClock(...)`: CRITICAL upstream risk, with direct callers `startEditorHtmlPlayback(...)` and `setPlaybackState(...)`, and affected flows through `handleHtmlPlaybackCommand(...)`, `startSelectionGesture(...)`, `send(...)`, and pointer-up gesture handlers.
- `playbackRequest(...)`: LOW upstream risk in graph terms, but semantically important because Python playback behavior depends on the returned payload.
- `startSelectionGesture(...)`: LOW direct graph risk, but it participates in complex user-visible selection/playback behavior.
- `setVisualizer(...)`: LOW graph-reported upstream impact because it is installed through the window contract rather than ordinary static calls; semantically it is high value because Python invokes it after prosody analysis.
- `initializeEditorRuntime(...)`: LOW graph-reported upstream impact because it is the bundle entry behavior and window-mounted, not called through normal application imports.

The mismatch between low static impact and high runtime importance is expected for injected WebView code. The refactor plan must treat `window.__aqe*` functions as public API even when GitNexus sees few static callers.

## Current Responsibilities By Module

### `settings_ui/src/editor-inline/runtime.ts`

Current responsibilities:

- installs the window contract
- resets note state
- scans Anki editor fields for audio references
- mounts and unmounts Svelte controls
- keeps a `Map<number, MountedField>`
- preserves existing mounts during delayed scans when graph analysis is busy or a graph is already rendered

Healthy aspects:

- small enough to understand
- clear runtime entry point
- field scanning logic is localized

Concerns:

- imports many individual functions from `actions.ts`
- exposes test helpers in the same place as production callbacks
- field mounting and runtime contract installation are distinct responsibilities but live together

### `settings_ui/src/editor-inline/EditorControls.svelte`

Current responsibilities:

- renders all inline editor buttons
- renders repeat playback control
- renders the visualizer SVG shell
- renders hidden audio clock element
- owns visualizer CSS
- initializes visualizer state and audio clock handlers in `onMount`
- reads `window.__AQE_EDITOR_CONFIG__` directly in markup

Healthy aspects:

- mostly declarative UI structure
- uses `COMMAND_BUTTONS` rather than duplicating command metadata
- keeps SVG shell stable for external rendering helpers

Concerns:

- direct global config reads make inputs less explicit
- `onMount` initialization calls behavior functions from `actions.ts`
- visualizer markup, control surface markup, and CSS are packed into one component

### `settings_ui/src/editor-inline/actions.ts`

Current responsibilities:

- DOM selectors for controls, buttons, repeat checkbox, visualizer, audio element
- global busy state
- editor command dispatch
- processing command busy behavior
- media URL encoding
- audio clock source setup
- audio element event handlers
- audio fallback bookkeeping
- cursor state and SVG cursor rendering
- selection/draft selection state
- pointer gesture lifecycle
- graph analysis request state
- prosody visualizer render orchestration
- graph status updates
- note reset cleanup
- manual playback clock
- audio playback clock
- loop boundary handling
- native/html playback request construction
- bridge request queuing
- Python playback state callback handling
- test audio driver
- test graph state extraction

Healthy aspects:

- many function names are locally understandable
- behavior is already highly covered by integration tests
- most logic is in TypeScript instead of string-injected JavaScript

Concerns:

- the module name `actions` no longer communicates the scope
- the DOM is the state store, renderer, query layer, and public API surface
- state fields are stringly typed through `HTMLElement.dataset`
- side effects are not explicit at function boundaries
- pure transition logic is difficult to test without jsdom
- audio timers and bridge dispatch are mixed with selection and cursor math
- test-only hooks are exported from the same module as production behavior
- long functions such as `startSelectionGesture`, `prepareForNewNote`, `startAudioProgressClock`, and `graphStateForTest` combine multiple decision layers

### `settings_ui/src/editor-inline/plot.ts`

Current responsibilities:

- plot dimensions
- time and pitch coordinate mapping
- intensity path construction
- pitch segment construction
- SVG pitch/label/x-axis rendering
- cursor hit testing against rendered SVG bounds

Healthy aspects:

- mostly cohesive
- clear inputs and outputs
- pure geometry helpers are easy to test
- DOM writes are constrained to SVG drawing helpers

Concerns:

- drawing helpers and pure geometry helpers are mixed, but the file is still small enough that this is not urgent

### `settings_ui/src/editor-inline/bridge.ts`

Current responsibilities:

- safe `pycmd` wrapper for editor bridge commands
- focus-then-command dispatch
- frontend log queue
- pending playback request queue
- last cursor intent storage

Healthy aspects:

- small and clear
- side effects are expected and named
- good bridge boundary

Concerns:

- pending playback and cursor intent storage on `window` should remain clearly documented as bridge state, not general app state

### `settings_ui/src/lib/async-jobs.ts`

Current responsibilities:

- settings-dialog async operation job IDs
- pending promise registry
- progress callback dispatch
- result narrowing for generated communication-contract payloads

Healthy aspects:

- cohesive
- side effects are limited to a private pending map and bridge dispatch
- result narrowing is explicit

Concerns:

- none urgent

### `settings_ui/src/App.svelte`

Current responsibilities:

- settings initial fallback state
- settings form state
- tab state
- save/cancel/reset bridge actions
- diagnostics async operations
- diagnostics report rendering
- all settings dialog markup
- all settings dialog CSS

Healthy aspects:

- currently manageable
- tests cover important save and diagnostics workflows

Concerns:

- it will become hard to extend if settings grow
- async diagnostics workflows are embedded directly in the component
- fallback default config duplicates schema defaults and should be kept under watch

### `settings_ui/src/lib/utils.ts`

Current responsibilities:

- `cn(...)`
- `debounce(...)`

Concerns:

- no imports found
- 0% coverage
- likely template residue unless planned for future UI work

Recommendation: delete it if unused after confirming no near-term planned use.

## State Management Assessment

The current inline editor state is primarily stored in DOM attributes:

- `document.body.dataset.aqeBusy`
- `visualizer.dataset.graphActive`
- `visualizer.dataset.graphBusy`
- `visualizer.dataset.hasTrack`
- `visualizer.dataset.durationMs`
- `visualizer.dataset.anchorMs`
- `visualizer.dataset.cursorMs`
- `visualizer.dataset.progressMs`
- `visualizer.dataset.sourceFilename`
- `visualizer.dataset.playbackState`
- `visualizer.dataset.playbackEngine`
- `visualizer.dataset.playbackStartMs`
- `visualizer.dataset.playbackEndMs`
- `visualizer.dataset.playbackRegionMode`
- `visualizer.dataset.repeatEnabled`
- `visualizer.dataset.selectionActive`
- `visualizer.dataset.selectionStartMs`
- `visualizer.dataset.selectionEndMs`
- `visualizer.dataset.selectionDraftActive`
- `visualizer.dataset.selectionDraftStartMs`
- `visualizer.dataset.selectionDraftEndMs`
- `visualizer.dataset.resumeRequiresRestart`
- `visualizer.dataset.progressClockMode`

This has practical benefits:

- CSS can respond to state without extra plumbing.
- tests can inspect behavior through DOM state.
- Python-injected code can remain simple.
- no framework-specific store is needed for cross-boundary callbacks.

The problem is that `dataset` is currently also the source of truth. That makes valid state transitions implicit and stringly typed. For example, playback can be stopped, paused, playing through HTML audio, playing through native Anki playback, preparing a native segment, or manually clocked after HTML audio failure. Those distinctions are spread across DOM attributes, Python session state, and bridge request payloads.

### Recommended Alternative

Use a small local typed state layer per mounted audio field:

```ts
interface EditorFieldState {
  ord: number;
  sourceFilename: string;
  graph: {
    active: boolean;
    busy: boolean;
    hasTrack: boolean;
    durationMs: number;
    analyzerName: string;
  };
  cursor: {
    ms: number;
    anchorMs: number;
    progressMs: number;
  };
  selection: {
    active: boolean;
    draftActive: boolean;
    startMs: number | null;
    endMs: number | null;
    draftStartMs: number | null;
    draftEndMs: number | null;
  };
  playback: {
    state: "stopped" | "playing" | "paused";
    engine: "html" | "native" | "";
    clockMode: "audio" | "manual" | "stopped";
    repeat: boolean;
    regionMode: "full" | "selection";
    startMs: number;
    endMs: number;
    resumeRequiresRestart: boolean;
  };
}
```

Then treat `dataset` as a rendered projection, not the source of truth. In other words:

- controller state is authoritative
- pure transition helpers update typed state
- renderer writes `dataset`, text labels, SVG positions, button labels, and hidden flags
- bridge adapters translate typed state into Python payloads

This keeps the current CSS and test affordances while making state transitions testable without a browser DOM.

### Why Not Add A State Library Now

A third-party state library is not the right first move.

Reasons:

- The editor runs as injected WebView code controlled by Python `window.__aqe*` callbacks, not as a normal routed SPA.
- The main problem is mixed responsibilities, not absence of a store.
- Svelte stores would help Svelte components, but much of the work is outside Svelte component reactivity: audio elements, `requestAnimationFrame`, Python bridge callbacks, and Anki field scanning.
- Redux-like libraries would add ceremony without reducing DOM/audio/bridge coupling by themselves.
- XState could eventually help because playback and selection are state-machine-shaped, but it should be evaluated only after extracting typed local transitions.

Recommended first step: plain TypeScript state objects, pure transition functions, and per-field controllers.

## Target Architecture

### Desired Module Map

The target architecture should keep the runtime small and make side effects obvious.

| Module | Responsibility | Inputs | Outputs | Allowed Side Effects |
|--------|----------------|--------|---------|----------------------|
| `runtime.ts` | Bundle entry, scan scheduling, top-level dispose, window contract installation | `EditorRuntimeConfig` | mounted controllers | `window.__aqe*`, timers for delayed scan |
| `field-scanner.ts` | Discover Anki editor fields and supported audio refs | DOM root/config | `FieldTarget[]` | DOM reads only |
| `field-controller.ts` | Per-field orchestration facade | target, bridge, renderer, audio clock, initial state | public controller methods | delegates side effects only |
| `field-state.ts` | Typed state model and pure transitions | state + event | next state / commands | none |
| `selection-state.ts` | Selection normalization and draft/commit transitions | duration/cursor/pointer values | selection state | none |
| `selection-gestures.ts` | Pointer event lifecycle | visualizer element, controller | events to controller | add/remove pointer/keyboard listeners |
| `playback-state.ts` | Playback request and transition decisions | state + event | next state / playback request | none |
| `playback-controller.ts` | HTML/native playback frontend behavior | controller state, audio element, bridge | playback side effects | audio element, animation frames, bridge dispatch |
| `audio-clock.ts` | HTML audio element source, readiness, seek/play/pause fallback | audio element, source filename, start ms | result flags/callbacks | audio element, audio events |
| `visualizer-renderer.ts` | Render typed state and prosody track into DOM/SVG | state, track, target elements | DOM projection | DOM writes only |
| `dom-selectors.ts` | Central typed selectors for editor controls | ord/root | elements/null | DOM reads only |
| `editor-commands.ts` | User command dispatch policy | command, controller state | action/bridge command | none or bridge through adapter |
| `test-contract.ts` | Test-only graph state and audio driver helpers | controller registry | test snapshots | test-only DOM/audio hooks |

This does not need to be created all at once. It is a refactoring destination.

### Public Runtime Contract

Keep the current `window.__aqe*` names stable until the refactor is complete. Python tests and e2e helpers already depend on them.

Production callbacks should remain:

- `__aqeScan`
- `__aqeSetBusy`
- `__aqeSetStatus`
- `__aqeSetVisualizer`
- `__aqeSetVisualizerStatus`
- `__aqeResetGraphAfterEdit`
- `__aqeSetPlaybackState`
- `__aqeGetPlaybackRequest`
- `__aqeStopEditorPlayback`
- `__aqeGetCursorMs`
- `__aqeGetCursorIntent`
- `__aqePrepareForNewNote`
- `__aqePopFrontendLog`

Test callbacks may remain temporarily, but should be installed through a single named test-contract adapter:

- `__aqeGraphStateForTest`
- `__aqeInstallAudioPlaybackTestDriverForTest`
- `__aqeSetCursorForTest`
- `__aqeSetCursorByClientXForTest`

The production controller should not need to know that tests observe state through those callbacks.

### Naming Improvements

Rename vague functions as they move:

| Current Name | Suggested Name | Why |
|--------------|----------------|-----|
| `send` | `dispatchEditorCommand` | States that it dispatches a UI command, not just sends bytes. |
| `requestGraph` | `startGraphAnalysisRequest` | Captures graph state reset plus Python analysis request. |
| `setVisualizer` | `renderProsodyVisualizer` or `applyProsodyTrack` | Captures Python callback and DOM rendering semantics. |
| `setVisualizerStatusFromPython` | `applyAnalyzerStatusFromPython` | Names the callback source and domain. |
| `prepareForNewNote` | `resetMountedControlsForNewNote` | Captures scope and side effect. |
| `setCursor` | `applyCursorPosition` | Captures DOM/state mutation. |
| `startProgressClock` | `startPlaybackClock` | More domain-specific. |
| `startManualProgressClock` | `startManualPlaybackClock` | Avoids vague progress-only wording. |
| `startAudioProgressClock` | `startHtmlAudioPlaybackClock` | Names browser audio engine. |
| `playbackRequest` | `buildPlaybackRequestForPython` | Captures bridge output. |
| `graphStateForTest` | `snapshotGraphStateForTest` | Makes test-only observation explicit. |

## Refactor Plan

### Phase 0: Baseline And Guardrails

Goal: make the current behavior harder to accidentally change before moving code.

Tasks:

1. Run and record baseline:
   - `python3 scripts/dev.py test-svelte`
   - `python3 scripts/dev.py test`
   - `python3 scripts/dev.py test-e2e`
2. Add frontend architecture tests before splitting modules:
   - max production frontend file size
   - max export count per frontend module
   - `pycmd` only in bridge modules
   - `window.__aqe*` installation only in `runtime.ts` or a named window-contract module
   - test-only `window.__aqe*ForTest` functions only installed through a named test-contract module
3. Add a contract test that compares installed `window.__aqe*` names in `runtime.ts` with `globals.d.ts`.
4. Add a contract test that all `aqe:*` commands in `COMMAND_BUTTONS` are represented in Python `BRIDGE_COMMANDS` or explicitly classified as frontend-only.
5. Add a no-unused-frontend-source test or remove `settings_ui/src/lib/utils.ts`.

Recommended tests:

- `settings_ui/tests/frontend-architecture.test.ts`
- `settings_ui/tests/editor-inline.window-contract.test.ts`
- Extend `tests/test_architecture/test_rule3_editor_bridge_contract.py` if the check must cover Python and TypeScript together.

Acceptance criteria:

- Architecture tests fail on another 1000-line frontend module.
- Runtime window contract drift is caught before e2e.
- Existing behavior tests remain green.

### Phase 1: Extract Pure State Without Changing Runtime Behavior

Goal: introduce typed state helpers while keeping `actions.ts` as the compatibility facade.

Tasks:

1. Add `settings_ui/src/editor-inline/field-state.ts`.
2. Define `EditorFieldState`, `EditorFieldEvent`, `PlaybackRegion`, and conversion helpers from the current DOM/dataset state.
3. Add pure helpers for:
   - initial field state
   - graph requested
   - graph rendered
   - graph failed/status changed
   - cursor moved
   - selection draft changed
   - selection committed
   - selection cleared
   - repeat toggled
   - playback started/paused/stopped
   - note reset
4. Keep `actions.ts` reading/writing DOM initially, but call pure helpers to compute decisions.

Recommended tests:

- initial state includes correct repeat default
- graph request resets graph, cursor, selection, playback region, busy flags
- graph rendered sets duration/source/analyzer and clears selection
- note reset returns to clean hidden visualizer state
- cursor clamps to `[0, durationMs]`
- selection normalizes reversed drag
- tiny selections are rejected
- clearing selection restores full playback region
- repeat flag does not alter selection state
- invalid payload values are normalized

Acceptance criteria:

- New state tests run without jsdom where practical.
- No user-visible behavior changes.
- `actions.ts` starts shrinking through delegation, even before moving side effects.

### Phase 2: Split Selection

Goal: isolate selection state and pointer gesture lifecycle.

Tasks:

1. Add `selection-state.ts` for pure selection math:
   - normalize start/end
   - draft creation
   - draft commit
   - clear
   - click-vs-selection threshold
   - selection playback region derivation
2. Add `selection-gestures.ts` for pointer lifecycle:
   - `pointermove`
   - `pointerup`
   - `pointercancel`
   - `keydown Escape`
   - `blur`
   - `lostpointercapture`
3. Move `startSelectionGesture`, `shouldTreatSelectionGestureAsClick`, `selectionForVisualizer`, `draftSelectionForVisualizer`, `setSelectionDraft`, `commitSelectionDraft`, `clearSelection`, and related helpers out of `actions.ts`.
4. Keep a compatibility re-export if tests or callers need migration time.

Recommended tests:

- click without Shift moves cursor and preserves existing selection
- Shift-click clears selection
- Shift-drag creates draft first and commits on pointerup
- reversed Shift-drag stores normalized start/end
- draft cancellation leaves committed selection unchanged
- Escape cancels draft
- blur cancels draft
- lost pointer capture cancels draft
- active playback is interrupted during selection drag and resumes when expected
- paused playback marks resume as requiring restart when selection changes
- selection clamps to duration bounds
- multi-field selections remain isolated

Acceptance criteria:

- Selection pure tests cover edge cases without mounted Svelte.
- Existing editor-inline integration tests still pass.
- E2E region selection workflow still passes.

### Phase 3: Split Playback

Goal: reduce the CRITICAL-risk playback cluster by extracting pure playback decisions first, then side effects.

Tasks:

1. Add `playback-state.ts`:
   - `buildPlaybackRequestForPython(state)`
   - `playbackEngineForState(state, audioReady)`
   - `startPlaybackTransition`
   - `pausePlaybackTransition`
   - `stopPlaybackTransition`
   - `completePlaybackTransition`
   - `loopBoundaryTransition`
   - `resumeRequiresRestart` rules
2. Add `audio-clock.ts`:
   - source setup
   - ready detection
   - seek
   - pause
   - play with fallback result
   - event handler installation
3. Add `playback-controller.ts`:
   - owns `requestAnimationFrame`
   - owns HTML audio/manual clock selection
   - stops other active fields through controller registry
   - queues Python playback requests through the bridge adapter
4. Move or wrap:
   - `startProgressClock`
   - `startManualProgressClock`
   - `startAudioProgressClock`
   - `pauseProgressClock`
   - `stopProgressClock`
   - `completePlayback`
   - `handleHtmlPlaybackCommand`
   - `startEditorHtmlPlayback`
   - `getPlaybackRequest`
   - `setPlaybackState`
   - `installAudioClockHandlers`
   - `configureAudioClock`
   - `seekAudioClock`

Recommended pure tests:

- stopped + play with no selection builds `start/full` request at anchor
- stopped + play with selection builds `start/selection` request at selection start
- playing + play builds pause request at current progress
- paused + play builds resume request when still inside selected region
- paused outside selected region builds start request at selected start
- repeat enabled includes loop flag
- selection fallback to full region when selection is too small
- native engine selected when no track or audio is not ready
- html engine selected when graph has track and audio is ready
- active engine is preserved while not stopped
- playback completion resets cursor to region start for selection
- playback completion resets cursor to anchor for full playback
- loop boundary returns next pass at region start
- manual clock clamps at playback end

Recommended jsdom/controller tests:

- HTML audio play success queues Python `aqe:play` request only after audio starts
- HTML audio play rejection falls back to native for full-region playback
- HTML audio play rejection does not claim native support for selected repeat playback
- audio `error` event while playing switches to manual clock
- audio `ended` triggers loop or completion
- second field playback stops first field playback
- processing command stops active playback before bridge dispatch
- Python `__aqeSetPlaybackState` can start, pause, and stop frontend clocks
- native playback request does not start browser audio clock

Recommended e2e focus:

- `e2e/test_editor_playback_workflow.py`
- `e2e/test_editor_region_loop_workflow.py`
- `e2e/test_editor_processing_workflow.py`

Acceptance criteria:

- `startProgressClock` disappears or becomes a thin compatibility wrapper.
- Playback decisions are testable without DOM.
- No regression in selected region one-shot, repeat loop, pause/resume, native fallback, or note switching.

### Phase 4: Split Visualizer Rendering And DOM Selectors

Goal: make graph rendering a named DOM projection rather than a side effect hidden in `setVisualizer`.

Tasks:

1. Add `dom-selectors.ts`:
   - `controlsForOrd`
   - `visualizerForOrd`
   - `buttonFor`
   - `graphButton`
   - `playButton`
   - repeat checkbox lookup
   - all visualizers/buttons
2. Add `visualizer-renderer.ts`:
   - render graph active/busy/hidden state
   - render cursor
   - render selection/draft selection
   - render status/spinner
   - render graph track through `plot.ts`
   - render/reset labels and button text
3. Move graph-specific behavior:
   - `setVisualizer`
   - `setVisualizerStatus`
   - `setVisualizerStatusFromPython`
   - `requestGraph`
   - `resetGraphAfterEdit`
   - `graphLogContext`
   - `clearText`
4. Decide whether `plot.ts` should remain mixed pure/drawing or split into `plot-geometry.ts` and `plot-renderer.ts`.

Recommended tests:

- renderer writes expected `dataset` projection for each graph state
- renderer clears stale intensity/pitch/x-axis on graph request
- renderer draws prosody payload with no NaN path values
- renderer handles missing optional SVG groups defensively
- graph status processing shows spinner and sets busy
- graph status error hides spinner and keeps controls usable
- redraw resets cursor and reanalyzes current clip
- graph render updates audio clock source from `sourceFilename`

Acceptance criteria:

- Python callback `__aqeSetVisualizer` remains stable.
- Visualizer rendering can be tested separately from command dispatch.
- `actions.ts` no longer owns SVG/status/button/selection rendering details.

### Phase 5: Introduce Per-Field Controller Registry

Goal: make each mounted audio field an explicit controller with typed state and controlled side effects.

Tasks:

1. Add `field-controller.ts`:
   - creates state
   - holds element references
   - exposes command methods matching the runtime contract
   - coordinates selection, playback, visualizer renderer, and bridge
2. Add a controller registry:
   - `getController(ord)`
   - `mountController(target)`
   - `disposeController(ord)`
   - `disposeAllControllers()`
   - `stopOtherControllers(ord)`
3. Change `runtime.ts` to mount controllers instead of relying on `actions.ts` globals.
4. Keep window callbacks as adapters that look up a controller by `ord`.

Recommended tests:

- mounting creates one controller per explicit field
- rescans preserve a controller while graph is busy
- rescans preserve rendered graph source during delayed reload scan
- source change disposes/replaces idle controller
- dispose removes DOM and cancels playback frame/audio test frame
- note reset resets all mounted controllers
- controller registry isolates state by field ord
- unknown ord callbacks return safe defaults

Acceptance criteria:

- state ownership is per field, not implicit in document queries.
- `runtime.ts` remains small.
- direct document-wide queries are limited to scanner/registry/selector modules.

### Phase 6: Separate Test Contract

Goal: keep test observability strong while separating it from production behavior.

Tasks:

1. Add `test-contract.ts`.
2. Move:
   - `graphStateForTest`
   - `installAudioPlaybackTestDriver`
   - `setCursorForTest`
   - `setCursorByClientXForTest`
   - `commandSlugsForTest`
3. Install test callbacks from one explicit runtime function such as `installEditorTestWindowContract(registry)`.
4. Keep names stable for existing e2e helpers unless there is a deliberate synchronized migration.

Recommended tests:

- production window contract does not accidentally include new test helpers
- test window contract has all expected helper names
- test helpers return typed snapshots from controller state
- audio playback test driver is opt-in and reset on dispose

Acceptance criteria:

- test helpers remain available to e2e.
- production modules do not import test helpers except through the runtime installation adapter.

### Phase 7: Settings UI Cleanup

Goal: prevent `App.svelte` from becoming the next `actions.ts`.

Tasks:

1. Split `App.svelte` into:
   - `SettingsApp.svelte`
   - `GeneralSettingsPanel.svelte`
   - `DiagnosticsPanel.svelte`
   - `SettingsFooter.svelte`
2. Add `settings-state.ts` or `settings-actions.ts` for:
   - fallback initial state
   - save payload normalization
   - diagnostics command helpers
3. Keep `settings_ui/src/lib/bridge.ts` as the only settings `pycmd` module.

Recommended tests:

- save payload always forces `enabled: true`
- diagnostics progress updates correct panel state
- support report copy errors display correctly
- show log success and failure display correctly
- reset/cancel commands remain bridge-only

Acceptance criteria:

- no component exceeds agreed line threshold without a documented exception.
- settings async behavior remains covered.

## Architecture Tests To Add

The refactor should add executable frontend architecture checks, not rely on this document.

Recommended `settings_ui/tests/frontend-architecture.test.ts` checks:

1. Production frontend file line limits:
   - `settings_ui/src/editor-inline/*.ts`: target max 500 after refactor
   - `settings_ui/src/editor-inline/*.svelte`: target max 300
   - `settings_ui/src/lib/*.ts`: target max 300, generated excluded
   - temporary allowlist for current `actions.ts` until phases complete
2. Export count limits:
   - target max 25 exports per hand-maintained module
   - temporary allowlist for current `actions.ts`
3. Side-effect ownership:
   - `pycmd` only in `src/lib/bridge.ts` and `src/editor-inline/bridge.ts`
   - `window.__aqe*` assignment only in runtime/window-contract modules
   - `document.querySelector*` only in scanner/selector/renderer modules, with temporary allowlist
   - `requestAnimationFrame` only in playback/audio test driver modules
   - `HTMLAudioElement.play/pause/load/currentTime` only in audio-clock/playback modules
4. Test helper isolation:
   - `ForTest` exports only from `test-contract.ts` or test files
   - `__aqe*ForTest` window assignments only in test-contract installation
5. Unused helper check:
   - fail if `src/lib/utils.ts` remains unimported, or delete it

Recommended Python architecture additions:

1. Extend Rule 3 or add a new rule to compare:
   - Python `BRIDGE_COMMANDS`
   - frontend `COMMAND_BUTTONS`
   - frontend command dispatch table/classification
2. Add a window-contract extraction test if practical:
   - TypeScript `globals.d.ts`
   - `runtime.ts` installation
   - Python tests that expect injected names in `tests/test_editor_ui.py`

## Behavioral Tests To Preserve Or Add

### Existing High-Value Tests To Preserve

Keep these green throughout every phase:

- `settings_ui/tests/editor-inline.integration.test.ts`
- `settings_ui/tests/editor-inline.actions.test.ts`
- `settings_ui/tests/editor-inline.edges.test.ts`
- `settings_ui/tests/editor-inline.plot.test.ts`
- `tests/test_editor_integration.py`
- `tests/test_editor_ui.py`
- `e2e/test_editor_graph_workflow.py`
- `e2e/test_editor_playback_workflow.py`
- `e2e/test_editor_region_loop_workflow.py`
- `e2e/test_editor_processing_workflow.py`
- `e2e/test_editor_deep_filter_workflow.py`

### New Characterization Tests Before Refactor

Add these before moving code:

1. `buildPlaybackRequestForPython` cases:
   - stopped/full
   - stopped/selection
   - playing/pause
   - paused/resume
   - paused/outside-selection restart
   - repeat enabled
   - native fallback
2. State projection cases:
   - graph requested
   - graph rendered
   - graph failed
   - note reset
   - processing command lock/unlock
3. Selection cases:
   - tiny selection threshold
   - reversed drag normalization
   - draft cancel
   - committed selection survival
   - multi-field isolation
4. Audio clock cases:
   - source setup encodes filename and preserves nested media slashes
   - load failure marks fallback
   - seek failure marks fallback
   - play rejection path
   - ended loop path
5. Bridge cases:
   - pending playback request is popped once
   - cursor intent survives until Python reads it
   - frontend log queue order is FIFO

### New E2E Tests To Consider

Add only if not already covered after reviewing current e2e behavior:

1. HTML playback succeeds, then Python receives `engine: "html"` only after browser audio starts.
2. HTML playback fails for full region and falls back to native Anki playback.
3. HTML playback fails for selected repeat and displays a warning without starting native selected playback.
4. Note switch while HTML audio is playing stops frontend clock and clears stale selection.
5. Two audio fields: starting playback in field 2 stops field 1 and preserves field 1 selection state.
6. Redraw during selected repeat stops playback, clears selection on successful graph render, and leaves field usable.
7. Cursor drag during playback restarts at released cursor when browser audio is available.
8. Cursor drag during paused playback marks resume as restart when required.

## Verification Plan For Each Phase

Minimum per phase:

```bash
python3 scripts/dev.py test-svelte
python3 scripts/dev.py test
```

For phases touching Python/frontend bridge, playback, graph callbacks, or field injection:

```bash
python3 scripts/dev.py test-e2e
```

For final merge of this refactor:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```

Before committing refactor changes:

- run GitNexus impact analysis on every function/class/method being changed, per repository policy
- run `gitnexus_detect_changes()` and confirm affected symbols/flows match the intended refactor scope
- if GitNexus reports HIGH or CRITICAL risk, stop and record the mitigation/tests before continuing

## Risk Register

### Playback Regressions

Playback is the highest-risk area. GitNexus marked `startProgressClock(...)` as CRITICAL because it is used by HTML playback, Python playback state callbacks, selected-region playback, and command dispatch.

Mitigation:

- extract pure playback decisions before moving timers/audio element behavior
- preserve e2e playback tests throughout
- keep compatibility wrappers until replacement modules are fully covered

### Window Contract Drift

Python calls frontend functions through string-based `web.eval(...)`, and frontend calls Python through `pycmd(...)`. Static TypeScript imports cannot protect this boundary.

Mitigation:

- add executable window-contract tests
- keep `globals.d.ts`, runtime installation, Python injection tests, and e2e helpers in sync

### Test Helpers Becoming Production API

The current `__aqe*ForTest` helpers are useful but blur the public API surface.

Mitigation:

- move them to `test-contract.ts`
- keep names stable, but install them from a clearly named adapter

### Over-Abstracting Too Early

The code can become harder to follow if the refactor creates many tiny modules before the state model is clear.

Mitigation:

- extract pure state first
- keep wrappers in place
- split modules around actual side-effect boundaries
- avoid adding a state library until local state helpers prove insufficient

### Dataset Compatibility

CSS, tests, and e2e helpers currently observe `dataset` values.

Mitigation:

- keep `dataset` as the rendered projection during refactor
- change source of truth internally without changing visible attributes
- add state projection tests

## Suggested Order Of Work

1. Add frontend architecture tests with temporary allowlists.
2. Delete or test `settings_ui/src/lib/utils.ts`.
3. Add pure state model and tests.
4. Extract selection state and gesture handling.
5. Extract playback state and audio clock handling.
6. Extract visualizer renderer and DOM selectors.
7. Introduce per-field controller registry.
8. Move test-only helpers behind `test-contract.ts`.
9. Split settings UI component if still needed.
10. Tighten architecture allowlists until the new boundaries are enforced.

## Done Criteria

The refactor is complete when:

- `actions.ts` is gone or reduced to a small compatibility shim with a clear removal path.
- No hand-maintained frontend module exceeds the agreed line/export thresholds without an explicit architecture-test allowlist reason.
- State transitions for playback, selection, graph lifecycle, and note reset have pure tests.
- DOM writes are concentrated in renderer modules.
- Audio/timer side effects are concentrated in playback/audio modules.
- `pycmd` and `window.__aqe*` boundaries are executable architecture checks.
- `python3 scripts/dev.py test-svelte` passes.
- `python3 scripts/dev.py test` passes.
- `python3 scripts/dev.py test-e2e` passes.
- GitNexus change detection reports only expected affected frontend/editor flows.

