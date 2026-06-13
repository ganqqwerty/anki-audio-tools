# Segmented Playback Button Placement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move segmented playback controls out of the Play split menu and into the graph-selection workflow.

**Architecture:** Keep the existing segmented playback state, geometry, and playback controller. Add a text entry point to the floating selection toolbar, render the existing controls as a graph-local rail, and remove the Play popover integration.

**Tech Stack:** Svelte 5, TypeScript, Vitest, Anki e2e pytest runner.

---

### Task 1: Selection Toolbar Entry

**Files:**
- Modify: `settings_ui/src/editor-inline/SelectionToolbar.svelte`
- Modify: `settings_ui/src/editor-inline/selection-toolbar-state.ts`
- Modify: `addon/anki_audio_quick_editor/locales/*.json`

- [ ] Add a text `Practice segments` button after the selection Play button.
- [ ] Wire it to enter segment editing for the current field and keep pointer events from starting graph gestures.
- [ ] Sync disabled/title state with the existing selection toolbar availability.
- [ ] Add locale keys for button label/title.

### Task 2: Graph-Local Rail

**Files:**
- Modify: `settings_ui/src/editor-inline/PlayPracticeOptions.svelte`
- Modify: `settings_ui/src/editor-inline/GraphVisualizer.svelte`
- Modify: `settings_ui/src/editor-inline/segment-practice-controller.ts`
- Modify: `settings_ui/src/editor-inline/styles/visualizer.css`

- [ ] Render the practice controls under the graph instead of inside the Play popover.
- [ ] Show controls only after `Practice segments` captures a base region.
- [ ] Add `Exit` to clear temporary segment mode.
- [ ] Keep marker row rendering and playback behavior unchanged.

### Task 3: Remove Play Popover Integration

**Files:**
- Modify: `settings_ui/src/editor-inline/PlaySplitButton.svelte`
- Modify: `settings_ui/src/editor-inline/styles/split-popovers.css`

- [ ] Remove `PlayPracticeOptions` import/render from the Play split menu.
- [ ] Remove segment-specific popover styles.
- [ ] Keep repeat and repeat-pause controls untouched.

### Task 4: Tests

**Files:**
- Modify: `settings_ui/tests/editor-inline.segment-practice.integration.test.ts`
- Modify: `e2e/test_editor_segmented_playback_workflow.py`

- [ ] Assert segment controls are absent from the Play split menu before entering segment mode.
- [ ] Click the selection toolbar `Practice segments` entry to show marker row and rail.
- [ ] Drive marker placement and practice controls from the rail.
- [ ] Keep zoomed marker placement and normal Play pause coverage.

### Task 5: Verification

- [ ] Run `npm test -- editor-inline.segment-practice-state.test.ts editor-inline.graph-overlay-geometry.test.ts editor-inline.segment-practice.integration.test.ts --run` from `settings_ui/`.
- [ ] Run `python3 scripts/dev.py check`.
- [ ] Run `python3 scripts/dev.py test-e2e`.
