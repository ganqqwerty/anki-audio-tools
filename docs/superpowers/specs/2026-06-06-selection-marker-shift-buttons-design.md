# Selection Marker Shift Buttons Design

Date: 2026-06-06
Status: Proposed

## Goal

Add opt-in selection-edge controls that let the user snap either side of the current selection band to the previous or next chorusing marker without dragging, while preserving the current selection, playback, zoom, tooltip, and marker-editing behavior.

## Scope

This design covers:

- a single settings toggle that enables or disables selection marker shift buttons
- four edge-mounted triangle buttons around the committed selection band
- button availability, disabled reasons, hover treatment, and tooltip copy
- marker-based snapping rules for the selection start and selection end
- narrow-band layout behavior
- frontend and Python config plumbing needed to persist the toggle into the inline editor runtime
- unit, frontend integration, Python, and e2e coverage for the feature

This design does not cover:

- changes to graph analysis payloads or prosody-analysis settings
- new marker types beyond the existing chorusing markers
- keyboard shortcuts for marker-based selection shifting
- changes to the chorusing toolbar or chorusing practice workflow beyond staying compatible with this feature

## User-Facing Outcome

When the feature toggle is on and a committed selection is visible on the graph, the selection band gains four small triangle buttons:

- left edge outer `◀`: move selection start to the previous marker
- left edge inner `▶`: move selection start to the next marker
- right edge inner `◀`: move selection end to the previous marker
- right edge outer `▶`: move selection end to the next marker

Each button moves only its own edge. The opposite edge stays fixed.

The feature is intentionally opt-in. Existing users should see no new graph chrome until they enable it in settings.

## Interaction Rules

### Visibility

Buttons are shown only when all of the following are true:

- the new setting is enabled
- the graph has a rendered track
- a committed selection exists
- no draft selection is active

Buttons for a given edge are hidden when that edge is outside the visible viewport.

If the band becomes too narrow for both inner buttons to coexist without overlap, hide the inner pair and keep the outer pair visible.

### Movement semantics

Each click resolves a real chorusing marker from the current marker list and applies that marker directly to the targeted edge.

- moving the start edge uses the chosen marker as the new `selectionStartMs`
- moving the end edge uses the chosen marker as the new `selectionEndMs`

The move must still satisfy the existing selection rules:

- the selection stays inside the graph duration
- the start edge never moves beyond the end edge
- the end edge never moves before the start edge
- minimum selection duration rules continue to apply exactly as they do for drag-resize

The system must recompute targets from the current marker list on every sync so marker additions and removals immediately affect button state.

### Disabled behavior

Buttons remain visible but disabled when their edge is visible and the feature is enabled, but no valid move exists in that direction.

Examples:

- no earlier marker exists for that edge
- no later marker exists for that edge
- the candidate marker would collide with or cross the opposite edge
- the candidate marker would violate minimum selection duration

Disabled buttons do nothing on click.

### Tooltip behavior

Tooltip copy should follow the existing disabled-clarification pattern used elsewhere in the editor UI.

Enabled examples:

- `Move selection start to previous marker`
- `Move selection start to next marker`
- `Move selection end to previous marker`
- `Move selection end to next marker`

Disabled reasons should be appended to the base action, for example:

- `No earlier marker is available.`
- `No later marker is available.`
- `That marker would cross the other selection edge.`
- `That marker would make the selection too short.`

### Hover and pointer behavior

Hover should add a lightweight emphasis consistent with the existing resize handles. It should not cause layout shift.

Buttons must stop pointer propagation so they do not start cursor drags or selection gestures when clicked.

## Settings Model

Add one persisted config key:

- `selection_marker_shift_buttons_enabled`: boolean

Recommended default:

- `false`

Rationale:

- the feature adds persistent graph controls that not every user will want
- default-off avoids surprising existing users and keeps current visuals unchanged after upgrade

## Architecture

### Keep graph-analysis contracts unchanged

This setting is UI-only. It should not be added to graph analysis request payloads and should not be mixed into `GraphSettings`.

Specifically, this feature should not change:

- `settings_ui/src/editor-inline/graph-settings.ts`
- prosody-analysis settings builders in Python
- graph request payload shape used by analysis callbacks

### Persist the toggle through the normal config path

The new config key should flow through the same layers as other inline editor defaults:

- `addon/anki_audio_quick_editor/config.schema.json`
- `addon/anki_audio_quick_editor/config.json`
- settings initial-state builders and fixtures in Python
- `settings_ui/src/settings/settings-state.ts`
- generated contracts via `python3 scripts/dev.py contracts-generate`
- `addon/anki_audio_quick_editor/editor_ui.py`
- `addon/anki_audio_quick_editor/editor_webview_injection.py`
- `settings_ui/src/editor-inline/types.ts`

### Runtime ownership

The inline editor already receives runtime defaults through `window.__AQE_EDITOR_CONFIG__`. The new setting should enter the runtime through that path, then be stamped onto each visualizer as DOM state during graph component setup.

The renderer and button-state sync code should read visualizer DOM state rather than reaching back into `window.__AQE_EDITOR_CONFIG__`.

### Rendering approach

Use HTML overlay buttons, not SVG buttons.

Rationale:

- existing tooltip and disabled-state patterns are already built around HTML buttons
- accessibility semantics are simpler with real buttons
- the selection toolbar already establishes a precedent for absolute-positioned controls layered over the graph

Add a small overlay component beside the existing selection toolbar inside `GraphVisualizer.svelte`. The overlay should own the static button markup and tooltip wiring. Dynamic positioning and availability should stay outside Svelte reactivity and be synchronized by the existing imperative visualizer flow.

### State and geometry split

Add a pure helper module for marker-shift decisions. It should answer:

- which previous or next marker is relevant for a given edge
- whether the move is valid
- what disabled reason applies if it is not

Keep rendering logic separate from marker-selection logic.

Extend the selection renderer to publish the overlay geometry it already knows:

- edge anchor positions
- whether each edge is visible
- whether the band is narrow enough to hide inner buttons

Add a small state-sync module for the four shift buttons. It should:

- read current selection state
- read current chorusing markers
- read busy and draft-selection state
- read overlay geometry from the visualizer wrapper
- update each button’s `hidden`, `disabled`, `aria`, and tooltip content

### Mutation path

Do not invent a parallel selection-update path.

Button clicks should route through the existing selection mutation infrastructure:

- button click
- action entrypoint in the inline editor frontend
- marker-shift helper resolves a target marker
- existing `setSelection(...)` path applies the new range

That keeps the current behavior intact for:

- redraw
- playback-region updates
- selection changed events
- chorusing marker row refresh
- selection toolbar sync

## Edge Cases

- No committed selection: no buttons.
- Draft selection active: no buttons.
- No chorusing markers: buttons for visible edges remain visible but disabled with the relevant no-marker reason.
- Marker list changes while buttons are visible: the next sync recomputes state from the current marker array with no cached marker indices.
- Zoomed viewport hides one edge: that edge’s buttons disappear, the visible edge continues to work.
- Very narrow selections: inner pair is hidden, outer pair remains visible.
- Existing chorusing practice state: moving an edge must continue to use the current selection mutation path so downstream chorusing state remains internally consistent.

## Testing

### Frontend unit tests

Add pure unit coverage for the marker-shift helper:

- previous and next marker resolution for start and end edges
- empty marker list
- candidate blocked by the opposite edge
- candidate blocked by minimum duration
- rounded or duplicate markers after normalization

Extend visualizer rendering tests to cover:

- overlay anchor geometry publication
- inner-button hiding for narrow bands
- hidden geometry reset when selection disappears

### Frontend integration tests

Add dedicated integration coverage around the inline editor graph for:

- moving selection start to previous and next markers
- moving selection end to previous and next markers
- disabled state when no valid marker exists
- disabled tooltip reason copy
- hidden inner pair on narrow selections
- viewport clipping behavior when only one edge is visible
- marker add and marker removal after the selection already exists
- suppression while draft selection is active
- compatibility with playback state after a shift move

Extend the frontend test contract to expose shift-button visibility, disabled state, and tooltip content so tests can assert behavior without brittle DOM traversal.

### Python tests

Update Python coverage for:

- settings initial-state payloads
- editor injection config payloads
- config defaults and schema expectations

The new setting should be verified both in the settings dialog initial state and in the inline editor runtime config embedded into the editor webview script.

### E2E tests

Add real end-to-end coverage, not just unit and integration coverage.

Required e2e scenarios:

- enable the setting in Settings, reopen or refresh the editor surface, and verify the buttons appear for a committed selection
- disable the setting and verify the buttons do not appear
- create a selection, add markers, and shift each edge by marker buttons inside a live Anki editor session
- verify the inner pair hides for a narrow selection
- verify marker edits after selection creation immediately change button availability
- verify the feature does not let the user move an edge outside the graph or through the other edge

The feature is not complete until the relevant e2e coverage exists and `python3 scripts/dev.py test-e2e` passes.

## Acceptance Criteria

- When the setting is off, no selection marker shift buttons are rendered.
- When the setting is on and a committed selection is visible, the correct edge buttons appear and track the selection band during redraw and zoom.
- Every successful click snaps to an actual current chorusing marker.
- Invalid moves are disabled rather than partially applied.
- Tooltip and disabled behavior match existing editor conventions.
- Existing selection resize, playback, zoom, and chorusing workflows continue to work.
- Unit, frontend integration, Python, and e2e tests cover the new behavior.
