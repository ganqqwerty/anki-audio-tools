# Selection Floating Toolbar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current selection-scoped panel buttons with a graph-local floating toolbar at the bottom-right of the selected region. The toolbar has small icon-only buttons for Play/Pause, Delete Region, Delete the rest, and Collapse, plus a collapsed blue halo dot that expands the toolbar on click.

**Architecture:** Keep the work inside the inline-editor frontend. Reuse the existing playback command path (`send("aqe:play", ...)`) and region-delete path (`sendRegionDelete(...)`). Add a small DOM overlay inside the visualizer, publish selection-relative pixel anchors from the existing renderer, and synchronize toolbar visibility, collapsed state, play state, destructive action availability, and hover previews from the canonical visualizer dataset.

**Tech Stack:** Svelte 5 + TypeScript inline editor, existing lucide icon wrapper, Vitest/jsdom frontend integration tests, Python e2e tests against Anki/Qt, existing `scripts/dev.py` quality gates.

---

## File Structure

- Modify `settings_ui/src/lib/icon-types.ts` and `settings_ui/src/lib/CommandIcon.svelte` if the collapse button uses a new `x` icon.
- Modify `settings_ui/src/editor-inline/dom-selectors.ts` to expose toolbar and plot-wrapper selectors.
- Modify `settings_ui/src/editor-inline/region-delete-state.ts` to export shared region-delete availability and to sync toolbar buttons instead of panel-only buttons.
- Add `settings_ui/src/editor-inline/selection-toolbar-state.ts` for toolbar visibility, collapsed state, preview state, play label sync, and test-state helpers.
- Modify `settings_ui/src/editor-inline/EditorControls.svelte` to move Delete Region/Delete the rest into a floating graph toolbar, add Play/Pause and Collapse, and add the collapsed dot.
- Modify `settings_ui/src/editor-inline/visualizer-renderer.ts` to publish selection overlay geometry as CSS custom properties on the graph plot wrapper.
- Modify `settings_ui/src/editor-inline/actions.ts`, `settings_ui/src/editor-inline/control-actions.ts`, `settings_ui/src/editor-inline/playback-actions.ts`, and graph redraw paths as needed so toolbar state stays synchronized after selection, draft, resize, busy, playback, and redraw changes.
- Modify `settings_ui/src/editor-inline/styles.css` for the toolbar, small icon-only buttons, collapsed halo dot, focus states, and red hover previews.
- Modify `settings_ui/src/editor-inline/types.ts` and `settings_ui/src/editor-inline/test-contract.ts` to expose toolbar state for tests and e2e assertions.
- Add `settings_ui/tests/editor-inline.selection-toolbar.integration.test.ts`.
- Modify `settings_ui/tests/editor-inline.selection-delete.integration.test.ts` and `settings_ui/tests/editor-inline.selection-playback.integration.test.ts` to target the toolbar controls.
- Modify `settings_ui/tests/editor-inline.integration.helpers.ts` with toolbar query and hover helpers.
- Modify `e2e/editor_graph_helpers.py` to expose toolbar state from the WebView.
- Modify `e2e/test_editor_region_delete_workflow.py` or add `e2e/test_editor_selection_toolbar_workflow.py` for the full end-to-end toolbar interaction.

## Baseline Requirements

- The approved design spec is `docs/superpowers/specs/2026-05-22-selection-floating-toolbar-design.md`.
- The static interaction prototype is `docs/prototypes/graph-selection-action-prototypes.html#chosen-floating-toolbar`.
- No Python bridge, audio-rendering, or command-contract changes are expected.
- Existing Backspace behavior must stay mapped to `delete-selection`.
- Existing selected-region playback semantics must stay owned by the playback controller.
- Existing delete requests must still be built at click time from current visualizer state, not from cached toolbar state.

## GitNexus Baseline

Before editing runtime symbols, run GitNexus impact for the existing symbols touched by this plan if GitNexus MCP tools are available:

```text
gitnexus_impact({repo: "anki-audio-tools", target: "syncRegionDeleteControl", direction: "upstream"})
gitnexus_impact({repo: "anki-audio-tools", target: "regionDeleteRequestFor", direction: "upstream"})
gitnexus_impact({repo: "anki-audio-tools", target: "renderSelection", direction: "upstream"})
gitnexus_impact({repo: "anki-audio-tools", target: "setCommandButtonLabel", direction: "upstream"})
gitnexus_impact({repo: "anki-audio-tools", target: "GraphStateForTest", direction: "upstream"})
```

Expected: frontend integration tests, e2e helpers, selection gesture flows, and playback label updates are the main upstream blast radius. No backend Python render path should be affected.

If GitNexus MCP is unavailable in the active session, record that explicitly in the work log and inspect direct callers with `rg` before editing each symbol. Do not silently skip the blast-radius step.

## Task 1: Write Failing Toolbar Tests

**Files:**
- Add: `settings_ui/tests/editor-inline.selection-toolbar.integration.test.ts`
- Modify: `settings_ui/tests/editor-inline.selection-delete.integration.test.ts`
- Modify: `settings_ui/tests/editor-inline.selection-playback.integration.test.ts`
- Modify: `settings_ui/tests/editor-inline.integration.helpers.ts`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `e2e/editor_graph_helpers.py`
- Modify: `e2e/test_editor_region_delete_workflow.py`
- Add: `e2e/test_editor_selection_toolbar_workflow.py`

- [ ] **Step 1: Add toolbar state fields to the test type first**

In `settings_ui/src/editor-inline/types.ts`, extend `GraphStateForTest` with fields the failing tests will use:

```ts
selectionToolbarCollapsed: boolean;
selectionToolbarDeleteRegionDisabled: boolean;
selectionToolbarDeleteRegionHidden: boolean;
selectionToolbarDeleteRestDisabled: boolean;
selectionToolbarDeleteRestHidden: boolean;
selectionToolbarDotHidden: boolean;
selectionToolbarHidden: boolean;
selectionToolbarLeftPx: number | null;
selectionToolbarPlayAriaLabel: string;
selectionToolbarPlayState: "pause" | "play";
selectionToolbarPreview: "none" | "region" | "rest";
selectionToolbarTopPx: number | null;
```

Keep the existing `regionDeleteButtonDisabled`, `regionDeleteButtonHidden`, `regionDeleteRestButtonDisabled`, and `regionDeleteRestButtonHidden` fields for compatibility with existing tests and e2e helpers. They should later point at the toolbar delete buttons.

- [ ] **Step 2: Add test helpers**

In `settings_ui/tests/editor-inline.integration.helpers.ts`, add helpers:

```ts
export function selectionToolbarButton(
  kind: "collapse" | "delete-region" | "delete-rest" | "play",
  ord = 0,
): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>(`[data-testid="aqe-selection-toolbar-${kind}-${ord}"]`)!;
}

export function selectionToolbarDot(ord = 0): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>(`[data-testid="aqe-selection-toolbar-dot-${ord}"]`)!;
}

export function hoverToolbarButton(button: HTMLElement): void {
  button.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));
}

export function leaveToolbarButton(button: HTMLElement): void {
  button.dispatchEvent(new MouseEvent("mouseleave", { bubbles: true }));
}
```

Use these helpers in new tests instead of repeatedly hardcoding selectors.

- [ ] **Step 3: Add a new failing toolbar integration test file**

Create `settings_ui/tests/editor-inline.selection-toolbar.integration.test.ts` with tests for:

1. Toolbar hidden with no graph track.
2. Toolbar hidden during a draft selection and visible after a committed valid selection.
3. Toolbar anchors near the bottom-right selection edge and clamps near the graph right edge.
4. Buttons are icon-only, small-command controls with `title` and `aria-label`.
5. Collapse hides the toolbar and shows the blue dot.
6. Clicking the blue dot expands the toolbar.
7. Creating a new selection resets collapsed state to expanded.
8. Hovering/focusing Delete Region sets preview state to `region`.
9. Hovering/focusing Delete the rest sets preview state to `rest`.
10. Preview clears on leave, blur, click, selection clear, and busy state.
11. Preview state is scoped to one visualizer when two audio fields are mounted.

Use this setup pattern:

```ts
initializeEditorRuntime({ audioFieldIndices: [0] });
scan({ audioFieldIndices: [0] });
window.__aqeSetVisualizer?.(0, track, 250);
const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
setGraphBounds(svg);
dragGraphSelection(svg, 0.2, 0.6);
```

Expected failing assertions before implementation:

```ts
expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
  selectionToolbarHidden: false,
  selectionToolbarCollapsed: false,
  selectionToolbarDotHidden: true,
  selectionToolbarPreview: "none",
  selectionToolbarPlayState: "play",
});
```

For icon-only buttons, assert that accessible labels exist and visible text labels do not:

```ts
const play = selectionToolbarButton("play");
expect(play.title).toBe("Play selection");
expect(play.getAttribute("aria-label")).toBe("Play selection");
expect(play.querySelector(".aqe-button-label")).toBeNull();
```

- [ ] **Step 4: Update delete tests to click toolbar buttons**

In `settings_ui/tests/editor-inline.selection-delete.integration.test.ts`, keep the request payload assertions but query toolbar buttons:

```ts
const button = selectionToolbarButton("delete-region");
```

and:

```ts
const button = selectionToolbarButton("delete-rest");
```

Update the whole-clip selection test to match the chosen behavior: the toolbar is not available for invalid whole-clip destructive actions.

```ts
expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
  selectionActive: true,
  selectionToolbarHidden: true,
  regionDeleteButtonHidden: true,
  regionDeleteRestButtonHidden: true,
});
```

Backspace expectations remain unchanged:

```ts
expect(window.__aqePopPendingRegionDeleteRequest?.()).toMatchObject({
  operation: "delete-selection",
  trigger: "backspace",
});
```

- [ ] **Step 5: Update playback tests to cover toolbar Play/Pause**

In `settings_ui/tests/editor-inline.selection-playback.integration.test.ts`, add a focused test that:

1. Creates a valid selection.
2. Installs/prepares the HTML audio test driver.
3. Clicks `selectionToolbarButton("play")`.
4. Verifies selected-region playback starts from the selection.
5. Verifies toolbar play state changes to pause.
6. Clicks the toolbar button again.
7. Verifies playback pauses through the existing command flow.

Expected state after first click:

```ts
expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
  playbackState: "playing",
  playbackRegionMode: "selection",
  playbackStartMs: 200,
  playbackEndMs: 600,
  selectionToolbarPlayState: "pause",
  selectionToolbarPlayAriaLabel: "Pause selection",
});
```

- [ ] **Step 6: Add failing e2e toolbar state support**

In `e2e/editor_graph_helpers.py`, extend `_visualizer_js(...)` with toolbar queries after the current delete-button queries:

```js
const toolbar = visualizer.querySelector('.aqe-selection-toolbar');
const toolbarDot = visualizer.querySelector('.aqe-selection-toolbar-dot');
const toolbarPlay = visualizer.querySelector('.aqe-selection-toolbar-play');
const toolbarDelete = visualizer.querySelector('.aqe-delete-region-button');
const toolbarDeleteRest = visualizer.querySelector('.aqe-delete-rest-button');
```

Return these fields in the state object:

```js
selectionToolbarHidden: toolbar ? toolbar.hidden : true,
selectionToolbarCollapsed: visualizer.dataset.selectionToolbarCollapsed === "true",
selectionToolbarDotHidden: toolbarDot ? toolbarDot.hidden : true,
selectionToolbarPreview: (
  visualizer.dataset.selectionToolbarPreview === "region"
  || visualizer.dataset.selectionToolbarPreview === "rest"
) ? visualizer.dataset.selectionToolbarPreview : "none",
selectionToolbarPlayState: toolbarPlay?.dataset.aqeButtonState || "",
selectionToolbarPlayAriaLabel: toolbarPlay?.getAttribute("aria-label") || "",
selectionToolbarDeleteRegionDisabled: toolbarDelete ? toolbarDelete.disabled : true,
selectionToolbarDeleteRegionHidden: toolbarDelete ? toolbarDelete.hidden : true,
selectionToolbarDeleteRestDisabled: toolbarDeleteRest ? toolbarDeleteRest.disabled : true,
selectionToolbarDeleteRestHidden: toolbarDeleteRest ? toolbarDeleteRest.hidden : true,
regionDeleteButtonDisabled: toolbarDelete ? toolbarDelete.disabled : true,
regionDeleteButtonHidden: toolbarDelete ? toolbarDelete.hidden : true,
regionDeleteRestButtonDisabled: toolbarDeleteRest ? toolbarDeleteRest.disabled : true,
regionDeleteRestButtonHidden: toolbarDeleteRest ? toolbarDeleteRest.hidden : true,
```

This is test-support code. It is expected to return hidden/disabled values before the toolbar implementation exists, which lets the new e2e tests fail on behavior instead of missing keys.

- [ ] **Step 7: Add a dedicated failing e2e toolbar workflow file**

Create `e2e/test_editor_selection_toolbar_workflow.py`:

```py
"""E2E tests for the selected-region floating toolbar."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_graph_helpers import (
    _click_graph_and_wait,
    _graph_state_js,
    _install_html_audio_test_driver,
    _wait_for_html_playback,
    _wait_for_visualizer_track,
)
from e2e.editor_note_helpers import (
    _basic_audio_note,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
    _wait_for_generated_mp3,
)
from e2e.helpers import click_selector, generate_tone, run_js, wait_for_js_condition


def _plot_pointer_script(ord_: int, start_ratio: float, end_ratio: float) -> str:
    return f"""
    (() => {{
      const ord = {ord_};
      const svg = document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${{ord}}"] .aqe-visualizer-svg`);
      const rect = svg.getBoundingClientRect();
      const plot = {{ width: 620, left: 44, right: 10 }};
      const plotLeft = rect.left + (plot.left / plot.width) * rect.width;
      const plotWidth = ((plot.width - plot.left - plot.right) / plot.width) * rect.width;
      const xFor = (ratio) => plotLeft + plotWidth * ratio;
      const EventCtor = window.PointerEvent || window.MouseEvent;
      svg.dispatchEvent(new EventCtor("pointerdown", {{
        bubbles: true,
        clientX: xFor({start_ratio}),
        clientY: rect.top + 20,
        shiftKey: true,
      }}));
      window.dispatchEvent(new EventCtor("pointermove", {{
        bubbles: true,
        clientX: xFor({end_ratio}),
        clientY: rect.top + 20,
        shiftKey: true,
      }}));
      window.dispatchEvent(new EventCtor("pointerup", {{
        bubbles: true,
        clientX: xFor({end_ratio}),
        clientY: rect.top + 20,
        shiftKey: true,
      }}));
    }})()
    """


def _shift_drag_region(editor, start_ratio: float, end_ratio: float, ord_: int = 0) -> None:
    run_js(editor.web, _plot_pointer_script(ord_, start_ratio, end_ratio))


def _toolbar_selector(kind: str, ord_: int = 0) -> str:
    return f'[data-testid="aqe-selection-toolbar-{kind}-{ord_}"]'


def _dispatch_toolbar_event(editor, kind: str, event_name: str, ord_: int = 0) -> None:
    run_js(
        editor.web,
        f"""
        (() => {{
          const button = document.querySelector({_toolbar_selector(kind, ord_)!r});
          if (!button) return false;
          button.dispatchEvent(new MouseEvent({event_name!r}, {{ bubbles: true }}));
          return true;
        }})()
        """,
    )


def _wait_for_toolbar(editor, predicate=lambda state: True, timeout: float = 5.0):
    return wait_for_js_condition(
        editor.web,
        _graph_state_js(),
        lambda state: state is not None
        and state["selectionToolbarHidden"] is False
        and predicate(state),
        timeout=timeout,
    )


def test_selection_toolbar_appears_collapses_and_expands(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_toolbar_expand_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _shift_drag_region(editor, 0.25, 0.625)
        visible = _wait_for_toolbar(
            editor,
            lambda state: state["selectionToolbarCollapsed"] is False
            and state["selectionToolbarDotHidden"] is True
            and state["selectionToolbarDeleteRegionHidden"] is False
            and state["selectionToolbarDeleteRestHidden"] is False,
        )
        assert visible["selectionStartMs"] == 500
        assert visible["selectionEndMs"] == 1250

        click_selector(editor.web, _toolbar_selector("collapse"), timeout=5.0)
        collapsed = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None
            and state["selectionToolbarCollapsed"] is True
            and state["selectionToolbarHidden"] is True
            and state["selectionToolbarDotHidden"] is False,
            timeout=5.0,
        )
        assert collapsed["selectionActive"] is True

        click_selector(editor.web, _toolbar_selector("dot"), timeout=5.0)
        expanded = _wait_for_toolbar(
            editor,
            lambda state: state["selectionToolbarCollapsed"] is False
            and state["selectionToolbarDotHidden"] is True,
        )
        assert expanded["selectionActive"] is True
    finally:
        editor.set_note(None)
        parent.close()


def test_selection_toolbar_delete_hover_previews_clear_and_switch(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_toolbar_preview_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _shift_drag_region(editor, 0.2, 0.6)
        _wait_for_toolbar(editor)

        _dispatch_toolbar_event(editor, "delete-region", "mouseenter")
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and state["selectionToolbarPreview"] == "region",
            timeout=5.0,
        )

        _dispatch_toolbar_event(editor, "delete-region", "mouseleave")
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and state["selectionToolbarPreview"] == "none",
            timeout=5.0,
        )

        _dispatch_toolbar_event(editor, "delete-rest", "mouseenter")
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None and state["selectionToolbarPreview"] == "rest",
            timeout=5.0,
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_selection_toolbar_play_pause_uses_selected_html_audio(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_toolbar_play_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _install_html_audio_test_driver(editor)
        _shift_drag_region(editor, 0.25, 0.625)
        _wait_for_toolbar(editor)

        click_selector(editor.web, _toolbar_selector("play"), timeout=5.0)
        playing = _wait_for_html_playback(
            editor,
            lambda state: state["playbackRegionMode"] == "selection"
            and 450 <= state["playbackStartMs"] <= 550
            and 1200 <= state["playbackEndMs"] <= 1300
            and state["selectionToolbarPlayState"] == "pause"
            and state["selectionToolbarPlayAriaLabel"] == "Pause selection",
        )
        assert playing["selectionActive"] is True

        click_selector(editor.web, _toolbar_selector("play"), timeout=5.0)
        wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None
            and state["playbackState"] == "paused"
            and state["selectionToolbarPlayState"] == "play",
            timeout=5.0,
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_selection_toolbar_delete_rest_keeps_selected_audio(anki_mw, ffmpeg_config) -> None:
    from anki_audio_quick_editor.audio_processor import (
        AudioProcessingConfig,
        probe_duration_ms,
    )

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_toolbar_delete_rest_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _shift_drag_region(editor, 0.25, 0.625)
        _wait_for_toolbar(
            editor,
            lambda state: state["selectionToolbarDeleteRestHidden"] is False
            and state["selectionToolbarDeleteRestDisabled"] is False,
        )

        previous_name = _sound_filename(note.fields[0])
        click_selector(editor.web, _toolbar_selector("delete-rest"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
        redrawn = _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_name
            and value["selectionActive"] is True
            and value["selectionToolbarHidden"] is True,
            timeout=10.0,
        )

        generated_duration = probe_duration_ms(media_dir / generated_name, AudioProcessingConfig.from_config({}))
        assert source.read_bytes() == original_bytes
        assert generated_name.startswith("editor_toolbar_delete_rest_source__aqe_")
        assert 600 <= generated_duration <= 900
        assert redrawn["playbackState"] == "stopped"
    finally:
        editor.set_note(None)
        parent.close()


def test_selection_toolbar_hides_for_whole_clip_selection(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_toolbar_whole_clip_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        _shift_drag_region(editor, 0.0, 1.0)
        whole_clip = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None
            and state["selectionActive"] is True
            and state["selectionToolbarHidden"] is True
            and state["regionDeleteButtonHidden"] is True
            and state["regionDeleteRestButtonHidden"] is True,
            timeout=5.0,
        )
        assert whole_clip["selectionStartMs"] == 0
        assert abs(whole_clip["selectionEndMs"] - whole_clip["durationMs"]) <= 1
    finally:
        editor.set_note(None)
        parent.close()
```

These five e2e tests should be introduced before implementation. They should fail because the toolbar selectors and toolbar state do not exist yet.

- [ ] **Step 8: Update existing region-delete e2e to expect toolbar controls**

In `e2e/test_editor_region_delete_workflow.py`, keep the generated-file assertions but update the selection wait predicates to require toolbar visibility:

```py
selected = wait_for_js_condition(
    editor.web,
    _graph_state_js(),
    lambda state: state is not None
    and state["selectionActive"] is True
    and state["selectionToolbarHidden"] is False
    and state["regionDeleteButtonHidden"] is False
    and state["regionDeleteButtonDisabled"] is False,
    timeout=5.0,
)
```

For the Delete the rest test:

```py
selected = wait_for_js_condition(
    editor.web,
    _graph_state_js(),
    lambda state: state is not None
    and state["selectionActive"] is True
    and state["selectionToolbarHidden"] is False
    and state["regionDeleteRestButtonHidden"] is False
    and state["regionDeleteRestButtonDisabled"] is False,
    timeout=5.0,
)
```

Keep the clicks using `_button_selector("aqe:delete-selection")` and `_button_selector("aqe:delete-rest")`; the implementation task must preserve `data-aqe-command` on the toolbar buttons.

- [ ] **Step 9: Run the targeted frontend and e2e tests and confirm failure**

Run:

```bash
cd settings_ui
npm run test -- tests/editor-inline.selection-toolbar.integration.test.ts tests/editor-inline.selection-delete.integration.test.ts tests/editor-inline.selection-playback.integration.test.ts
```

Expected: FAIL because toolbar markup, state fields, and selectors do not exist yet.

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_selection_toolbar_workflow.py
python3 scripts/dev.py test-e2e e2e/test_editor_region_delete_workflow.py
```

Expected: FAIL because `aqe-selection-toolbar-*` selectors and toolbar state are not implemented yet. The failure should be a missing selector or `selectionToolbarHidden is True`, not a Python import error.

## Task 2: Add Toolbar State And Shared Delete Availability

**Files:**
- Modify: `settings_ui/src/editor-inline/dom-selectors.ts`
- Modify: `settings_ui/src/editor-inline/region-delete-state.ts`
- Add: `settings_ui/src/editor-inline/selection-toolbar-state.ts`

- [ ] **Step 1: Run pre-edit impact checks**

Run impact checks for:

```text
syncRegionDeleteControl
syncAllRegionDeleteControls
regionDeleteRequestFor
buttonFor
```

Expected: changes are frontend-only, with `actions.ts`, `control-actions.ts`, tests, and e2e helpers as the likely callers.

- [ ] **Step 2: Add toolbar selectors**

In `settings_ui/src/editor-inline/dom-selectors.ts`, add:

```ts
export function visualizerPlotForOrd(ord: number): HTMLElement | null {
  return visualizerForOrd(ord)?.querySelector<HTMLElement>(".aqe-visualizer-plot") ?? null;
}

export function selectionToolbarForOrd(ord: number): HTMLElement | null {
  return visualizerForOrd(ord)?.querySelector<HTMLElement>(".aqe-selection-toolbar") ?? null;
}

export function selectionToolbarDotForOrd(ord: number): HTMLButtonElement | null {
  return visualizerForOrd(ord)?.querySelector<HTMLButtonElement>(".aqe-selection-toolbar-dot") ?? null;
}
```

- [ ] **Step 3: Export region-delete availability**

In `settings_ui/src/editor-inline/region-delete-state.ts`, export a small availability helper and reuse it from `syncRegionDeleteControl(...)` and `regionDeleteRequestFor(...)`:

```ts
export interface RegionDeleteAvailability {
  hasSelection: boolean;
  valid: boolean;
  wholeSelection: boolean;
}

export function regionDeleteAvailabilityFor(visualizer: VisualizerElement): RegionDeleteAvailability {
  const region = selectionForVisualizer(visualizer);
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const wholeSelection = !!region && isWholeSelection(region, durationMs);
  return {
    hasSelection: region !== null,
    valid: isValidRegionDeleteSelection(region, durationMs),
    wholeSelection,
  };
}
```

Also export `titleForOperation(...)` if toolbar sync needs the same invalid-state titles.

- [ ] **Step 4: Add `selection-toolbar-state.ts`**

Create `settings_ui/src/editor-inline/selection-toolbar-state.ts` with responsibilities:

- read canonical visualizer state,
- show toolbar only for a committed, valid selection,
- hide toolbar while draft selection is active,
- reset collapsed state when the committed selection changes,
- collapse/expand toolbar,
- set preview state,
- sync toolbar Play/Pause icon, title, and `aria-label`,
- sync Delete Region/Delete the rest disabled states,
- expose a compact object for `test-contract.ts`.

Use an explicit preview type:

```ts
export type SelectionToolbarPreview = "none" | "region" | "rest";
```

Use a stable selection key to reset collapsed state only when selection changes:

```ts
function selectionKey(visualizer: VisualizerElement): string {
  return [
    visualizer.dataset.sourceFilename || "",
    visualizer.dataset.selectionStartMs || "",
    visualizer.dataset.selectionEndMs || "",
    visualizer.dataset.durationMs || "",
  ].join("|");
}
```

Core exported functions:

```ts
export function syncSelectionToolbar(visualizer: VisualizerElement): void;
export function syncAllSelectionToolbars(): void;
export function collapseSelectionToolbar(visualizer: VisualizerElement): void;
export function expandSelectionToolbar(visualizer: VisualizerElement): void;
export function setSelectionToolbarPreview(
  visualizer: VisualizerElement,
  preview: SelectionToolbarPreview,
): void;
```

Implementation notes:

- Store collapsed state in `visualizer.dataset.selectionToolbarCollapsed`.
- Store preview state in `visualizer.dataset.selectionToolbarPreview`.
- Store last selection key in `visualizer.dataset.selectionToolbarSelectionKey`.
- Set `toolbar.hidden` and `dot.hidden`; also set `aria-hidden` consistently.
- Set delete button `hidden` to the inverse of availability so existing `regionDeleteButtonHidden` state remains meaningful.
- Clear preview whenever the toolbar hides or busy state changes.

- [ ] **Step 5: Preserve old sync exports**

Keep `syncRegionDeleteControl(...)` and `syncAllRegionDeleteControls(...)` exported for compatibility, but make them either:

- delegate to `syncSelectionToolbar(...)`, or
- only sync delete buttons that now live inside the toolbar.

Avoid introducing an import cycle. If `region-delete-state.ts` cannot import `selection-toolbar-state.ts` cleanly, invert the dependency:

- `selection-toolbar-state.ts` imports `regionDeleteAvailabilityFor(...)`,
- `actions.ts` and `control-actions.ts` call `syncSelectionToolbar(...)`,
- old `syncRegionDeleteControl(...)` only syncs delete buttons when called by legacy paths.

- [ ] **Step 6: Run targeted tests**

Run:

```bash
cd settings_ui
npm run test -- tests/editor-inline.selection-toolbar.integration.test.ts tests/editor-inline.selection-delete.integration.test.ts
```

Expected: still FAIL because markup and renderer geometry are not in place yet, but TypeScript imports should resolve.

## Task 3: Render Toolbar Markup And Wire Actions

**Files:**
- Modify: `settings_ui/src/lib/icon-types.ts`
- Modify: `settings_ui/src/lib/CommandIcon.svelte`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/src/editor-inline/actions.ts`
- Modify: `settings_ui/src/editor-inline/control-actions.ts`
- Modify: `settings_ui/src/editor-inline/playback-actions.ts`

- [ ] **Step 1: Run pre-edit impact checks**

Run impact checks for:

```text
EditorControls
setSelectionDraft
commitSelectionDraft
clearSelection
setSelection
setControlsBusy
setCommandButtonLabel
setPlaybackButtonLabel
```

Expected: frontend integration tests, playback tests, and selection gesture flows are the main blast radius.

- [ ] **Step 2: Add the collapse icon if needed**

If using an X icon for Collapse, update `settings_ui/src/lib/icon-types.ts`:

```ts
| "x"
```

and `settings_ui/src/lib/CommandIcon.svelte`:

```ts
import X from "@lucide/svelte/icons/x";
```

```svelte
{:else if icon === "x"}
  <X {size} {strokeWidth} />
```

- [ ] **Step 3: Move selection delete buttons into the graph overlay**

In `settings_ui/src/editor-inline/EditorControls.svelte`, remove the standalone panel-level hidden delete buttons that currently sit before `.aqe-status`.

Inside `.aqe-visualizer`, wrap the SVG in a positioned plot wrapper:

```svelte
<div class="aqe-visualizer-plot" data-testid={`aqe-visualizer-plot-${target.ord}`}>
  <!-- Move the existing .aqe-visualizer-svg block here unchanged. -->
  <svg class="aqe-visualizer-svg" data-testid={`aqe-graph-svg-${target.ord}`}>
  </svg>
  <div
    class="aqe-selection-toolbar"
    data-testid={`aqe-selection-toolbar-${target.ord}`}
    role="toolbar"
    aria-label="Selection actions"
    hidden
  >
    <!-- Add the four toolbar buttons in Step 4. -->
  </div>
  <button
    type="button"
    class="aqe-selection-toolbar-dot"
    data-testid={`aqe-selection-toolbar-dot-${target.ord}`}
    title="Expand selection actions"
    aria-label="Expand selection actions"
    hidden
  ></button>
</div>
```

The existing `.aqe-visualizer-meta` remains after the plot wrapper.

- [ ] **Step 4: Add toolbar buttons**

Add four toolbar controls in this order:

1. Play/Pause
2. Delete Region
3. Delete the rest
4. Collapse

Use icon-only markup. Do not render `.aqe-button-label` inside toolbar buttons.

Suggested markup for Play/Pause:

```svelte
<button
  type="button"
  class="aqe-button aqe-selection-toolbar-button aqe-selection-toolbar-play"
  data-testid={`aqe-selection-toolbar-play-${target.ord}`}
  data-aqe-button-state="play"
  title="Play selection"
  aria-label="Play selection"
  onmousedown={(event) => event.preventDefault()}
  onclick={() => send("aqe:play", target.node, target.ord)}
>
  <EditorCommandIcon className="aqe-button-icon-default" icon="play" />
  <EditorCommandIcon className="aqe-button-icon-active" icon="pause" />
</button>
```

Suggested delete buttons:

```svelte
<button
  type="button"
  class="aqe-button aqe-selection-toolbar-button aqe-delete-region-button"
  data-aqe-command="aqe:delete-selection"
  data-testid={`aqe-selection-toolbar-delete-region-${target.ord}`}
  title={t("editor.command.delete_region.title")}
  aria-label={t("editor.command.delete_region.title")}
  onmousedown={(event) => event.preventDefault()}
  onfocus={() => setSelectionToolbarPreviewForOrd(target.ord, "region")}
  onblur={() => setSelectionToolbarPreviewForOrd(target.ord, "none")}
  onmouseenter={() => setSelectionToolbarPreviewForOrd(target.ord, "region")}
  onmouseleave={() => setSelectionToolbarPreviewForOrd(target.ord, "none")}
  onclick={() => sendRegionDelete("button", target.node, target.ord)}
>
  <EditorCommandIcon icon="trash-2" />
</button>
```

For Delete the rest, keep `data-aqe-command="aqe:delete-rest"`, use test id `aqe-selection-toolbar-delete-rest-${target.ord}`, preview `"rest"`, and call:

```svelte
onclick={() => sendRegionDelete("button", target.node, target.ord, "delete-rest")}
```

For Collapse:

```svelte
<button
  type="button"
  class="aqe-button aqe-selection-toolbar-button aqe-selection-toolbar-collapse"
  data-testid={`aqe-selection-toolbar-collapse-${target.ord}`}
  title="Collapse selection actions"
  aria-label="Collapse selection actions"
  onmousedown={(event) => event.preventDefault()}
  onclick={() => collapseSelectionToolbarForOrd(target.ord)}
>
  <EditorCommandIcon icon="x" />
</button>
```

For the dot:

```svelte
onclick={() => expandSelectionToolbarForOrd(target.ord)}
```

Expose thin `ForOrd` wrappers from `selection-toolbar-state.ts` if that keeps Svelte markup simple.

- [ ] **Step 5: Synchronize toolbar after selection mutations**

In `settings_ui/src/editor-inline/actions.ts`, replace or augment `syncRegionDeleteControl(visualizer)` calls with `syncSelectionToolbar(visualizer)` after:

- `clearSelectionDraft(...)`,
- `setSelectionDraft(...)`,
- `commitSelectionDraft(...)`,
- `clearSelection(...)`,
- `setSelection(...)`,
- `initializePlaybackRegionState(...)` if needed.

This is required so the toolbar hides during draft drag and reappears after commit.

- [ ] **Step 6: Synchronize toolbar during busy changes**

In `settings_ui/src/editor-inline/control-actions.ts`, replace `syncAllRegionDeleteControls()` with `syncAllSelectionToolbars()` or call both if legacy tests still depend on the old name.

Ensure `setControlsBusy(...)` disables toolbar buttons because they keep the `.aqe-button` class.

- [ ] **Step 7: Synchronize toolbar Play/Pause state**

In `settings_ui/src/editor-inline/playback-actions.ts`, after `setPlaybackButtonLabel(...)` updates the main play button, also sync the toolbar play button for the same visualizer.

The toolbar button state should be:

- `data-aqe-button-state="play"` and `aria-label="Play selection"` when playback is stopped or paused,
- `data-aqe-button-state="pause"` and `aria-label="Pause selection"` when playback is playing.

Use current visualizer dataset as the source of truth, not the text label passed to the main button.

- [ ] **Step 8: Run targeted tests**

Run:

```bash
cd settings_ui
npm run test -- tests/editor-inline.selection-toolbar.integration.test.ts tests/editor-inline.selection-delete.integration.test.ts tests/editor-inline.selection-playback.integration.test.ts
```

Expected: some tests may still FAIL on position/CSS preview until renderer and styles are added, but click handlers should now dispatch through existing paths.

## Task 4: Add Geometry, Styling, And Hover Previews

**Files:**
- Modify: `settings_ui/src/editor-inline/visualizer-renderer.ts`
- Modify: `settings_ui/src/editor-inline/styles.css`
- Modify: `settings_ui/src/editor-inline/test-contract.ts`

- [ ] **Step 1: Run pre-edit impact checks**

Run impact checks for:

```text
renderSelection
resetVisualizerPlot
graphStateForTest
```

Expected: selection rendering, resize handles, and e2e graph state are the affected areas.

- [ ] **Step 2: Publish overlay geometry from the renderer**

In `settings_ui/src/editor-inline/visualizer-renderer.ts`, add helpers that update the plot wrapper:

```ts
function plotWrapperFor(visualizer: VisualizerElement): HTMLElement | null {
  return visualizer.querySelector<HTMLElement>(".aqe-visualizer-plot");
}

function setSelectionOverlayGeometry(
  visualizer: VisualizerElement,
  startX: number,
  endX: number,
  plotBottom: number,
): void {
  const wrapper = plotWrapperFor(visualizer);
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  if (!wrapper || !svg) return;
  const rect = svg.getBoundingClientRect();
  const scaleX = rect.width > 0 ? rect.width / PLOT.width : 1;
  const scaleY = rect.height > 0 ? rect.height / PLOT.height : 1;
  const startPx = startX * scaleX;
  const endPx = endX * scaleX;
  const bottomPx = plotBottom * scaleY;
  wrapper.style.setProperty("--aqe-selection-start-px", `${startPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-end-px", `${endPx.toFixed(2)}px`);
  wrapper.style.setProperty("--aqe-selection-bottom-px", `${bottomPx.toFixed(2)}px`);
  wrapper.dataset.selectionOverlayReady = "true";
}
```

When selection is hidden, clear the data flag and preview variables:

```ts
function clearSelectionOverlayGeometry(visualizer: VisualizerElement): void {
  const wrapper = plotWrapperFor(visualizer);
  if (!wrapper) return;
  wrapper.dataset.selectionOverlayReady = "false";
  wrapper.style.removeProperty("--aqe-selection-start-px");
  wrapper.style.removeProperty("--aqe-selection-end-px");
  wrapper.style.removeProperty("--aqe-selection-bottom-px");
}
```

Call `setSelectionOverlayGeometry(...)` after `startX`, `endX`, and `plotBottom` are computed in `renderSelection(...)`. Call `clearSelectionOverlayGeometry(...)` on every early hidden-selection path.

- [ ] **Step 3: Add test-contract toolbar state**

In `settings_ui/src/editor-inline/test-contract.ts`, query:

```ts
const toolbar = visualizer.querySelector<HTMLElement>(".aqe-selection-toolbar");
const toolbarDot = visualizer.querySelector<HTMLButtonElement>(".aqe-selection-toolbar-dot");
const toolbarPlay = visualizer.querySelector<HTMLButtonElement>(".aqe-selection-toolbar-play");
```

Populate the `GraphStateForTest` fields added in Task 1 from DOM state and CSS custom properties:

```ts
selectionToolbarHidden: toolbar ? toolbar.hidden : true,
selectionToolbarCollapsed: visualizer.dataset.selectionToolbarCollapsed === "true",
selectionToolbarDotHidden: toolbarDot ? toolbarDot.hidden : true,
selectionToolbarPreview: visualizer.dataset.selectionToolbarPreview === "region"
  || visualizer.dataset.selectionToolbarPreview === "rest"
  ? visualizer.dataset.selectionToolbarPreview
  : "none",
selectionToolbarPlayState: toolbarPlay?.dataset.aqeButtonState === "pause" ? "pause" : "play",
selectionToolbarPlayAriaLabel: toolbarPlay?.getAttribute("aria-label") || "",
selectionToolbarLeftPx: cssPixelNumber(toolbar, "--aqe-selection-toolbar-left-px"),
selectionToolbarTopPx: cssPixelNumber(toolbar, "--aqe-selection-toolbar-top-px"),
```

If left/top are actual inline `style.left` and `style.top` values instead of custom properties, expose those values consistently.

- [ ] **Step 4: Add toolbar CSS**

In `settings_ui/src/editor-inline/styles.css`, move graph spacing from the SVG to the wrapper:

```css
.aqe-visualizer-plot {
  margin-top: 4px;
  position: relative;
}

.aqe-visualizer-svg {
  margin-top: 0;
}
```

Add toolbar styles:

```css
.aqe-selection-toolbar {
  align-items: center;
  background: Canvas;
  border: 1px solid ButtonBorder;
  border-radius: 8px;
  box-shadow: 0 3px 10px color-mix(in srgb, currentColor 18%, transparent);
  display: flex;
  gap: 2px;
  height: 30px;
  padding: 2px;
  position: absolute;
  transform: translate(calc(-100% + 6px), 4px);
  z-index: 4;
}

.aqe-selection-toolbar[hidden],
.aqe-selection-toolbar-dot[hidden] {
  display: none;
}

.aqe-selection-toolbar-button {
  border-radius: 6px;
  height: 26px;
  min-height: 26px;
  min-width: 26px;
  padding: 0;
  width: 26px;
}
```

Use CSS custom properties from the renderer for placement:

```css
.aqe-selection-toolbar,
.aqe-selection-toolbar-dot {
  left: var(--aqe-selection-end-px, 0);
  top: var(--aqe-selection-bottom-px, 0);
}
```

If CSS-only clamping is unreliable in the embedded WebEngine, compute clamped `left`/`top` in TypeScript and set `--aqe-selection-toolbar-left-px` / `--aqe-selection-toolbar-top-px` explicitly.

- [ ] **Step 5: Add the collapsed dot and halo CSS**

Add:

```css
.aqe-selection-toolbar-dot {
  background: Highlight;
  border: 2px solid Canvas;
  border-radius: 999px;
  box-shadow: 0 0 0 4px color-mix(in srgb, Highlight 24%, transparent);
  height: 22px;
  padding: 0;
  position: absolute;
  transform: translate(-50%, 6px);
  width: 22px;
  z-index: 4;
}

.aqe-selection-toolbar-dot:hover,
.aqe-selection-toolbar-dot:focus-visible {
  box-shadow: 0 0 0 7px color-mix(in srgb, Highlight 34%, transparent);
  outline: none;
}
```

If `color-mix(...)` is not supported by Anki's WebEngine, replace it with static rgba colors after visual verification.

- [ ] **Step 6: Add preview CSS**

For Delete Region hover/focus:

```css
.aqe-visualizer[data-selection-toolbar-preview="region"] .aqe-selection {
  fill: #dc2626;
  fill-opacity: 0.24;
  stroke: #dc2626;
  stroke-opacity: 0.9;
}
```

For Delete the rest hover/focus, add two absolute overlay divs inside `.aqe-visualizer-plot` if needed:

```svelte
<div class="aqe-selection-rest-preview aqe-selection-rest-preview-before" aria-hidden="true"></div>
<div class="aqe-selection-rest-preview aqe-selection-rest-preview-after" aria-hidden="true"></div>
```

and CSS:

```css
.aqe-selection-rest-preview {
  background: rgba(220, 38, 38, 0.18);
  border-color: rgba(220, 38, 38, 0.55);
  display: none;
  pointer-events: none;
  position: absolute;
  top: calc(var(--aqe-plot-top-px, 10px));
  z-index: 3;
}

.aqe-visualizer[data-selection-toolbar-preview="rest"] .aqe-selection-rest-preview {
  display: block;
}

.aqe-selection-rest-preview-before {
  left: calc(var(--aqe-plot-left-px, 44px));
  width: max(0px, calc(var(--aqe-selection-start-px, 44px) - var(--aqe-plot-left-px, 44px)));
}

.aqe-selection-rest-preview-after {
  left: var(--aqe-selection-end-px, 0);
  right: calc(var(--aqe-plot-right-px, 10px));
}
```

Renderer should publish `--aqe-plot-left-px`, `--aqe-plot-right-px`, `--aqe-plot-top-px`, and `--aqe-plot-height-px` if the preview overlays need exact plot area boundaries.

- [ ] **Step 7: Run targeted tests**

Run:

```bash
cd settings_ui
npm run test -- tests/editor-inline.selection-toolbar.integration.test.ts tests/editor-inline.selection-delete.integration.test.ts tests/editor-inline.selection-playback.integration.test.ts
```

Expected: PASS for frontend toolbar behavior. If a positioning assertion fails because jsdom has zero wrapper dimensions, set SVG bounds through `setGraphBounds(...)` and derive from SVG rect only.

## Task 5: Redraw, Busy, Accessibility, And Visual QA

**Files:**
- Modify as needed:
  - `settings_ui/src/editor-inline/graph-actions.ts`
  - `settings_ui/src/editor-inline/actions.ts`
  - `settings_ui/src/editor-inline/control-actions.ts`
  - `settings_ui/src/editor-inline/styles.css`
  - `settings_ui/src/editor-inline/test-contract.ts`

- [ ] **Step 1: Run impact checks for any additional symbols**

If this task touches symbols not covered earlier, run GitNexus impact or document unavailable GitNexus plus `rg` caller inspection before editing.

- [ ] **Step 2: Reset toolbar state on graph redraw and track changes**

When a new graph request starts or a new track is rendered, ensure:

```ts
visualizer.dataset.selectionToolbarCollapsed = "false";
visualizer.dataset.selectionToolbarPreview = "none";
visualizer.dataset.selectionToolbarSelectionKey = "";
```

Then call `syncSelectionToolbar(visualizer)` after the graph's final selection is established.

Do not clear the selected full-track region after generated-file redraw if current behavior intentionally selects the whole new file. The toolbar should simply hide because whole-track delete operations are invalid.

- [ ] **Step 3: Verify keyboard and pointer isolation**

Toolbar buttons must prevent graph gestures from starting:

```svelte
onpointerdown={(event) => event.stopPropagation()}
onmousedown={(event) => event.preventDefault()}
```

Use standard `button` keyboard activation; do not add custom keydown handling unless tests show WebView needs it.

- [ ] **Step 4: Verify accessible names and focus styles**

All toolbar controls must have:

- `title`,
- `aria-label`,
- visible focus indication,
- disabled state when unavailable or busy,
- no visible text label.

The collapsed dot must have `title="Expand selection actions"` and `aria-label="Expand selection actions"`.

- [ ] **Step 5: Run frontend validation**

Run:

```bash
cd settings_ui
npm run check
npm run typecheck
npm run test -- tests/editor-inline.selection-toolbar.integration.test.ts tests/editor-inline.selection-delete.integration.test.ts tests/editor-inline.selection-playback.integration.test.ts
```

Expected: all commands PASS.

## Task 6: Make E2E Coverage Pass

**Files:**
- Modify: `e2e/editor_graph_helpers.py`
- Modify: `e2e/test_editor_region_delete_workflow.py`
- Modify: `e2e/test_editor_selection_toolbar_workflow.py`

- [ ] **Step 1: Recheck the e2e graph state helper against runtime markup**

Task 1 introduced the failing e2e state fields. After the runtime toolbar exists, make sure `e2e/editor_graph_helpers.py` queries the final selector names:

```js
const toolbar = visualizer.querySelector('.aqe-selection-toolbar');
const toolbarDot = visualizer.querySelector('.aqe-selection-toolbar-dot');
const toolbarPlay = visualizer.querySelector('.aqe-selection-toolbar-play');
const toolbarDelete = visualizer.querySelector('.aqe-delete-region-button');
const toolbarDeleteRest = visualizer.querySelector('.aqe-delete-rest-button');
```

The returned fields must match the frontend test contract:

```js
selectionToolbarHidden: toolbar ? toolbar.hidden : true,
selectionToolbarCollapsed: visualizer.dataset.selectionToolbarCollapsed === "true",
selectionToolbarDotHidden: toolbarDot ? toolbarDot.hidden : true,
selectionToolbarPreview: (
  visualizer.dataset.selectionToolbarPreview === "region"
  || visualizer.dataset.selectionToolbarPreview === "rest"
) ? visualizer.dataset.selectionToolbarPreview : "none",
selectionToolbarPlayState: toolbarPlay?.dataset.aqeButtonState || "",
selectionToolbarPlayAriaLabel: toolbarPlay?.getAttribute("aria-label") || "",
selectionToolbarDeleteRegionDisabled: toolbarDelete ? toolbarDelete.disabled : true,
selectionToolbarDeleteRegionHidden: toolbarDelete ? toolbarDelete.hidden : true,
selectionToolbarDeleteRestDisabled: toolbarDeleteRest ? toolbarDeleteRest.disabled : true,
selectionToolbarDeleteRestHidden: toolbarDeleteRest ? toolbarDeleteRest.hidden : true,
regionDeleteButtonDisabled: toolbarDelete ? toolbarDelete.disabled : true,
regionDeleteButtonHidden: toolbarDelete ? toolbarDelete.hidden : true,
regionDeleteRestButtonDisabled: toolbarDeleteRest ? toolbarDeleteRest.disabled : true,
regionDeleteRestButtonHidden: toolbarDeleteRest ? toolbarDeleteRest.hidden : true,
```

- [ ] **Step 2: Keep existing delete workflow e2e passing through toolbar buttons**

Existing tests in `e2e/test_editor_region_delete_workflow.py` use `_button_selector("aqe:delete-selection")` and `_button_selector("aqe:delete-rest")`. Make toolbar delete buttons keep `data-aqe-command` so those selectors continue to work.

Update wait predicates to assert toolbar visibility:

```py
and state["selectionToolbarHidden"] is False
and state["regionDeleteRestButtonHidden"] is False
and state["regionDeleteRestButtonDisabled"] is False
```

- [ ] **Step 3: Run the toolbar e2e tests that were added in Task 1**

Run:

```bash
python3 scripts/dev.py test-e2e e2e/test_editor_selection_toolbar_workflow.py
python3 scripts/dev.py test-e2e e2e/test_editor_region_delete_workflow.py
```

Expected: targeted e2e tests PASS. If they fail, fix runtime behavior rather than weakening the assertions unless the failure shows the test is checking the wrong contract.

## Task 7: Final Quality Gate And Review

**Files:**
- All changed files from prior tasks.

- [ ] **Step 1: Run full frontend validation**

Run:

```bash
cd settings_ui
npm run validate
```

Expected: Svelte check, ESLint, TypeScript, and coverage tests PASS.

- [ ] **Step 2: Run repository checks**

Run:

```bash
python3 scripts/dev.py check
```

Expected: full reusable QC gate PASS.

- [ ] **Step 3: Run required e2e gate**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: full e2e suite PASS.

- [ ] **Step 4: Run GitNexus change detection before committing**

If GitNexus is available, run:

```text
gitnexus_detect_changes({repo: "anki-audio-tools"})
```

Expected: changed symbols are limited to inline-editor toolbar/selection/playback sync, tests, CSS, and e2e helpers. No backend audio rendering flow should be reported.

If GitNexus is unavailable, record that explicitly and include `git diff --stat` plus targeted test results in the final work log.

- [ ] **Step 5: Manual visual verification**

Open the editor UI or prototype-equivalent local bundle and verify:

- toolbar appears at the selected region's bottom-right edge,
- toolbar remains inside graph bounds near the right edge,
- buttons are 26 px icon-only controls,
- collapsed dot is 22 px blue with a subtle halo,
- dot hover/focus intensifies halo,
- Delete Region hover makes the selected region red,
- Delete the rest hover makes the outside regions red,
- text does not overlap graph labels or resize handles,
- focus states are visible in both light and dark Anki themes.

- [ ] **Step 6: Final implementation summary**

Summarize:

- files changed,
- tests run and pass/fail output,
- whether full e2e passed,
- whether GitNexus was available,
- any remaining visual or WebEngine compatibility risks.
