# Chorusing Auto-Advance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dedicated Chorusing split menu with field-local controls for pause between repeats, auto-advance, and repeat count; persist those controls as Chorusing defaults; and make Chorusing automatically move through suffix segments after the configured number of repeats.

**Architecture:** Keep Chorusing as a non-mutating editor workflow. Store persisted defaults in the existing add-on config and bridge save-defaults path, mirror them into the existing field-local split-state layer, render a dedicated Chorusing split component instead of expanding the generic split button, and add a narrow playback-loop hook so auto-advance can reuse the current Chorusing controller.

**Tech Stack:** Python config/bridge, JSON Schema contracts, Svelte 5, TypeScript, Vitest, pytest, Playwright e2e

**Approved Spec:** `docs/superpowers/specs/2026-06-13-chorusing-autoadvance-design.md`

---

### Task 1: Add persisted Chorusing defaults and bridge validation

**Files:**
- Modify: `addon/anki_audio_quick_editor/config.json`
- Modify: `addon/anki_audio_quick_editor/config.schema.json`
- Modify: `addon/anki_audio_quick_editor/editor_split_defaults.py`
- Modify: `addon/anki_audio_quick_editor/editor_ui.py`
- Modify: `addon/anki_audio_quick_editor/editor_webview_injection.py`
- Modify: `tests/test_contract_generation.py`
- Modify: `tests/test_editor_bridge_facade_commands.py`
- Modify: `tests/test_editor_ui.py`
- Modify: `tests/test_config_migration_defaults.py`

- [ ] **Step 1: Write failing backend/default tests for the three config keys**

```py
assert "chorusing_pause_seconds" in schema["properties"]
assert schema["properties"]["chorusing_pause_seconds"]["default"] == 0.0
assert schema["properties"]["chorusing_auto_advance_by_default"]["default"] is False
assert schema["properties"]["chorusing_auto_advance_repeats"]["default"] == 3
```

```py
updates = split_default_config_updates(
    {
        "chorusingPauseSeconds": 2.6,
        "chorusingAutoAdvanceByDefault": True,
        "chorusingAutoAdvanceRepeats": 5,
    }
)
assert updates == {
    "chorusing_pause_seconds": 2.6,
    "chorusing_auto_advance_by_default": True,
    "chorusing_auto_advance_repeats": 5,
}
```

```py
updates = split_default_config_updates(
    {
        "chorusingPauseSeconds": -4,
        "chorusingAutoAdvanceByDefault": "yes",
        "chorusingAutoAdvanceRepeats": 200,
    }
)
assert updates == {
    "chorusing_pause_seconds": 0.0,
    "chorusing_auto_advance_repeats": 20,
}
```

- [ ] **Step 2: Run the focused failing Python tests**

```bash
python3 -m pytest tests/test_contract_generation.py tests/test_editor_bridge_facade_commands.py tests/test_editor_ui.py tests/test_config_migration_defaults.py -q
```

Expected output before implementation:

```text
FAILED tests/test_contract_generation.py
FAILED tests/test_editor_bridge_facade_commands.py
FAILED tests/test_editor_ui.py
FAILED tests/test_config_migration_defaults.py
```

- [ ] **Step 3: Add the config defaults and schema properties**

```json
"chorusing_pause_seconds": 0.0,
"chorusing_auto_advance_by_default": false,
"chorusing_auto_advance_repeats": 3
```

```json
"chorusing_pause_seconds": {
  "type": "number",
  "minimum": 0,
  "maximum": 10,
  "default": 0.0
},
"chorusing_auto_advance_by_default": {
  "type": "boolean",
  "default": false
},
"chorusing_auto_advance_repeats": {
  "type": "integer",
  "minimum": 1,
  "maximum": 20,
  "default": 3
}
```

- [ ] **Step 4: Add backend sanitization for Chorusing split-default saves**

```py
MAX_CHORUSING_REPEAT_COUNT = 20


def _chorusing_updates(raw_defaults: Mapping[str, Any]) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    raw_pause = raw_defaults.get("chorusingPauseSeconds")
    if isinstance(raw_pause, (int, float)) and not isinstance(raw_pause, bool):
        updates["chorusing_pause_seconds"] = round(
            _clamp_float(float(raw_pause), 0.0, MAX_REPEAT_PAUSE_SECONDS),
            1,
        )

    raw_auto_advance = raw_defaults.get("chorusingAutoAdvanceByDefault")
    if isinstance(raw_auto_advance, bool):
        updates["chorusing_auto_advance_by_default"] = raw_auto_advance

    raw_repeats = raw_defaults.get("chorusingAutoAdvanceRepeats")
    if isinstance(raw_repeats, (int, float)) and not isinstance(raw_repeats, bool):
        updates["chorusing_auto_advance_repeats"] = int(
            _clamp_float(round(float(raw_repeats)), 1, MAX_CHORUSING_REPEAT_COUNT)
        )
    return updates
```

- [ ] **Step 5: Include the defaults in editor webview injection and fallback state**

```py
"chorusingPauseSeconds": float(config.get("chorusing_pause_seconds", 0.0)),
"chorusingAutoAdvanceByDefault": bool(config.get("chorusing_auto_advance_by_default", False)),
"chorusingAutoAdvanceRepeats": int(config.get("chorusing_auto_advance_repeats", 3)),
```

- [ ] **Step 6: Regenerate and verify contracts/config**

```bash
python3 scripts/dev.py contracts-generate
```

```bash
python3 scripts/dev.py contracts-check
```

```bash
python3 scripts/dev.py config-schema
```

- [ ] **Step 7: Re-run the focused Python tests**

```bash
python3 -m pytest tests/test_contract_generation.py tests/test_editor_bridge_facade_commands.py tests/test_editor_ui.py tests/test_config_migration_defaults.py -q
```

Expected output after implementation:

```text
passed
```

- [ ] **Step 8: Commit the backend defaults slice**

```bash
git add addon/anki_audio_quick_editor/config.json addon/anki_audio_quick_editor/config.schema.json addon/anki_audio_quick_editor/editor_split_defaults.py addon/anki_audio_quick_editor/editor_ui.py addon/anki_audio_quick_editor/editor_webview_injection.py tests/test_contract_generation.py tests/test_editor_bridge_facade_commands.py tests/test_editor_ui.py tests/test_config_migration_defaults.py
git commit -m "Persist chorusing split defaults" -m "Chorusing needs its own default values so field-local menu choices can be saved and restored without sharing Play settings. This adds schema-backed defaults, bridge validation, and editor injection so the webview receives stable Chorusing behavior on first render. Focused schema, contract, and bridge tests were run; the full check and e2e routines were not run for this slice."
```

### Task 2: Extend field-local split state for Chorusing

**Files:**
- Modify: `settings_ui/src/editor-inline/editor-runtime-types.ts`
- Modify: `settings_ui/src/editor-inline/split-button-state-defaults.ts`
- Modify: `settings_ui/src/editor-inline/split-button-state-core.ts`
- Modify: `settings_ui/src/editor-inline/split-button-state-setters.ts`
- Modify: `settings_ui/src/editor-inline/split-button-state-commands.ts`
- Modify: `settings_ui/src/editor-inline/split-button-state.ts`
- Modify: `settings_ui/tests/split-button-state-state.test.ts`
- Modify: `settings_ui/tests/split-button-state-payloads.test.ts`

- [ ] **Step 1: Write failing split-state tests for isolated Chorusing values**

```ts
const state = getSplitButtonState(0);
expect(state.chorusingPauseSeconds).toBe(0);
expect(state.chorusingAutoAdvance).toBe(false);
expect(state.chorusingRepeatCount).toBe(3);
expect(state.chorusingEdited).toBe(false);
```

```ts
setChorusingPauseSecondsForField(0, 1.5);
setChorusingAutoAdvanceForField(0, true);
setChorusingRepeatCountForField(0, 6);

const state = getSplitButtonState(0);
expect(state.chorusingPauseSeconds).toBe(1.5);
expect(state.chorusingAutoAdvance).toBe(true);
expect(state.chorusingRepeatCount).toBe(6);
expect(state.chorusingEdited).toBe(true);
```

```ts
const request = buildSplitDefaultSaveRequestFromState("aqe:chorusing-practice", getSplitButtonState(0));
expect(request.defaults).toEqual({
  chorusingPauseSeconds: 1.5,
  chorusingAutoAdvanceByDefault: true,
  chorusingAutoAdvanceRepeats: 6,
});
```

- [ ] **Step 2: Run the focused failing split-state tests**

```bash
npm --prefix settings_ui test -- split-button-state-state.test.ts split-button-state-payloads.test.ts
```

Expected output before implementation:

```text
FAIL  settings_ui/tests/split-button-state-state.test.ts
FAIL  settings_ui/tests/split-button-state-payloads.test.ts
```

- [ ] **Step 3: Add Chorusing fields to runtime split-state types**

```ts
export interface SplitButtonDefaults {
  repeatPauseSeconds: number;
  chorusingPauseSeconds: number;
  chorusingAutoAdvanceByDefault: boolean;
  chorusingAutoAdvanceRepeats: number;
}

export interface FieldSplitButtonState {
  repeatPauseSeconds: number;
  defaultRepeatPauseSeconds: number;
  repeatPauseEdited: boolean;
  chorusingPauseSeconds: number;
  defaultChorusingPauseSeconds: number;
  chorusingAutoAdvance: boolean;
  defaultChorusingAutoAdvance: boolean;
  chorusingRepeatCount: number;
  defaultChorusingRepeatCount: number;
  chorusingEdited: boolean;
}
```

- [ ] **Step 4: Add clamp/format helpers and defaults**

```ts
export const CHORUSING_REPEAT_COUNT_MIN = 1;
export const CHORUSING_REPEAT_COUNT_MAX = 20;
export const DEFAULT_CHORUSING_PAUSE_SECONDS = 0;
export const DEFAULT_CHORUSING_AUTO_ADVANCE = false;
export const DEFAULT_CHORUSING_REPEAT_COUNT = 3;

export function clampChorusingRepeatCount(value: number): number {
  return Math.min(CHORUSING_REPEAT_COUNT_MAX, Math.max(CHORUSING_REPEAT_COUNT_MIN, Math.round(value)));
}
```

- [ ] **Step 5: Initialize, sync, and promote Chorusing split defaults**

```ts
const defaultChorusingPauseSeconds = clampRepeatPauseSeconds(defaults.chorusingPauseSeconds);
const defaultChorusingAutoAdvance = defaults.chorusingAutoAdvanceByDefault === true;
const defaultChorusingRepeatCount = clampChorusingRepeatCount(defaults.chorusingAutoAdvanceRepeats);
```

```ts
chorusingPauseSeconds: defaultChorusingPauseSeconds,
defaultChorusingPauseSeconds,
chorusingAutoAdvance: defaultChorusingAutoAdvance,
defaultChorusingAutoAdvance,
chorusingRepeatCount: defaultChorusingRepeatCount,
defaultChorusingRepeatCount,
chorusingEdited: false,
```

- [ ] **Step 6: Add Chorusing setters and export them**

```ts
export const CHORUSING_SPLIT_STATE_CHANGED_EVENT = "aqe-chorusing-split-state-changed";

export function setChorusingAutoAdvanceForField(ord: number, enabled: boolean): void {
  updateSplitButtonStateForField(ord, (state) => ({
    ...state,
    chorusingAutoAdvance: enabled,
    chorusingEdited: true,
  }));
  dispatchSplitStateChanged(CHORUSING_SPLIT_STATE_CHANGED_EVENT, ord);
}
```

- [ ] **Step 7: Add the Chorusing save-default payload case**

```ts
case "aqe:chorusing-practice":
  return {
    command,
    defaults: {
      chorusingPauseSeconds: state.chorusingPauseSeconds,
      chorusingAutoAdvanceByDefault: state.chorusingAutoAdvance,
      chorusingAutoAdvanceRepeats: state.chorusingRepeatCount,
    },
  };
```

- [ ] **Step 8: Re-run the focused split-state tests**

```bash
npm --prefix settings_ui test -- split-button-state-state.test.ts split-button-state-payloads.test.ts
```

Expected output after implementation:

```text
PASS  settings_ui/tests/split-button-state-state.test.ts
PASS  settings_ui/tests/split-button-state-payloads.test.ts
```

- [ ] **Step 9: Commit the frontend state slice**

```bash
git add settings_ui/src/editor-inline/editor-runtime-types.ts settings_ui/src/editor-inline/split-button-state-defaults.ts settings_ui/src/editor-inline/split-button-state-core.ts settings_ui/src/editor-inline/split-button-state-setters.ts settings_ui/src/editor-inline/split-button-state-commands.ts settings_ui/src/editor-inline/split-button-state.ts settings_ui/tests/split-button-state-state.test.ts settings_ui/tests/split-button-state-payloads.test.ts
git commit -m "Track chorusing split state per field" -m "Chorusing auto-advance must be adjustable without leaking into Play split settings or other fields. This adds isolated field-local state, default promotion, sanitization, and save-default payloads for the dedicated Chorusing menu. Focused Vitest split-state tests were run; the full check and e2e routines were not run for this slice."
```

### Task 3: Expose Chorusing defaults in Settings

**Files:**
- Modify: `settings_ui/src/settings/settings-state.ts`
- Modify: `settings_ui/src/settings/ToolbarPanelSettingsFields.svelte`
- Modify: `settings_ui/tests/settings-app-helpers.ts`
- Modify: `settings_ui/tests/settings-bridge.test.ts`
- Modify: `settings_ui/tests/async-jobs.test.ts`
- Modify: `tests/settings_command_fixtures.py`
- Modify: `tests/test_settings_initial_state.py`
- Modify: `tests/test_settings_state.py`
- Modify: `e2e/conftest.py`
- Modify: `e2e/editor_note_helpers.py`
- Modify: `addon/anki_audio_quick_editor/locales/en.json`
- Modify: `addon/anki_audio_quick_editor/locales/de.json`
- Modify: `addon/anki_audio_quick_editor/locales/ja.json`
- Modify: `addon/anki_audio_quick_editor/locales/ru.json`
- Modify: `addon/anki_audio_quick_editor/locales/vi.json`
- Modify: `addon/anki_audio_quick_editor/locales/zh_CN.json`
- Modify: `addon/anki_audio_quick_editor/locales/zh_TW.json`

- [ ] **Step 1: Write failing Settings tests/fixture expectations**

```ts
expect(config.chorusing_pause_seconds).toBe(0);
expect(config.chorusing_auto_advance_by_default).toBe(false);
expect(config.chorusing_auto_advance_repeats).toBe(3);
```

```py
assert initial["config"]["chorusing_pause_seconds"] == 0.0
assert initial["config"]["chorusing_auto_advance_by_default"] is False
assert initial["config"]["chorusing_auto_advance_repeats"] == 3
```

- [ ] **Step 2: Run the focused failing Settings tests**

```bash
npm --prefix settings_ui test -- settings-bridge.test.ts async-jobs.test.ts
```

```bash
python3 -m pytest tests/test_settings_initial_state.py tests/test_settings_state.py -q
```

Expected output before implementation:

```text
FAILED tests/test_settings_initial_state.py
FAILED tests/test_settings_state.py
```

- [ ] **Step 3: Add fallback Settings config values**

```ts
chorusing_pause_seconds: 0,
chorusing_auto_advance_by_default: false,
chorusing_auto_advance_repeats: 3,
```

- [ ] **Step 4: Add Chorusing fields to the command-specific Settings panel**

```svelte
{#if command === "aqe:chorusing-practice"}
  <UnitNumberInput
    id="chorusing-pause-seconds"
    label={t("settings.chorusing.pause_seconds")}
    bind:value={config.chorusing_pause_seconds}
    min={0}
    max={10}
    step={0.1}
    unit={t("settings.unit.seconds")}
    testId="chorusing-pause-seconds"
  />
  <label class="aqe-settings-checkbox-row">
    <input
      type="checkbox"
      bind:checked={config.chorusing_auto_advance_by_default}
      data-testid="chorusing-auto-advance-by-default"
    />
    <span>{t("settings.chorusing.auto_advance_by_default")}</span>
  </label>
  <UnitNumberInput
    id="chorusing-auto-advance-repeats"
    label={t("settings.chorusing.auto_advance_repeats")}
    bind:value={config.chorusing_auto_advance_repeats}
    min={1}
    max={20}
    step={1}
    unit={t("settings.unit.times")}
    testId="chorusing-auto-advance-repeats"
  />
{/if}
```

- [ ] **Step 5: Add localized labels to every locale catalog**

```json
"settings.chorusing.pause_seconds": "Pause between repeats",
"settings.chorusing.auto_advance_by_default": "Auto-advance by default",
"settings.chorusing.auto_advance_repeats": "Repeats before auto-advance"
```

- [ ] **Step 6: Update Settings/e2e fixtures so the new required keys are present**

```py
"chorusing_pause_seconds": 0.0,
"chorusing_auto_advance_by_default": False,
"chorusing_auto_advance_repeats": 3,
```

```ts
chorusing_pause_seconds: 0,
chorusing_auto_advance_by_default: false,
chorusing_auto_advance_repeats: 3,
```

- [ ] **Step 7: Re-run Settings verification**

```bash
npm --prefix settings_ui test -- settings-bridge.test.ts async-jobs.test.ts
```

```bash
python3 -m pytest tests/test_settings_initial_state.py tests/test_settings_state.py -q
```

Expected output after implementation:

```text
passed
```

- [ ] **Step 8: Commit the Settings slice**

```bash
git add settings_ui/src/settings/settings-state.ts settings_ui/src/settings/ToolbarPanelSettingsFields.svelte settings_ui/tests/settings-app-helpers.ts settings_ui/tests/settings-bridge.test.ts settings_ui/tests/async-jobs.test.ts tests/settings_command_fixtures.py tests/test_settings_initial_state.py tests/test_settings_state.py e2e/conftest.py e2e/editor_note_helpers.py addon/anki_audio_quick_editor/locales
git commit -m "Expose chorusing defaults in settings" -m "Chorusing split-menu defaults need a visible persistent source so users can choose their normal practice behavior once. This wires the new config keys into Settings, fixtures, and localization without changing Play defaults. Focused Settings tests were run; the full check and e2e routines were not run for this slice."
```

### Task 4: Add the dedicated Chorusing split menu

**Files:**
- Add: `settings_ui/src/editor-inline/ChorusingSplitButton.svelte`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/src/editor-inline/styles/split-popovers.css`
- Modify: `settings_ui/tests/editor-inline.chorusing.integration.test.ts`
- Modify: `addon/anki_audio_quick_editor/locales/en.json`
- Modify: `addon/anki_audio_quick_editor/locales/de.json`
- Modify: `addon/anki_audio_quick_editor/locales/ja.json`
- Modify: `addon/anki_audio_quick_editor/locales/ru.json`
- Modify: `addon/anki_audio_quick_editor/locales/vi.json`
- Modify: `addon/anki_audio_quick_editor/locales/zh_CN.json`
- Modify: `addon/anki_audio_quick_editor/locales/zh_TW.json`

- [ ] **Step 1: Write failing Chorusing split-menu UI tests**

```ts
expect(document.querySelector('[data-testid="aqe-split-0-chorusing-practice"]')).toBeInTheDocument();

document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-chorusing-practice-menu"]')!.click();

expect(document.querySelector('[data-testid="aqe-split-0-chorusing-popover"]')).toHaveTextContent(
  "Auto-advance"
);
expect(document.querySelector('[data-testid="aqe-split-0-chorusing-repeat-count"]')).toBeInTheDocument();
```

```ts
document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-chorusing-auto-advance"]')!.click();
document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-chorusing-repeat-count"]')!.value = "4";
document.querySelector<HTMLInputElement>('[data-testid="aqe-split-0-chorusing-repeat-count"]')!.dispatchEvent(
  new Event("input", { bubbles: true })
);

expect(getSplitButtonState(0).chorusingAutoAdvance).toBe(true);
expect(getSplitButtonState(0).chorusingRepeatCount).toBe(4);
```

- [ ] **Step 2: Run the focused failing Chorusing UI test**

```bash
npm --prefix settings_ui test -- editor-inline.chorusing.integration.test.ts
```

Expected output before implementation:

```text
FAIL  settings_ui/tests/editor-inline.chorusing.integration.test.ts
```

- [ ] **Step 3: Create the dedicated split component with AqeTooltip-backed controls**

```svelte
<button
  type="button"
  class="aqe-button aqe-toolbar-button aqe-split-main-button"
  data-testid={`aqe-split-${ord}-chorusing-practice`}
  onclick={() => send("aqe:chorusing-practice", ord)}
>
  <Icon />
  <span>{t("editor.command.chorusing_practice")}</span>
</button>
<button
  type="button"
  class="aqe-button aqe-toolbar-button aqe-split-menu-button"
  aria-expanded={open ? "true" : "false"}
  data-testid={`aqe-split-${ord}-chorusing-practice-menu`}
  onclick={() => (open = !open)}
>
  <ChevronDown size={14} aria-hidden="true" />
</button>
```

```svelte
<UnitNumberInput
  id={`aqe-split-${ord}-chorusing-pause-seconds`}
  label={t("editor.chorusing.pause_between_repeats")}
  value={state.chorusingPauseSeconds}
  min={0}
  max={10}
  step={0.1}
  unit={t("settings.unit.seconds")}
  testId={`aqe-split-${ord}-chorusing-pause-seconds`}
  onValue={(value) => setChorusingPauseSecondsForField(ord, value)}
/>
```

```svelte
<label class="aqe-split-checkbox-row">
  <input
    type="checkbox"
    checked={state.chorusingAutoAdvance}
    data-testid={`aqe-split-${ord}-chorusing-auto-advance`}
    onchange={(event) => setChorusingAutoAdvanceForField(ord, event.currentTarget.checked)}
  />
  <span>{t("editor.chorusing.auto_advance")}</span>
</label>
```

- [ ] **Step 4: Replace only the practice button inside the Chorusing toolbar panel**

```svelte
{#if panel.id === "chorusing" && button.command === "aqe:chorusing-practice"}
  <ChorusingSplitButton {button} {ord} disabled={disabledReason !== null} />
{:else}
  <EditorToolbarButton {button} {ord} disabledReason={disabledReason} />
{/if}
```

- [ ] **Step 5: Add editor locale strings for the split menu**

```json
"editor.chorusing.pause_between_repeats": "Pause between repeats",
"editor.chorusing.auto_advance": "Auto-advance",
"editor.chorusing.auto_advance_description": "Repeat the active segment, then move to the next one.",
"editor.chorusing.repeat_count": "Repeats",
"editor.chorusing.save_defaults": "Save Chorusing defaults"
```

- [ ] **Step 6: Re-run the focused Chorusing UI test**

```bash
npm --prefix settings_ui test -- editor-inline.chorusing.integration.test.ts
```

Expected output after implementation:

```text
PASS  settings_ui/tests/editor-inline.chorusing.integration.test.ts
```

- [ ] **Step 7: Commit the dedicated menu slice**

```bash
git add settings_ui/src/editor-inline/ChorusingSplitButton.svelte settings_ui/src/editor-inline/EditorControls.svelte settings_ui/src/editor-inline/styles/split-popovers.css settings_ui/tests/editor-inline.chorusing.integration.test.ts addon/anki_audio_quick_editor/locales
git commit -m "Add a dedicated chorusing split menu" -m "Chorusing needs controls that are related to repeat practice but separate from Play, so the toolbar now renders a dedicated split menu for practice while keeping next and previous as ordinary buttons. The menu edits field-local Chorusing values and can save them as Chorusing defaults. Focused Chorusing UI tests were run; the full check and e2e routines were not run for this slice."
```

### Task 5: Implement auto-advance on Chorusing loop boundaries

**Files:**
- Modify: `settings_ui/src/editor-inline/chorusing-state.ts`
- Modify: `settings_ui/src/editor-inline/chorusing-controller.ts`
- Modify: `settings_ui/src/editor-inline/playback-controller.ts`
- Modify: `settings_ui/src/editor-inline/actions-playback.ts`
- Modify: `settings_ui/tests/editor-inline.chorusing.integration.test.ts`

- [ ] **Step 1: Write failing playback tests for repeat counting and auto-advance**

```ts
setChorusingAutoAdvanceForField(0, true);
setChorusingRepeatCountForField(0, 2);

document.querySelector<HTMLButtonElement>('[data-command="aqe:chorusing-practice"]')!.click();

handlePlaybackBoundary(visualizer, 1000);
expect(visualizer.dataset.chorusingState).toContain('"repeatPassesCompleted":1');
expect(activeChorusingMarkerIndex()).toBe(2);

handlePlaybackBoundary(visualizer, 1000);
expect(activeChorusingMarkerIndex()).toBe(1);
expect(visualizer.dataset.chorusingState).toContain('"repeatPassesCompleted":0');
```

```ts
setChorusingAutoAdvanceForField(0, true);
setChorusingRepeatCountForField(0, 1);

startChorusingOnLastSuffix();
handlePlaybackBoundary(visualizer, 1000);

expect(isChorusingPaused()).toBe(true);
expect(activeChorusingMarkerIndex()).toBe(lastSuffixIndex);
```

- [ ] **Step 2: Run the focused failing Chorusing playback test**

```bash
npm --prefix settings_ui test -- editor-inline.chorusing.integration.test.ts
```

Expected output before implementation:

```text
FAIL  settings_ui/tests/editor-inline.chorusing.integration.test.ts
```

- [ ] **Step 3: Track repeat passes in Chorusing state**

```ts
export interface ChorusingState {
  activeMarkerIndex: number | null;
  baseRegion: Region | null;
  markersMs: number[];
  ordinaryRepeatEnabled: boolean;
  practiceState: ChorusingPracticeState;
  repeatPassesCompleted: number;
  sourceFilename: string | null;
}
```

```ts
export function emptyChorusingState(): ChorusingState {
  return {
    activeMarkerIndex: null,
    baseRegion: null,
    markersMs: [],
    ordinaryRepeatEnabled: false,
    practiceState: "idle",
    repeatPassesCompleted: 0,
    sourceFilename: null,
  };
}
```

- [ ] **Step 4: Add a playback loop-boundary hook**

```ts
export interface PlaybackControllerDependencies {
  buildPlaybackRequest?: typeof buildPlaybackRequest;
  getCurrentSelectionForPlayback?: typeof getCurrentSelectionForPlayback;
  startPlayback?: typeof startPlayback;
  sendPlaybackPause?: typeof sendPlaybackPause;
  completePlayback?: typeof completePlayback;
  restartLoopPlaybackNow?: typeof restartLoopPlaybackNow;
  scheduleRepeatLoopPlayback?: typeof scheduleRepeatLoopPlayback;
  handleLoopBoundary?: (visualizer: VisualizerElement, pass: PlaybackPass) => boolean;
}
```

```ts
if (deps.handleLoopBoundary?.(visualizer, boundary.pass) === true) {
  return true;
}
```

- [ ] **Step 5: Handle Chorusing auto-advance before normal repeat-loop restart**

```ts
export function handleChorusingLoopBoundary(visualizer: VisualizerElement): boolean {
  const state = readChorusingState(visualizer);
  if (state.practiceState !== "playing" || state.activeMarkerIndex === null) {
    return false;
  }

  const splitState = getSplitButtonState(ordForVisualizer(visualizer));
  if (!splitState.chorusingAutoAdvance) {
    return false;
  }

  const completed = state.repeatPassesCompleted + 1;
  if (completed < splitState.chorusingRepeatCount) {
    writeChorusingState(visualizer, { ...state, repeatPassesCompleted: completed });
    return false;
  }

  const next = moveActiveMarkerIndex(state, "next");
  if (next === state.activeMarkerIndex) {
    pauseChorusing(visualizer, { ...state, repeatPassesCompleted: completed });
    return true;
  }

  moveChorusing(visualizer, "next", { resetRepeatPasses: true });
  return true;
}
```

- [ ] **Step 6: Reset the repeat counter on initial start and manual next/previous**

```ts
writeChorusingState(visualizer, {
  ...state,
  practiceState: "playing",
  repeatPassesCompleted: 0,
});
```

```ts
moveChorusing(visualizer, direction, { resetRepeatPasses: true });
```

- [ ] **Step 7: Wire the hook through playback dependencies**

```ts
export function playbackControllerDependencies(): PlaybackControllerDependencies {
  return {
    handleLoopBoundary: handleChorusingLoopBoundary,
  };
}
```

- [ ] **Step 8: Re-run the focused Chorusing playback test**

```bash
npm --prefix settings_ui test -- editor-inline.chorusing.integration.test.ts
```

Expected output after implementation:

```text
PASS  settings_ui/tests/editor-inline.chorusing.integration.test.ts
```

- [ ] **Step 9: Commit the auto-advance behavior slice**

```bash
git add settings_ui/src/editor-inline/chorusing-state.ts settings_ui/src/editor-inline/chorusing-controller.ts settings_ui/src/editor-inline/playback-controller.ts settings_ui/src/editor-inline/actions-playback.ts settings_ui/tests/editor-inline.chorusing.integration.test.ts
git commit -m "Auto-advance chorusing after configured repeats" -m "Chorusing practice should progress through suffixes when users want repeated listening without manual next clicks. This adds a loop-boundary hook that counts completed passes for Chorusing only, advances to the next suffix at the configured threshold, and pauses when no later suffix exists. Focused Chorusing playback tests were run; the full check and e2e routines were not run for this slice."
```

### Task 6: Add e2e coverage and run final verification

**Files:**
- Modify: `e2e/test_editor_chorusing_playback_workflow.py`
- Modify: any source or test file required by failures found during verification

- [ ] **Step 1: Add an e2e test that configures the menu and observes auto-advance**

```py
await _click_chorusing_practice(editor_frame, suffix="1")
await editor_frame.get_by_test_id("aqe-split-0-chorusing-practice-menu").click()
await editor_frame.get_by_test_id("aqe-split-0-chorusing-auto-advance").check()
repeat_count = editor_frame.get_by_test_id("aqe-split-0-chorusing-repeat-count")
await repeat_count.fill("2")

await _force_repeat_wrap(editor_frame)
await expect_active_chorusing_suffix(editor_frame, "1")

await _force_repeat_wrap(editor_frame)
await expect_active_chorusing_suffix(editor_frame, "2")
```

- [ ] **Step 2: Add an e2e assertion that manual next/previous still work while auto-advance is enabled**

```py
await _click_chorusing_next(editor_frame)
await expect_active_chorusing_suffix(editor_frame, "3")
await _click_chorusing_previous(editor_frame)
await expect_active_chorusing_suffix(editor_frame, "2")
```

- [ ] **Step 3: Run the focused e2e Chorusing workflow**

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_chorusing_playback_workflow.py
```

Expected output after implementation:

```text
passed
```

- [ ] **Step 4: Run focused frontend and Python suites**

```bash
npm --prefix settings_ui test -- split-button-state-state.test.ts split-button-state-payloads.test.ts editor-inline.chorusing.integration.test.ts settings-bridge.test.ts async-jobs.test.ts
```

```bash
python3 -m pytest tests/test_contract_generation.py tests/test_editor_bridge_facade_commands.py tests/test_editor_ui.py tests/test_config_migration_defaults.py tests/test_settings_initial_state.py tests/test_settings_state.py -q
```

- [ ] **Step 5: Run schema, contract, lint/type, and full QC gates**

```bash
python3 scripts/dev.py config-schema
```

```bash
python3 scripts/dev.py contracts-check
```

```bash
python3 scripts/dev.py lint
```

```bash
python3 scripts/dev.py typecheck
```

```bash
python3 scripts/dev.py check
```

- [ ] **Step 6: Commit e2e/final verification fixes**

```bash
git add e2e/test_editor_chorusing_playback_workflow.py
git add -u
git commit -m "Cover chorusing auto-advance end to end" -m "The new Chorusing menu changes a real playback workflow, so it needs browser-level coverage for repeat-driven advancement and manual navigation while auto-advance is enabled. This adds e2e coverage and any verification fixes from the final QC pass. Focused e2e and full check routines were run."
```

- [ ] **Step 7: Confirm final state**

```bash
git status --short
```

Expected output after all planned commits:

```text
```
