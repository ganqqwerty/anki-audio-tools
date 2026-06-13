# Segment Practice Floating Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `Practice segments` toggle a segment practice panel inside the floating selection toolbar, thicken the marker stripe, and render selection-boundary markers.

**Architecture:** Keep the current segment state/playback model. Add panel-open state on the visualizer dataset, render the practice controls inside `SelectionToolbar.svelte`, and render boundary markers as visual-only DOM markers derived from `baseRegion`.

**Tech Stack:** Svelte 5, TypeScript, CSS, Vitest, Anki e2e pytest runner.

---

### Task 1: Floating Toolbar Panel

**Files:**
- Modify: `settings_ui/src/editor-inline/segment-practice-controller.ts`
- Modify: `settings_ui/src/editor-inline/SelectionToolbar.svelte`
- Modify: `settings_ui/src/editor-inline/SegmentPracticePanel.svelte`
- Modify: `settings_ui/src/editor-inline/GraphVisualizer.svelte`

- [ ] Add `data-segment-panel-open`.
- [ ] Make `Practice segments` toggle panel open/closed.
- [ ] Move the practice controls into the floating selection toolbar.
- [ ] Remove the under-graph rail render.

### Task 2: Marker Stripe Rendering

**Files:**
- Modify: `settings_ui/src/editor-inline/segment-practice-dom.ts`
- Modify: `settings_ui/src/editor-inline/styles/visualizer.css`

- [ ] Render boundary markers at `baseRegion.startMs` and `baseRegion.endMs`.
- [ ] Use separate classes for boundary markers.
- [ ] Make the marker row and shading thicker.

### Task 3: Tests And Verification

**Files:**
- Modify: `settings_ui/src/editor-inline/test-contract.ts`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `settings_ui/tests/editor-inline.segment-practice.integration.test.ts`
- Modify: `e2e/test_editor_segmented_playback_workflow.py`

- [ ] Assert the panel toggles from the selection toolbar.
- [ ] Assert segment controls are in the floating toolbar panel, not under the graph.
- [ ] Assert boundary markers render.
- [ ] Run focused Vitest, targeted e2e, full `check`, and full `test-e2e`.
