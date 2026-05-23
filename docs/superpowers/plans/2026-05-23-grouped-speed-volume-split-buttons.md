# Grouped Speed And Volume Split Buttons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace duplicate speed and volume split-menu triggers with one shared menu per action pair while preserving both primary action buttons.

**Architecture:** Keep the current field-local split-button state and payload builders unchanged. Limit the change to toolbar rendering, split-menu component composition, grouped test IDs/selectors, and tests that verify the grouped behavior from the frontend through E2E.

**Tech Stack:** Svelte 5, TypeScript, CSS, Vitest, pytest E2E

---

### Task 1: Add grouped toolbar rendering for speed and volume

**Files:**
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/src/editor-inline/SplitButton.svelte`
- Modify: `settings_ui/src/editor-inline/SplitValueOptions.svelte`

- [ ] **Step 1: Write or update the failing frontend integration assertions for grouped selectors**

```ts
expect(document.querySelector('[data-testid="aqe-split-0-volume-menu"]')).not.toBeNull();
expect(document.querySelector('[data-testid="aqe-split-0-volume-up-menu"]')).toBeNull();
expect(document.querySelector('[data-testid="aqe-split-0-speed-menu"]')).not.toBeNull();
expect(document.querySelector('[data-testid="aqe-split-0-faster-menu"]')).toBeNull();
```

- [ ] **Step 2: Render grouped triples in the toolbar**

```svelte
<span class="aqe-split-group">
  <SplitButton button={volumeDown} menuOnly={false} ... />
  <SplitButton button={volumeUp} menuOnly={false} ... />
  <SplitButton button={volumeUp} groupSlug="volume" menuOnly={true} ... />
</span>
```

- [ ] **Step 3: Teach the split-button component to separate primary-button and menu-trigger rendering**

```svelte
{#if showPrimary}
  <button data-aqe-command={button.command} ...>
    ...
  </button>
{/if}
{#if showMenu}
  <Popover.Trigger data-testid={`aqe-split-${target.ord}-${menuSlug()}-menu`} ... />
{/if}
```

### Task 2: Keep grouped menus wired to the existing shared field state

**Files:**
- Modify: `settings_ui/src/editor-inline/SplitButton.svelte`
- Modify: `settings_ui/src/editor-inline/SplitValueOptions.svelte`
- Modify: `settings_ui/tests/split-button-state.test.ts`
- Modify: `settings_ui/tests/editor-inline.command-splits.integration.test.ts`

- [ ] **Step 1: Add failing tests that prove one grouped menu controls both commands**

```ts
document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-menu"]')!.click();
document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-preset-6"]')!.click();
document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-down"]')!.click();
expect(window.__aqePendingCommandPayload?.overrides?.volumeStepDb).toBe(6);
document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();
expect(window.__aqePendingCommandPayload?.overrides?.volumeStepDb).toBe(6);
```

- [ ] **Step 2: Use grouped slugs only for menu/popover test IDs while keeping command-specific payload logic**

```ts
function menuSlug(): string {
  return groupSlug ?? COMMAND_SLUGS[button.command];
}
```

- [ ] **Step 3: Keep the value formatting and descriptions stable for grouped speed and volume menus**

```ts
if (menuGroup === "volume") return formatVolumeDb(volumeStepDb);
if (menuGroup === "speed") return formatSpeedStep(speedStep, button.command);
```

### Task 3: Update E2E coverage for grouped selectors and shared behavior

**Files:**
- Modify: `e2e/test_editor_processing_split_buttons_workflow.py`
- Modify: `e2e/test_editor_processing_split_buttons_parameter_workflow.py`
- Modify: `e2e/test_editor_processing_workflow.py`
- Modify: `e2e/test_editor_processing_graph_default_workflow.py`
- Modify: `e2e/test_dpdfnet_attenuation_integration.py`

- [ ] **Step 1: Update helper selectors to resolve grouped speed/volume menu slugs**

```py
if command in {"aqe:volume-up", "aqe:volume-down"}:
    slug = "volume"
elif command in {"aqe:faster", "aqe:slower"}:
    slug = "speed"
else:
    slug = command.removeprefix("aqe:")
```

- [ ] **Step 2: Add or extend E2E assertions that the grouped menu drives both primary buttons without changing settings**

```py
click_selector(editor.web, _split_menu_selector("aqe:volume-up"), timeout=5.0)
click_selector(editor.web, '[data-testid="aqe-split-0-volume-preset-6"]', timeout=5.0)
_click_and_wait_for_new_file(editor, note, media_dir, "aqe:volume-down", source.name)
_click_and_wait_for_new_file(editor, note, media_dir, "aqe:volume-up", current_name)
assert anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID)["volume_step_db"] == 3
```

- [ ] **Step 3: Add or extend save-default coverage to use grouped menu selectors**

```py
click_selector(editor.web, '[data-testid="aqe-split-0-volume-menu"]', timeout=5.0)
click_selector(editor.web, '[data-testid="aqe-split-0-volume-save-default"]', timeout=5.0)
```

### Task 4: Verify the grouped behavior

**Files:**
- No code changes

- [ ] **Step 1: Run focused settings UI tests**

```bash
cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools && npm --prefix settings_ui test -- split-button-state.test.ts split-button-popover.integration.test.ts editor-inline.command-splits.integration.test.ts
```

- [ ] **Step 2: Run focused E2E tests for grouped speed and volume behavior**

```bash
cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools && python3 scripts/dev.py test-e2e -- --pytest-args "e2e/test_editor_processing_split_buttons_workflow.py e2e/test_editor_processing_split_buttons_parameter_workflow.py e2e/test_editor_processing_graph_default_workflow.py"
```

- [ ] **Step 3: If focused verification passes, report exact scope**

```text
Verified grouped speed/volume menus, shared field-local overrides, save-default wiring, and graph-default workflow compatibility.
```
