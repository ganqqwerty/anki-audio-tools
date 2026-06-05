# Recording Countdown Overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make voice recording countdown opt-in by default and render a large graph overlay for positive countdown values.

**Architecture:** Reuse the existing `voice_recording_countdown_seconds` numeric default, with `0` as the disabled state. Keep countdown timing in `recording-actions.ts`, add a stable overlay host to `GraphVisualizer.svelte`, and update only config/default fixtures plus focused tests.

**Tech Stack:** Svelte 5, TypeScript, Vitest, Python config/editor tests, Anki editor webview bundle built through `scripts/dev.py`.

---

## File Structure

- Modify `settings_ui/tests/editor-inline.recording.integration.test.ts`
  Add focused coverage for immediate dispatch at `0` and visible graph overlay for positive countdowns.

- Modify `settings_ui/src/editor-inline/GraphVisualizer.svelte`
  Add a stable countdown overlay host inside `.aqe-visualizer-plot`.

- Modify `settings_ui/src/editor-inline/recording-actions.ts`
  Skip countdown state entirely at `0`; render and clear the countdown overlay for positive countdown states.

- Modify `settings_ui/src/editor-inline/styles/visualizer.css`
  Style the overlay as centered, non-interactive, readable in light and dark themes, and contained within the graph plot.

- Modify `settings_ui/src/editor-inline/split-button-state.ts`
  Change fallback countdown defaults and invalid fallback from `3` to `0`.

- Modify `addon/anki_audio_quick_editor/config.json`
  Change the committed add-on default countdown from `3` to `0`.

- Modify `settings_ui/src/settings/settings-state.ts`
  Change settings fallback initial state from `3` to `0`.

- Modify default fixtures and expected values:
  `tests/test_editor_ui.py`, `tests/test_settings_initial_state.py`, `tests/test_settings_state.py`, `tests/settings_command_fixtures.py`, `e2e/conftest.py`, `e2e/editor_note_helpers.py`, and `e2e/test_settings_save_command.py`.

---

### Task 1: Add Failing Frontend Countdown Tests

**Files:**
- Modify: `settings_ui/tests/editor-inline.recording.integration.test.ts`
- Test: `settings_ui/tests/editor-inline.recording.integration.test.ts`

- [ ] **Step 1: Add a config helper for positive countdowns**

Insert this helper below `recordingConfig()`:

```ts
function recordingConfigWithCountdown(seconds: number): EditorRuntimeConfig {
  const config = recordingConfig();
  return {
    ...config,
    splitButtonDefaults: {
      ...config.splitButtonDefaults,
      voiceRecordingCountdownSeconds: seconds,
    },
  };
}
```

- [ ] **Step 2: Strengthen the existing immediate-dispatch test**

In the test named `renders the opt-in grouped buttons and dispatches record after the configured countdown`, keep the existing setup and add these assertions immediately after `recordButton.click();`:

```ts
    const overlay = document.querySelector<HTMLElement>('[data-testid="aqe-recording-countdown-overlay-0"]')!;
    expect(overlay).not.toBeNull();
    expect(overlay.hidden).toBe(true);
    expect(window.__aqeGraphStateForTest?.(0)?.learnerRecordingStatus).toBe("idle");
```

The expected behavior is that `0` dispatches immediately without setting frontend countdown state.

- [ ] **Step 3: Add a positive-countdown overlay test**

Add this test after the immediate-dispatch test:

```ts
  it("shows a graph overlay while a positive recording countdown runs", async () => {
    vi.useFakeTimers();
    const config = recordingConfigWithCountdown(3);
    initializeEditorRuntime(config);
    scan(config);
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    await Promise.resolve();

    const recordButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-record-voice"]')!;
    recordButton.click();

    let overlay = document.querySelector<HTMLElement>('[data-testid="aqe-recording-countdown-overlay-0"]')!;
    expect(overlay).not.toBeNull();
    expect(overlay.hidden).toBe(false);
    expect(overlay).toHaveTextContent("3");
    expect(overlay).toHaveAttribute("aria-label", "Recording starts in 3s");
    expect(bridgeCommands()).not.toContain("aqe:command-payload");

    await vi.advanceTimersByTimeAsync(1000);
    await Promise.resolve();
    overlay = document.querySelector<HTMLElement>('[data-testid="aqe-recording-countdown-overlay-0"]')!;
    expect(overlay).toHaveTextContent("2");
    expect(overlay).toHaveAttribute("aria-label", "Recording starts in 2s");

    await vi.advanceTimersByTimeAsync(1000);
    await Promise.resolve();
    overlay = document.querySelector<HTMLElement>('[data-testid="aqe-recording-countdown-overlay-0"]')!;
    expect(overlay).toHaveTextContent("1");
    expect(overlay).toHaveAttribute("aria-label", "Recording starts in 1s");

    await vi.advanceTimersByTimeAsync(1000);
    await Promise.resolve();
    overlay = document.querySelector<HTMLElement>('[data-testid="aqe-recording-countdown-overlay-0"]')!;
    expect(overlay.hidden).toBe(true);
    expect(bridgeCommands()).toContain("focus:0");
    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:record-voice",
      fieldOrd: 0,
    });
  });
```

- [ ] **Step 4: Run the focused test and confirm it fails**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.recording.integration.test.ts
```

Expected: FAIL because `aqe-recording-countdown-overlay-0` does not exist and `0` still sets countdown state before dispatch.

---

### Task 2: Implement Countdown Overlay Behavior

**Files:**
- Modify: `settings_ui/src/editor-inline/GraphVisualizer.svelte`
- Modify: `settings_ui/src/editor-inline/recording-actions.ts`
- Modify: `settings_ui/src/editor-inline/styles/visualizer.css`
- Test: `settings_ui/tests/editor-inline.recording.integration.test.ts`

- [ ] **Step 1: Add the overlay host**

In `settings_ui/src/editor-inline/GraphVisualizer.svelte`, insert this element inside `.aqe-visualizer-plot`, after the selection preview halo elements and before the marker hitbox tooltip:

```svelte
    <div
      class="aqe-recording-countdown-overlay"
      data-testid={`aqe-recording-countdown-overlay-${target.ord}`}
      aria-live="polite"
      aria-atomic="true"
      hidden
    >
      <span class="aqe-recording-countdown-value"></span>
    </div>
```

- [ ] **Step 2: Skip countdown state at `0`**

In `settings_ui/src/editor-inline/recording-actions.ts`, replace the `countdownSeconds <= 0` branch with:

```ts
  if (countdownSeconds <= 0) {
    dispatch();
    return true;
  }
```

- [ ] **Step 3: Avoid rendering a `0` countdown tick**

In the `tick` function in `recording-actions.ts`, move the dispatch check before `setLearnerRecordingState`:

```ts
  const tick = (): void => {
    if (remaining <= 0) {
      dispatch();
      return;
    }
    setLearnerRecordingState({
      fieldOrd: ord,
      status: "countdown",
      countdownSeconds: remaining,
      targetDurationMs,
    });
    remaining -= 1;
    visualizer.__aqeRecordCountdownTimer = window.setTimeout(tick, 1000);
  };
```

- [ ] **Step 4: Render and clear the overlay from learner state**

Add these helpers near `renderRecordingStatus` in `recording-actions.ts`:

```ts
function renderRecordingCountdownOverlay(
  visualizer: VisualizerElement,
  payload: LearnerRecordingStatePayload,
): void {
  const overlay = visualizer.querySelector<HTMLElement>(".aqe-recording-countdown-overlay");
  if (!overlay) return;
  const valueNode = overlay.querySelector<HTMLElement>(".aqe-recording-countdown-value");
  const seconds = countdownOverlaySeconds(payload);
  if (seconds == null) {
    overlay.hidden = true;
    overlay.removeAttribute("aria-label");
    if (valueNode) valueNode.textContent = "";
    return;
  }
  const message = t("editor.recording.countdown", { seconds });
  overlay.hidden = false;
  overlay.setAttribute("aria-label", message);
  if (valueNode) valueNode.textContent = String(seconds);
}

function countdownOverlaySeconds(payload: LearnerRecordingStatePayload): number | null {
  if (payload.status !== "countdown") return null;
  const seconds = Number(payload.countdownSeconds);
  if (!Number.isFinite(seconds) || seconds <= 0) return null;
  return Math.round(seconds);
}
```

Then call the helper inside `setLearnerRecordingState`, in the existing `if (visualizer) { ... }` block after the cursor start/stop logic:

```ts
    renderRecordingCountdownOverlay(visualizer, payload);
```

- [ ] **Step 5: Style the overlay**

Add this block to `settings_ui/src/editor-inline/styles/visualizer.css`, below `.aqe-visualizer-plot`:

```css
.aqe-recording-countdown-overlay,
.aqe-ui-root .aqe-recording-countdown-overlay {
  align-items: center;
  background: color-mix(in srgb, var(--aqe-surface-color) 84%, transparent);
  border: 1px solid color-mix(in srgb, var(--aqe-border-color) 70%, transparent);
  border-radius: 8px;
  box-sizing: border-box;
  color: inherit;
  display: flex;
  inset: 0;
  justify-content: center;
  pointer-events: none;
  position: absolute;
  z-index: 3;
}

.aqe-recording-countdown-overlay[hidden],
.aqe-ui-root .aqe-recording-countdown-overlay[hidden] {
  display: none;
}

.aqe-recording-countdown-value,
.aqe-ui-root .aqe-recording-countdown-value {
  font-size: 72px;
  font-weight: 700;
  line-height: 1;
  text-align: center;
}
```

- [ ] **Step 6: Run the focused frontend test**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.recording.integration.test.ts
```

Expected: PASS for `editor-inline.recording.integration.test.ts`.

- [ ] **Step 7: Commit**

Run:

```bash
git add settings_ui/src/editor-inline/GraphVisualizer.svelte \
  settings_ui/src/editor-inline/recording-actions.ts \
  settings_ui/src/editor-inline/styles/visualizer.css \
  settings_ui/tests/editor-inline.recording.integration.test.ts
git commit -m "Render recording countdown over the graph" \
  -m "Issue #17 needs the countdown to be visible where users watch the target graph, so positive countdowns now render a large non-interactive overlay and 0-second countdowns start recording immediately without a transient countdown state." \
  -m "This affects only frontend countdown timing and graph presentation; the Python recorder lifecycle and command payload shape remain unchanged. Full check and e2e routines were not run for this focused frontend commit."
```

---

### Task 3: Change Countdown Defaults to Zero

**Files:**
- Modify: `settings_ui/src/editor-inline/split-button-state.ts`
- Modify: `addon/anki_audio_quick_editor/config.json`
- Modify: `settings_ui/src/settings/settings-state.ts`
- Modify: `tests/test_editor_ui.py`
- Modify: `tests/test_settings_initial_state.py`
- Modify: `tests/test_settings_state.py`
- Modify: `tests/settings_command_fixtures.py`
- Modify: `e2e/conftest.py`
- Modify: `e2e/editor_note_helpers.py`
- Modify: `e2e/test_settings_save_command.py`
- Test: focused Python tests and frontend recording test

- [ ] **Step 1: Write/update default expectations**

Change every default expectation for `voice_recording_countdown_seconds` and `voiceRecordingCountdownSeconds` from `3` to `0` in:

```text
addon/anki_audio_quick_editor/config.json
settings_ui/src/settings/settings-state.ts
settings_ui/src/editor-inline/split-button-state.ts
tests/test_editor_ui.py
tests/test_settings_initial_state.py
tests/test_settings_state.py
tests/settings_command_fixtures.py
e2e/conftest.py
e2e/editor_note_helpers.py
e2e/test_settings_save_command.py
```

In `settings_ui/src/editor-inline/split-button-state.ts`, update both defaults:

```ts
  voiceRecordingCountdownSeconds: 0,
```

```ts
    return 0;
```

- [ ] **Step 2: Confirm there are no stale `3` defaults**

Run:

```bash
rg -n 'voice_recording_countdown_seconds.: 3|voiceRecordingCountdownSeconds: 3|return 3|voice_recording_countdown_seconds=3' addon settings_ui tests e2e contracts
```

Expected: no countdown-default matches. Ignore unrelated matches such as helper functions returning `3` for non-countdown tests.

- [ ] **Step 3: Run focused Python/default tests**

Run:

```bash
python3 -m pytest \
  tests/test_editor_ui.py \
  tests/test_settings_initial_state.py \
  tests/test_settings_state.py \
  tests/test_settings_commands_save.py
```

Expected: PASS.

- [ ] **Step 4: Run config schema validation**

Run:

```bash
python3 scripts/dev.py config-schema
```

Expected: PASS.

- [ ] **Step 5: Run the focused frontend test again**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.recording.integration.test.ts
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add addon/anki_audio_quick_editor/config.json \
  settings_ui/src/settings/settings-state.ts \
  settings_ui/src/editor-inline/split-button-state.ts \
  tests/test_editor_ui.py \
  tests/test_settings_initial_state.py \
  tests/test_settings_state.py \
  tests/settings_command_fixtures.py \
  e2e/conftest.py \
  e2e/editor_note_helpers.py \
  e2e/test_settings_save_command.py
git commit -m "Default recording countdown to immediate start" \
  -m "Issue #17 asks for no countdown by default, so the shared config and fallback defaults now use 0 seconds while preserving the existing 0-to-10 second setting for users who want a delay." \
  -m "This updates Python, Svelte, and e2e fixtures so new installs and fallback states agree on immediate recording. Full check and e2e routines were not run for this focused default-update commit."
```

---

### Task 4: Run Quality Gates

**Files:**
- Verify only; no planned source edits.

- [ ] **Step 1: Run Svelte/frontend validation**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected: PASS. This rebuilds frontend bundles, runs Svelte validation, ESLint, TypeScript, and Vitest coverage.

- [ ] **Step 2: Run repository unit and architecture tests**

Run:

```bash
python3 scripts/dev.py test
```

Expected: PASS.

- [ ] **Step 3: Run the full QC gate**

Run:

```bash
python3 scripts/dev.py check
```

Expected: PASS.

- [ ] **Step 4: Run e2e tests**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS.

- [ ] **Step 5: Record any verification limitations**

If `check` or `test-e2e` cannot complete because of environment constraints, record the exact failing command and the first actionable failure in the final response and in any commit body created after this point.
