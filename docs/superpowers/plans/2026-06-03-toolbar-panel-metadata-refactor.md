# Toolbar Panel Metadata Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize Editor toolbar panel definitions so settings visibility, Editor toolbar rendering, and future toolbar panels share one source of intent.

**Architecture:** Add shared panel metadata in `settings_ui/src/lib`, then consume it from both settings visibility logic and the Editor inline toolbar render model. Keep DOM classes and panel appearance in Editor inline components, and replace behavior coupling to `.aqe-toolbar-panel` with a semantic button-container data attribute.

**Tech Stack:** Svelte 5, TypeScript, Vitest, Python e2e tests through `scripts/dev.py`, Anki Qt WebEngine.

---

## File Structure

- Create `settings_ui/src/lib/editor-toolbar-panel-definitions.ts`
  Shared atomic panel metadata and matching helpers. This is the source of truth for which commands form an indivisible toolbar panel.

- Create `settings_ui/src/editor-inline/editor-toolbar-render-items.ts`
  Pure Editor toolbar render model. Converts visible toolbar buttons into button, split-group, and toolbar-panel render items without Svelte markup.

- Modify `settings_ui/src/lib/editor-toolbar-visibility.ts`
  Use shared panel definitions for settings panel construction and visibility normalization.

- Modify `settings_ui/src/editor-inline/EditorControls.svelte`
  Remove local panel-matching logic and render the new `toolbar-panel` render item shape.

- Modify `settings_ui/src/editor-inline/EditorToolbarPanel.svelte`
  Add `data-aqe-toolbar-button-container="true"` so behavior code can find toolbar buttons without depending on visual CSS classes.

- Modify `settings_ui/src/editor-inline/recording-actions.ts`
  Replace `.aqe-toolbar-panel` traversal with the semantic button-container selector.

- Modify `settings_ui/tests/editor-toolbar-visibility.test.ts`
  Add tests proving both settings and normalization consume the shared panel definitions.

- Create `settings_ui/tests/editor-toolbar-render-items.test.ts`
  Test the pure Editor render model independently from Svelte.

- Modify `settings_ui/tests/editor-inline.integration.test.ts`
  Keep Back-chaining DOM coverage and assert the semantic button-container attribute.

- Modify `settings_ui/tests/editor-inline.recording.integration.test.ts`
  Keep Record / Play yours DOM and disabled-state coverage, assert the semantic button-container attribute.

- Modify `e2e/test_editor_back_chaining_playback_workflow.py`
  Extend existing toolbar panel e2e assertion to verify the semantic container attribute.

- Modify `e2e/test_editor_voice_recording_comparison_workflow.py`
  Extend existing recording panel e2e assertion to verify the semantic container attribute while keeping record/play behavior checks.

- Modify `e2e/reviewer_css_isolation_helpers.py`
  Extend reviewer Back-chaining style isolation to verify the semantic container attribute.

---

### Task 1: Add Shared Toolbar Panel Definitions

**Files:**
- Create: `settings_ui/src/lib/editor-toolbar-panel-definitions.ts`
- Modify: `settings_ui/src/lib/editor-toolbar-visibility.ts`
- Test: `settings_ui/tests/editor-toolbar-visibility.test.ts`

- [ ] **Step 1: Write failing shared-definition tests**

Add these cases to `settings_ui/tests/editor-toolbar-visibility.test.ts`:

```ts
import {
  TOOLBAR_PANEL_DEFINITIONS,
  toolbarPanelDefinitionAt,
} from "../src/lib/editor-toolbar-panel-definitions.js";
```

```ts
  it("defines atomic toolbar panels in one shared list", () => {
    expect(TOOLBAR_PANEL_DEFINITIONS.map((definition) => ({
      commands: definition.commands,
      labelKey: definition.labelKey,
      slug: definition.slug,
      titleKey: definition.titleKey,
    }))).toEqual([
      {
        commands: [
          "aqe:back-chain-practice",
          "aqe:back-chain-previous",
          "aqe:back-chain-next",
        ],
        labelKey: "editor.back_chaining.title",
        slug: "back-chaining",
        titleKey: "editor.command.back_chain_practice.title",
      },
      {
        commands: [
          "aqe:record-voice",
          "aqe:play-recording",
        ],
        labelKey: "editor.command.record_group.label",
        slug: "record-play-yours",
        titleKey: "editor.command.record_group.label",
      },
    ]);
  });

  it("matches shared panel definitions against consecutive toolbar buttons", () => {
    const buttons = toolbarButtons();
    const backChainingIndex = buttons.findIndex((button) => button.command === "aqe:back-chain-practice");
    const recordingIndex = buttons.findIndex((button) => button.command === "aqe:record-voice");

    expect(toolbarPanelDefinitionAt(buttons, backChainingIndex)?.definition.slug).toBe("back-chaining");
    expect(toolbarPanelDefinitionAt(buttons, recordingIndex)?.definition.slug).toBe("record-play-yours");
    expect(toolbarPanelDefinitionAt(buttons, 0)).toBeUndefined();
  });

  it("normalizes partial learner recording visibility to the full panel", () => {
    expect(
      normalizeVisibleEditorButtons(
        toolbarButtons(),
        ["aqe:play", "aqe:play-recording", "aqe:settings"] as EditorCommand[],
      ),
    ).toEqual([
      "aqe:play",
      "aqe:record-voice",
      "aqe:play-recording",
      "aqe:settings",
    ]);
  });
```

- [ ] **Step 2: Run the targeted test and confirm it fails**

Run:

```bash
cd settings_ui
npm run test -- editor-toolbar-visibility.test.ts
```

Expected: FAIL because `../src/lib/editor-toolbar-panel-definitions.js` does not exist.

- [ ] **Step 3: Create shared panel definitions**

Create `settings_ui/src/lib/editor-toolbar-panel-definitions.ts`:

```ts
import type { EditorCommand, ToolbarButtonSpec } from "./editor-toolbar-buttons.js";

export type ToolbarPanelSlug = "back-chaining" | "record-play-yours";

export interface ToolbarPanelDefinition {
  commands: readonly EditorCommand[];
  labelKey: string;
  primaryCommand: EditorCommand;
  slug: ToolbarPanelSlug;
  titleKey: string;
}

export interface MatchedToolbarPanel<TButton extends { command: EditorCommand }> {
  buttons: readonly TButton[];
  definition: ToolbarPanelDefinition;
}

export const TOOLBAR_PANEL_DEFINITIONS = [
  {
    commands: [
      "aqe:back-chain-practice",
      "aqe:back-chain-previous",
      "aqe:back-chain-next",
    ],
    labelKey: "editor.back_chaining.title",
    primaryCommand: "aqe:back-chain-practice",
    slug: "back-chaining",
    titleKey: "editor.command.back_chain_practice.title",
  },
  {
    commands: [
      "aqe:record-voice",
      "aqe:play-recording",
    ],
    labelKey: "editor.command.record_group.label",
    primaryCommand: "aqe:record-voice",
    slug: "record-play-yours",
    titleKey: "editor.command.record_group.label",
  },
] as const satisfies readonly ToolbarPanelDefinition[];

export function toolbarPanelDefinitionAt<TButton extends Pick<ToolbarButtonSpec, "command">>(
  buttons: readonly TButton[],
  index: number,
): MatchedToolbarPanel<TButton> | undefined {
  for (const definition of TOOLBAR_PANEL_DEFINITIONS) {
    const matches = definition.commands.every(
      (command, offset) => buttons[index + offset]?.command === command,
    );
    if (matches) {
      return {
        buttons: buttons.slice(index, index + definition.commands.length),
        definition,
      };
    }
  }
  return undefined;
}
```

- [ ] **Step 4: Refactor visibility logic to use shared definitions**

In `settings_ui/src/lib/editor-toolbar-visibility.ts`, replace local command constants with imports:

```ts
import {
  TOOLBAR_PANEL_DEFINITIONS,
  toolbarPanelDefinitionAt,
} from "./editor-toolbar-panel-definitions.js";
```

Update `toolbarPanels()` to use the shared matcher:

```ts
export function toolbarPanels(
  buttons: readonly ToolbarButtonSpec[] = toolbarButtons(),
): readonly ToolbarPanelSpec[] {
  const panels: ToolbarPanelSpec[] = [];
  for (let index = 0; index < buttons.length; index += 1) {
    const button = buttons[index];
    if (!button) continue;
    const matchedPanel = toolbarPanelDefinitionAt(buttons, index);
    if (matchedPanel) {
      const primaryButton = matchedPanel.buttons.find(
        (candidate) => candidate.command === matchedPanel.definition.primaryCommand,
      ) ?? matchedPanel.buttons[0]!;
      panels.push({
        buttons: matchedPanel.buttons,
        commands: matchedPanel.definition.commands,
        icon: primaryButton.icon,
        label: t(matchedPanel.definition.labelKey),
        primaryButton,
        slug: matchedPanel.definition.slug,
        title: t(matchedPanel.definition.titleKey),
      });
      index += matchedPanel.buttons.length - 1;
      continue;
    }
    panels.push({
      buttons: [button],
      commands: [button.command],
      icon: button.icon,
      label: button.label,
      primaryButton: button,
      slug: COMMAND_SLUGS[button.command],
      title: button.title,
    });
  }
  return panels;
}
```

Update `normalizeVisibleEditorButtons()` to iterate shared definitions:

```ts
  for (const definition of TOOLBAR_PANEL_DEFINITIONS) {
    if (definition.commands.some((command) => requested.has(command))) {
      for (const command of definition.commands) {
        if (availableCommands.has(command)) requested.add(command);
      }
    }
  }
```

Update `defaultRuntimeVisibleCommands()`:

```ts
function defaultRuntimeVisibleCommands(buttons: readonly ToolbarButtonSpec[]): readonly EditorCommand[] {
  const recordingDefinition = TOOLBAR_PANEL_DEFINITIONS.find(
    (definition) => definition.slug === "record-play-yours",
  );
  const recordingCommands = new Set<EditorCommand>(recordingDefinition?.commands ?? []);
  return buttons
    .map((button) => button.command)
    .filter((command) => !recordingCommands.has(command));
}
```

- [ ] **Step 5: Run targeted tests**

Run:

```bash
cd settings_ui
npm run test -- editor-toolbar-visibility.test.ts
```

Expected: PASS with the existing Back-chaining tests plus new Recording/shared-definition tests.

- [ ] **Step 6: Commit Task 1**

Run:

```bash
git add settings_ui/src/lib/editor-toolbar-panel-definitions.ts settings_ui/src/lib/editor-toolbar-visibility.ts settings_ui/tests/editor-toolbar-visibility.test.ts
git commit -m "refactor: centralize toolbar panel definitions" -m "Back-chaining and Record / Play yours are atomic toolbar panels in both settings and editor runtime. Keeping their command sequences in one shared definition prevents future drift between visibility normalization and UI rendering."
```

---

### Task 2: Extract Editor Toolbar Render Items

**Files:**
- Create: `settings_ui/src/editor-inline/editor-toolbar-render-items.ts`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Test: `settings_ui/tests/editor-toolbar-render-items.test.ts`
- Test: `settings_ui/tests/editor-inline.integration.test.ts`
- Test: `settings_ui/tests/editor-inline.recording.integration.test.ts`

- [ ] **Step 1: Write failing pure render-model tests**

Create `settings_ui/tests/editor-toolbar-render-items.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { toolbarButtons } from "../src/lib/editor-toolbar-buttons.js";
import { buildEditorToolbarRenderItems } from "../src/editor-inline/editor-toolbar-render-items.js";

describe("editor toolbar render items", () => {
  it("renders shared atomic panels as toolbar panel items", () => {
    const items = buildEditorToolbarRenderItems(toolbarButtons());
    const panels = items.filter((item) => item.kind === "toolbar-panel");

    expect(panels.map((item) => ({
      commands: item.buttons.map((button) => button.command),
      label: item.label,
      slug: item.definition.slug,
    }))).toEqual([
      {
        commands: [
          "aqe:back-chain-practice",
          "aqe:back-chain-previous",
          "aqe:back-chain-next",
        ],
        label: "Back-chaining",
        slug: "back-chaining",
      },
      {
        commands: [
          "aqe:record-voice",
          "aqe:play-recording",
        ],
        label: "Record / Play yours",
        slug: "record-play-yours",
      },
    ]);
  });

  it("keeps speed and volume as split run groups, not toolbar panels", () => {
    const items = buildEditorToolbarRenderItems(toolbarButtons());
    expect(items.filter((item) => item.kind === "split-run-group").map((item) => item.menuSlug)).toEqual([
      "speed",
      "volume",
    ]);
  });
});
```

- [ ] **Step 2: Run the targeted test and confirm it fails**

Run:

```bash
cd settings_ui
npm run test -- editor-toolbar-render-items.test.ts
```

Expected: FAIL because `editor-toolbar-render-items.js` does not exist.

- [ ] **Step 3: Create the pure render-item helper**

Create `settings_ui/src/editor-inline/editor-toolbar-render-items.ts`:

```ts
import { toolbarPanelDefinitionAt, type ToolbarPanelDefinition } from "../lib/editor-toolbar-panel-definitions.js";
import { t } from "../lib/i18n.js";
import type { ButtonSpec } from "./types.js";

export type ToolbarRenderItem =
  | { button: ButtonSpec; kind: "button" }
  | {
    buttons: readonly ButtonSpec[];
    definition: ToolbarPanelDefinition;
    kind: "toolbar-panel";
    label: string;
  }
  | {
    buttons: readonly [ButtonSpec, ButtonSpec];
    kind: "split-run-group";
    menuLabel: string;
    menuSlug: "speed" | "volume";
  };

export function buildEditorToolbarRenderItems(buttons: readonly ButtonSpec[]): readonly ToolbarRenderItem[] {
  const items: ToolbarRenderItem[] = [];
  for (let index = 0; index < buttons.length; index += 1) {
    const button = buttons[index];
    if (!button) continue;
    const matchedPanel = toolbarPanelDefinitionAt(buttons, index);
    if (matchedPanel) {
      items.push({
        buttons: matchedPanel.buttons,
        definition: matchedPanel.definition,
        kind: "toolbar-panel",
        label: t(matchedPanel.definition.labelKey),
      });
      index += matchedPanel.buttons.length - 1;
      continue;
    }
    const next = buttons[index + 1];
    if (button.command === "aqe:slower" && next?.command === "aqe:faster") {
      items.push({
        buttons: [button, next],
        kind: "split-run-group",
        menuLabel: t("editor.split.group.speed"),
        menuSlug: "speed",
      });
      index += 1;
      continue;
    }
    if (button.command === "aqe:volume-down" && next?.command === "aqe:volume-up") {
      items.push({
        buttons: [button, next],
        kind: "split-run-group",
        menuLabel: t("editor.split.group.volume"),
        menuSlug: "volume",
      });
      index += 1;
      continue;
    }
    items.push({ button, kind: "button" });
  }
  return items;
}
```

- [ ] **Step 4: Run pure render-model tests**

Run:

```bash
cd settings_ui
npm run test -- editor-toolbar-render-items.test.ts
```

Expected: PASS.

- [ ] **Step 5: Refactor `EditorControls.svelte` to consume render items**

In `settings_ui/src/editor-inline/EditorControls.svelte`, remove the local `ToolbarRenderItem` type and `buildToolbarRenderItems()` function. Add:

```ts
  import { buildEditorToolbarRenderItems } from "./editor-toolbar-render-items.js";
```

Keep:

```ts
  const renderItems = buildEditorToolbarRenderItems(buttons);
```

Update the `{#each}` key expression:

```svelte
    {#each renderItems as item (item.kind === "split-run-group" ? `${item.menuSlug}:${item.buttons[0].command}` : item.kind === "toolbar-panel" ? `${item.definition.slug}:${item.buttons[0]?.command}` : item.button.command)}
```

Rename the split run branch from `item.kind === "group"` to `item.kind === "split-run-group"`.

Replace the recording/back-chaining branches with one `toolbar-panel` branch:

```svelte
      {:else if item.kind === "toolbar-panel"}
        <EditorToolbarPanel
          label={item.label}
          panelClass={item.definition.slug === "back-chaining" ? "aqe-back-chaining-toolbar-panel" : "aqe-recording-group"}
          testId={`aqe-${item.definition.slug === "back-chaining" ? "back-chaining" : "recording"}-toolbar-panel-${target.ord}`}
        >
          {#if item.definition.slug === "record-play-yours"}
            {@const record = item.buttons.find((button) => button.command === "aqe:record-voice")}
            {@const playRecording = item.buttons.find((button) => button.command === "aqe:play-recording")}
            {#if record && playRecording}
              <span class="aqe-split-group">
                <SplitButton
                  button={record}
                  displayMode={buttonDisplayMode(record.command, buttonModes)}
                  primaryGroupPosition="start"
                  showMenu={false}
                  {target}
                />
                <SplitButton
                  button={playRecording}
                  displayMode={buttonDisplayMode(playRecording.command, buttonModes)}
                  primaryGroupPosition="middle"
                  showMenu={false}
                  {target}
                />
                <SplitButton
                  button={record}
                  displayMode={buttonDisplayMode(record.command, buttonModes)}
                  groupLabel={item.label}
                  showPrimary={false}
                  showRunButton={false}
                  {target}
                />
              </span>
            {/if}
          {:else}
            {#each item.buttons as button (button.command)}
              <EditorToolbarButton
                {button}
                displayMode={buttonDisplayMode(button.command, buttonModes)}
                disabled={initialButtonDisabled(button.command)}
                disabledTitle={disabledTitle(button.command)}
                {target}
              />
            {/each}
          {/if}
        </EditorToolbarPanel>
```

- [ ] **Step 6: Run Editor integration tests**

Run:

```bash
cd settings_ui
npm run test -- editor-toolbar-render-items.test.ts editor-inline.integration.test.ts editor-inline.recording.integration.test.ts editor-inline.back-chaining.integration.test.ts
```

Expected: PASS. Back-chaining and Record / Play yours remain visually grouped and behaviorally unchanged.

- [ ] **Step 7: Commit Task 2**

Run:

```bash
git add settings_ui/src/editor-inline/editor-toolbar-render-items.ts settings_ui/src/editor-inline/EditorControls.svelte settings_ui/tests/editor-toolbar-render-items.test.ts
git commit -m "refactor: extract editor toolbar render model" -m "EditorControls should render toolbar items, not decide which command sequences form reusable panels. A pure render-item helper makes panel intent testable and keeps Svelte markup focused on presentation."
```

---

### Task 3: Replace Visual Class Coupling With Semantic Container Attribute

**Files:**
- Modify: `settings_ui/src/editor-inline/EditorToolbarPanel.svelte`
- Modify: `settings_ui/src/editor-inline/recording-actions.ts`
- Test: `settings_ui/tests/editor-inline.integration.test.ts`
- Test: `settings_ui/tests/editor-inline.recording.integration.test.ts`

- [ ] **Step 1: Update integration tests first**

In `settings_ui/tests/editor-inline.integration.test.ts`, extend the Back-chaining panel assertion:

```ts
    expect(panel).toHaveAttribute("data-aqe-toolbar-button-container", "true");
```

In `settings_ui/tests/editor-inline.recording.integration.test.ts`, extend both recording panel assertions:

```ts
    expect(group).toHaveAttribute("data-aqe-toolbar-button-container", "true");
```

- [ ] **Step 2: Run integration tests and confirm failure**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.integration.test.ts editor-inline.recording.integration.test.ts
```

Expected: FAIL because `EditorToolbarPanel` does not yet render `data-aqe-toolbar-button-container`.

- [ ] **Step 3: Add the semantic container attribute**

Modify `settings_ui/src/editor-inline/EditorToolbarPanel.svelte`:

```svelte
<span
  class={classes}
  data-aqe-toolbar-button-container="true"
  data-testid={testId}
  role="group"
  aria-label={label}
>
  <span class="aqe-toolbar-panel-label" aria-hidden="true">{label}</span>
  {@render children()}
</span>
```

- [ ] **Step 4: Update recording traversal to use semantic intent**

Modify `settings_ui/src/editor-inline/recording-actions.ts`:

```ts
    if (
      node.matches(".aqe-split-group")
      || node.matches(".aqe-split-button")
      || node.matches('[data-aqe-toolbar-button-container="true"]')
      || node.matches(".aqe-button-tooltip-target")
    ) {
      buttons.push(...Array.from(node.querySelectorAll<HTMLButtonElement>(".aqe-button")));
    }
```

- [ ] **Step 5: Run focused integration tests**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.integration.test.ts editor-inline.recording.integration.test.ts editor-inline.back-chaining.integration.test.ts
```

Expected: PASS. Recording disabled-state assertions stay green, proving the behavior traversal still reaches nested toolbar buttons.

- [ ] **Step 6: Commit Task 3**

Run:

```bash
git add settings_ui/src/editor-inline/EditorToolbarPanel.svelte settings_ui/src/editor-inline/recording-actions.ts settings_ui/tests/editor-inline.integration.test.ts settings_ui/tests/editor-inline.recording.integration.test.ts
git commit -m "refactor: mark toolbar panels as button containers" -m "Recording control sync needs to find toolbar buttons inside reusable panels, but it should not depend on presentation classes. A semantic container attribute keeps behavior traversal tied to intent instead of CSS."
```

---

### Task 4: Extend E2E Coverage For Shared Panel Semantics

**Files:**
- Modify: `e2e/test_editor_back_chaining_playback_workflow.py`
- Modify: `e2e/test_editor_voice_recording_comparison_workflow.py`
- Modify: `e2e/reviewer_css_isolation_helpers.py`

- [ ] **Step 1: Update Back-chaining e2e panel assertion**

In `e2e/test_editor_back_chaining_playback_workflow.py`, add `container` to the returned object:

```python
                container: panel.getAttribute("data-aqe-toolbar-button-container"),
```

Add this predicate condition:

```python
            and value["container"] == "true"
```

- [ ] **Step 2: Update Record / Play yours e2e panel assertion**

In `e2e/test_editor_voice_recording_comparison_workflow.py`, add `container` to the returned object:

```python
                container: panel.getAttribute("data-aqe-toolbar-button-container"),
```

Add this predicate condition:

```python
            and value["container"] == "true"
```

- [ ] **Step 3: Update reviewer Back-chaining isolation helper**

In `e2e/reviewer_css_isolation_helpers.py`, add `panelContainer` to the returned object:

```python
            panelContainer: panel.getAttribute("data-aqe-toolbar-button-container"),
```

Add this assertion:

```python
    assert back_chaining_style["panelContainer"] == "true"
```

- [ ] **Step 4: Run targeted e2e tests**

Run:

```bash
python3 scripts/dev.py test-e2e -- e2e/test_editor_back_chaining_playback_workflow.py e2e/test_editor_voice_recording_comparison_workflow.py e2e/test_reviewer_audio_editor_workflow.py
```

Expected: PASS for the targeted workflows. If `scripts/dev.py test-e2e -- ...` is not supported by the runner, run the full e2e command in Step 5 and rely on the focused frontend tests from earlier tasks for fast feedback.

- [ ] **Step 5: Run full e2e**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS.

- [ ] **Step 6: Commit Task 4**

Run:

```bash
git add e2e/test_editor_back_chaining_playback_workflow.py e2e/test_editor_voice_recording_comparison_workflow.py e2e/reviewer_css_isolation_helpers.py
git commit -m "test: cover reusable editor toolbar panel semantics" -m "The panel refactor is only useful if real editor and reviewer webviews keep exposing grouped controls as semantic button containers. E2E coverage protects Back-chaining and Record / Play yours against regressions in rendered structure and visual grouping."
```

---

### Task 5: Full Verification And Final Commit Hygiene

**Files:**
- Verify: all files changed by Tasks 1-4

- [ ] **Step 1: Run frontend targeted tests**

Run:

```bash
cd settings_ui
npm run test -- editor-toolbar-visibility.test.ts editor-toolbar-render-items.test.ts editor-inline.integration.test.ts editor-inline.recording.integration.test.ts editor-inline.back-chaining.integration.test.ts
```

Expected: PASS.

- [ ] **Step 2: Run full repository check**

Run:

```bash
python3 scripts/dev.py check
```

Expected: PASS. Existing file-length warnings may appear; they are not introduced by this refactor.

- [ ] **Step 3: Run full e2e**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS.

- [ ] **Step 4: Inspect final diff**

Run:

```bash
git status --short
git diff --stat
git diff --check
```

Expected:

```text
git diff --check exits 0
```

The diff should include only shared panel metadata, Editor toolbar render-model extraction, semantic container attributes, and related tests.

- [ ] **Step 5: Create final refactor commit if earlier task commits were squashed or skipped**

If the work was not committed task-by-task, run:

```bash
git add settings_ui/src/lib/editor-toolbar-panel-definitions.ts settings_ui/src/lib/editor-toolbar-visibility.ts settings_ui/src/editor-inline/editor-toolbar-render-items.ts settings_ui/src/editor-inline/EditorControls.svelte settings_ui/src/editor-inline/EditorToolbarPanel.svelte settings_ui/src/editor-inline/recording-actions.ts settings_ui/tests/editor-toolbar-visibility.test.ts settings_ui/tests/editor-toolbar-render-items.test.ts settings_ui/tests/editor-inline.integration.test.ts settings_ui/tests/editor-inline.recording.integration.test.ts e2e/test_editor_back_chaining_playback_workflow.py e2e/test_editor_voice_recording_comparison_workflow.py e2e/reviewer_css_isolation_helpers.py
git commit -m "refactor: centralize editor toolbar panel intent" -m "Toolbar panel command groups were duplicated between settings visibility and editor rendering, which made future panel additions easy to drift. Shared panel definitions and a pure editor render model keep atomic panel intent in one place while preserving the existing visual wrapper and command behavior."
```

---

## Self-Review

- Spec coverage: The plan centralizes toolbar panel metadata, makes the Editor render path consume the same definitions, replaces CSS-class behavior coupling with a semantic attribute, and lists focused integration and e2e coverage for Back-chaining and Record / Play yours.
- Placeholder scan: No task contains unresolved placeholder work. Every created file and modified test includes concrete code.
- Type consistency: `ToolbarPanelDefinition`, `ToolbarPanelSlug`, `toolbarPanelDefinitionAt`, and `buildEditorToolbarRenderItems` are named consistently across tasks.
- Scope check: This is one refactor with no user-facing behavior change. The plan intentionally leaves speed/volume split run groups separate because they are not toolbar panels with the new labeled panel appearance.
