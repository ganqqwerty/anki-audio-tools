# Editor Region Resize Handles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add visible, draggable edge handles so an existing inline-editor audio selection can be resized without holding Shift.

**Architecture:** Keep the feature inside the existing inline-editor frontend. Add pure resize math to selection state, render SVG handles beside the selected region edges, and route handle pointer events through a resize gesture that reuses draft/commit selection state and existing playback controls.


---

## File Structure

- Modify `settings_ui/src/editor-inline/selection-state.ts`: add pure resize range helpers and exported `SelectionResizeEdge` type.
- Modify `settings_ui/tests/selection-state.test.ts`: unit coverage for preserving the opposite edge, clamping, no edge swapping, minimum duration, and invalid duration.
- Modify `settings_ui/src/editor-inline/EditorControls.svelte`: add two SVG handle elements with stable `data-testid` values and pointerdown handlers.
- Modify `settings_ui/src/editor-inline/visualizer-renderer.ts`: position, show, hide, and draft-hide the handles when selection rendering updates.
- Modify `settings_ui/src/editor-inline/styles.css`: style handle targets and `ew-resize` cursor.
- Modify `settings_ui/src/editor-inline/actions.ts`: expose a thin `startSelectionResizeGesture(...)` wrapper and wire dependencies.
- Modify `settings_ui/src/editor-inline/selection-gestures.ts`: add the resize gesture lifecycle and playback interruption/restart behavior.
- Modify `settings_ui/tests/editor-inline.integration.helpers.ts`: add handle pointer helpers for frontend integration tests.
- Modify `settings_ui/tests/editor-inline.selection.integration.test.ts`: frontend interaction coverage for handle visibility, handle drag, cancellation, and graph gesture isolation.
- Modify `settings_ui/tests/editor-inline.selection-playback.integration.test.ts`: frontend playback coverage for resize while stopped, playing, paused, and repeating.
- Modify `settings_ui/src/editor-inline/types.ts`: extend `GraphStateForTest` with handle visibility and position fields for e2e assertions.
- Modify `settings_ui/src/editor-inline/test-contract.ts`: expose handle visibility and positions in `__aqeGraphStateForTest`.
- Modify `e2e/editor_region_loop_helpers.py`: add handle drag helpers that dispatch pointer events to the SVG handle elements.
- Add `e2e/test_editor_region_resize_workflow.py`: selected-region resize e2e coverage including playback and delete-region consumers.


Pre-plan impact checks already run on 2026-05-19:

- `startSelectionGesture` in `settings_ui/src/editor-inline/selection-gestures.ts`: LOW risk, 1 direct caller (`handleVisualizerPointerDown`).
- `handleVisualizerPointerDown` in `settings_ui/src/editor-inline/selection-gestures.ts`: LOW risk, no upstream callers detected.
- `renderSelection` in `settings_ui/src/editor-inline/visualizer-renderer.ts`: LOW risk, no upstream callers detected by the index.
- `setSelection` in `settings_ui/src/editor-inline/selection-controller.ts`: LOW risk, 1 direct caller (`commitSelectionDraft`).
- `normalizeSelectionRange` in `settings_ui/src/editor-inline/selection-state.ts`: LOW risk, 4 direct callers plus `commitDraftSelectionState`.


### Task 1: Pure Resize Math

**Files:**
- Modify: `settings_ui/tests/selection-state.test.ts`
- Modify: `settings_ui/src/editor-inline/selection-state.ts`



```json
{
  "repo": "anki-audio-tools",
  "target": "normalizeSelectionRange",
  "file_path": "settings_ui/src/editor-inline/selection-state.ts",
  "kind": "Function",
  "direction": "upstream",
  "maxDepth": 3,
  "includeTests": true
}
```

Expected: LOW risk. Direct callers include `selectionRegion`, `draftSelectionRegion`, `setSelectionRange`, and `setDraftSelectionRange`.

- [ ] **Step 2: Write failing unit tests for resize math**

Add `resizeSelectionRange` to the import list in `settings_ui/tests/selection-state.test.ts`:

```ts
import {
  clearDraftSelectionState,
  commitDraftSelectionState,
  draftSelectionRegion,
  emptySelectionState,
  normalizeSelectionRange,
  resizeSelectionRange,
  selectionRegion,
  setDraftSelectionRange,
  setSelectionRange,
  shouldTreatSelectionGestureAsClick,
} from "../src/editor-inline/selection-state.js";
```

Add these tests inside `describe("selection state", () => { ... })`:

```ts
  it("resizes selection edges while preserving the opposite edge", () => {
    expect(resizeSelectionRange({ startMs: 500, endMs: 1250 }, "start", 250, 2000)).toEqual({
      startMs: 250,
      endMs: 1250,
    });
    expect(resizeSelectionRange({ startMs: 500, endMs: 1250 }, "end", 1500, 2000)).toEqual({
      startMs: 500,
      endMs: 1500,
    });
  });

  it("clamps resized edges to duration without swapping handle roles", () => {
    expect(resizeSelectionRange({ startMs: 500, endMs: 1250 }, "start", -200, 2000)).toEqual({
      startMs: 0,
      endMs: 1250,
    });
    expect(resizeSelectionRange({ startMs: 500, endMs: 1250 }, "end", 2500, 2000)).toEqual({
      startMs: 500,
      endMs: 2000,
    });
    expect(resizeSelectionRange({ startMs: 500, endMs: 1250 }, "start", 1500, 2000)).toEqual({
      startMs: 1200,
      endMs: 1250,
    });
    expect(resizeSelectionRange({ startMs: 500, endMs: 1250 }, "end", 300, 2000)).toEqual({
      startMs: 500,
      endMs: 550,
    });
  });

  it("rejects resized selections when audio duration cannot contain the minimum region", () => {
    expect(resizeSelectionRange({ startMs: 0, endMs: 30 }, "end", 30, 30)).toBeNull();
    expect(resizeSelectionRange({ startMs: 0, endMs: 500 }, "end", 500, 0)).toBeNull();
  });
```

- [ ] **Step 3: Run the unit test and verify it fails**

Run:

```bash
cd settings_ui
npm run test -- selection-state.test.ts
```

Expected: FAIL with an export/import error for `resizeSelectionRange`.

- [ ] **Step 4: Implement pure resize math**

Add this type and function to `settings_ui/src/editor-inline/selection-state.ts` after `normalizeSelectionRange(...)`:

```ts
export type SelectionResizeEdge = "end" | "start";

export function resizeSelectionRange(
  selection: SelectionRange,
  edge: SelectionResizeEdge,
  edgeMs: number,
  durationMs: number,
  minDurationMs = MIN_SELECTION_DURATION_MS,
): SelectionRange | null {
  const duration = Math.max(0, Number(durationMs) || 0);
  const minimum = Math.max(0, Number(minDurationMs) || 0);
  if (!duration || duration < minimum) return null;

  const start = clampMs(selection.startMs, duration);
  const end = clampMs(selection.endMs, duration);

  if (edge === "start") {
    const fixedEnd = Math.max(minimum, end);
    const resizedStart = Math.min(clampMs(edgeMs, duration), fixedEnd - minimum);
    return {
      startMs: Math.round(Math.max(0, resizedStart)),
      endMs: Math.round(fixedEnd),
    };
  }

  const fixedStart = Math.min(start, duration - minimum);
  const resizedEnd = Math.max(clampMs(edgeMs, duration), fixedStart + minimum);
  return {
    startMs: Math.round(fixedStart),
    endMs: Math.round(Math.min(duration, resizedEnd)),
  };
}
```

- [ ] **Step 5: Run the unit test and verify it passes**

Run:

```bash
cd settings_ui
npm run test -- selection-state.test.ts
```

Expected: PASS for all `selection-state.test.ts` tests.



```json
{
  "repo": "anki-audio-tools",
  "scope": "all"
}
```

Expected: changed symbols are limited to `selection-state.ts` and `selection-state.test.ts`.

- [ ] **Step 7: Commit Task 1**

```bash
git add settings_ui/src/editor-inline/selection-state.ts settings_ui/tests/selection-state.test.ts
git commit -m "Add selection resize range math"
```

### Task 2: Render Visible Edge Handles

**Files:**
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/src/editor-inline/visualizer-renderer.ts`
- Modify: `settings_ui/src/editor-inline/styles.css`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `settings_ui/src/editor-inline/test-contract.ts`
- Modify: `settings_ui/tests/editor-inline.selection.integration.test.ts`



```json
{
  "repo": "anki-audio-tools",
  "target": "renderSelection",
  "file_path": "settings_ui/src/editor-inline/visualizer-renderer.ts",
  "kind": "Function",
  "direction": "upstream",
  "maxDepth": 3,
  "includeTests": true
}
```

Expected: LOW risk.

- [ ] **Step 2: Write failing integration assertions for handle visibility**

In `settings_ui/tests/editor-inline.selection.integration.test.ts`, extend the first test after the existing band visibility assertions:

```ts
    const startHandle = document.querySelector('[data-testid="aqe-selection-resize-start-0"]')!;
    const endHandle = document.querySelector('[data-testid="aqe-selection-resize-end-0"]')!;

    dragGraphSelection(svg, 0.2, 0.6);
    expect(startHandle).toHaveAttribute("visibility", "visible");
    expect(endHandle).toHaveAttribute("visibility", "visible");
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartHandleVisible: true,
      selectionEndHandleVisible: true,
    });

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.5), true);
    dispatchGraphPointer(svg, "pointerup", graphClientX(svg, 0.5), true);
    expect(startHandle).toHaveAttribute("visibility", "hidden");
    expect(endHandle).toHaveAttribute("visibility", "hidden");
```

Keep the existing selection creation/clear assertions in that test. If the repeated `dragGraphSelection(...)` makes the test awkward, split the handle assertions into a new `it("shows resize handles only for committed selections", () => { ... })` test with the same setup.

- [ ] **Step 3: Run the integration test and verify it fails**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.selection.integration.test.ts
```

Expected: FAIL because the `aqe-selection-resize-start-0` and `aqe-selection-resize-end-0` elements do not exist.

- [ ] **Step 4: Add handle elements to the SVG**

In `settings_ui/src/editor-inline/EditorControls.svelte`, add these two `rect` elements after the existing selection edge lines and before the cursor line:

```svelte
      <rect
        class="aqe-selection-resize-handle aqe-selection-resize-start"
        data-testid={`aqe-selection-resize-start-${target.ord}`}
        x={PLOT.left - 5}
        y={PLOT.top}
        width="10"
        height={PLOT.height - PLOT.top - PLOT.bottom}
        rx="3"
        visibility="hidden"
        onpointerdown={(event) => startSelectionResizeGesture(event, target.ord, "start")}
      ></rect>
      <rect
        class="aqe-selection-resize-handle aqe-selection-resize-end"
        data-testid={`aqe-selection-resize-end-${target.ord}`}
        x={PLOT.left - 5}
        y={PLOT.top}
        width="10"
        height={PLOT.height - PLOT.top - PLOT.bottom}
        rx="3"
        visibility="hidden"
        onpointerdown={(event) => startSelectionResizeGesture(event, target.ord, "end")}
      ></rect>
```

Also update the import from `./actions.js` at the top of the file so it includes `startSelectionResizeGesture`:

```ts
import {
  handleCommand,
  handleSplitOptionChange,
  handleSplitValueChange,
  handleVisualizerKeyDown,
  handleVisualizerPointerDown,
  startSelectionResizeGesture,
  toggleRepeat,
} from "./actions.js";
```

- [ ] **Step 5: Update renderer positioning**

In `settings_ui/src/editor-inline/visualizer-renderer.ts`, update `renderSelection(...)` so it queries and renders handles. The function body should use this structure:

```ts
export function renderSelection(
  visualizer: VisualizerElement,
  selection: PlaybackRegion | null,
  draftSelection: PlaybackRegion | null,
): void {
  const band = visualizer.querySelector<SVGRectElement>(".aqe-selection");
  const startEdge = visualizer.querySelector<SVGLineElement>(".aqe-selection-start");
  const endEdge = visualizer.querySelector<SVGLineElement>(".aqe-selection-end");
  const startHandle = visualizer.querySelector<SVGRectElement>(".aqe-selection-resize-start");
  const endHandle = visualizer.querySelector<SVGRectElement>(".aqe-selection-resize-end");
  const handles = [startHandle, endHandle].filter((handle): handle is SVGRectElement => handle !== null);
  const activeSelection = draftSelection ?? selection;
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  if (!band || !startEdge || !endEdge || !activeSelection || !durationMs) {
    band?.setAttribute("width", "0");
    band?.setAttribute("visibility", "hidden");
    band?.classList.remove("aqe-selection-draft");
    startEdge?.setAttribute("visibility", "hidden");
    endEdge?.setAttribute("visibility", "hidden");
    for (const handle of handles) {
      handle.setAttribute("visibility", "hidden");
    }
    return;
  }
  const startX = xForMs(activeSelection.startMs, durationMs);
  const endX = xForMs(activeSelection.endMs, durationMs);
  const showHandles = selection !== null && draftSelection === null;
  band.setAttribute("visibility", "visible");
  band.classList.toggle("aqe-selection-draft", draftSelection !== null);
  band.setAttribute("x", startX.toFixed(2));
  band.setAttribute("y", String(PLOT.top));
  band.setAttribute("width", Math.max(0, endX - startX).toFixed(2));
  band.setAttribute("height", String(PLOT.height - PLOT.top - PLOT.bottom));
  startEdge.setAttribute("visibility", "visible");
  endEdge.setAttribute("visibility", "visible");
  for (const [edge, x] of [[startEdge, startX], [endEdge, endX]] as const) {
    edge.setAttribute("x1", x.toFixed(2));
    edge.setAttribute("x2", x.toFixed(2));
    edge.setAttribute("y1", String(PLOT.top));
    edge.setAttribute("y2", String(PLOT.height - PLOT.bottom));
  }
  for (const [handle, x] of [[startHandle, startX], [endHandle, endX]] as const) {
    if (!handle) continue;
    handle.setAttribute("visibility", showHandles ? "visible" : "hidden");
    handle.setAttribute("x", (x - 5).toFixed(2));
    handle.setAttribute("y", String(PLOT.top));
    handle.setAttribute("width", "10");
    handle.setAttribute("height", String(PLOT.height - PLOT.top - PLOT.bottom));
  }
}
```

- [ ] **Step 6: Add handle state to the test contract**

In `settings_ui/src/editor-inline/types.ts`, add these fields to `GraphStateForTest`:

```ts
  selectionEndHandleVisible: boolean;
  selectionEndHandleX: number | null;
  selectionStartHandleVisible: boolean;
  selectionStartHandleX: number | null;
```

In `settings_ui/src/editor-inline/test-contract.ts`, add handle lookups before the returned object:

```ts
  const startHandle = visualizer.querySelector<SVGRectElement>(".aqe-selection-resize-start");
  const endHandle = visualizer.querySelector<SVGRectElement>(".aqe-selection-resize-end");
```

Then add these fields to the returned object:

```ts
    selectionStartHandleVisible: startHandle?.getAttribute("visibility") === "visible",
    selectionStartHandleX: startHandle?.getAttribute("x") ? Number(startHandle.getAttribute("x")) : null,
    selectionEndHandleVisible: endHandle?.getAttribute("visibility") === "visible",
    selectionEndHandleX: endHandle?.getAttribute("x") ? Number(endHandle.getAttribute("x")) : null,
```

- [ ] **Step 7: Style the handles**

Add to `settings_ui/src/editor-inline/styles.css` after `.aqe-selection-edge`:

```css
.aqe-selection-resize-handle {
  cursor: ew-resize;
  fill: ButtonFace;
  opacity: 0.92;
  pointer-events: auto;
  stroke: currentColor;
  stroke-width: 1;
}

.aqe-selection-resize-handle:hover {
  fill: Highlight;
}
```

- [ ] **Step 8: Add a temporary no-op action export so the build reaches renderer tests**

In `settings_ui/src/editor-inline/actions.ts`, import the type:

```ts
import type { SelectionResizeEdge } from "./selection-state.js";
```

Add this exported function near `startSelectionGesture(...)`:

```ts
export function startSelectionResizeGesture(
  event: PointerEvent,
  _ord: number,
  _edge: SelectionResizeEdge,
): void {
  event.preventDefault();
  event.stopPropagation();
}
```

This function is intentionally minimal in this task. Task 3 replaces it with real resize behavior.

- [ ] **Step 9: Run the frontend tests and verify handle rendering passes**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.selection.integration.test.ts
npm run check
```

Expected: PASS.



```json
{
  "repo": "anki-audio-tools",
  "scope": "all"
}
```

Expected: changed symbols are limited to inline-editor rendering/action/test contract files plus the integration test.

- [ ] **Step 11: Commit Task 2**

```bash
git add settings_ui/src/editor-inline/EditorControls.svelte settings_ui/src/editor-inline/actions.ts settings_ui/src/editor-inline/styles.css settings_ui/src/editor-inline/test-contract.ts settings_ui/src/editor-inline/types.ts settings_ui/src/editor-inline/visualizer-renderer.ts settings_ui/tests/editor-inline.selection.integration.test.ts
git commit -m "Show selected region resize handles"
```

### Task 3: Stopped-State Resize Gesture

**Files:**
- Modify: `settings_ui/tests/editor-inline.integration.helpers.ts`
- Modify: `settings_ui/tests/editor-inline.selection.integration.test.ts`
- Modify: `settings_ui/src/editor-inline/actions.ts`
- Modify: `settings_ui/src/editor-inline/selection-gestures.ts`



```json
{
  "repo": "anki-audio-tools",
  "target": "startSelectionGesture",
  "file_path": "settings_ui/src/editor-inline/selection-gestures.ts",
  "kind": "Function",
  "direction": "upstream",
  "maxDepth": 3,
  "includeTests": true
}
```

```json
{
  "repo": "anki-audio-tools",
  "target": "handleVisualizerPointerDown",
  "file_path": "settings_ui/src/editor-inline/selection-gestures.ts",
  "kind": "Function",
  "direction": "upstream",
  "maxDepth": 3,
  "includeTests": true
}
```

Expected: LOW risk for both.

- [ ] **Step 2: Add frontend helper functions for dragging handles**

In `settings_ui/tests/editor-inline.integration.helpers.ts`, add:

```ts
export function dispatchHandlePointer(handle: Element, type: string, clientX: number): void {
  const EventCtor = window.PointerEvent || window.MouseEvent;
  const event = new EventCtor(type, {
    bubbles: true,
    clientX,
    clientY: 20,
  });
  if (type === "pointerdown") {
    handle.dispatchEvent(event);
    return;
  }
  window.dispatchEvent(event);
}

export function dragSelectionHandle(svg: SVGSVGElement, edge: "end" | "start", endRatio: number, ord = 0): void {
  const handle = document.querySelector(`[data-testid="aqe-selection-resize-${edge}-${ord}"]`)!;
  dispatchHandlePointer(handle, "pointerdown", graphClientX(svg, edge === "start" ? 0.2 : 0.6));
  dispatchHandlePointer(handle, "pointermove", graphClientX(svg, endRatio));
  dispatchHandlePointer(handle, "pointerup", graphClientX(svg, endRatio));
}
```

- [ ] **Step 3: Write failing stopped-state resize tests**

In `settings_ui/tests/editor-inline.selection.integration.test.ts`, add `dragSelectionHandle` to the helper imports:

```ts
  dragSelectionHandle,
```

Add these tests before the final normal click/drag test:

```ts
  it("resizes committed selections by dragging visible handles without Shift", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    dragSelectionHandle(svg, "start", 0.1);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 100,
      selectionEndMs: 600,
      selectionDraftActive: false,
      cursorMs: 100,
      playbackStartMs: 100,
      playbackEndMs: 600,
      playButtonLabel: "Play",
    });

    dragSelectionHandle(svg, "end", 0.8);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 100,
      selectionEndMs: 800,
      cursorMs: 100,
      playbackStartMs: 100,
      playbackEndMs: 800,
      playButtonLabel: "Play",
    });
  });

  it("clamps handle drags at the minimum duration without swapping edges", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    dragSelectionHandle(svg, "start", 0.8);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 550,
      selectionEndMs: 600,
    });

    dragSelectionHandle(svg, "end", 0.1);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 550,
      selectionEndMs: 600,
    });
  });

  it("cancels resize drafts without replacing the committed selection", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);
    const handle = document.querySelector('[data-testid="aqe-selection-resize-end-0"]')!;

    dispatchHandlePointer(handle, "pointerdown", graphClientX(svg, 0.6));
    dispatchHandlePointer(handle, "pointermove", graphClientX(svg, 0.9));
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 200,
      selectionEndMs: 600,
      selectionDraftActive: true,
      selectionDraftStartMs: 200,
      selectionDraftEndMs: 900,
    });

    window.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "Escape" }));
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 200,
      selectionEndMs: 600,
      selectionDraftActive: false,
    });
  });
```

Also add `dispatchHandlePointer` to the import list for the cancellation test.

- [ ] **Step 4: Run the integration test and verify it fails**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.selection.integration.test.ts
```

Expected: FAIL because the handle pointerdown no-op does not update draft or committed selection state.

- [ ] **Step 5: Extend gesture dependencies**

In `settings_ui/src/editor-inline/selection-gestures.ts`, update imports:

```ts
import {
  resizeSelectionRange,
  shouldTreatSelectionGestureAsClick,
  type SelectionResizeEdge,
} from "./selection-state.js";
```

Add no new dependency methods yet; the existing `selectionForVisualizer`, `setSelectionDraft`, and `commitSelectionDraft` are enough for stopped-state behavior.

- [ ] **Step 6: Implement resize gesture lifecycle**

Add this function to `settings_ui/src/editor-inline/selection-gestures.ts` after `startSelectionGesture(...)`:

```ts
export function startSelectionResizeGesture(
  event: PointerEvent,
  visualizer: VisualizerElement,
  ord: number,
  edge: SelectionResizeEdge,
  deps: SelectionGestureDependencies,
): void {
  event.preventDefault();
  event.stopPropagation();
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const selection = deps.selectionForVisualizer(visualizer);
  if (!svg || !durationMs || !selection) return;

  const previousPlaybackState = deps.playbackStateFor(visualizer);
  const frozenProgressMs = deps.currentProgressMs(visualizer) ?? Number(visualizer.dataset.cursorMs || "0");
  let stoppedForDrag = false;
  let move = (_moveEvent: PointerEvent): void => {};
  let up = (_upEvent: PointerEvent): void => {};
  let cancel = (): void => {};
  let keydown = (_keyEvent: KeyboardEvent): void => {};

  const cleanup = (): void => {
    window.removeEventListener("pointermove", move);
    window.removeEventListener("pointerup", up);
    window.removeEventListener("pointercancel", cancel);
    window.removeEventListener("keydown", keydown);
    window.removeEventListener("blur", cancel);
    svg.removeEventListener("lostpointercapture", cancel);
  };
  const stopForDrag = (): void => {
    if (stoppedForDrag || previousPlaybackState !== "playing") return;
    stoppedForDrag = true;
    deps.stopProgressClock(visualizer, { clearEngine: false });
    deps.setCursor(visualizer, frozenProgressMs, false, { updateAnchor: false });
  };
  const resizedRangeFor = (pointerEvent: PointerEvent): PlaybackRegion | null => {
    const resized = resizeSelectionRange(selection, edge, cursorMsFromEvent(pointerEvent, svg, durationMs), durationMs);
    return resized ? { ...resized, mode: "selection" } : null;
  };

  move = (moveEvent: PointerEvent): void => {
    const resized = resizedRangeFor(moveEvent);
    if (!resized) {
      deps.clearSelectionDraft(visualizer);
      return;
    }
    stopForDrag();
    deps.setSelectionDraft(visualizer, resized.startMs, resized.endMs);
  };
  up = (upEvent: PointerEvent): void => {
    cleanup();
    const resized = resizedRangeFor(upEvent);
    if (!resized) {
      deps.clearSelectionDraft(visualizer);
      return;
    }
    stopForDrag();
    deps.setSelectionDraft(visualizer, resized.startMs, resized.endMs, { redraw: false });
    const selected = deps.commitSelectionDraft(visualizer);
    if (previousPlaybackState === "paused") {
      visualizer.dataset.resumeRequiresRestart = "true";
    }
    if (selected && previousPlaybackState === "playing") {
      const committed = deps.selectionForVisualizer(visualizer);
      deps.startEditorHtmlPlayback(
        visualizer,
        deps.playbackRequestForStart(visualizer, ord, committed?.startMs ?? resized.startMs, "html"),
      );
    }
  };
  cancel = (): void => {
    cleanup();
    deps.clearSelectionDraft(visualizer);
    if (previousPlaybackState === "playing" && stoppedForDrag) {
      deps.startEditorHtmlPlayback(
        visualizer,
        deps.playbackRequestForStart(visualizer, ord, frozenProgressMs, "html"),
      );
    }
  };
  keydown = (keyEvent: KeyboardEvent): void => {
    if (keyEvent.key === "Escape") {
      cancel();
    }
  };

  stopForDrag();
  window.addEventListener("pointermove", move);
  window.addEventListener("pointerup", up);
  window.addEventListener("pointercancel", cancel);
  window.addEventListener("keydown", keydown);
  window.addEventListener("blur", cancel);
  svg.addEventListener("lostpointercapture", cancel);
}
```

- [ ] **Step 7: Replace the no-op action wrapper**

In `settings_ui/src/editor-inline/actions.ts`, add this import from `selection-gestures.ts`:

```ts
  startSelectionResizeGesture as startSelectionResizeGestureFlow,
```

Replace the no-op `startSelectionResizeGesture(...)` with:

```ts
export function startSelectionResizeGesture(
  event: PointerEvent,
  ord: number,
  edge: SelectionResizeEdge,
): void {
  visualizerForOrd(ord)?.focus();
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return;
  startSelectionResizeGestureFlow(event, visualizer, ord, edge, selectionGestureDependencies());
}
```

- [ ] **Step 8: Run stopped-state frontend tests**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.selection.integration.test.ts selection-state.test.ts
npm run check
```

Expected: PASS.



```json
{
  "repo": "anki-audio-tools",
  "scope": "all"
}
```

Expected: changed symbols are in `selection-gestures.ts`, `actions.ts`, frontend test helpers, and frontend selection tests.

- [ ] **Step 10: Commit Task 3**

```bash
git add settings_ui/src/editor-inline/actions.ts settings_ui/src/editor-inline/selection-gestures.ts settings_ui/tests/editor-inline.integration.helpers.ts settings_ui/tests/editor-inline.selection.integration.test.ts
git commit -m "Resize selected regions from edge handles"
```

### Task 4: Playback-Aware Resize Integration

**Files:**
- Modify: `settings_ui/tests/editor-inline.selection-playback.integration.test.ts`
- Modify: `settings_ui/src/editor-inline/selection-gestures.ts`

- [ ] **Step 1: Write failing playback resize tests**

In `settings_ui/tests/editor-inline.selection-playback.integration.test.ts`, add these imports from `./editor-inline.integration.helpers.js`:

```ts
  dispatchHandlePointer,
  dragSelectionHandle,
```

Add these tests before the multi-field isolation test:

```ts
  it("freezes active selected playback during resize and restarts from the resized start", async () => {
    const frames = mockAnimationFrames();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.25, 0.75);
    const audio = prepareHtmlAudio();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    audio.currentTime = 0.5;
    frames.shift()?.(performance.now() + 500);
    const handle = document.querySelector('[data-testid="aqe-selection-resize-end-0"]')!;

    dispatchHandlePointer(handle, "pointerdown", graphClientX(svg, 0.75));
    dispatchHandlePointer(handle, "pointermove", graphClientX(svg, 0.9));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "stopped",
      cursorMs: 500,
      selectionDraftActive: true,
      selectionDraftStartMs: 250,
      selectionDraftEndMs: 900,
    });

    dispatchHandlePointer(handle, "pointerup", graphClientX(svg, 0.9));
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      playButtonLabel: "Pause",
      cursorMs: 250,
      selectionStartMs: 250,
      selectionEndMs: 900,
      playbackStartMs: 250,
      playbackEndMs: 900,
      playbackRegionMode: "selection",
    });
    expect(audio.play).toHaveBeenCalledTimes(2);
  });

  it("keeps paused playback paused after resize and requires restart from resized start", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.25, 0.75);
    window.__aqeSetPlaybackState?.(0, "paused", 500);

    dragSelectionHandle(svg, "start", 0.1);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "paused",
      playButtonLabel: "Play",
      resumeRequiresRestart: true,
      selectionStartMs: 100,
      selectionEndMs: 750,
      playbackStartMs: 100,
      playbackEndMs: 750,
    });

    const audio = prepareHtmlAudio();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      cursorMs: 100,
      playbackStartMs: 100,
      playbackEndMs: 750,
    });
    expect(audio.play).toHaveBeenCalledTimes(1);
  });

  it("uses resized repeat boundaries after handle resize", async () => {
    const frames = mockAnimationFrames();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.25, 0.75);
    dragSelectionHandle(svg, "end", 0.9);
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-repeat-0"]')!.click();
    const audio = prepareHtmlAudio();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    audio.currentTime = 0.91;
    frames.shift()?.(performance.now() + 900);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      cursorMs: 250,
      playbackStartMs: 250,
      playbackEndMs: 900,
      repeatEnabled: true,
    });
  });
```

- [ ] **Step 2: Run playback tests and verify the failure**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.selection-playback.integration.test.ts
```

Expected: At least the active playback test fails if the Task 3 implementation does not preserve play button state or restart from the resized selection start.

- [ ] **Step 3: Confirm resize gesture playback behavior**

If the Task 3 implementation does not pass these tests, edit only `settings_ui/src/editor-inline/selection-gestures.ts`. The required release branch is:

```ts
    const selected = deps.commitSelectionDraft(visualizer);
    if (previousPlaybackState === "paused") {
      visualizer.dataset.resumeRequiresRestart = "true";
    }
    if (selected && previousPlaybackState === "playing") {
      const committed = deps.selectionForVisualizer(visualizer);
      deps.startEditorHtmlPlayback(
        visualizer,
        deps.playbackRequestForStart(visualizer, ord, committed?.startMs ?? resized.startMs, "html"),
      );
    }
```

The required pointer-down/move behavior is:

```ts
  const stopForDrag = (): void => {
    if (stoppedForDrag || previousPlaybackState !== "playing") return;
    stoppedForDrag = true;
    deps.stopProgressClock(visualizer, { clearEngine: false });
    deps.setCursor(visualizer, frozenProgressMs, false, { updateAnchor: false });
  };
```

- [ ] **Step 4: Run playback and selection tests**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.selection-playback.integration.test.ts editor-inline.selection.integration.test.ts
```

Expected: PASS.



```json
{
  "repo": "anki-audio-tools",
  "scope": "all"
}
```

Expected: changed symbols remain limited to selection gesture and playback integration test files.

- [ ] **Step 6: Commit Task 4**

```bash
git add settings_ui/src/editor-inline/selection-gestures.ts settings_ui/tests/editor-inline.selection-playback.integration.test.ts
git commit -m "Keep playback coherent while resizing selections"
```

### Task 5: E2E Resize Coverage

**Files:**
- Modify: `e2e/editor_region_loop_helpers.py`
- Add: `e2e/test_editor_region_resize_workflow.py`

- [ ] **Step 1: Add e2e handle pointer helpers**

In `e2e/editor_region_loop_helpers.py`, add:

```py
def _selection_handle_pointer_event_script(
    ord_: int,
    edge: str,
    ratio: float,
    event_type: str,
) -> str:
    target = "handle" if event_type == "pointerdown" else "window"
    return f"""
    (() => {{
      const ord = {ord_};
      const edge = {edge!r};
      const ratio = {ratio};
      const handle = document.querySelector(`[data-testid="aqe-selection-resize-${{edge}}-${{ord}}"]`);
      const svg = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${{ord}}"] .aqe-visualizer-svg`);
      const rect = svg.getBoundingClientRect();
      const plot = {{ width: 620, left: 44, right: 10 }};
      const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
      const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
      const x = plotLeft + plotWidth * ratio;
      const EventCtor = window.PointerEvent || window.MouseEvent;
      {target}.dispatchEvent(new EventCtor("{event_type}", {{
        bubbles: true,
        clientX: x,
        clientY: rect.top + 20,
      }}));
    }})()
    """


def _resize_handle_down(editor, edge: str, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _selection_handle_pointer_event_script(ord_, edge, ratio, "pointerdown"))


def _resize_handle_move(editor, edge: str, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _selection_handle_pointer_event_script(ord_, edge, ratio, "pointermove"))


def _resize_handle_up(editor, edge: str, ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _selection_handle_pointer_event_script(ord_, edge, ratio, "pointerup"))


def _drag_resize_handle(editor, edge: str, start_ratio: float, end_ratio: float, ord_: int = 0) -> None:
    _resize_handle_down(editor, edge, start_ratio, ord_)
    _resize_handle_move(editor, edge, end_ratio, ord_)
    _resize_handle_up(editor, edge, end_ratio, ord_)
```

- [ ] **Step 2: Write e2e tests for resize gestures and consumers**

Create `e2e/test_editor_region_resize_workflow.py` with:

```py
"""E2E tests for resizing selected inline graph regions."""

from __future__ import annotations

import time

from e2e.editor_graph_helpers import _wait_for_html_playback
from e2e.editor_note_helpers import _button_selector, _sound_filename, _wait_for_generated_mp3
from e2e.editor_playback_helpers import PLAYBACK_INTERVAL_TOLERANCE_MS, _record_fake_playback
from e2e.editor_region_loop_helpers import (
    _drag_resize_handle,
    _force_repeat_wrap,
    _normal_drag,
    _open_tone_editor,
    _resize_handle_down,
    _resize_handle_move,
    _resize_handle_up,
    _set_repeat,
    _shift_drag_region,
    _state,
)
from e2e.helpers import click_selector, wait_for_condition


def test_resize_handles_update_stopped_selection_and_preserve_graph_gestures(anki_mw, ffmpeg_config) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_resize_stopped.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.625)
        selected = _state(
            editor,
            lambda state: state["selectionStartMs"] == 500
            and state["selectionEndMs"] == 1250
            and state["selectionStartHandleVisible"] is True
            and state["selectionEndHandleVisible"] is True,
        )
        assert selected["playButtonLabel"] == "Play"

        _drag_resize_handle(editor, "end", 0.625, 0.75)
        right_resized = _state(
            editor,
            lambda state: state["selectionStartMs"] == 500
            and state["selectionEndMs"] == 1500
            and state["playbackEndMs"] == 1500,
        )
        assert right_resized["cursorMs"] == 500

        _drag_resize_handle(editor, "start", 0.25, 0.125)
        left_resized = _state(
            editor,
            lambda state: state["selectionStartMs"] == 250
            and state["selectionEndMs"] == 1500
            and state["cursorMs"] == 250,
        )
        assert left_resized["playButtonLabel"] == "Play"

        _normal_drag(editor, 0.9, 0.9)
        scrubbed = _state(editor, lambda state: 1750 <= state["cursorMs"] <= 1850)
        assert scrubbed["selectionStartMs"] == 250
        assert scrubbed["selectionEndMs"] == 1500

        _shift_drag_region(editor, 0.1, 0.3)
        replaced = _state(
            editor,
            lambda state: state["selectionStartMs"] == 200
            and state["selectionEndMs"] == 600,
        )
        assert replaced["selectionStartHandleVisible"] is True
    finally:
        editor.set_note(None)
        parent.close()


def test_resize_while_playing_restarts_progress_from_resized_region_start(anki_mw, ffmpeg_config) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_resize_playing.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.65)
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 650)

            _resize_handle_down(editor, "end", 0.65)
            frozen = _state(editor, lambda state: state["playbackState"] == "stopped")
            _resize_handle_move(editor, "end", 0.85)
            draft = _state(
                editor,
                lambda state: state["selectionDraftActive"] is True
                and state["selectionDraftEndMs"] == 1700,
            )
            frozen_progress = frozen["progressMs"]
            deadline = time.monotonic() + 0.25
            wait_for_condition(
                lambda: time.monotonic() >= deadline,
                timeout=1.0,
                message="resize freeze checkpoint failed",
            )
            still_frozen = _state(editor)
            assert abs(still_frozen["progressMs"] - frozen_progress) <= PLAYBACK_INTERVAL_TOLERANCE_MS * 2
            _resize_handle_up(editor, "end", 0.85)
            restarted = _wait_for_html_playback(
                editor,
                lambda state: state["playbackState"] == "playing"
                and state["playButtonLabel"] == "Pause"
                and state["selectionStartMs"] == 500
                and state["selectionEndMs"] == 1700
                and state["playbackStartMs"] == 500
                and state["playbackEndMs"] == 1700
                and state["audioClockCurrentMs"] >= 500 - PLAYBACK_INTERVAL_TOLERANCE_MS,
            )

        assert playback.attempts == []
        assert frozen["cursorMs"] >= 500
        assert draft["selectionDraftStartMs"] == 500
        assert restarted["cursorMs"] >= 500 - PLAYBACK_INTERVAL_TOLERANCE_MS
    finally:
        editor.set_note(None)
        parent.close()


def test_resize_paused_and_repeat_playback_use_updated_boundaries(anki_mw, ffmpeg_config) -> None:
    media_dir, source, _note, editor, parent, track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_resize_repeat.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.65)
        with _record_fake_playback(
            media_dir,
            {source.name: round(track["durationMs"])},
            ffmpeg_config=ffmpeg_config,
        ) as playback:
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _wait_for_html_playback(editor, lambda state: state["progressMs"] >= 600)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            paused = _state(editor, lambda state: state["playbackState"] == "paused")

            _drag_resize_handle(editor, "start", 0.25, 0.1)
            resized_paused = _state(
                editor,
                lambda state: state["selectionStartMs"] == 200
                and state["selectionEndMs"] == 1300
                and state["playbackState"] == "paused"
                and state["resumeRequiresRestart"] is True,
            )

            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            restarted = _wait_for_html_playback(
                editor,
                lambda state: state["playbackState"] == "playing"
                and state["playbackStartMs"] == 200,
            )
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            _set_repeat(editor, True)
            _drag_resize_handle(editor, "end", 0.65, 0.85)
            click_selector(editor.web, _button_selector("aqe:play"), timeout=5.0)
            looped = _force_repeat_wrap(editor, 200)

        assert playback.attempts == []
        assert paused["playButtonLabel"] == "Play"
        assert resized_paused["playButtonLabel"] == "Play"
        assert restarted["cursorMs"] >= 200 - PLAYBACK_INTERVAL_TOLERANCE_MS
        assert looped["playbackEndMs"] == 1700
    finally:
        editor.set_note(None)
        parent.close()


def test_delete_region_after_resize_uses_resized_range(anki_mw, ffmpeg_config) -> None:
    from anki_audio_quick_editor.audio_processor import AudioProcessingConfig, probe_duration_ms

    media_dir, source, note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_region_resize_delete.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.25, 0.625)
        _drag_resize_handle(editor, "end", 0.625, 0.75)
        selected = _state(
            editor,
            lambda state: state["selectionStartMs"] == 500
            and state["selectionEndMs"] == 1500,
        )
        assert selected["regionDeleteButtonDisabled"] is False

        previous_name = _sound_filename(note.fields[0])
        click_selector(editor.web, _button_selector("aqe:delete-selection"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
        generated_duration = probe_duration_ms(media_dir / generated_name, AudioProcessingConfig.from_config({}))

        assert source.exists()
        assert generated_name.startswith("editor_region_resize_delete__aqe_")
        assert 850 <= generated_duration <= 1150
    finally:
        editor.set_note(None)
        parent.close()
```

- [ ] **Step 3: Run the new e2e file and verify expected failures**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_region_resize_workflow.py
```

Expected before frontend bundle rebuild: FAIL if the generated editor bundle does not include handles.

- [ ] **Step 4: Rebuild frontend bundles**

Run:

```bash
python3 scripts/dev.py build
```

Expected: PASS. Generated bundle files under `addon/anki_audio_quick_editor/templates/` may update locally and remain ignored by git.

- [ ] **Step 5: Run the new e2e file again**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_region_resize_workflow.py
```

Expected: PASS.

- [ ] **Step 6: Run existing region e2e tests affected by resize**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_region_loop_workflow.py e2e/test_editor_region_loop_playback_workflow.py e2e/test_editor_region_delete_workflow.py
```

Expected: PASS.



```json
{
  "repo": "anki-audio-tools",
  "scope": "all"
}
```

Expected: changed execution flows are inline editor selection/playback and e2e helpers/tests.

- [ ] **Step 8: Commit Task 5**

```bash
git add e2e/editor_region_loop_helpers.py e2e/test_editor_region_resize_workflow.py
git commit -m "Cover selected region resize workflows"
```

### Task 6: Final Verification And Cleanup

**Files:**
- Review: all files touched by Tasks 1-5
- No planned source changes unless verification exposes a concrete failure

- [ ] **Step 1: Run frontend validation**

Run:

```bash
cd settings_ui
npm run validate
```

Expected: PASS.

- [ ] **Step 2: Run focused Python/e2e verification**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_region_resize_workflow.py e2e/test_editor_region_loop_workflow.py e2e/test_editor_region_loop_playback_workflow.py e2e/test_editor_region_delete_workflow.py
```

Expected: PASS.

- [ ] **Step 3: Run the repository QC gate**

Run:

```bash
python3 scripts/dev.py check
```

Expected: PASS.



```json
{
  "repo": "anki-audio-tools",
  "scope": "all"
}
```

Expected: changed symbols and affected flows match inline-editor selected region resize, frontend tests, and e2e tests.

- [ ] **Step 5: Summarize implementation state**


Report:

```text
Implemented visible resize handles for selected audio regions.
Verified frontend validation and focused e2e region resize/playback/delete workflows.
```

## Self-Review Notes

Spec coverage:

- Visible handles are covered by Task 2.
- Normal drag on handles and unchanged graph gestures are covered by Task 3 and Task 5.
- Clamp/minimum duration/no handle swapping is covered by Task 1, Task 3, and Task 5.
- Playing, paused, stopped, repeat, progress indicator, and play button behavior are covered by Task 4 and Task 5.
- Delete-region consumer behavior is covered by Task 5.
- No backend contract changes are planned.

Known execution caution:

- The current worktree contains unrelated local modifications. Each task must stage only files listed in that task.
- Generated webview bundles are ignored by git; rebuild them for runtime/e2e verification but do not hand-edit them.
