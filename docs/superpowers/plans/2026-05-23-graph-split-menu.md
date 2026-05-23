# Graph Split Menu Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace graph split sliders with radio-style button groups where requested, reorder the graph menu, and remove the popover's current-settings summary sentence.

**Architecture:** Keep the existing graph split state and payload builders unchanged. Limit the change to the graph split popover presentation layer, localized labels, and the tests that exercise those controls.

**Tech Stack:** Svelte 5, TypeScript, CSS, Vitest

---

### Task 1: Update the approved spec-facing tests first

**Files:**
- Modify: `settings_ui/tests/editor-inline.command-splits.integration.test.ts`
- Modify: `settings_ui/tests/split-button-state.test.ts`

- [ ] **Step 1: Update graph label expectations**

```ts
expect(formatGraphVoiceRange("child")).toBe("Child/falcetto");
```

- [ ] **Step 2: Update graph split integration selectors to click button options**

```ts
document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-graph-voice-range-child"]')!.click();
document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-graph-voice-lock-stable"]')!.click();
document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-graph-smoothness-very_smooth"]')!.click();
```

- [ ] **Step 3: Assert the removed summary sentence**

```ts
expect(document.querySelector('[data-testid="aqe-split-0-graph-popover"]')).not.toHaveTextContent("Current settings:");
```

### Task 2: Replace the graph popover controls

**Files:**
- Modify: `settings_ui/src/editor-inline/GraphSplitOptions.svelte`
- Modify: `settings_ui/src/editor-inline/styles/split-popovers.css`

- [ ] **Step 1: Replace the three graph range inputs with button groups**

```svelte
<div class="aqe-split-presets" role="radiogroup" aria-label={t("editor.graph.options.voice_range")}>
  {#each GRAPH_VOICE_RANGES as option}
    <button
      type="button"
      class="aqe-button aqe-split-preset"
      role="radio"
      aria-checked={voiceRange === option ? "true" : "false"}
      onclick={() => onVoiceRange(option)}
    >
      {formatGraphVoiceRange(option)}
    </button>
  {/each}
</div>
```

- [ ] **Step 2: Reorder the sections to match the approved sequence**

```svelte
Speaker's voice -> Voice lock -> Smoothness -> Connect short dropouts -> Recording condition
```

- [ ] **Step 3: Add any small CSS needed for grouped graph buttons to wrap cleanly**

```css
.aqe-graph-option-group {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
```

### Task 3: Remove the popover summary sentence and rename visible labels

**Files:**
- Modify: `settings_ui/src/editor-inline/SplitButton.svelte`
- Modify: `settings_ui/src/lib/i18n.ts`
- Modify: `addon/anki_audio_quick_editor/locales/en.json`

- [ ] **Step 1: Remove the graph-only description paragraph**

```svelte
{#if button.command !== "aqe:analyze"}
  <p class="aqe-split-popover-description">{popoverDescription()}</p>
{/if}
```

- [ ] **Step 2: Rename the graph option label**

```ts
"editor.graph.options.voice_range": "Speaker's voice",
```

- [ ] **Step 3: Update the visible voice-range captions**

```ts
"settings.graph_voice_range.bass": "Bass voice",
"settings.graph_voice_range.general": "Normal voice",
"settings.graph_voice_range.child": "Child/falcetto",
```

### Task 4: Verify the change

**Files:**
- No code changes

- [ ] **Step 1: Run the focused settings UI tests**

```bash
cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools && npm --prefix settings_ui test -- split-button-state.test.ts editor-inline.command-splits.integration.test.ts
```

- [ ] **Step 2: If the focused tests pass, report the exact scope verified**

```text
Verified graph split labels, button-group selection behavior, payload wiring, and the removed summary sentence.
```
