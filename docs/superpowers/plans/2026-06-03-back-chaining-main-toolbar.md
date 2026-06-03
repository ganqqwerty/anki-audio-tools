# Back-Chaining Main Toolbar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move back-chaining from the graph selection submenu to whole-file main-toolbar practice with always-editable markers and mid-practice marker support.

**Architecture:** Keep back-chaining in the editor frontend. Pure marker/index semantics live in `back-chaining-state.ts`; DOM dataset serialization lives in `back-chaining-dom.ts`; controller logic owns whole-file session creation, marker-row clicks, playback requests, and toolbar button state. Settings/config remain schema-first and are propagated through generated contracts.

**Tech Stack:** Svelte 5, TypeScript, Vitest/jsdom, Python config tests, Anki e2e tests, repository `scripts/dev.py` workflow.

---

## File Structure

Modify:

- `settings_ui/src/editor-inline/back-chaining-state.ts`: remove edit/panel/clear/previous state, add active-index normalization and whole-file control availability.
- `settings_ui/src/editor-inline/back-chaining-dom.ts`: serialize the reduced back-chaining state and expose controls snapshots for tests.
- `settings_ui/src/editor-inline/back-chaining-controller.ts`: create whole-file sessions, route toolbar actions, allow marker edits whenever a session exists, restart practice after mid-practice marker edits.
- `settings_ui/src/editor-inline/command-actions.ts`: intercept `aqe:back-chain-practice` and `aqe:back-chain-next` before Python bridge dispatch.
- `settings_ui/src/editor-inline/SelectionToolbar.svelte`: remove the Back-chaining submenu entry and panel.
- `settings_ui/src/editor-inline/BackChainingPanel.svelte`: delete this component.
- `settings_ui/src/editor-inline/GraphVisualizer.svelte`: remove edit/panel dataset attributes, keep marker row.
- `settings_ui/src/editor-inline/styles/visualizer.css`: make marker row hitbox active for whole-file sessions, not edit mode.
- `settings_ui/src/editor-inline/styles/selection.css`: remove back-chaining panel and selection-toolbar Back-chaining styles.
- `settings_ui/src/editor-inline/test-contract.ts`: expose reduced state plus `backChainingSessionActive`.
- `settings_ui/src/lib/editor-toolbar-buttons.ts`: add the two main toolbar commands, defaults, button modes, labels, slugs.
- `settings_ui/src/settings/settings-state.ts`: add the new defaults to fallback settings.
- `settings_ui/src/settings/ToolbarVisibilitySettings.svelte`: no special settings fields are needed; tests prove the new buttons appear.
- `addon/anki_audio_quick_editor/config.schema.json`: add command IDs to `visible_editor_buttons` and `editor_button_modes`.
- `addon/anki_audio_quick_editor/config.json`: include both buttons in default visible buttons and editor button modes.
- `addon/anki_audio_quick_editor/locales/*.json`: add labels/titles for new commands; remove unused Back-chaining submenu strings if no longer referenced.
- `e2e/conftest.py`: add defaults for the two commands.
- Existing settings fixtures under `tests/` and `settings_ui/tests/`: add the new command IDs where defaults are enumerated.
- `settings_ui/tests/editor-inline.back-chaining-state.test.ts`: add pure state tests.
- `settings_ui/tests/editor-inline.back-chaining.integration.test.ts`: rewrite integration coverage around main toolbar and whole-file sessions.
- `settings_ui/tests/editor-inline.actions.test.ts`: add command slug assertions and guard frontend-only commands.
- `settings_ui/tests/app.test.ts` or `settings_ui/tests/settings-state.test.ts`: assert settings visibility includes and persists the new commands.
- `tests/test_config_migration.py`, `tests/test_settings_commands_save.py`, `tests/test_editor_ui.py`, `tests/test_settings_initial_state.py`, `tests/test_settings_state.py`, `tests/settings_command_fixtures.py`: update config/default assertions.
- `e2e/test_editor_back_chaining_playback_workflow.py`: rewrite helpers and add mid-practice marker e2e.

Generate:

- `addon/anki_audio_quick_editor/contracts_generated.py`
- `settings_ui/src/lib/generated/contracts.ts`

These generated files may be absent in a clean worktree and are produced by `python3 scripts/dev.py contracts-generate`.

---

### Task 1: Pure Back-Chaining State

**Files:**
- Modify: `settings_ui/src/editor-inline/back-chaining-state.ts`
- Test: `settings_ui/tests/editor-inline.back-chaining-state.test.ts`

- [ ] **Step 1: Write failing state tests**

Add these imports in `settings_ui/tests/editor-inline.back-chaining-state.test.ts`:

```ts
import {
  activeMarkerIndexAfterMarkerToggle,
  backChainingControlAvailability,
  chooseInitialActiveMarkerIndex,
  defaultBackChainingMarkers,
  deriveActiveSuffix,
  emptyBackChainingState,
  markerNavigationAvailability,
  moveActiveMarkerIndex,
  normalizeBackChainingMarkers,
  toggleBackChainingMarker,
} from "../src/editor-inline/back-chaining-state.js";
```

Add tests:

```ts
it("normalizes the active marker after inserting before the current marker", () => {
  expect(activeMarkerIndexAfterMarkerToggle([0, 500, 750], [0, 250, 500, 750], 1)).toBe(2);
});

it("normalizes the active marker after inserting after the current marker", () => {
  expect(activeMarkerIndexAfterMarkerToggle([0, 500, 750], [0, 500, 625, 750], 1)).toBe(1);
});

it("normalizes the active marker after removing the current marker", () => {
  expect(activeMarkerIndexAfterMarkerToggle([0, 500, 750], [0, 750], 1)).toBe(1);
});

it("normalizes the active marker to null when all markers are removed", () => {
  expect(activeMarkerIndexAfterMarkerToggle([500], [], 0)).toBeNull();
});

it("exposes only whole-file practice availability", () => {
  expect(backChainingControlAvailability({
    ...emptyBackChainingState(),
    baseRegion,
    markersMs: [1200, 1500, 1900],
    activeMarkerIndex: 2,
  })).toEqual({
    canNext: true,
    canPractice: true,
  });
});
```

- [ ] **Step 2: Run the focused state test and verify it fails**

Run:

```bash
cd settings_ui && npm test -- --run tests/editor-inline.back-chaining-state.test.ts
```

Expected: FAIL because `activeMarkerIndexAfterMarkerToggle` is not exported and `backChainingControlAvailability` still returns removed availability fields.

- [ ] **Step 3: Implement the reduced state model**

In `settings_ui/src/editor-inline/back-chaining-state.ts`, replace the state and availability interfaces with:

```ts
export interface BackChainingState {
  activeMarkerIndex: number | null;
  baseRegion: PlaybackRegion | null;
  markersMs: number[];
  ordinaryRepeatEnabled: boolean | null;
  practiceState: BackChainingStatus;
  sourceFilename: string;
}

export interface BackChainingControlAvailability {
  canNext: boolean;
  canPractice: boolean;
}
```

Update `emptyBackChainingState()`:

```ts
export function emptyBackChainingState(): BackChainingState {
  return {
    activeMarkerIndex: null,
    baseRegion: null,
    markersMs: [],
    ordinaryRepeatEnabled: null,
    practiceState: "stopped",
    sourceFilename: "",
  };
}
```

Add the active-index helper:

```ts
export function activeMarkerIndexAfterMarkerToggle(
  previousMarkersMs: readonly number[],
  nextMarkersMs: readonly number[],
  activeMarkerIndex: number | null,
): number | null {
  if (!nextMarkersMs.length) return null;
  const active = normalizeActiveMarkerIndex(previousMarkersMs, activeMarkerIndex);
  const activeMarker = previousMarkersMs[active];
  if (typeof activeMarker !== "number" || !Number.isFinite(activeMarker)) {
    return chooseInitialActiveMarkerIndex(nextMarkersMs);
  }
  const exactIndex = nextMarkersMs.findIndex((marker) => marker === activeMarker);
  if (exactIndex >= 0) return exactIndex;
  const insertionPoint = nextMarkersMs.findIndex((marker) => marker > activeMarker);
  if (insertionPoint < 0) return nextMarkersMs.length - 1;
  return insertionPoint;
}
```

Update availability:

```ts
export function backChainingControlAvailability(state: BackChainingState): BackChainingControlAvailability {
  const hasBaseRegion = state.baseRegion !== null;
  const hasMarkers = state.markersMs.length > 0;
  return {
    canNext: markerNavigationAvailability(state.markersMs, state.activeMarkerIndex).canNext,
    canPractice: hasBaseRegion && hasMarkers,
  };
}
```

- [ ] **Step 4: Run the state test and verify it passes**

Run:

```bash
cd settings_ui && npm test -- --run tests/editor-inline.back-chaining-state.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```bash
git add settings_ui/src/editor-inline/back-chaining-state.ts settings_ui/tests/editor-inline.back-chaining-state.test.ts
git commit -m "refactor: simplify back-chaining state for whole-file practice" -m "Back-chaining no longer has a submenu or edit mode, so the state model now only tracks the whole-file session data needed for practice. The new marker-index helper makes mid-practice marker edits deterministic and testable.

Full check and e2e routines were not run for this incremental state-only commit."
```

---

### Task 2: Toolbar Commands, Config, And Contracts

**Files:**
- Modify: `settings_ui/src/lib/editor-toolbar-buttons.ts`
- Modify: `settings_ui/src/settings/settings-state.ts`
- Modify: `addon/anki_audio_quick_editor/config.schema.json`
- Modify: `addon/anki_audio_quick_editor/config.json`
- Modify: `addon/anki_audio_quick_editor/locales/en.json`
- Modify: locale files under `addon/anki_audio_quick_editor/locales/`
- Modify: `tests/settings_command_fixtures.py`
- Modify: `tests/test_settings_initial_state.py`
- Modify: `tests/test_settings_state.py`
- Modify: `settings_ui/tests/settings-app-helpers.ts`
- Modify: `settings_ui/tests/settings-state.test.ts`
- Generate: `addon/anki_audio_quick_editor/contracts_generated.py`
- Generate: `settings_ui/src/lib/generated/contracts.ts`

- [ ] **Step 1: Write failing toolbar/default tests**

In `settings_ui/tests/editor-inline.actions.test.ts`, extend the first test:

```ts
expect(commandSlugsForTest()["aqe:back-chain-practice"]).toBe("back-chain-practice");
expect(commandSlugsForTest()["aqe:back-chain-next"]).toBe("back-chain-next");
```

In `settings_ui/tests/settings-state.test.ts`, add both commands to `visible_editor_buttons`:

```ts
VisibleEditorButton.AqeBackChainPractice,
VisibleEditorButton.AqeBackChainNext,
```

In `tests/test_settings_commands_save.py`, update the stale-button test payload:

```python
"visible_editor_buttons": [
    "aqe:play",
    "aqe:back-chain-practice",
    "aqe:stale-button",
    "aqe:back-chain-next",
    "aqe:settings",
],
```

and expected saved value:

```python
assert saved_config["visible_editor_buttons"] == [
    "aqe:play",
    "aqe:back-chain-practice",
    "aqe:back-chain-next",
    "aqe:settings",
]
```

- [ ] **Step 2: Run focused tests and verify they fail**

Run:

```bash
cd settings_ui && npm test -- --run tests/editor-inline.actions.test.ts tests/settings-state.test.ts
python3 -m pytest tests/test_settings_commands_save.py::test_settings_save_drops_stale_visible_editor_buttons -q
```

Expected: FAIL because the generated `VisibleEditorButton` enum and toolbar command metadata do not yet include the new commands.

- [ ] **Step 3: Add toolbar command metadata**

In `settings_ui/src/lib/editor-toolbar-buttons.ts`, add to `EditorCommand`:

```ts
| "aqe:back-chain-practice"
| "aqe:back-chain-next"
```

Add both commands to `DEFAULT_VISIBLE_EDITOR_BUTTONS` after Graph:

```ts
"aqe:back-chain-practice",
"aqe:back-chain-next",
```

Add modes to `DEFAULT_EDITOR_BUTTON_MODES`:

```ts
"aqe:back-chain-practice": EditorButtonMode.Icon,
"aqe:back-chain-next": EditorButtonMode.Icon,
```

Add buttons in `commandButtons()` after Graph:

```ts
{
  activeIcon: "pause",
  command: "aqe:back-chain-practice",
  icon: "repeat-2",
  iconOnly: true,
  label: t("editor.command.back_chain_practice.label"),
  title: t("editor.command.back_chain_practice.title"),
},
{
  command: "aqe:back-chain-next",
  icon: "skip-forward",
  iconOnly: true,
  label: t("editor.command.back_chain_next.label"),
  title: t("editor.command.back_chain_next.title"),
},
```

- [ ] **Step 4: Add config schema/defaults**

In `addon/anki_audio_quick_editor/config.schema.json`, add both command IDs to the two enum lists:

```json
"aqe:back-chain-practice",
"aqe:back-chain-next",
```

In `addon/anki_audio_quick_editor/config.json`, add both command IDs to `visible_editor_buttons` after `aqe:analyze`, and add these modes:

```json
"aqe:back-chain-practice": "icon",
"aqe:back-chain-next": "icon",
```

In `settings_ui/src/settings/settings-state.ts`, add:

```ts
VisibleEditorButton.AqeBackChainPractice,
VisibleEditorButton.AqeBackChainNext,
```

to `DEFAULT_VISIBLE_EDITOR_BUTTONS` and `FALLBACK_INITIAL_STATE.config.visible_editor_buttons`.

- [ ] **Step 5: Add localization**

In `addon/anki_audio_quick_editor/locales/en.json`, add:

```json
"editor.command.back_chain_practice.label": "Back-chain",
"editor.command.back_chain_practice.title": "Practice the file from the end with editable back-chaining markers.",
"editor.command.back_chain_next.label": "Longer suffix",
"editor.command.back_chain_next.title": "Move to the next longer back-chaining suffix."
```

Add the same English strings to other locale JSON files so runtime lookup succeeds before translation.

- [ ] **Step 6: Regenerate contracts**

Run:

```bash
python3 scripts/dev.py contracts-generate
```

Expected: generated Python and TypeScript contracts contain `AqeBackChainPractice = "aqe:back-chain-practice"` and `AqeBackChainNext = "aqe:back-chain-next"`.

- [ ] **Step 7: Update remaining default fixtures**

Add the new commands and modes to these files wherever defaults enumerate visible buttons or editor button modes:

```text
tests/settings_command_fixtures.py
tests/test_settings_initial_state.py
tests/test_settings_state.py
settings_ui/tests/settings-app-helpers.ts
settings_ui/tests/bridge.test.ts
settings_ui/tests/async-jobs.test.ts
settings_ui/tests/app.test.ts
e2e/conftest.py
```

Use this visible-button order:

```text
aqe:play
aqe:analyze
aqe:back-chain-practice
aqe:back-chain-next
aqe:show-file
```

Use `"icon"` for both new modes.

- [ ] **Step 8: Run config and contract tests**

Run:

```bash
python3 scripts/dev.py config-schema
python3 scripts/dev.py contracts-check
cd settings_ui && npm test -- --run tests/editor-inline.actions.test.ts tests/settings-state.test.ts tests/bridge.test.ts tests/async-jobs.test.ts tests/app.test.ts
python3 -m pytest tests/test_settings_commands_save.py tests/test_settings_initial_state.py tests/test_settings_state.py tests/test_editor_ui.py -q
```

Expected: PASS.

- [ ] **Step 9: Commit Task 2**

```bash
git add contracts addon/anki_audio_quick_editor settings_ui/src/lib settings_ui/src/settings settings_ui/tests tests e2e/conftest.py
git commit -m "feat: expose back-chaining as toolbar-configurable commands" -m "The submenu is being removed, so back-chaining needs first-class toolbar command IDs that settings, schema validation, and generated contracts all understand. Adding defaults keeps the workflow discoverable while preserving the existing toolbar visibility controls.

Full check and e2e routines were not run for this incremental config and contract commit."
```

---

### Task 3: Whole-File Controller And Toolbar Routing

**Files:**
- Modify: `settings_ui/src/editor-inline/back-chaining-controller.ts`
- Modify: `settings_ui/src/editor-inline/back-chaining-dom.ts`
- Modify: `settings_ui/src/editor-inline/command-actions.ts`
- Modify: `settings_ui/src/editor-inline/control-actions.ts`
- Modify: `settings_ui/src/editor-inline/dom-selectors.ts`
- Modify: `settings_ui/src/editor-inline/test-contract.ts`
- Test: `settings_ui/tests/editor-inline.back-chaining.integration.test.ts`

- [ ] **Step 1: Write failing integration tests for toolbar routing**

In `settings_ui/tests/editor-inline.back-chaining.integration.test.ts`, replace the old selection-submenu entry helper with toolbar clicks:

```ts
function backChainPracticeButton(ord = 0): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>(`[data-testid="aqe-button-${ord}-back-chain-practice"]`)!;
}

function backChainNextButton(ord = 0): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>(`[data-testid="aqe-button-${ord}-back-chain-next"]`)!;
}
```

Add:

```ts
it("starts whole-file back-chaining from the main toolbar and ignores a graph selection", async () => {
  const { svg } = await prepareBackChainingSelection();
  prepareHtmlAudio();

  backChainPracticeButton().click();
  await Promise.resolve();

  expect(document.querySelector('[data-testid="aqe-selection-toolbar-back-chaining-0"]')).toBeNull();
  expect(document.querySelector('[data-testid="aqe-back-chaining-0-panel"]')).toBeNull();
  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    backChainingBaseStartMs: 0,
    backChainingBaseEndMs: 1000,
    backChainingMarkersMs: [0, 333, 667],
    backChainingState: "playing",
    selectionStartMs: 667,
    selectionEndMs: 1000,
  });
  expect(svg).not.toBeNull();
});
```

Add mid-practice insertion coverage:

```ts
it("uses markers added during practice for the next longer suffix", async () => {
  const { row, svg } = await prepareBackChainingSelection();
  prepareHtmlAudio();
  backChainPracticeButton().click();
  await Promise.resolve();

  clickMarkerRow(row, svg, 0.5);
  await Promise.resolve();
  expect(window.__aqeGraphStateForTest?.(0)?.backChainingMarkersMs).toEqual([0, 333, 500, 667]);

  backChainNextButton().click();
  await Promise.resolve();
  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    backChainingActiveMarkerIndex: 2,
    selectionStartMs: 500,
    selectionEndMs: 1000,
  });
});
```

- [ ] **Step 2: Run the integration test and verify it fails**

Run:

```bash
cd settings_ui && npm test -- --run tests/editor-inline.back-chaining.integration.test.ts
```

Expected: FAIL because toolbar commands are still sent to the Python bridge and back-chaining still depends on selection submenu state.

- [ ] **Step 3: Reduce DOM serialization state**

In `settings_ui/src/editor-inline/back-chaining-dom.ts`, update `BackChainingControlsState`:

```ts
export interface BackChainingControlsState {
  activeMarkerIndex: number | null;
  activeSuffixEndMs: number | null;
  activeSuffixStartMs: number | null;
  baseEndMs: number | null;
  baseStartMs: number | null;
  canNext: boolean;
  canPractice: boolean;
  markersMs: number[];
  practiceState: BackChainingStatus;
  sessionActive: boolean;
  visibleActiveRange: { endX: number; startX: number } | null;
  visibleMarkers: Array<{ ms: number; x: number }>;
}
```

Update `writeBackChainingState()` so it does not write edit/panel datasets and does write session activity:

```ts
visualizer.dataset.backChainingActive = state.baseRegion ? "true" : "false";
visualizer.dataset.backChainingBaseStartMs = state.baseRegion ? String(Math.round(state.baseRegion.startMs)) : "";
visualizer.dataset.backChainingBaseEndMs = state.baseRegion ? String(Math.round(state.baseRegion.endMs)) : "";
visualizer.dataset.backChainingMarkersMs = state.markersMs.join(",");
visualizer.dataset.backChainingActiveMarkerIndex = state.activeMarkerIndex === null ? "" : String(state.activeMarkerIndex);
visualizer.dataset.backChainingState = state.practiceState;
```

Update `backChainingStateForVisualizer()` so it no longer reads `editing` or `panelOpen`, and update `controlsSnapshot()` to return only `canNext`, `canPractice`, and `sessionActive`.

- [ ] **Step 4: Implement whole-file controller entry**

In `settings_ui/src/editor-inline/back-chaining-controller.ts`, add imports:

```ts
import { setButtonTooltipContent } from "../lib/rich-tooltip.js";
import { t } from "../lib/i18n.js";
import { buttonFor } from "./dom-selectors.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
```

Remove `enterBackChainingForOrd`, `toggleBackChainingPanelForOrd`, `startBackChainingEditingForOrd`, `clearBackChainingMarkersForOrd`, and `clearBackChainingMarkers`.

Add:

```ts
function wholeFileBaseRegion(visualizer: VisualizerElement): BackChainingState["baseRegion"] {
  const endMs = readVisualizerTargetDurationMs(visualizer);
  if (!Number.isFinite(endMs) || endMs <= 0) return null;
  return { endMs, mode: "full", startMs: 0 };
}

function commitBackChainingState(visualizer: VisualizerElement, state: BackChainingState): void {
  writeBackChainingState(visualizer, state);
  syncBackChainingToolbarButtons(visualizer);
}
```

Update `installBackChainingHandlers()` to call `commitBackChainingState()` for initial state and to clear state on source changes.

Add:

```ts
function ensureWholeFileSession(visualizer: VisualizerElement, state: BackChainingState): BackChainingState | null {
  const baseRegion = state.baseRegion ?? wholeFileBaseRegion(visualizer);
  if (!baseRegion) return null;
  const markersMs = state.markersMs.length ? state.markersMs : defaultBackChainingMarkers(baseRegion);
  const activeMarkerIndex = state.activeMarkerIndex ?? chooseInitialActiveMarkerIndex(markersMs);
  if (activeMarkerIndex === null) return null;
  const nextState = {
    ...state,
    activeMarkerIndex,
    baseRegion,
    markersMs,
    ordinaryRepeatEnabled: state.ordinaryRepeatEnabled ?? readOrdinaryRepeat(visualizer),
    sourceFilename: visualizer.dataset.sourceFilename || "",
  };
  commitBackChainingState(visualizer, nextState);
  return nextState;
}
```

Update `ensurePracticeReady()` to call `ensureWholeFileSession()` instead of `selectionForVisualizer()`.

- [ ] **Step 5: Allow marker clicks during a session and restart practice**

In `handleBackChainingMarkerPointerDown()`, replace the guard:

```ts
if (!visualizer || !svg || !state?.baseRegion) return;
```

Use `activeMarkerIndexAfterMarkerToggle()`:

```ts
const nextActiveMarkerIndex = activeMarkerIndexAfterMarkerToggle(
  state.markersMs,
  toggled.markersMs,
  state.activeMarkerIndex,
);
const nextState = {
  ...state,
  activeMarkerIndex: nextActiveMarkerIndex,
  markersMs: toggled.markersMs,
  practiceState: toggled.markersMs.length ? state.practiceState : "stopped",
};
commitBackChainingState(visualizer, nextState);
if (!toggled.markersMs.length) {
  stopProgressClock(visualizer);
  focusAndSendCommand(Number(visualizer.dataset.aqeFieldOrd || "0"), "aqe:stop-playback");
  return;
}
if (state.practiceState === "playing") startPracticePlayback(visualizer, nextState);
```

- [ ] **Step 6: Add toolbar button sync**

Add:

```ts
function syncBackChainingToolbarButtons(visualizer: VisualizerElement): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const state = backChainingStateForVisualizer(visualizer);
  const availability = backChainingControlAvailability(state);
  const practice = buttonFor(ord, "aqe:back-chain-practice");
  if (practice) {
    const playing = state.practiceState === "playing";
    practice.dataset.aqeButtonState = playing ? "pause" : "default";
    practice.setAttribute("aria-pressed", playing ? "true" : "false");
    setButtonTooltipContent(practice, playing
      ? t("editor.command.back_chain_practice.pause_title")
      : t("editor.command.back_chain_practice.title"));
  }
  const next = buttonFor(ord, "aqe:back-chain-next");
  if (next) {
    next.disabled = document.body.dataset.aqeBusy === "true" || !availability.canNext;
    next.setAttribute("aria-disabled", next.disabled ? "true" : "false");
  }
}
```

Add a pause title string in locales:

```json
"editor.command.back_chain_practice.pause_title": "Pause back-chaining practice."
```

In `control-actions.ts`, update `setControlsBusy()` to call a new exported `syncAllBackChainingToolbarButtons()` from the controller after `allButtons().forEach(updateButtonDisabledState)`.

- [ ] **Step 7: Route frontend-only toolbar commands**

In `settings_ui/src/editor-inline/command-actions.ts`, import:

```ts
import { moveBackChainingForOrd, toggleBackChainingForOrd } from "./back-chaining-controller.js";
```

Then add before playback/Python bridge logic:

```ts
if (command === "aqe:back-chain-practice") {
  toggleBackChainingForOrd(ord);
  return;
}
if (command === "aqe:back-chain-next") {
  moveBackChainingForOrd(ord, "next");
  return;
}
```

- [ ] **Step 8: Run integration test**

Run:

```bash
cd settings_ui && npm test -- --run tests/editor-inline.back-chaining.integration.test.ts
```

Expected: PASS.

- [ ] **Step 9: Commit Task 3**

```bash
git add settings_ui/src/editor-inline settings_ui/tests/editor-inline.back-chaining.integration.test.ts addon/anki_audio_quick_editor/locales
git commit -m "feat: run whole-file back-chaining from toolbar commands" -m "Back-chaining practice now starts from toolbar commands and creates a whole-file session instead of depending on selected-region submenu state. Marker clicks update the active session immediately so mid-practice edits affect playback and navigation.

Full check and e2e routines were not run for this incremental controller commit."
```

---

### Task 4: Remove Selection Submenu UI And Styles

**Files:**
- Modify: `settings_ui/src/editor-inline/SelectionToolbar.svelte`
- Delete: `settings_ui/src/editor-inline/BackChainingPanel.svelte`
- Modify: `settings_ui/src/editor-inline/GraphVisualizer.svelte`
- Modify: `settings_ui/src/editor-inline/styles/visualizer.css`
- Modify: `settings_ui/src/editor-inline/styles/selection.css`
- Modify: `settings_ui/src/editor-inline/selection-toolbar-state.ts`
- Modify: `settings_ui/src/editor-inline/test-contract.ts`
- Test: `settings_ui/tests/editor-inline.back-chaining.integration.test.ts`

- [ ] **Step 1: Write failing removal assertions**

In `settings_ui/tests/editor-inline.back-chaining.integration.test.ts`, assert:

```ts
expect(document.querySelector('[data-testid="aqe-selection-toolbar-back-chaining-0"]')).toBeNull();
expect(document.querySelector('[data-testid="aqe-back-chaining-0-panel"]')).toBeNull();
expect(document.querySelector('[data-testid="aqe-back-chaining-0-edit"]')).toBeNull();
expect(document.querySelector('[data-testid="aqe-back-chaining-0-clear"]')).toBeNull();
expect(document.querySelector('[data-testid="aqe-back-chaining-0-previous"]')).toBeNull();
```

- [ ] **Step 2: Run the integration test and verify it fails**

Run:

```bash
cd settings_ui && npm test -- --run tests/editor-inline.back-chaining.integration.test.ts
```

Expected: FAIL while the old submenu component is still rendered.

- [ ] **Step 3: Remove submenu component usage**

In `SelectionToolbar.svelte`, remove:

```ts
import { toggleBackChainingPanelForOrd } from "./back-chaining-controller.js";
import BackChainingPanel from "./BackChainingPanel.svelte";
```

Delete the Back-chaining `<AqeTooltip>` button block and remove:

```svelte
<BackChainingPanel {target} />
```

Delete `settings_ui/src/editor-inline/BackChainingPanel.svelte`.

- [ ] **Step 4: Remove selection-toolbar sync for Back-chaining button**

In `selection-toolbar-state.ts`, delete:

```ts
function backChainingButtonFor(visualizer: VisualizerElement): HTMLButtonElement | null {
  return visualizer.querySelector<HTMLButtonElement>(".aqe-selection-toolbar-back-chaining");
}

function syncToolbarBackChainingButton(visualizer: VisualizerElement, busy: boolean): void {
  const button = backChainingButtonFor(visualizer);
  if (!button) return;
  const panelOpen = visualizer.dataset.backChainingPanelOpen === "true";
  button.disabled = busy;
  button.dataset.aqeButtonState = busy ? "unavailable" : panelOpen ? "active" : "default";
  button.setAttribute("aria-expanded", panelOpen ? "true" : "false");
  button.setAttribute("aria-pressed", panelOpen ? "true" : "false");
  setButtonTooltipContent(button, t("editor.back_chaining.entry_title"));
  button.setAttribute("aria-disabled", button.disabled ? "true" : "false");
}
```

Remove the call to `syncToolbarBackChainingButton(visualizer, busy)`.

- [ ] **Step 5: Remove edit/panel datasets**

In `GraphVisualizer.svelte`, remove:

```svelte
data-back-chaining-editing="false"
data-back-chaining-panel-open="false"
```

Keep:

```svelte
data-back-chaining-active="false"
data-back-chaining-state="stopped"
```

- [ ] **Step 6: Update CSS**

In `styles/visualizer.css`, replace:

```css
.aqe-visualizer[data-back-chaining-editing="true"] .aqe-back-chaining-marker-hitbox,
.aqe-visualizer[data-back-chaining-state="playing"] .aqe-back-chaining-marker-hitbox,
.aqe-visualizer[data-back-chaining-state="paused"] .aqe-back-chaining-marker-hitbox {
  pointer-events: all;
}
```

with:

```css
.aqe-visualizer[data-back-chaining-active="true"] .aqe-back-chaining-marker-hitbox {
  pointer-events: all;
}
```

In `styles/selection.css`, remove the `.aqe-back-chaining-panel`, `.aqe-back-chaining-header`, `.aqe-back-chaining-controls`, `.aqe-back-chaining-button`, and `.aqe-selection-toolbar-back-chaining` style blocks.

- [ ] **Step 7: Run integration test**

Run:

```bash
cd settings_ui && npm test -- --run tests/editor-inline.back-chaining.integration.test.ts
```

Expected: PASS.

- [ ] **Step 8: Commit Task 4**

```bash
git add settings_ui/src/editor-inline settings_ui/tests/editor-inline.back-chaining.integration.test.ts
git add -u settings_ui/src/editor-inline/BackChainingPanel.svelte
git commit -m "refactor: remove back-chaining selection submenu" -m "Back-chaining is now a whole-file toolbar workflow, so the selected-region disclosure, panel, edit action, clear action, and shorter-suffix action are obsolete. Removing the UI and dataset sync prevents the old selection-scoped behavior from surviving by accident.

Full check and e2e routines were not run for this incremental UI-removal commit."
```

---

### Task 5: Frontend Coverage And Settings Visibility

**Files:**
- Modify: `settings_ui/tests/editor-inline.back-chaining.integration.test.ts`
- Modify: `settings_ui/tests/editor-inline.actions.test.ts`
- Modify: `settings_ui/tests/app.test.ts`
- Modify: `settings_ui/tests/settings-state.test.ts`

- [ ] **Step 1: Add complete Svelte integration coverage**

Ensure `settings_ui/tests/editor-inline.back-chaining.integration.test.ts` includes these test cases:

```ts
it("renders main toolbar back-chaining controls when visible", async () => {
  await prepareBackChainingSelection();
  expect(backChainPracticeButton()).not.toBeNull();
  expect(backChainNextButton()).not.toBeNull();
});
```

```ts
it("removes a marker during practice and clamps the active suffix", async () => {
  const { row, svg } = await prepareBackChainingSelection();
  prepareHtmlAudio();
  backChainPracticeButton().click();
  await Promise.resolve();
  clickMarkerRow(row, svg, 2 / 3);
  await Promise.resolve();
  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    backChainingMarkersMs: [0, 333],
    backChainingActiveMarkerIndex: 1,
    selectionStartMs: 333,
  });
});
```

```ts
it("does not send back-chaining toolbar commands to Python", async () => {
  await prepareBackChainingSelection();
  backChainPracticeButton().click();
  backChainNextButton().click();
  expect(bridgeCommands()).not.toContain("aqe:back-chain-practice");
  expect(bridgeCommands()).not.toContain("aqe:back-chain-next");
});
```

- [ ] **Step 2: Add settings visibility assertions**

In `settings_ui/tests/app.test.ts`, add an assertion in the toolbar visibility test:

```ts
expect(screen.getByTestId("button-settings-back-chain-practice")).not.toBeNull();
expect(screen.getByTestId("button-settings-back-chain-next")).not.toBeNull();
```

`settings_ui/tests/app.test.ts` already imports Testing Library `screen`, so use the `screen.getByTestId(...)` assertions above.

- [ ] **Step 3: Run Svelte tests**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected: PASS.

- [ ] **Step 4: Commit Task 5**

```bash
git add settings_ui/tests
git commit -m "test: cover toolbar back-chaining frontend behavior" -m "The removed submenu and new toolbar commands need frontend tests that lock the intended behavior: whole-file sessions, editable markers without edit mode, mid-practice marker changes, and settings visibility. This prevents regressions back to selection-scoped practice.

Full check and e2e routines were not run for this frontend-test commit."
```

---

### Task 6: Python Config And Editor Injection Coverage

**Files:**
- Modify: `tests/test_config_migration.py`
- Modify: `tests/test_settings_commands_save.py`
- Modify: `tests/test_editor_ui.py`
- Modify: `tests/test_settings_initial_state.py`
- Modify: `tests/test_settings_state.py`
- Modify: `tests/settings_command_fixtures.py`

- [ ] **Step 1: Add focused Python assertions**

In `tests/test_editor_ui.py`, extend `test_injection_script_embeds_audio_field_indices_and_bundle()`:

```python
assert "aqe:back-chain-practice" in script
assert "aqe:back-chain-next" in script
```

In `tests/test_config_migration.py`, update defaults in visible/mode tests to include:

```python
"aqe:back-chain-practice",
"aqe:back-chain-next",
```

and:

```python
"aqe:back-chain-practice": "icon",
"aqe:back-chain-next": "icon",
```

In `tests/test_settings_commands_save.py`, keep the assertion from Task 2 proving sanitization preserves the new commands.

- [ ] **Step 2: Run focused Python tests**

Run:

```bash
python3 -m pytest tests/test_config_migration.py tests/test_settings_commands_save.py tests/test_editor_ui.py tests/test_settings_initial_state.py tests/test_settings_state.py -q
```

Expected: PASS.

- [ ] **Step 3: Run schema/contract checks**

Run:

```bash
python3 scripts/dev.py config-schema
python3 scripts/dev.py contracts-check
```

Expected: PASS.

- [ ] **Step 4: Commit Task 6**

```bash
git add tests addon/anki_audio_quick_editor/config.schema.json addon/anki_audio_quick_editor/config.json addon/anki_audio_quick_editor/contracts_generated.py settings_ui/src/lib/generated/contracts.ts
git commit -m "test: validate back-chaining toolbar config plumbing" -m "Back-chaining toolbar commands are persisted settings values, so Python schema, generated contracts, migration cleanup, settings save sanitization, and editor config injection all need coverage. These tests protect the command IDs from being dropped as stale config.

Full check and e2e routines were not run for this focused config-test commit."
```

---

### Task 7: E2E Workflow Updates

**Files:**
- Modify: `e2e/test_editor_back_chaining_playback_workflow.py`
- Modify: `e2e/reviewer_css_isolation_helpers.py`
- Modify: `e2e/test_reviewer_audio_editor_workflow.py` only if it still calls the removed CSS helper expectations

- [ ] **Step 1: Rewrite e2e helpers for toolbar actions**

In `e2e/test_editor_back_chaining_playback_workflow.py`, replace `_enable_back_chaining_editing()` with:

```python
def _start_back_chaining_practice(editor) -> None:
    wait_for_js_condition(
        editor.web,
        """
        (() => {
          const button = document.querySelector('[data-testid="aqe-button-0-back-chain-practice"]');
          if (!button || button.disabled) return null;
          if (window.__aqeGraphStateForTest?.(0)?.backChainingState !== "playing") button.click();
          return window.__aqeGraphStateForTest?.(0) || null;
        })()
        """,
        lambda state: state is not None
        and state["backChainingState"] == "playing"
        and state["backChainingBaseStartMs"] == 0
        and state["backChainingBaseEndMs"] == 2000
        and state["backChainingMarkersMs"] == [0, 667, 1333],
        timeout=5.0,
    )
```

Replace `_click_back_chaining_practice()` with this pause/resume helper:

```python
def _click_back_chaining_practice(editor, *, expected_state: str) -> None:
    wait_for_js_condition(
        editor.web,
        """
        (() => {
          const button = document.querySelector('[data-testid="aqe-button-0-back-chain-practice"]');
          if (!button || button.disabled) return null;
          button.click();
          return window.__aqeGraphStateForTest?.(0) || null;
        })()
        """,
        lambda state: state is not None and state["backChainingState"] == expected_state,
        timeout=5.0,
    )
```

Replace `_click_back_chaining_next()` selector with:

```python
const button = document.querySelector('[data-testid="aqe-button-0-back-chain-next"]');
```

- [ ] **Step 2: Update existing e2e expectations**

In `test_back_chaining_practice_loops_suffixes_and_pauses_for_normal_play`, remove `_shift_drag_region()` as a precondition for back-chaining and expect:

```python
state["backChainingMarkersMs"] == [0, 667, 1333]
state["selectionStartMs"] == 1333
state["selectionEndMs"] == 2000
```

After one longer-suffix click, expect:

```python
state["backChainingActiveMarkerIndex"] == 1
state["selectionStartMs"] == 667
```

After the second longer-suffix click, expect:

```python
state["backChainingActiveMarkerIndex"] == 0
state["selectionStartMs"] == 0
```

Update the status guidance string only if product copy changes; otherwise keep the existing assertion because Python playback still sees `source: "back_chaining"`.

- [ ] **Step 3: Add e2e selection-ignored test**

Add:

```python
def test_back_chaining_ignores_committed_graph_selection(anki_mw, ffmpeg_config) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_back_chaining_whole_file.wav",
        2.0,
    )
    try:
        _shift_drag_region(editor, 0.2, 0.8)
        _start_back_chaining_practice(editor)
        state = _state(
            editor,
            lambda value: value["backChainingBaseStartMs"] == 0
            and value["backChainingBaseEndMs"] == 2000
            and value["selectionStartMs"] == 1333
            and value["selectionEndMs"] == 2000,
        )
        assert state["backChainingMarkersMs"] == [0, 667, 1333]
    finally:
        editor.set_note(None)
        parent.close()
```

- [ ] **Step 4: Add e2e mid-practice marker test**

Add:

```python
def test_back_chaining_marker_added_mid_practice_affects_next_suffix(anki_mw, ffmpeg_config) -> None:
    _media_dir, _source, _note, editor, parent, _track = _open_tone_editor(
        anki_mw,
        ffmpeg_config,
        "editor_back_chaining_mid_practice_marker.wav",
        2.0,
    )
    try:
        _start_back_chaining_practice(editor)
        run_js(editor.web, "window.__aqeSetTimeViewportForTest?.(0, 0, 2000)")
        _click_back_chaining_marker(editor, 0.5, expected_count=4)
        _click_back_chaining_next(editor, expected_index=2)
        state = _state(
            editor,
            lambda value: value["backChainingMarkersMs"] == [0, 667, 1000, 1333]
            and value["selectionStartMs"] == 1000
            and value["selectionEndMs"] == 2000,
        )
        assert state["backChainingActiveMarkerIndex"] == 2
    finally:
        editor.set_note(None)
        parent.close()
```

- [ ] **Step 5: Update reviewer CSS isolation helper**

In `e2e/reviewer_css_isolation_helpers.py`, remove `assert_reviewer_back_chaining_panel_css_isolated()` or change it to assert the removed UI is absent:

```python
def assert_reviewer_back_chaining_panel_removed(reviewer, field_ord: int) -> None:
    result = wait_for_js_condition(
        reviewer.web,
        f"""
        (() => {{
          return {{
            entry: Boolean(document.querySelector('[data-testid="aqe-selection-toolbar-back-chaining-{field_ord}"]')),
            panel: Boolean(document.querySelector('[data-testid="aqe-back-chaining-{field_ord}-panel"]')),
          }};
        }})()
        """,
        lambda value: value is not None,
        timeout=5.0,
    )
    assert result == {"entry": False, "panel": False}
```

Update `e2e/test_reviewer_audio_editor_workflow.py` imports and calls accordingly.

- [ ] **Step 6: Run focused e2e**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS for the full e2e suite, including the back-chaining workflow.

- [ ] **Step 7: Commit Task 7**

```bash
git add e2e
git commit -m "test: cover whole-file back-chaining e2e workflow" -m "The user-facing behavior changes from a selected-region submenu to whole-file toolbar practice, so e2e needs to prove selections are ignored, zoomed marker placement still works, marker-row hit testing remains correct, and markers added during practice affect the next suffix.

Full check was not run for this e2e-focused commit; the focused e2e command was run."
```

---

### Task 8: Final Verification And Documentation Audit

**Files:**
- Modify docs only if tests reveal stale back-chaining documentation.

- [ ] **Step 1: Run the full Svelte test suite**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected: PASS.

- [ ] **Step 2: Run the reusable quality gate**

Run:

```bash
python3 scripts/dev.py check
```

Expected: PASS.

- [ ] **Step 3: Run full e2e**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS.

- [ ] **Step 4: Search for stale submenu references**

Run:

```bash
rg -n "back-chaining.*submenu|BackChainingPanel|aqe-selection-toolbar-back-chaining|edit_markers|clear_title|previous_title|panelOpen|backChainingEditing|backChainingPanelOpen" .
```

Expected: no source references to removed UI/state. Remove locale-only references to obsolete keys unless an active source reference still uses the key.

- [ ] **Step 5: Update documentation if stale references remain**

Update any product docs found by the stale-reference search. Do not change generated bundles by hand. When the search finds no stale docs, leave docs unchanged and record that result in the final summary.

- [ ] **Step 6: Final commit**

When Step 5 changed docs:

```bash
git add docs README.md AGENTS.md WEBVIEW_AND_TEMPLATES.md EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md
git commit -m "docs: align back-chaining docs with toolbar workflow" -m "Back-chaining now starts from toolbar commands and no longer has a selected-region submenu, so any docs that described the old workflow need to match the implemented behavior.

Full check and e2e routines were run after implementation."
```

When Step 5 made no changes, do not create an empty commit.
