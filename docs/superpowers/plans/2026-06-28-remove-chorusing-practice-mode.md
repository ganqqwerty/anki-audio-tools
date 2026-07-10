# Remove Chorusing Practice Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the dedicated `Play chorusing` mode so marker navigation, normal selected playback, repeat, and auto-advance work as one ordinary Play workflow.

**Architecture:** Keep the marker row and two marker navigation buttons, but make them write the normal editor selection instead of starting a practice mode. Move auto-advance into the normal selected-repeat playback boundary path and keep the existing config keys during this implementation for compatibility. Remove `source: "chorusing"` playback and the `aqe:chorusing-practice` command after the selected-playback path has tests.

**Tech Stack:** Svelte 5, TypeScript, Vitest, Python config/schema, generated JSON contracts, pytest, real-Anki e2e

**Input Analysis:** `docs/remove-chorusing-practice-mode.md`

---

## Implementation Assumptions

- Do not rename `aqe:chorusing-next` and `aqe:chorusing-previous` command IDs in this implementation. Existing user config may contain them. Update user-facing labels later if desired.
- Remove `aqe:chorusing-practice` from defaults/schema/toolbar rendering in this implementation.
- Keep config keys `chorusing_auto_advance_by_default`, `chorusing_auto_advance_repeats`, and `chorusing_marker_interval_ms` for compatibility, but expose auto-advance controls from the Play menu and Play settings.
- Stop selected playback at the leftmost marker after the auto-advance threshold is reached. Do not wrap. Leave the selection at the leftmost suffix and reset the auto-advance counter to `0`.
- If auto-advance is enabled but playback is full-source or no selection exists, ignore auto-advance.
- The Back/longer-suffix button initializes the rightmost suffix when no selection is active; it does not start playback.

## File Structure

- `settings_ui/src/editor-inline/selection-auto-advance.ts`: new pure decision functions for selected-repeat auto-advance.
- `settings_ui/src/editor-inline/selection-auto-advance-controller.ts`: new DOM/controller bridge that reads field state, marker state, split state, updates selection, and starts/stops playback after a boundary decision.
- `settings_ui/src/editor-inline/chorusing-state.ts`: keep marker generation/toggle utilities during this migration, but remove mode-only fields and functions once replacement coverage is green.
- `settings_ui/src/editor-inline/chorusing-controller.ts`: reduce to marker initialization, marker toggle, and selection-start navigation.
- `settings_ui/src/editor-inline/chorusing-toolbar.ts`: sync only the two navigation buttons.
- `settings_ui/src/editor-inline/PlaySplitButton.svelte`: add auto-advance controls next to Repeat.
- `settings_ui/src/editor-inline/ChorusingSplitButton.svelte`: delete after Play owns the controls.
- `settings_ui/src/lib/editor-toolbar-buttons.ts`, `settings_ui/src/lib/editor-toolbar-defaults.ts`, `settings_ui/src/lib/editor-toolbar-panel-definitions.ts`, `settings_ui/src/lib/editor-toolbar-command-slugs.ts`: remove the practice command from button metadata while preserving the two navigation commands.
- `addon/anki_audio_quick_editor/config.json`, `addon/anki_audio_quick_editor/config.schema.json`, `addon/anki_audio_quick_editor/editor_actions.py`: remove practice command defaults/schema entries.
- `addon/anki_audio_quick_editor/editor_playback_request.py`: remove chorusing-specific status guidance.
- `e2e/editor_chorusing_helpers.py`, `e2e/test_editor_chorusing_playback_workflow.py`, `e2e/test_editor_chorusing_markers_workflow.py`: rewrite practice-mode e2e as selected-playback workflows.

### Task 1: Write the Selected-Playback Target Tests

**Files:**
- Move: `settings_ui/tests/editor-inline.chorusing-auto-advance.integration.test.ts` -> `settings_ui/tests/editor-inline.selected-repeat-auto-advance.integration.test.ts`
- Move: `settings_ui/tests/editor-inline.chorusing-auto-advance.helpers.ts` -> `settings_ui/tests/editor-inline.selected-repeat-auto-advance.helpers.ts`
- Modify: `settings_ui/tests/editor-inline.chorusing.integration.test.ts`

- [ ] **Step 1: Rename the focused Svelte test files**

Run:

```bash
git mv settings_ui/tests/editor-inline.chorusing-auto-advance.integration.test.ts settings_ui/tests/editor-inline.selected-repeat-auto-advance.integration.test.ts
git mv settings_ui/tests/editor-inline.chorusing-auto-advance.helpers.ts settings_ui/tests/editor-inline.selected-repeat-auto-advance.helpers.ts
```

Expected: git status shows two renames and no deleted untracked files.

- [ ] **Step 2: Replace practice-start helper with selected-playback helpers**

In `settings_ui/tests/editor-inline.selected-repeat-auto-advance.helpers.ts`, replace `startAutoAdvancePractice()` with:

```ts
export async function configureSelectedRepeatAutoAdvance(repeatCount = 2): Promise<HTMLAudioElement> {
  const audio = prepareHtmlAudio();
  setRepeatEnabledForOrd(0, true);
  setChorusingAutoAdvanceForField(0, true);
  setChorusingRepeatCountForField(0, repeatCount);
  await flushPlaybackWork();
  return audio;
}

export async function startSelectedPlayback(): Promise<void> {
  playButton().click();
  await flushPlaybackWork();
}

export function longerSuffixButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-chorusing-next"]')!;
}

export function shorterSuffixButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-chorusing-previous"]')!;
}

function playButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!;
}
```

Also update imports at the top of the helper:

```ts
import { handlePlaybackBoundary, setRepeatEnabledForOrd } from "../src/editor-inline/actions.js";
```

- [ ] **Step 3: Write failing test for Back initializing selection without playback**

Add this test near the top of `settings_ui/tests/editor-inline.selected-repeat-auto-advance.integration.test.ts`:

```ts
it("longer suffix initializes the rightmost suffix without starting playback", async () => {
  await prepareChorusingGraph();
  const audio = prepareHtmlAudio();

  longerSuffixButton().click();
  await flushPlaybackWork();

  expect(audio.play).not.toHaveBeenCalled();
  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    chorusingRepeatPassesCompleted: 0,
    playbackState: "stopped",
    selectionEndMs: 1000,
    selectionStartMs: 500,
  });
});
```

Expected current failure: the longer-suffix button is disabled or no selection is initialized without practice.

- [ ] **Step 4: Rewrite the uninterrupted auto-advance test to use Play**

Replace the old `auto-advances through suffixes without navigation clicks` body with:

```ts
await prepareChorusingGraph();
const audio = await configureSelectedRepeatAutoAdvance(2);
longerSuffixButton().click();
await flushPlaybackWork();
await startSelectedPlayback();

expect(audio.play).toHaveBeenCalledTimes(1);
expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
  playbackStartMs: 500,
  playbackState: "playing",
  repeatEnabled: true,
  selectionEndMs: 1000,
  selectionStartMs: 500,
});

await forceAudioEndedBoundary();
expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
  chorusingRepeatPassesCompleted: 1,
  playbackState: "playing",
  selectionStartMs: 500,
});

await forceAudioEndedBoundary();
expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
  chorusingRepeatPassesCompleted: 0,
  playbackStartMs: 0,
  playbackState: "playing",
  selectionEndMs: 1000,
  selectionStartMs: 0,
});
expect(audio.play).toHaveBeenCalledTimes(2);
```

- [ ] **Step 5: Rewrite the remaining focused scenarios**

Use these expected state changes:

```ts
// Manual longer/shorter navigation resets the counter.
expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
  chorusingRepeatPassesCompleted: 0,
  selectionStartMs: 0,
});

// Cursor movement keeps selection anchors; the next audio-ended boundary still advances.
expect(readHtmlAudioSessionState(0)).toMatchObject({
  kind: "playing",
  request: {
    cursorMs: 750,
    source: "user",
  },
});

// Selection edits reset the counter and keep normal playback active.
expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
  chorusingRepeatPassesCompleted: 0,
  playbackEndMs: 800,
  playbackStartMs: 300,
  playbackState: "playing",
  selectionEndMs: 800,
  selectionStartMs: 300,
});

// Marker edits do not reset the counter.
expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
  chorusingMarkersMs: [0, 250, 500],
  chorusingRepeatPassesCompleted: 1,
});
```

- [ ] **Step 6: Run Svelte tests and confirm target tests fail for behavior, not syntax**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected before implementation: failures in `editor-inline.selected-repeat-auto-advance.integration.test.ts` that show selection is not initialized by navigation, auto-advance does not run for normal Play, or `source` is still `chorusing`.

- [ ] **Step 7: Commit the failing target tests**

```bash
git add settings_ui/tests/editor-inline.selected-repeat-auto-advance.integration.test.ts settings_ui/tests/editor-inline.selected-repeat-auto-advance.helpers.ts settings_ui/tests/editor-inline.chorusing.integration.test.ts
git commit -m "Test selected repeat auto-advance without practice mode" -m "The product direction is to make marker navigation and auto-advance work through ordinary selected playback. These tests lock that behavior before removing the dedicated chorusing practice path. This commit intentionally contains failing tests and was done without full check and e2e routines being run."
```

### Task 2: Add Pure Selected Auto-Advance Decisions

**Files:**
- Create: `settings_ui/src/editor-inline/selection-auto-advance.ts`
- Create: `settings_ui/tests/selection-auto-advance.test.ts`
- Modify: `settings_ui/src/editor-inline/chorusing-state.ts`

- [ ] **Step 1: Write pure decision tests**

Create `settings_ui/tests/selection-auto-advance.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { resolveSelectionAutoAdvanceBoundary } from "../src/editor-inline/selection-auto-advance.js";

describe("selection auto-advance", () => {
  it("counts repeats until the configured threshold", () => {
    expect(resolveSelectionAutoAdvanceBoundary({
      autoAdvance: true,
      markersMs: [0, 500],
      repeatCount: 2,
      repeatPassesCompleted: 0,
      selection: { startMs: 500, endMs: 1000 },
    })).toEqual({
      action: "repeat",
      nextRepeatPassesCompleted: 1,
      nextSelection: null,
    });
  });

  it("moves the selection start to the nearest marker on threshold", () => {
    expect(resolveSelectionAutoAdvanceBoundary({
      autoAdvance: true,
      markersMs: [0, 250, 500],
      repeatCount: 2,
      repeatPassesCompleted: 1,
      selection: { startMs: 500, endMs: 1000 },
    })).toEqual({
      action: "advance",
      nextRepeatPassesCompleted: 0,
      nextSelection: { startMs: 250, endMs: 1000 },
    });
  });

  it("stops at the leftmost marker instead of wrapping", () => {
    expect(resolveSelectionAutoAdvanceBoundary({
      autoAdvance: true,
      markersMs: [0, 500],
      repeatCount: 2,
      repeatPassesCompleted: 1,
      selection: { startMs: 0, endMs: 1000 },
    })).toEqual({
      action: "complete",
      nextRepeatPassesCompleted: 0,
      nextSelection: null,
    });
  });

  it("ignores full playback or disabled auto-advance", () => {
    expect(resolveSelectionAutoAdvanceBoundary({
      autoAdvance: false,
      markersMs: [0, 500],
      repeatCount: 2,
      repeatPassesCompleted: 1,
      selection: { startMs: 500, endMs: 1000 },
    })).toEqual({
      action: "ignore",
      nextRepeatPassesCompleted: 1,
      nextSelection: null,
    });
  });
});
```

- [ ] **Step 2: Run the new pure test and confirm it fails**

Run:

```bash
cd settings_ui && npx vitest run tests/selection-auto-advance.test.ts
```

Expected before implementation:

```text
Failed to resolve import "../src/editor-inline/selection-auto-advance.js"
```

- [ ] **Step 3: Implement the pure decision module**

Create `settings_ui/src/editor-inline/selection-auto-advance.ts`:

```ts
import type { SelectionRange } from "./selection-state.js";

export type SelectionAutoAdvanceAction = "advance" | "complete" | "ignore" | "repeat";

export interface SelectionAutoAdvanceInput {
  autoAdvance: boolean;
  markersMs: readonly number[];
  repeatCount: number;
  repeatPassesCompleted: number;
  selection: SelectionRange | null;
}

export interface SelectionAutoAdvanceDecision {
  action: SelectionAutoAdvanceAction;
  nextRepeatPassesCompleted: number;
  nextSelection: SelectionRange | null;
}

export function resolveSelectionAutoAdvanceBoundary(
  input: SelectionAutoAdvanceInput,
): SelectionAutoAdvanceDecision {
  if (!input.autoAdvance || !input.selection) {
    return {
      action: "ignore",
      nextRepeatPassesCompleted: input.repeatPassesCompleted,
      nextSelection: null,
    };
  }
  const repeatCount = Math.max(1, Math.round(input.repeatCount));
  const completed = input.repeatPassesCompleted + 1;
  if (completed < repeatCount) {
    return {
      action: "repeat",
      nextRepeatPassesCompleted: completed,
      nextSelection: null,
    };
  }
  const currentStart = Math.round(input.selection.startMs);
  const nextStart = nearestMarkerLeftOf(input.markersMs, currentStart);
  if (nextStart === null) {
    return {
      action: "complete",
      nextRepeatPassesCompleted: 0,
      nextSelection: null,
    };
  }
  return {
    action: "advance",
    nextRepeatPassesCompleted: 0,
    nextSelection: {
      endMs: input.selection.endMs,
      startMs: nextStart,
    },
  };
}

function nearestMarkerLeftOf(markersMs: readonly number[], startMs: number): number | null {
  for (let index = markersMs.length - 1; index >= 0; index -= 1) {
    const marker = markersMs[index];
    if (typeof marker === "number" && Number.isFinite(marker) && Math.round(marker) < startMs) {
      return Math.round(marker);
    }
  }
  return null;
}
```

- [ ] **Step 4: Keep the existing marker utility exports compiling**

If `chorusing-state.ts` still exports `resolveChorusingLoopBoundary`, leave it in place until Task 5 removes callers. Do not delete it in this task.

- [ ] **Step 5: Re-run the pure test**

Run:

```bash
cd settings_ui && npx vitest run tests/selection-auto-advance.test.ts
```

Expected after implementation:

```text
✓ tests/selection-auto-advance.test.ts
```

- [ ] **Step 6: Commit the pure decision slice**

```bash
git add settings_ui/src/editor-inline/selection-auto-advance.ts settings_ui/tests/selection-auto-advance.test.ts settings_ui/src/editor-inline/chorusing-state.ts
git commit -m "Model selected repeat auto-advance decisions" -m "Auto-advance should be independent from chorusing practice playback. This adds a pure decision layer that can be tested before wiring it into audio boundaries. Focused Vitest coverage was run; the full check and e2e routines were not run for this slice."
```

### Task 3: Make Marker Navigation Write Selection Without Playback

**Files:**
- Modify: `settings_ui/src/editor-inline/chorusing-controller.ts`
- Modify: `settings_ui/src/editor-inline/chorusing-state.ts`
- Modify: `settings_ui/src/editor-inline/chorusing-dom.ts`
- Modify: `settings_ui/src/editor-inline/chorusing-toolbar.ts`
- Modify: `settings_ui/src/editor-inline/test-contract.ts`
- Test: `settings_ui/tests/editor-inline.selected-repeat-auto-advance.integration.test.ts`
- Test: `settings_ui/tests/editor-inline.chorusing.integration.test.ts`

- [ ] **Step 1: Run the Svelte tests from Task 1 and confirm navigation failures**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected before implementation: tests fail because the navigation buttons still depend on practice state and do not initialize the rightmost suffix from no selection.

- [ ] **Step 2: Add a rightmost suffix initializer**

In `chorusing-controller.ts`, add:

```ts
function rightmostSuffixSelection(state: ChorusingState): { startMs: number; endMs: number } | null {
  if (!state.baseRegion || !state.markersMs.length) return null;
  const startMs = state.markersMs[state.markersMs.length - 1];
  if (typeof startMs !== "number" || !Number.isFinite(startMs)) return null;
  return {
    endMs: state.baseRegion.endMs,
    startMs,
  };
}
```

- [ ] **Step 3: Rewrite `moveChorusing()` to move selection only**

Replace the practice-oriented body with selection-only behavior:

```ts
function moveChorusing(
  visualizer: VisualizerElement,
  direction: ChorusingMarkerDirection,
  options: { resetRepeatPasses?: boolean } = {},
): boolean {
  const readyState = ensureChorusingBase(visualizer, chorusingStateForVisualizer(visualizer));
  if (!readyState?.baseRegion || !readyState.markersMs.length) return false;
  const selection = selectionForVisualizer(visualizer);
  const nextSelection = selection
    ? selectionAfterMarkerNavigation(selection, readyState.markersMs, direction, readyState.baseRegion.endMs)
    : rightmostSuffixSelection(readyState);
  if (!nextSelection) return false;
  writeState(visualizer, {
    ...readyState,
    activeMarkerIndex: markerIndexForExactStart(readyState.markersMs, nextSelection.startMs),
    activeStartMs: nextSelection.startMs,
    activeEndMs: nextSelection.endMs,
    repeatPassesCompleted: options.resetRepeatPasses === false ? readyState.repeatPassesCompleted : 0,
  });
  setSelectionFromController(visualizer, nextSelection.startMs, nextSelection.endMs, { setCursor: () => undefined }, { updateCursor: false });
  syncSelectionToolbar(visualizer);
  notifySelectionChanged(visualizer, "chorusing");
  return true;
}
```

Add this helper in the same file:

```ts
function selectionAfterMarkerNavigation(
  selection: { startMs: number; endMs: number },
  markersMs: readonly number[],
  direction: ChorusingMarkerDirection,
  durationMs: number,
): { startMs: number; endMs: number } | null {
  const targetIndex = moveActiveMarkerIndexForSuffix(
    markersMs,
    markerIndexForExactStart(markersMs, selection.startMs),
    direction,
    selection.startMs,
    selection.endMs,
  );
  const startMs = targetIndex === null ? null : markersMs[targetIndex];
  if (typeof startMs !== "number" || !Number.isFinite(startMs)) return null;
  const endMs = Math.min(selection.endMs, durationMs);
  if (Math.round(startMs) >= Math.round(endMs)) return null;
  return { startMs, endMs };
}
```

- [ ] **Step 4: Keep marker edits from starting playback**

In `handleChorusingMarkerPointerDown()`, remove this branch:

```ts
if (previousSuffix?.startMs !== nextSuffix.startMs || previousSuffix?.endMs !== nextSuffix.endMs) {
  startPracticePlayback(visualizer, nextState);
}
```

Replace it with:

```ts
if (readyState.practiceState === "playing") {
  writeState(visualizer, {
    ...nextState,
    repeatPassesCompleted: readyState.repeatPassesCompleted,
  });
}
```

This temporary assignment keeps tests green during migration; Task 6 removes `practiceState`.

- [ ] **Step 5: Update toolbar availability for no-selection initialization**

In `chorusing-toolbar.ts`, allow the longer-suffix button when a track and markers exist even without active selection:

```ts
const canInitializeSuffix = controls.markersMs.length > 0 && hasPlayableTrack;
syncChorusingNavButton(
  buttonFor(ord, "aqe:chorusing-next"),
  controls.canNext || canInitializeSuffix,
  busy,
  t("editor.command.chorusing_next.title"),
  t("editor.command.chorusing_next.disabled_title"),
);
```

If `controls.markersMs` is not exposed, add it to `ChorusingControlsState` in `chorusing-dom.ts`.

- [ ] **Step 6: Re-run Svelte tests**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected after implementation: the navigation-only selected suffix tests pass; auto-advance tests may still fail because the generic boundary hook is not wired.

- [ ] **Step 7: Commit marker navigation**

```bash
git add settings_ui/src/editor-inline/chorusing-controller.ts settings_ui/src/editor-inline/chorusing-state.ts settings_ui/src/editor-inline/chorusing-dom.ts settings_ui/src/editor-inline/chorusing-toolbar.ts settings_ui/src/editor-inline/test-contract.ts settings_ui/tests/editor-inline.selected-repeat-auto-advance.integration.test.ts settings_ui/tests/editor-inline.chorusing.integration.test.ts
git commit -m "Make marker navigation drive normal selection" -m "Back-chaining markers are useful without a dedicated practice mode. This changes marker navigation to set the ordinary selected region and lets Play remain the only playback entry point. Svelte tests were run; the full check and e2e routines were not run for this slice."
```

### Task 4: Move Auto-Advance Controls Into Play Settings

**Files:**
- Modify: `settings_ui/src/editor-inline/PlaySplitButton.svelte`
- Modify: `settings_ui/src/editor-inline/split-button-state-setters.ts`
- Modify: `settings_ui/src/editor-inline/split-button-state.ts`
- Modify: `settings_ui/src/settings/ToolbarBasicSettingsFields.svelte`
- Modify: `settings_ui/tests/split-button-state-state.test.ts`
- Modify: `settings_ui/tests/editor-inline.playback.integration.test.ts`

- [ ] **Step 1: Write failing split-state setter test for selected-repeat auto-advance**

In `settings_ui/tests/split-button-state-state.test.ts`, add:

```ts
it("updates selected-repeat auto-advance field state", () => {
  expect(setChorusingAutoAdvanceForField(0, true).chorusingAutoAdvance).toBe(true);
  expect(setChorusingRepeatCountForField(0, 4).chorusingRepeatCount).toBe(4);
  expect(getSplitButtonState(0)).toMatchObject({
    chorusingAutoAdvance: true,
    chorusingRepeatCount: 4,
  });
});
```

Expected current result: this likely already passes; keep it as guard coverage before moving the controls.

- [ ] **Step 2: Write failing Play popover rendering and save-default test**

In `settings_ui/tests/editor-inline.playback.integration.test.ts`, add:

```ts
it("renders and saves selected-repeat auto-advance controls in the Play menu", async () => {
  initializeEditorRuntime({ audioFieldIndices: [0] });
  scan({ audioFieldIndices: [0] });
  await Promise.resolve();
  window.__aqeSetVisualizer?.(0, track, 0);

  document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-play-menu"]')!.click();
  await Promise.resolve();

  const autoAdvance = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-play-auto-advance"]')!;
  const repeats = document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-play-auto-advance-repeats"]')!;
  expect(autoAdvance).not.toBeNull();
  expect(repeats).not.toBeNull();

  autoAdvance.click();
  repeats.value = "4";
  repeats.dispatchEvent(new Event("input", { bubbles: true }));
  document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-play-save-default"]')!.click();

  expect(window.__aqePopPendingSplitDefaultSaveRequest?.()).toMatchObject({
    defaults: {
      chorusingAutoAdvanceByDefault: true,
      chorusingAutoAdvanceRepeats: 4,
      repeatPauseSeconds: 0,
      repeatPlaybackByDefault: false,
    },
    fieldOrd: 0,
  });
});
```

- [ ] **Step 3: Run focused Svelte tests and confirm failures**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected before implementation: Play popover test fails because the auto-advance controls are still rendered by `ChorusingSplitButton.svelte`.

- [ ] **Step 4: Include auto-advance in Play default save requests**

In `PlaySplitButton.svelte`, change `saveCurrentDefaults()`:

```ts
const request = {
  defaults: {
    chorusingAutoAdvanceByDefault: autoAdvance,
    chorusingAutoAdvanceRepeats: autoAdvanceRepeats,
    repeatPauseSeconds,
    repeatPlaybackByDefault: pressed,
  },
  fieldOrd: target.ord,
};
```

Keep the two auto-advance keys exactly as shown because the backend already sanitizes them.

- [ ] **Step 5: Render Play auto-advance controls**

In `PlaySplitButton.svelte`, import the existing setters:

```ts
import {
  getSplitButtonState,
  promoteSplitDefaultsForField,
  REPEAT_PAUSE_STATE_CHANGED_EVENT,
  setChorusingAutoAdvanceForField,
  setChorusingRepeatCountForField,
  setRepeatPauseSecondsForField,
  type RepeatPauseStateChangedDetail,
} from "./split-button-state.js";
```

Add state:

```ts
let autoAdvance = $state(false);
let autoAdvanceRepeats = $state(3);
```

Update `syncRepeatState()`:

```ts
autoAdvance = state.chorusingAutoAdvance;
autoAdvanceRepeats = state.chorusingRepeatCount;
```

Add handlers:

```ts
function applyAutoAdvance(value: boolean): void {
  defaultSaved = false;
  autoAdvance = setChorusingAutoAdvanceForField(target.ord, value).chorusingAutoAdvance;
}

function applyAutoAdvanceRepeats(value: number): void {
  defaultSaved = false;
  autoAdvanceRepeats = setChorusingRepeatCountForField(target.ord, value).chorusingRepeatCount;
}
```

Add controls below the repeat pause controls:

```svelte
<label class="aqe-split-checkbox-row">
  <input
    type="checkbox"
    checked={autoAdvance}
    data-testid={`aqe-split-${target.ord}-play-auto-advance`}
    onchange={(event) => applyAutoAdvance((event.currentTarget as HTMLInputElement).checked)}
  />
  <span>{t("editor.play.auto_advance")}</span>
</label>
<div class="aqe-split-popover-header">
  <span>{t("editor.play.auto_advance_repeats")}</span>
  <UnitNumberInput
    inputClass="aqe-split-value-input"
    testId={`aqe-split-${target.ord}-play-auto-advance-repeats`}
    min="1"
    max="20"
    step="1"
    unit="x"
    value={autoAdvanceRepeats}
    ariaLabel={t("editor.play.auto_advance_repeats")}
    onValueInput={applyAutoAdvanceRepeats}
  />
</div>
```

- [ ] **Step 6: Move settings UI fields from practice to Play**

In `ToolbarBasicSettingsFields.svelte`, move these fields from the `aqe:chorusing-practice` block into the `aqe:play` block:

```svelte
<label class="settings-toggle">
  <input
    data-testid="chorusing-auto-advance-by-default"
    type="checkbox"
    bind:checked={config.chorusing_auto_advance_by_default}
  />
  <span class="settings-label-text">{t("settings.chorusing_auto_advance_by_default")}</span>
</label>
<label class="settings-field">
  <span>{t("settings.chorusing_auto_advance_repeats")}</span>
  <UnitNumberInput
    inputClass="settings-input"
    testId="chorusing-auto-advance-repeats"
    min="1"
    max="20"
    step="1"
    unit="x"
    bind:value={config.chorusing_auto_advance_repeats}
  />
</label>
```

Leave `chorusing_marker_interval_ms` under the marker panel for this implementation.

- [ ] **Step 7: Run focused Svelte tests**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected after implementation: Play popover and split payload tests pass; selected auto-advance behavior still fails until Task 5 wiring.

- [ ] **Step 8: Commit Play settings**

```bash
git add settings_ui/src/editor-inline/PlaySplitButton.svelte settings_ui/src/editor-inline/split-button-state-setters.ts settings_ui/src/editor-inline/split-button-state.ts settings_ui/src/settings/ToolbarBasicSettingsFields.svelte settings_ui/tests/split-button-state-state.test.ts settings_ui/tests/editor-inline.playback.integration.test.ts
git commit -m "Expose auto-advance from Play settings" -m "Auto-advance is selected-repeat playback behavior, not a separate chorusing mode. This moves the controls and saved defaults into the Play surface while preserving existing config keys for compatibility. Svelte tests were run; the full check and e2e routines were not run for this slice."
```

### Task 5: Wire Auto-Advance Into Generic Playback Boundaries

**Files:**
- Create: `settings_ui/src/editor-inline/selection-auto-advance-controller.ts`
- Modify: `settings_ui/src/editor-inline/playback-controller.ts`
- Modify: `settings_ui/src/editor-inline/playback-controller-dependencies.ts`
- Modify: `settings_ui/src/editor-inline/playback-actions.ts`
- Modify: `settings_ui/src/editor-inline/actions-audio-clock.ts`
- Modify: `settings_ui/src/editor-inline/visualizer-runtime-state.ts`
- Test: `settings_ui/tests/editor-inline.selected-repeat-auto-advance.integration.test.ts`
- Test: `settings_ui/tests/editor-inline.playback.integration.test.ts`

- [ ] **Step 1: Extend loop-boundary result type**

In `playback-controller.ts`, define:

```ts
export type LoopBoundaryResult = "complete" | "handled" | false;
```

Change dependency type:

```ts
handleLoopBoundary?: (visualizer: VisualizerElement, pass: PlaybackPass) => LoopBoundaryResult;
```

Update `handlePlaybackBoundary()`:

```ts
const loopBoundary = deps.handleLoopBoundary?.(visualizer, boundary.pass) ?? false;
if (loopBoundary === "complete") {
  completePlayback(visualizer, deps);
  return true;
}
if (loopBoundary === "handled") {
  return true;
}
```

- [ ] **Step 2: Create controller bridge for selected auto-advance**

Create `selection-auto-advance-controller.ts`:

```ts
import { dispatchHtmlAudioSessionEvent } from "./html-audio-session-controller.js";
import { startSourcePlaybackAction } from "./source-playback-actions.js";
import { getSplitButtonState } from "./split-button-state.js";
import { selectionForVisualizer, setSelection as setSelectionFromController } from "./selection-controller.js";
import { chorusingStateForVisualizer, writeChorusingState } from "./chorusing-dom.js";
import { resolveSelectionAutoAdvanceBoundary } from "./selection-auto-advance.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";
import type { PlaybackPass } from "./playback-model.js";
import type { VisualizerElement } from "./types.js";

export function handleSelectedRepeatAutoAdvanceBoundary(
  visualizer: VisualizerElement,
  pass: PlaybackPass,
): "complete" | "handled" | false {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const selection = selectionForVisualizer(visualizer);
  if (!selection || pass.regionMode !== "selection") return false;
  if (Math.round(pass.startMs) !== Math.round(selection.startMs)) return false;
  if (Math.round(pass.endMs) !== Math.round(selection.endMs)) return false;

  const markerState = chorusingStateForVisualizer(visualizer);
  const splitState = getSplitButtonState(ord);
  const decision = resolveSelectionAutoAdvanceBoundary({
    autoAdvance: splitState.chorusingAutoAdvance,
    markersMs: markerState.markersMs,
    repeatCount: splitState.chorusingRepeatCount,
    repeatPassesCompleted: markerState.repeatPassesCompleted,
    selection,
  });

  writeChorusingState(visualizer, {
    ...markerState,
    repeatPassesCompleted: decision.nextRepeatPassesCompleted,
  });

  if (decision.action === "ignore") return false;
  if (decision.action === "repeat") return false;
  if (decision.action === "complete") {
    dispatchHtmlAudioSessionEvent(ord, {
      cursorMs: selection.startMs,
      type: "StopRequested",
    });
    return "complete";
  }
  if (!decision.nextSelection) return false;
  setSelectionFromController(
    visualizer,
    decision.nextSelection.startMs,
    decision.nextSelection.endMs,
    { setCursor: () => undefined },
    { updateCursor: false },
  );
  syncSelectionToolbar(visualizer);
  startSourcePlaybackAction(visualizer, {
    action: "start",
    cursorMs: Math.round(decision.nextSelection.startMs),
    endMs: Math.round(decision.nextSelection.endMs),
    engine: "html",
    loop: true,
    ord,
    regionMode: "selection",
    source: "user",
  });
  return "handled";
}
```

- [ ] **Step 3: Use the generic hook from playback actions**

In `playback-actions.ts`, replace:

```ts
import { handleChorusingLoopBoundary } from "./chorusing-controller.js";
```

with:

```ts
import { handleSelectedRepeatAutoAdvanceBoundary } from "./selection-auto-advance-controller.js";
```

Change:

```ts
return playbackControllerDependencies({ handleLoopBoundary: handleSelectedRepeatAutoAdvanceBoundary });
```

- [ ] **Step 4: Use the generic hook from audio-ended handling**

In `actions-audio-clock.ts`, replace `handleChorusingLoopBoundary` imports and `session.request.source === "chorusing"` branches with:

```ts
if (
  (session.kind === "starting" || session.kind === "playing") &&
  handleSelectedRepeatAutoAdvanceBoundary(visualizer, playbackPassForSessionRequest(session.request))
) {
  return;
}
```

Keep this before `dispatchSourceSessionBoundary(...)` so real audio `ended` uses the same auto-advance path as manual boundary tests.

- [ ] **Step 5: Reset counter on selection edits and play-start changes**

In `chorusing-controller.ts`, keep the existing selection change listener but replace practice-only syncing with:

```ts
function scheduleUserSelectionChorusingSync(visualizer: VisualizerElement): void {
  queueMicrotask(() => {
    const state = chorusingStateForVisualizer(visualizer);
    writeState(visualizer, {
      ...state,
      activeEndMs: null,
      activeMarkerIndex: null,
      activeStartMs: null,
      repeatPassesCompleted: 0,
    });
  });
}
```

If Task 6 has already removed `active*` fields, reset only `repeatPassesCompleted`.

- [ ] **Step 6: Run Svelte tests**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected after implementation: selected-repeat auto-advance tests pass through both `handlePlaybackBoundary()` and audio `ended` paths; tests that still expect `source: "chorusing"` fail and are updated in Task 6.

- [ ] **Step 7: Commit generic boundary wiring**

```bash
git add settings_ui/src/editor-inline/selection-auto-advance-controller.ts settings_ui/src/editor-inline/playback-controller.ts settings_ui/src/editor-inline/playback-controller-dependencies.ts settings_ui/src/editor-inline/playback-actions.ts settings_ui/src/editor-inline/actions-audio-clock.ts settings_ui/src/editor-inline/visualizer-runtime-state.ts settings_ui/tests/editor-inline.selected-repeat-auto-advance.integration.test.ts settings_ui/tests/editor-inline.playback.integration.test.ts
git commit -m "Run auto-advance through selected playback" -m "The repeat boundary is the natural place to advance selected suffixes, so auto-advance no longer needs a chorusing playback source. This wires the pure decision into manual and HTML audio boundaries while preserving normal repeat behavior. Svelte tests were run; the full check and e2e routines were not run for this slice."
```

### Task 6: Remove Chorusing Playback Source and Practice State

**Files:**
- Modify: `settings_ui/src/editor-inline/chorusing-state.ts`
- Modify: `settings_ui/src/editor-inline/chorusing-controller.ts`
- Modify: `settings_ui/src/editor-inline/actions-playback.ts`
- Modify: `settings_ui/src/editor-inline/actions-audio-clock.ts`
- Modify: `settings_ui/src/editor-inline/html-audio-session-controller.ts`
- Modify: `settings_ui/src/editor-inline/html-audio-session-types.ts`
- Modify: `settings_ui/src/editor-inline/source-playback-controller.ts`
- Modify: `settings_ui/src/editor-inline/editor-playback-types.ts`
- Modify: `settings_ui/src/editor-inline/test-contract.ts`
- Modify: `settings_ui/tests/editor-inline.selected-repeat-auto-advance.integration.test.ts`
- Modify: `settings_ui/tests/editor-inline.chorusing.integration.test.ts`

- [ ] **Step 1: Remove mode-only fields from state**

In `chorusing-state.ts`, reduce `ChorusingState`:

```ts
export interface ChorusingState {
  baseRegion: PlaybackRegion | null;
  markersMs: number[];
  repeatPassesCompleted: number;
  sourceFilename: string;
}
```

Update `emptyChorusingState()`:

```ts
export function emptyChorusingState(): ChorusingState {
  return {
    baseRegion: null,
    markersMs: [],
    repeatPassesCompleted: 0,
    sourceFilename: "",
  };
}
```

- [ ] **Step 2: Delete practice helpers from controller**

Remove these functions from `chorusing-controller.ts`:

```ts
toggleChorusingForOrd
toggleChorusing
ensurePracticeReady
startPracticePlayback
pauseChorusing
pauseChorusingForNormalPlay
chorusingPlaybackRequestForCurrentSuffix
handleChorusingLoopBoundary
chorusingPassMatchesActiveSuffix
setSelectionToActiveSuffix
restoreOrdinaryRepeat
readOrdinaryRepeat
writeRepeatForPractice
```

Keep:

```ts
installChorusingHandlers
moveChorusingForOrd
handleChorusingMarkerPointerDown
clearChorusing
```

- [ ] **Step 3: Remove chorusing source from playback types**

In `editor-playback-types.ts`:

```ts
source?: "post_edit" | "user";
```

In `html-audio-session-types.ts`:

```ts
source: "user" | "post_edit" | "learner_recording";
```

In `source-playback-controller.ts`:

```ts
source: "user" | "post_edit";
```

- [ ] **Step 4: Remove source-specific pass start hacks**

In `actions-audio-clock.ts`, make `playbackPassForSessionRequest()` use request cursor directly:

```ts
return {
  endMs: request.endMs,
  loop: request.loop,
  regionMode: request.regionMode,
  resetCursorMs: request.resetCursorMs ?? request.cursorMs,
  startMs: request.cursorMs,
};
```

In `html-audio-session-controller.ts`, make `playbackPassForRequest()` do the same.

- [ ] **Step 5: Remove generic playback request override**

In `actions-playback.ts`, remove:

```ts
import { chorusingPlaybackRequestForCurrentSuffix } from "./chorusing-controller.js";
```

and:

```ts
const chorusingRequest = chorusingPlaybackRequestForCurrentSuffix(visualizer, ord, startMs);
if (chorusingRequest) return chorusingRequest;
```

- [ ] **Step 6: Update test contract fields**

In `test-contract.ts`, keep marker and counter fields, but set mode fields to stable compatibility values if existing tests still read them:

```ts
chorusingRepeatPassesCompleted: chorusingStateForVisualizer(visualizer).repeatPassesCompleted,
chorusingState: "stopped",
```

Remove `chorusingActiveStartMs`, `chorusingActiveEndMs`, and `chorusingActiveMarkerIndex` from tests once all selected-playback tests assert selection state instead.

- [ ] **Step 7: Run typecheck-focused Svelte tests**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected after implementation: no references remain to `source: "chorusing"` or practice state fields; selected-repeat tests pass.

- [ ] **Step 8: Commit source/state removal**

```bash
git add settings_ui/src/editor-inline/chorusing-state.ts settings_ui/src/editor-inline/chorusing-controller.ts settings_ui/src/editor-inline/actions-playback.ts settings_ui/src/editor-inline/actions-audio-clock.ts settings_ui/src/editor-inline/html-audio-session-controller.ts settings_ui/src/editor-inline/html-audio-session-types.ts settings_ui/src/editor-inline/source-playback-controller.ts settings_ui/src/editor-inline/editor-playback-types.ts settings_ui/src/editor-inline/test-contract.ts settings_ui/tests/editor-inline.selected-repeat-auto-advance.integration.test.ts settings_ui/tests/editor-inline.chorusing.integration.test.ts
git commit -m "Remove chorusing playback mode state" -m "After auto-advance moved to ordinary selected playback, the dedicated chorusing source and practice state only duplicated selection and repeat state. This removes that mode-specific path so Play remains the single playback entry point. Svelte tests were run; the full check and e2e routines were not run for this slice."
```

### Task 7: Remove the Practice Command From UI, Config, and Backend Guidance

**Files:**
- Delete: `settings_ui/src/editor-inline/ChorusingSplitButton.svelte`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/src/editor-inline/command-actions.ts`
- Modify: `settings_ui/src/editor-inline/control-actions.ts`
- Modify: `settings_ui/src/editor-inline/chorusing-toolbar.ts`
- Modify: `settings_ui/src/lib/editor-toolbar-buttons.ts`
- Modify: `settings_ui/src/lib/editor-toolbar-defaults.ts`
- Modify: `settings_ui/src/lib/editor-toolbar-panel-definitions.ts`
- Modify: `settings_ui/src/lib/editor-toolbar-command-slugs.ts`
- Modify: `addon/anki_audio_quick_editor/config.json`
- Modify: `addon/anki_audio_quick_editor/config.schema.json`
- Modify: `addon/anki_audio_quick_editor/editor_actions.py`
- Modify: `addon/anki_audio_quick_editor/editor_playback_request.py`
- Modify: `addon/anki_audio_quick_editor/locales/en.json`
- Modify: other locale files touched by `python3 scripts/dev.py i18n`
- Test: `settings_ui/tests/editor-inline.window-contract.test.ts`
- Test: `settings_ui/tests/editor-inline.chorusing.integration.test.ts`
- Test: `tests/test_config_schema.py` or the existing config schema test file that references editor command enums

- [ ] **Step 1: Remove `ChorusingSplitButton` render branch**

In `EditorControls.svelte`, delete:

```ts
import ChorusingSplitButton from "./ChorusingSplitButton.svelte";
```

Delete the special render branch:

```svelte
{#if item.definition.slug === "chorusing" && button.command === "aqe:chorusing-practice"}
  <ChorusingSplitButton ... />
{:else}
```

Render remaining chorusing panel buttons with `EditorToolbarButton`.

- [ ] **Step 2: Remove command dispatch for practice**

In `command-actions.ts`, delete:

```ts
if (command === "aqe:chorusing-practice") {
  toggleChorusingForOrd(ord);
  return;
}
if (command === "aqe:play" && pauseChorusingForNormalPlay(ord)) {
  return;
}
```

Remove deleted imports:

```ts
toggleChorusingForOrd
pauseChorusingForNormalPlay
```

- [ ] **Step 3: Remove practice from toolbar metadata**

In `editor-toolbar-buttons.ts`, remove `aqe:chorusing-practice` from the `EditorCommand` union and command button list.

In `editor-toolbar-defaults.ts`, remove:

```ts
"aqe:chorusing-practice",
"aqe:chorusing-practice": EditorButtonMode.Icon,
```

In `editor-toolbar-panel-definitions.ts`, set chorusing panel commands to:

```ts
commands: [
  "aqe:chorusing-next",
  "aqe:chorusing-previous",
],
primaryCommand: "aqe:chorusing-next",
```

In `editor-toolbar-command-slugs.ts`, remove:

```ts
"aqe:chorusing-practice": "chorusing-practice",
```

- [ ] **Step 4: Remove practice from config defaults and schema**

In `addon/anki_audio_quick_editor/config.json`, remove `aqe:chorusing-practice` from:

```json
"visible_editor_buttons"
```

and:

```json
"editor_button_modes"
```

In `config.schema.json`, remove `aqe:chorusing-practice` from visible button and button mode enum lists.

In `editor_actions.py`, delete:

```py
CMD_BACK_CHAIN_PRACTICE = "aqe:chorusing-practice"
```

- [ ] **Step 5: Remove backend guidance for chorusing playback**

In `editor_playback_request.py`, replace:

```py
if source == "chorusing":
    return f"{message}. {t('editor.playback.chorusing_guidance')}"
return message
```

with:

```py
return message
```

Remove `editor.playback.chorusing_guidance` from locale files after i18n tells you which catalogs need updates.

- [ ] **Step 6: Update English copy for remaining panel**

In `locales/en.json`, change remaining labels to remove practice-mode wording:

```json
"editor.chorusing.title": "Markers",
"editor.chorusing.panel_description": "Move the selected region between practice markers.",
"editor.command.chorusing_next.label": "Back",
"editor.command.chorusing_next.title": "Move the selection start to the previous marker.",
"editor.command.chorusing_previous.label": "Forward",
"editor.command.chorusing_previous.title": "Move the selection start to the next marker."
```

Keep existing translation keys for now to minimize generated contract churn.

- [ ] **Step 7: Run schema, contracts, i18n, and Svelte tests**

Run:

```bash
python3 scripts/dev.py config-schema
python3 scripts/dev.py contracts-generate
python3 scripts/dev.py contracts-check
python3 scripts/dev.py i18n
python3 scripts/dev.py test-svelte
```

Expected after implementation: no config enum includes `aqe:chorusing-practice`; Svelte compiles without `ChorusingSplitButton`.

- [ ] **Step 8: Commit command removal**

```bash
git add settings_ui/src/editor-inline/EditorControls.svelte settings_ui/src/editor-inline/command-actions.ts settings_ui/src/editor-inline/control-actions.ts settings_ui/src/editor-inline/chorusing-toolbar.ts settings_ui/src/lib/editor-toolbar-buttons.ts settings_ui/src/lib/editor-toolbar-defaults.ts settings_ui/src/lib/editor-toolbar-panel-definitions.ts settings_ui/src/lib/editor-toolbar-command-slugs.ts addon/anki_audio_quick_editor/config.json addon/anki_audio_quick_editor/config.schema.json addon/anki_audio_quick_editor/editor_actions.py addon/anki_audio_quick_editor/editor_playback_request.py addon/anki_audio_quick_editor/locales settings_ui/src/lib/generated/contracts.ts
git rm settings_ui/src/editor-inline/ChorusingSplitButton.svelte
git commit -m "Remove the chorusing practice command" -m "Marker navigation now prepares ordinary selected playback, so a separate practice command adds UI and state complexity without adding behavior. This removes the command from toolbar metadata, config defaults, schema, and playback guidance. Focused schema, i18n, contract, and Svelte checks were run; the full check and e2e routines were not run for this slice."
```

### Task 8: Rewrite E2E Workflows Around Play

**Files:**
- Modify: `e2e/editor_chorusing_helpers.py`
- Modify: `e2e/test_editor_chorusing_playback_workflow.py`
- Modify: `e2e/test_editor_chorusing_markers_workflow.py`
- Modify: `e2e/reviewer_css_isolation_helpers.py`

- [ ] **Step 1: Replace practice helper with selection navigation helper**

In `e2e/editor_chorusing_helpers.py`, replace `_click_chorusing_practice()` with:

```py
def _click_longer_suffix(editor, *, expected_start_ms: int):
    return wait_for_js_condition(
        editor.web,
        """
        (() => {
          const button = document.querySelector('[data-testid="aqe-button-0-chorusing-next"]');
          if (!button || button.disabled) return null;
          button.click();
          return window.__aqeGraphStateForTest?.(0) || null;
        })()
        """,
        lambda state: state is not None and state["selectionStartMs"] == expected_start_ms,
        timeout=5.0,
    )
```

Add:

```py
def _click_play(editor):
    return wait_for_js_condition(
        editor.web,
        """
        (() => {
          const button = document.querySelector('[data-testid="aqe-button-0-play"]');
          if (!button || button.disabled) return null;
          button.click();
          return window.__aqeGraphStateForTest?.(0) || null;
        })()
        """,
        lambda state: state is not None and state["playbackState"] == "playing",
        timeout=5.0,
    )
```

- [ ] **Step 2: Rewrite auto-advance e2e to use Play**

In `test_editor_chorusing_playback_workflow.py`, replace `_click_chorusing_practice(editor)` with:

```py
_click_longer_suffix(editor, expected_start_ms=1500)
_click_play(editor)
```

Update assertions:

```py
assert initial["playbackState"] == "playing"
assert initial["selectionStartMs"] == 1500
assert initial["repeatEnabled"] is True
```

Remove assertions that require:

```py
state["chorusingState"] == "playing"
```

- [ ] **Step 3: Rewrite mixed workflow e2e**

Use the same shape:

```py
_click_longer_suffix(editor, expected_start_ms=1500)
_click_play(editor)
first_repeat = _force_repeat_wrap(editor, 1500)
manual_next = _click_chorusing_next(editor, expected_start_ms=1000)
manual_previous = _click_chorusing_previous(editor, expected_start_ms=1500)
```

Change helper predicates from `chorusingActiveMarkerIndex` to `selectionStartMs`.

- [ ] **Step 4: Update marker e2e expectations**

In `test_editor_chorusing_markers_workflow.py`, remove expectations that the toolbar commands include `aqe:chorusing-practice`. Expected commands should be:

```py
[
    "aqe:chorusing-next",
    "aqe:chorusing-previous",
]
```

After marker insertion, use `_click_longer_suffix()` and assert selected region, not practice state:

```py
selected = _click_longer_suffix(editor, expected_start_ms=1500)
assert selected["selectionStartMs"] == 1500
assert selected["selectionEndMs"] == 2000
```

- [ ] **Step 5: Update reviewer CSS isolation helper**

In `e2e/reviewer_css_isolation_helpers.py`, remove `practice_selector` and `practiceFontSize` expectations. Keep marker row and two navigation button style assertions.

- [ ] **Step 6: Run targeted e2e**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_chorusing_playback_workflow.py
python3 scripts/dev.py test-e2e e2e/test_editor_chorusing_markers_workflow.py
```

Expected after implementation: both targeted real-Anki workflows pass with normal Play.

- [ ] **Step 7: Commit e2e rewrite**

```bash
git add e2e/editor_chorusing_helpers.py e2e/test_editor_chorusing_playback_workflow.py e2e/test_editor_chorusing_markers_workflow.py e2e/reviewer_css_isolation_helpers.py
git commit -m "Test marker practice through normal Play" -m "The real-Anki workflow should match how users actually practice: choose a suffix, then press Play with repeat and auto-advance. These e2e updates remove dependence on the deleted practice command while preserving marker and auto-advance coverage. Targeted e2e tests were run; the full check and parallel e2e routines were not run for this slice."
```

### Task 9: Remove Obsolete Tests and Finish Verification

**Files:**
- Modify: `settings_ui/tests/editor-inline.selected-repeat-auto-advance.integration.test.ts`
- Modify: `settings_ui/tests/editor-inline.chorusing.integration.test.ts`
- Modify: `settings_ui/tests/editor-inline.window-contract.test.ts`
- Modify: `docs/remove-chorusing-practice-mode.md`
- Modify: `WEBVIEW_AND_TEMPLATES.md` only if it references `Play chorusing`

- [ ] **Step 1: Search for deleted command and source**

Run:

```bash
rg "aqe:chorusing-practice|ChorusingSplitButton|source: \"chorusing\"|chorusing_guidance|pauseChorusingForNormalPlay|toggleChorusingForOrd" .
```

Expected after cleanup: no source/test references remain except historical docs under `docs/archive` or this plan. If live docs reference the deleted command, update them.

- [ ] **Step 2: Update window contract test**

If `editor-inline.window-contract.test.ts` expects removed test IDs or globals, update the expected list so no deleted `ChorusingSplitButton` test IDs are required. Keep graph marker test APIs.

- [ ] **Step 3: Run full Svelte and Python checks**

Run:

```bash
python3 scripts/dev.py test-svelte
python3 scripts/dev.py test
python3 scripts/dev.py typecheck
python3 scripts/dev.py lint
python3 scripts/dev.py config-schema
python3 scripts/dev.py contracts-check
```

Expected: all pass.

- [ ] **Step 4: Run targeted e2e again**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_chorusing_playback_workflow.py
```

Expected: pass.

- [ ] **Step 5: Run full gates**

Run:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e-parallel
```

Expected: both pass. If `check` still reports unrelated pre-existing line-count warnings, include them in the final implementation summary.

- [ ] **Step 6: Commit final cleanup**

```bash
git add settings_ui/tests/editor-inline.selected-repeat-auto-advance.integration.test.ts settings_ui/tests/editor-inline.chorusing.integration.test.ts settings_ui/tests/editor-inline.window-contract.test.ts docs/remove-chorusing-practice-mode.md WEBVIEW_AND_TEMPLATES.md
git commit -m "Finish chorusing practice mode removal" -m "The implementation no longer exposes a separate practice mode, and remaining tests/docs now describe marker navigation plus ordinary Play. This final cleanup removes stale references and confirms the full quality gates. Full check and parallel e2e were run for this slice."
```

## Self-Review

- Spec coverage: The plan removes the practice command, keeps marker navigation, moves auto-advance to normal selected repeat playback, re-homes Play settings, removes `source: "chorusing"`, updates config/schema/locales, and rewrites Svelte and e2e coverage.
- Type consistency: The plan consistently uses `resolveSelectionAutoAdvanceBoundary`, `handleSelectedRepeatAutoAdvanceBoundary`, `repeatPassesCompleted`, existing `chorusingAutoAdvance` fields, and existing `chorusingRepeatCount` fields.
- Scope: Config key renaming is intentionally deferred. Command ID renaming for the two navigation buttons is intentionally deferred to avoid breaking existing toolbar config.
