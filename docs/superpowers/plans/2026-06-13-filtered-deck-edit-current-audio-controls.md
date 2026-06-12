# Filtered Deck Edit Current Audio Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure Audio Quick Editor controls mount in Anki's Edit Current dialog when a reviewed filtered-deck card's editor fields render after the add-on's initial frontend scans.

**Architecture:** The Python side already sends the correct note audio metadata through `editor_will_load_note`; the failure is on the frontend scanner when `.field-container` nodes are not present during the fixed `0/250/1000ms` scans. Keep Python hooks unchanged and make the editor runtime observe editor DOM mutations so late field containers trigger another bounded scan.

**Tech Stack:** Anki 25.09 EditCurrent/e2e, PyQt6 WebEngine, Svelte 5 editor-inline bundle, Vitest, `scripts/dev.py` quality runner.

---

## Current Evidence

- Added `e2e/test_edit_current_filtered_deck_workflow.py`.
- Native filtered-deck Edit Current cases pass locally on macOS/Anki 25.09 for:
  - question side + rescheduling filtered deck
  - answer side + rescheduling filtered deck
  - question side + preview/non-rescheduling filtered deck
  - answer side + preview/non-rescheduling filtered deck
- Deterministic race reproducer initially strict-xfailed before the runtime fix:
  - `test_edit_current_from_filtered_deck_recovers_when_fields_render_late`
  - Python config contains `audioFieldIndices: [1]`.
  - Frontend logs `scan mounted explicit fields` with `count: 0` after all fixed scans.
- Implementation result: the runtime now observes field DOM mutations, the delayed-field e2e is active, and full e2e passes locally.

## File Structure

- Modify: `settings_ui/src/editor-inline/runtime.ts`
  - Add a MutationObserver-backed DOM scan trigger for late Anki editor field containers.
  - Disconnect it in `disposeEditorRuntime()`.
- Modify: `settings_ui/tests/editor-inline.runtime.integration.test.ts`
  - Add a Vitest regression for field containers inserted after all scheduled scans.
- Modify: `e2e/test_edit_current_filtered_deck_workflow.py`
  - Remove the strict xfail from the delayed-field filtered-deck test once the runtime observes late fields.

---

### Task 1: Add A Frontend Failing Test For Late Field Containers

**Files:**
- Modify: `settings_ui/tests/editor-inline.runtime.integration.test.ts`

- [x] **Step 1: Add the failing Vitest case**

Append this test inside `describe("editor inline runtime scan integration", () => { ... })`:

```ts
it("mounts explicit audio controls when field containers appear after scheduled scans", async () => {
    vi.useFakeTimers();
    try {
        document.body.innerHTML = `<main id="editor-root"></main>`;

        initializeEditorRuntime({
            audioFieldIndices: [1],
            audioFieldSources: {1: "late-field.wav"},
            showGraphByDefault: false,
        });

        vi.runOnlyPendingTimers();
        expect(document.querySelectorAll(".aqe-controls")).toHaveLength(0);

        document.getElementById("editor-root")!.insertAdjacentHTML(
            "beforeend",
            `
            <div class="field-container" data-index="1">
              <div contenteditable="true">Answer [sound:late-field.wav]</div>
            </div>
            `,
        );

        await Promise.resolve();
        vi.runOnlyPendingTimers();

        expect(document.querySelectorAll('.aqe-controls[data-aqe-field-ord="1"]')).toHaveLength(1);
        expect(document.querySelector(".aqe-controls")?.getAttribute("data-aqe-source-filename")).toBe("late-field.wav");
    } finally {
        vi.useRealTimers();
    }
});
```

- [x] **Step 2: Run the frontend test and confirm it fails**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected before the fix: fail on `expect(document.querySelectorAll('.aqe-controls[data-aqe-field-ord="1"]')).toHaveLength(1)`.

---

### Task 2: Add A Bounded DOM Mutation Scan

**Files:**
- Modify: `settings_ui/src/editor-inline/runtime.ts`

- [x] **Step 1: Add observer state near the existing timer state**

```ts
let scheduledScanTimers: number[] = [];
let mutationScanTimer: number | null = null;
let editorDomObserver: MutationObserver | null = null;
let globalErrorHandlersInstalled = false;
```

- [x] **Step 2: Install the observer during runtime initialization**

In `initializeEditorRuntime()`, after the existing fixed `scheduleScan()` calls:

```ts
installEditorDomObserver(scanWithConfig);
```

- [x] **Step 3: Dispose the observer and pending mutation scan**

Update `disposeEditorRuntime()`:

```ts
export function disposeEditorRuntime(): void {
    scheduledScanTimers.forEach((timer) => window.clearTimeout(timer));
    scheduledScanTimers = [];
    if (mutationScanTimer !== null) {
        window.clearTimeout(mutationScanTimer);
        mutationScanTimer = null;
    }
    editorDomObserver?.disconnect();
    editorDomObserver = null;
    disposeAllControllers();
}
```

- [x] **Step 4: Add helper functions below `scheduleScan()`**

```ts
function installEditorDomObserver(callback: () => void): void {
    editorDomObserver?.disconnect();
    editorDomObserver = null;
    if (typeof MutationObserver === "undefined" || !document.body) return;

    editorDomObserver = new MutationObserver((records) => {
        if (records.some(recordAffectsFieldScan)) {
            scheduleMutationScan(callback);
        }
    });
    editorDomObserver.observe(document.body, {childList: true, subtree: true});
}

function recordAffectsFieldScan(record: MutationRecord): boolean {
    return [...record.addedNodes, ...record.removedNodes].some(nodeAffectsFieldScan);
}

function nodeAffectsFieldScan(node: Node): boolean {
    if (!(node instanceof HTMLElement)) return false;
    return (
        node.matches(FIELD_SCAN_SELECTOR)
        || node.querySelector(FIELD_SCAN_SELECTOR) !== null
    );
}

function scheduleMutationScan(callback: () => void): void {
    if (mutationScanTimer !== null) return;
    mutationScanTimer = window.setTimeout(() => {
        mutationScanTimer = null;
        callback();
    }, 0);
}
```

Add this selector near the top of the file:

```ts
const FIELD_SCAN_SELECTOR = '.field-container, .field, [contenteditable="true"], [data-field-ord], .aqe-review-audio-target';
```

- [x] **Step 5: Run the frontend regression**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected after the fix: the new test passes and existing runtime scan tests still pass.

---

### Task 3: Promote The E2E Reproducer

**Files:**
- Modify: `e2e/test_edit_current_filtered_deck_workflow.py`

- [x] **Step 1: Remove the xfail marker**

Delete the `@pytest.mark.xfail(...)` decorator from:

```python
def test_edit_current_from_filtered_deck_recovers_when_fields_render_late(
    anki_mw,
    ffmpeg_config,
) -> None:
```

- [x] **Step 2: Run the targeted e2e**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_edit_current_filtered_deck_workflow.py
```

Expected after the fix: all five tests pass.

---

### Task 4: Verification

**Files:**
- No additional edits.

- [x] **Step 1: Run frontend validation**

```bash
python3 scripts/dev.py test-svelte
```

Expected: pass.

- [x] **Step 2: Run Anki API compatibility if Python hooks changed**

Skipped because only `runtime.ts`, frontend tests, and e2e tests changed. If any Anki-facing Python hook code changes, run:

```bash
python3 scripts/dev.py test-anki-api
```

Expected: pass.

- [x] **Step 3: Run targeted e2e**

```bash
python3 scripts/dev.py test-e2e e2e/test_edit_current_filtered_deck_workflow.py
```

Expected: pass with no xfail.

- [x] **Step 4: Run full e2e before declaring the feature complete**

```bash
python3 scripts/dev.py test-e2e
```

Expected: pass.

---

## Self-Review

- Spec coverage: the plan covers the filtered-deck Edit Current path, the frontend timing failure, and regression verification.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: helper names and file paths match the current codebase.
