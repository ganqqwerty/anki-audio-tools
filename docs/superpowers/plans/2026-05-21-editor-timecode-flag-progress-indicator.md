# Editor Timecode Flag Progress Indicator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the plain progress text with an editor-style timecode flag attached to the playback cursor.

**Architecture:** Keep playback state and cursor behavior unchanged. Add SVG flag elements next to the existing `.aqe-cursor`, update them from `renderCursor()`, and keep the existing `.aqe-progress-label` as screen-reader/status text instead of the primary visible UI. Use fixed-size SVG geometry so the flag is stable in Anki WebView and clamp the flag within the plot bounds.

**Tech Stack:** Svelte 5, TypeScript, SVG, Vitest/jsdom, existing Anki editor webview bundle build.

---

## File Structure

- Modify `settings_ui/src/editor-inline/EditorControls.svelte`: add SVG flag group after the cursor line.
- Modify `settings_ui/src/editor-inline/visualizer-renderer.ts`: position the flag, update current/total text, and reset it.
- Modify `settings_ui/src/editor-inline/styles.css`: style the playhead line, flag bubble, notch, and text.
- Modify `settings_ui/tests/editor-inline.plot.test.ts`: cover the existing `formatTime()` expectations if time formatting changes.
- Modify `settings_ui/tests/editor-inline.integration.test.ts` or `settings_ui/tests/editor-inline.actions.test.ts`: assert the flag follows cursor/progress updates.
- Build only generated bundles with `python3 scripts/dev.py build`; do not commit generated bundle files.

## Implementation Details

Use the existing SVG coordinate system. The current graph plot is `PLOT.left` to `PLOT.width - PLOT.right`, with the cursor line already set by `renderCursor()`.

Flag geometry:

- Fixed width: `82`
- Fixed height: `20`
- Gap above plot: flag top at `PLOT.top + 4`
- Flag center: follows cursor `x`, clamped to stay inside `[PLOT.left + 41, PLOT.width - PLOT.right - 41]`
- Cursor line: remains at exact cursor `x`
- Notch: small downward triangle centered on real cursor `x`, clamped visually by using a separate path under the flag group if needed
- Text: `current / total`, for example `02.55s / 06.08s`; for short clips use milliseconds only when duration is below two seconds, matching current `formatTime()`.

## Task 1: Add SVG Markup For The Flag

**Files:**
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`

- [ ] **Step 1: Add the flag group after the existing `.aqe-cursor` line**

Add this immediately after the existing cursor `<line>`:

```svelte
      <g
        class="aqe-cursor-flag"
        data-testid={`aqe-cursor-flag-${target.ord}`}
        visibility="hidden"
        aria-hidden="true"
      >
        <rect class="aqe-cursor-flag-box" x="-41" y="0" width="82" height="20" rx="4"></rect>
        <path class="aqe-cursor-flag-notch" d="M -5 20 L 0 26 L 5 20 Z"></path>
        <text class="aqe-cursor-flag-text" x="0" y="14">
          <tspan class="aqe-cursor-flag-current">0 ms</tspan>
          <tspan class="aqe-cursor-flag-total"> / 0 ms</tspan>
        </text>
      </g>
```

- [ ] **Step 2: Keep existing HTML label for accessibility/status**

Keep this existing node in `.aqe-visualizer-meta`:

```svelte
<span class="aqe-cursor-label" data-testid={`aqe-progress-label-${target.ord}`}>0 ms</span>
```

Do not remove it. Task 3 makes it screen-reader-only so assistive tech keeps a text progress value.

## Task 2: Render And Clamp The Timecode Flag

**Files:**
- Modify: `settings_ui/src/editor-inline/visualizer-renderer.ts`
- Test: `settings_ui/tests/editor-inline.integration.test.ts` or `settings_ui/tests/editor-inline.actions.test.ts`

- [ ] **Step 1: Write a failing integration assertion**

In an existing cursor/progress test, after setting a visualizer duration and cursor, assert the SVG flag state:

```ts
const flag = document.querySelector<SVGGElement>('[data-testid="aqe-cursor-flag-0"]')!;
const current = flag.querySelector<SVGTextElement>(".aqe-cursor-flag-current")!;
const total = flag.querySelector<SVGTextElement>(".aqe-cursor-flag-total")!;

expect(flag.getAttribute("visibility")).toBe("visible");
expect(flag.getAttribute("transform")).toBe("translate(327.00 14)");
expect(current.textContent).toBe("2.50s");
expect(total.textContent).toBe(" / 6.00s");
```

Adjust the expected `translate(...)` value to the exact cursor location used in the test. Use `xForMs()` to compute it if the test already imports plot helpers.

- [ ] **Step 2: Update `renderCursor()`**

Extend `renderCursor()` so it updates the line, old label, and new flag:

```ts
const FLAG_WIDTH = 82;
const FLAG_HALF_WIDTH = FLAG_WIDTH / 2;
const FLAG_Y = PLOT.top + 4;

function clampedFlagX(cursorX: number): number {
  const minX = PLOT.left + FLAG_HALF_WIDTH;
  const maxX = PLOT.width - PLOT.right - FLAG_HALF_WIDTH;
  return Math.max(minX, Math.min(cursorX, maxX));
}

export function renderCursor(visualizer: VisualizerElement, ms: number, durationMs: number): void {
  const x = xForMs(ms, durationMs);
  const cursor = visualizer.querySelector<SVGLineElement>(".aqe-cursor");
  if (cursor) {
    cursor.setAttribute("x1", x.toFixed(2));
    cursor.setAttribute("x2", x.toFixed(2));
  }

  const currentText = formatTime(ms, durationMs);
  const totalText = formatTime(durationMs, durationMs);

  const label = visualizer.querySelector<HTMLElement>(".aqe-cursor-label");
  if (label) label.textContent = `${currentText} / ${totalText}`;

  const flag = visualizer.querySelector<SVGGElement>(".aqe-cursor-flag");
  if (flag && durationMs > 0) {
    flag.setAttribute("visibility", "visible");
    flag.setAttribute("transform", `translate(${clampedFlagX(x).toFixed(2)} ${FLAG_Y})`);
    flag.querySelector<SVGTextElement>(".aqe-cursor-flag-current")!.textContent = currentText;
    flag.querySelector<SVGTextElement>(".aqe-cursor-flag-total")!.textContent = ` / ${totalText}`;
  }
}
```

- [ ] **Step 3: Update reset behavior**

Update `resetCursorProjection()` so the flag returns to the left edge and hidden/no-duration state:

```ts
const flag = visualizer.querySelector<SVGGElement>(".aqe-cursor-flag");
if (flag) {
  flag.setAttribute("visibility", "hidden");
  flag.setAttribute("transform", `translate(${PLOT.left + FLAG_HALF_WIDTH} ${FLAG_Y})`);
  flag.querySelector<SVGTextElement>(".aqe-cursor-flag-current")!.textContent = "0 ms";
  flag.querySelector<SVGTextElement>(".aqe-cursor-flag-total")!.textContent = " / 0 ms";
}
```

## Task 3: Style The Flag

**Files:**
- Modify: `settings_ui/src/editor-inline/styles.css`

- [ ] **Step 1: Add flag styles near `.aqe-cursor`**

```css
.aqe-cursor {
  opacity: 0.9;
  pointer-events: none;
  stroke: currentColor;
  stroke-width: 1.5;
}

.aqe-cursor-flag {
  pointer-events: none;
}

.aqe-cursor-flag-box,
.aqe-cursor-flag-notch {
  fill: Canvas;
  stroke: currentColor;
  stroke-width: 1;
  vector-effect: non-scaling-stroke;
}

.aqe-cursor-flag-text {
  fill: currentColor;
  font-size: 10px;
  font-weight: 700;
  text-anchor: middle;
}

.aqe-cursor-flag-total {
  opacity: 0.62;
  font-weight: 600;
}
```

- [ ] **Step 2: Reduce duplicate visual weight of the old label**

Keep the old label visible only if it still helps the meta row; otherwise make it screen-reader-only:

```css
.aqe-cursor-label {
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  height: 1px;
  overflow: hidden;
  position: absolute;
  white-space: nowrap;
  width: 1px;
}
```

Prefer screen-reader-only if the SVG flag is visually clear in e2e screenshots.

## Task 4: Add Edge-Case Tests

**Files:**
- Modify: `settings_ui/tests/editor-inline.integration.test.ts` or `settings_ui/tests/editor-inline.actions.test.ts`

- [ ] **Step 1: Assert left and right clamping**

Add coverage for cursor near start and end:

```ts
window.__aqeSetVisualizer?.(0, track, 100);
window.__aqeSetCursorByClientXForTest?.(0, graphClientX(svg, 0), false);
expect(document.querySelector('[data-testid="aqe-cursor-flag-0"]')?.getAttribute("transform")).toContain("85.00");

window.__aqeSetCursorByClientXForTest?.(0, graphClientX(svg, 1), false);
expect(document.querySelector('[data-testid="aqe-cursor-flag-0"]')?.getAttribute("transform")).toContain("569.00");
```

The exact clamp values come from `PLOT.left + 41` and `PLOT.width - PLOT.right - 41`.

- [ ] **Step 2: Assert live playback updates the flag**

Reuse the existing playback fake audio setup. After advancing audio time:

```ts
audio.currentTime = 0.7;
frames.shift()?.(performance.now() + 700);

const flag = document.querySelector<SVGGElement>('[data-testid="aqe-cursor-flag-0"]')!;
expect(flag.querySelector(".aqe-cursor-flag-current")?.textContent).toBe("700 ms");
expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
  progressMs: 700,
});
```

## Task 5: E2E Coverage

**Files:**
- Modify: `e2e/editor_graph_helpers.py`
- Modify: `e2e/test_editor_playback_workflow.py`

- [ ] **Step 1: Expose flag details in graph helper state**

Extend the helper JS object with:

```js
const flag = visualizer.querySelector('.aqe-cursor-flag');
const flagCurrent = visualizer.querySelector('.aqe-cursor-flag-current');
const flagTotal = visualizer.querySelector('.aqe-cursor-flag-total');

timecodeFlagVisible: flag?.getAttribute('visibility') === 'visible',
timecodeFlagTransform: flag?.getAttribute('transform') || '',
timecodeFlagCurrent: flagCurrent?.textContent || '',
timecodeFlagTotal: flagTotal?.textContent || '',
```

- [ ] **Step 2: Assert the flag appears and updates during playback**

Add a focused test named `test_timecode_flag_tracks_html_playback_progress`:

```py
state = _wait_for_html_playback(
    editor,
    lambda state: state["timecodeFlagVisible"] and state["timecodeFlagTotal"] == " / 2.00s",
)
assert state["timecodeFlagCurrent"] in {"0 ms", "0.00s"} or state["timecodeFlagCurrent"].endswith("ms")
```

Use tolerant assertions for live current time because animation timing varies.

## Task 6: Verification

- [ ] **Step 1: Run focused frontend checks**

```bash
cd settings_ui
npm run check
npm run typecheck
npm run test -- editor-inline.integration.test.ts editor-inline.actions.test.ts editor-inline.plot.test.ts
npm run lint
```

Expected: `check` and `typecheck` pass; focused tests pass; lint may report existing max-lines warnings only.

- [ ] **Step 2: Rebuild webview bundles**

```bash
python3 scripts/dev.py build
```

Expected: contract generation and settings/editor/batch Vite builds complete with exit code 0.

- [ ] **Step 3: Run focused e2e**

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_playback_workflow.py
```

Expected: playback workflow passes with the timecode flag visible and updating.

## Self-Review

- Spec coverage: The plan implements Timecode Flag visuals, current/total time information, cursor following, edge clamping, playback updates, and local webview build.
- Placeholder scan: No TBD/TODO placeholders remain.
- Type consistency: The plan uses existing `VisualizerElement`, `PLOT`, `xForMs()`, `formatTime()`, `renderCursor()`, `.aqe-cursor-label`, and current test helper conventions.
