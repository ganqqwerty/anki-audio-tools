# Selection Floating Toolbar Design

## Goal

Move the selection-scoped graph actions to the selected region itself, so users do not need to move between the graph and the main button panel after selecting audio.

When a valid graph selection exists, show a small floating toolbar at the bottom-right edge of the selected region. The toolbar provides:

- Play/Pause
- Delete Region
- Delete the rest
- Collapse

The toolbar uses icon-only buttons with native titles and accessible labels. The collapse button hides the toolbar and leaves a small blue circular affordance with a subtle halo. Hovering the circle strengthens the halo. Clicking it expands the toolbar again.

## Current Context

The inline editor already has the underlying commands and state:

- `EditorControls.svelte` renders the graph, play button, hidden selection delete buttons, and resize handles.
- `selection-controller.ts` stores committed selection state on the visualizer dataset.
- `visualizer-renderer.ts` positions the selection band, selection edges, resize handles, and cursor.
- `region-delete-state.ts` validates the selected interval and builds region-delete requests for both operations.
- `region-delete.ts` stops playback, marks controls busy, queues the request, and sends the existing bridge command.
- `playback-actions.ts` and `playback-controller.ts` own play, pause, selected-region playback, repeat, and progress state.

The new toolbar should reuse those flows. No Python bridge, media-rendering, or command-contract change is required.

## Chosen UX

Use the approved prototype direction from `docs/prototypes/graph-selection-action-prototypes.html#chosen-floating-toolbar`.

The toolbar appears only when all of these are true:

- the graph has a rendered track,
- a committed selection exists,
- there is no draft selection gesture in progress,
- the selection is valid for region delete operations,
- the editor is not busy.

The toolbar is positioned below the selection band and right-aligned to the selection end edge. If the selection is near the right edge, the toolbar remains inside the graph bounds by clamping its right edge to the plot area. If the selection is near the bottom of the graph, the toolbar may sit just above the selection bottom rather than overflowing below the SVG viewport.

Button order is:

1. Play/Pause
2. Delete Region
3. Delete the rest
4. Collapse

All buttons are small icon-only controls. Tooltips, `title`, and `aria-label` text identify each action. The Play/Pause icon follows playback state: play when stopped or paused, pause when selected-region playback is active.

Collapsing does not clear the selection and does not change playback. It only replaces the toolbar with the blue halo circle. The collapsed state is local to that graph selection. Creating a new selection, clearing the selection, changing fields, or redrawing the graph resets the toolbar to expanded.

## Hover Previews

The toolbar should keep the prototype's preview behavior:

- Hovering or focusing **Delete Region** makes the selected region red.
- Hovering or focusing **Delete the rest** makes the non-selected audio before and after the selection red.

The preview is visual only. It must not alter selection state, playback region state, pending delete requests, or cursor state.

Preview state clears on mouse leave, blur, button click, selection clear, selection resize, graph redraw, and busy-state changes.

## Architecture

Keep the implementation inside the inline-editor frontend.

Expected responsibilities:

- `EditorControls.svelte`: render the toolbar markup inside a positioned wrapper around the SVG.
- `visualizer-renderer.ts`: update CSS custom properties and data attributes that locate the toolbar and preview regions from the current selection start/end.
- `region-delete-state.ts`: remain the source of truth for whether Delete Region and Delete the rest are available. Export a shared availability helper used by the toolbar and request builder.
- `region-delete.ts`: continue sending both delete operations. Toolbar buttons should call the same `sendRegionDelete(...)` path as the current buttons.
- `playback-actions.ts` / `playback-controller.ts`: continue owning playback transitions. The toolbar play button should call `send("aqe:play", target.node, target.ord)` so it goes through the same HTML/native playback routing as the existing play split button primary action.
- `styles.css`: define toolbar positioning, icon-only button styling, collapsed circle, halo states, tooltip behavior, and red preview fills.
- `test-contract.ts`: expose toolbar visibility, collapsed state, active play state, and preview state for integration tests.

The toolbar should not duplicate backend operation logic. It is an alternate local control surface over existing commands.

## DOM And Positioning

Add a graph-local overlay container inside `.aqe-visualizer` by wrapping the SVG:

```html
<div class="aqe-visualizer-plot">
  <svg class="aqe-visualizer-svg">...</svg>
  <div class="aqe-selection-toolbar">...</div>
  <button class="aqe-selection-toolbar-dot">...</button>
</div>
```

The wrapper should be `position: relative`. The SVG remains the pointer target for graph gestures. The toolbar and dot are absolutely positioned over the same plot area with a higher z-index.

`renderSelection(...)` already computes `startX` and `endX` in SVG viewBox coordinates. It should also publish toolbar coordinates as pixel CSS custom properties on the plot wrapper:

- `--aqe-selection-start-px`
- `--aqe-selection-end-px`
- `--aqe-selection-bottom-px`

The renderer should read the rendered SVG box, convert viewBox coordinates to wrapper-relative pixels, and clamp the toolbar anchor inside the plot width. This avoids depending on newer CSS math support in Anki's embedded WebEngine.

The overlay must not shift layout when it appears, collapses, or changes play state.

## Action Semantics

### Play/Pause

Clicking toolbar Play/Pause does the same thing as clicking the existing play split button's primary action:

- stopped + selection: start selected-region playback from selection start,
- playing: pause current playback,
- paused: resume unless existing playback state requires restart,
- repeat mode continues to use existing repeat behavior.

The toolbar play state mirrors the canonical visualizer playback state. It must update when playback changes from any path, including the main play button, native callbacks, HTML audio callbacks, graph gestures, resize gestures, and Python playback callbacks.

### Delete Region

Clicking Delete Region sends the existing `delete-selection` operation through `sendRegionDelete("button", ...)`.

Backspace remains unchanged. It still triggers Delete Region only when the focused graph has a valid selection.

### Delete the rest

Clicking Delete the rest sends the existing `delete-rest` operation through `sendRegionDelete("button", ..., "delete-rest")`.

No new keyboard shortcut is added.

### Collapse And Expand

Clicking Collapse hides the toolbar and shows the blue dot. The dot is positioned at the bottom-right selection edge, using the same anchor as the toolbar.

Clicking the dot expands the toolbar. The expanded toolbar should restore the current canonical button states, not stale states from before collapse.

## Existing Main Panel Buttons

The current revealed Delete Region and Delete the rest buttons in the main controls panel should be removed as visible controls and replaced by toolbar buttons. Tests should target the toolbar buttons instead of panel buttons.

The chosen behavior is: when a selection exists, Delete Region and Delete the rest are visible in the graph-local toolbar only. The main play button remains visible because it is a global editor control, but the toolbar provides the nearby selection-scoped play/pause shortcut.

## Accessibility

Each toolbar button must have:

- a stable `data-testid`,
- a `title`,
- an `aria-label`,
- keyboard focus styles,
- disabled state when the operation is unavailable or the editor is busy.

Suggested labels:

- Play/Pause: `Play selection` or `Pause selection`, matching current state.
- Delete Region: `Delete selected region`
- Delete the rest: `Delete audio outside selected region`
- Collapse: `Collapse selection actions`
- Expand dot: `Expand selection actions`

The toolbar should be reachable by tab navigation when visible. The collapsed dot should be reachable by tab navigation when collapsed. The dot's halo must not be the only state signal; it also needs an accessible label.

## Styling

Use these existing editor and Anki-compatible colors:

- toolbar background: `Canvas`,
- border: `ButtonBorder`,
- button foreground: `currentColor`,
- destructive hover: red/danger color already used in prototypes,
- collapsed dot: stable blue with light/dark halo variants.

Buttons should be smaller than the main control buttons: 26 px square for toolbar buttons and 22 px square for the collapsed dot. The toolbar must keep a stable size when Play changes to Pause.

Cards or nested panels are not needed. The toolbar should read as a small utility surface attached to the selection.

## Data Flow

Selection creation, resize, clear, graph redraw, busy state, and playback state already mutate visualizer datasets. The toolbar should derive from those canonical datasets:

- selection active/start/end,
- draft active/start/end,
- duration,
- graph busy / global busy,
- playback state,
- playback region mode,
- source filename.

On every selection-affecting update:

1. render the SVG selection as today,
2. update toolbar coordinates,
3. show or hide the toolbar/dot based on selection validity,
4. clear transient preview classes,
5. reset collapsed state if the committed selection changed.

On every playback state update:

1. update the existing play button as today,
2. update toolbar Play/Pause icon, label, and pressed state.

On every region-delete availability update:

1. update toolbar Delete Region and Delete the rest disabled states,
2. keep title/aria labels accurate,
3. hide or disable the toolbar for whole-clip selections.

## Error Handling

If a toolbar action is clicked while state has become invalid, the action should no-op through the existing guards:

- no selection,
- whole-clip selection,
- missing source filename,
- busy editor,
- stale visualizer,
- invalid operation.

The frontend must not build a delete request from cached toolbar data. It should re-read current visualizer state through the existing request builder at click time.

## Testing

Use test-first implementation where practical.

### TypeScript / Integration Tests

Add or update tests for:

- toolbar hidden with no graph track,
- toolbar hidden with no committed selection,
- toolbar visible for a valid committed selection,
- toolbar hidden during draft selection gestures,
- toolbar coordinates update after selection creation,
- toolbar coordinates update after resize,
- toolbar remains within graph bounds near the right edge,
- toolbar buttons are icon-only but have titles and aria labels,
- Play/Pause button dispatches the existing play flow,
- Play/Pause icon and aria label update when playback starts, pauses, resumes, and stops,
- Delete Region queues the same `delete-selection` request as the existing button,
- Delete the rest queues the same `delete-rest` request as the existing button,
- Backspace behavior is unchanged,
- Collapse hides toolbar and shows dot,
- dot hover class/state intensifies the halo,
- clicking dot expands toolbar,
- new selection resets collapsed state to expanded,
- busy state disables or hides toolbar actions,
- whole-clip selection does not enable destructive actions.

### Preview Tests

Add focused tests for:

- hovering/focusing Delete Region adds the selected-region danger preview,
- leaving/blurring Delete Region clears the preview,
- hovering/focusing Delete the rest adds outside-region danger previews,
- leaving/blurring Delete the rest clears the preview,
- clicking either delete action clears preview while the existing delete flow proceeds,
- previews are scoped per field and do not affect another visualizer.

### E2E Tests

Add at least one end-to-end browser/Anki test for the full workflow:

- render a graph,
- create a mid-clip selection,
- verify toolbar appears near the selected region,
- click Play/Pause from the toolbar and confirm selected playback state,
- hover Delete Region and verify selected band preview,
- hover Delete the rest and verify outside-region preview,
- collapse toolbar, verify blue dot appears,
- hover dot, verify halo intensifies,
- click dot, verify toolbar returns,
- click Delete the rest and confirm the existing generated-file workflow still succeeds.

Keep existing region-delete and playback e2e tests as backend behavior protection.

## Risks

The main UX risk is visual clutter over the graph. Keeping the toolbar small, icon-only, bottom-aligned, and collapsible reduces that risk.

The main implementation risk is state drift between the toolbar and existing controls. The design avoids this by deriving toolbar state from the visualizer dataset and by reusing existing playback and delete request paths.

The main interaction risk is conflict with graph gestures and resize handles. The toolbar must use pointer targets outside the resize handles and stop pointer events from starting graph scrubs or selection gestures.

## Out Of Scope

- New backend commands.
- New audio rendering behavior.
- A keyboard shortcut for Delete the rest.
- Persistent user preference for collapsed/expanded toolbar.
- Moving the selected region by dragging the selection band.
- Replacing the main play button or play split menu.
