# Back-Chaining Main Toolbar Design

## Goal

Move back-chaining practice out of the selected-region submenu and make it a whole-file editor toolbar workflow with always-editable markers.

## Scope

In scope:

- Remove the selected-region Back-chaining submenu and panel.
- Remove Clear markers, Move to shorter suffix, and Edit markers actions.
- Add two configurable main editor toolbar commands: Practice/Pause Back-chaining and Longer suffix.
- Treat marker editing as always available while a back-chaining session exists.
- Support marker additions and removals during active practice.
- Restrict back-chaining practice to the whole audio file.
- Update settings, config schema, generated contracts, localization, frontend tests, Python config tests, and e2e tests.

Out of scope:

- Persisting back-chaining markers.
- Supporting practice on graph selections.
- Adding shorter-suffix navigation through keyboard shortcuts or hidden UI.
- Changing Python playback transport semantics beyond the existing `source: "back_chaining"` request path.

## Approved UX

Back-chaining appears in the main inline editor toolbar, beside other editor buttons governed by toolbar visibility settings.

Toolbar commands:

- `aqe:back-chain-practice`: starts back-chaining practice, pauses active practice, and resumes from the active suffix.
- `aqe:back-chain-next`: moves to the longer suffix to the left.

Both commands are normal toolbar buttons and appear in Settings under "Editor toolbar buttons." Defaults include both commands so the feature remains discoverable after the submenu is removed. Users can hide either button through settings.

The selected-region toolbar keeps only selection-scoped actions such as Play selection, Delete region, Delete rest, collapse, and expand. It no longer renders Back-chaining, the back-chaining panel, or any disclosure/submenu UI.

## State Model

Remove these state concepts from the back-chaining model:

- `editing`
- `panelOpen`
- `canClear`
- `canEdit`
- `canPrevious`

Back-chaining state keeps only the data required for whole-file practice:

- active marker index,
- whole-file base region,
- marker list,
- ordinary repeat state to restore after pausing,
- practice state,
- source filename.

A back-chaining session exists when the current source file has a whole-file base region and marker list. Marker editing is available whenever that session exists, including while practice is playing or paused.

Changing source media still clears temporary back-chaining state and restores repeat state.

## Whole-File Behavior

Starting back-chaining derives the base region from the visualizer target duration:

```ts
{ startMs: 0, endMs: readVisualizerTargetDurationMs(visualizer), mode: "full" }
```

Committed graph selections are ignored for back-chaining base-region creation. The active suffix that is played may still be written into selection/playback visual state so the graph can highlight the practiced suffix, but that selection must be derived from the whole-file markers, not from the user's prior selection.

If a visualizer has no positive target duration, back-chaining start is rejected and leaves state unchanged.

Default markers are generated across the whole file using the existing three-marker strategy. The initial active marker is the rightmost marker.

## Marker Editing During Practice

Marker row clicks toggle markers whenever a session exists. The pointer handler no longer checks an edit-mode flag.

When a marker is added or removed while practice is playing or paused:

- normalize and sort the new marker list,
- keep the currently active marker when it still exists,
- otherwise clamp the active index to the nearest valid marker index,
- if no markers remain, stop practice and leave the session unable to practice until a marker is added again,
- if practice is playing and a valid active suffix still exists, restart playback for the updated active suffix.

This ensures mid-practice marker edits affect the next playback/navigation step immediately instead of being ignored.

## Settings And Contracts

Add both command IDs everywhere the toolbar command inventory is defined:

- `settings_ui/src/lib/editor-toolbar-buttons.ts`
- `addon/anki_audio_quick_editor/config.schema.json`
- `addon/anki_audio_quick_editor/config.json`
- generated Python and TypeScript contracts
- settings fallback state
- settings fixtures and Python test fixtures
- command slug tests

Default display mode is icon for both new commands. Use clear labels and titles in `addon/anki_audio_quick_editor/locales/en.json`; update other locale files with English fallback text if the project has no translation workflow for this change.

## Architecture

`settings_ui/src/editor-inline/back-chaining-state.ts` owns pure marker/index state. It should expose helpers for whole-file base creation, marker normalization, active-index normalization, and control availability.

`settings_ui/src/editor-inline/back-chaining-controller.ts` owns visualizer state transitions, marker row clicks, playback requests, and repeat restoration. It should not depend on selection-toolbar state for entry.

`settings_ui/src/editor-inline/command-actions.ts` routes the two new toolbar commands to the controller before bridge dispatch. These commands are frontend-only and must not be sent to Python as editor bridge commands.

`SelectionToolbar.svelte` should stop importing or rendering back-chaining UI. `GraphVisualizer.svelte` keeps the marker row because the row is part of the graph surface, not the removed submenu.

## Testing

Pure state tests:

- default markers use whole-file base regions,
- active index normalization handles marker insertion before, at, and after the current marker,
- active index normalization handles marker removal before, at, and after the current marker,
- no markers disables practice without throwing.

Svelte integration tests:

- the main toolbar renders `aqe:back-chain-practice` and `aqe:back-chain-next` when visible,
- the Settings visibility grid renders both commands and can toggle them,
- the selection toolbar no longer renders Back-chaining entry or a back-chaining panel,
- starting back-chaining ignores an existing committed graph selection and uses the full file,
- marker row clicks work without edit mode,
- adding a marker mid-practice changes the next longer suffix to the newly added marker,
- removing a marker mid-practice clamps the active marker index predictably.

Python/config tests:

- config schema accepts both new command IDs in `visible_editor_buttons` and `editor_button_modes`,
- settings save sanitization keeps the new command IDs and drops stale IDs,
- editor config injection includes both default visible buttons and button modes.

E2E tests:

- whole-file back-chaining starts from the rightmost default marker and loops to the end of the file,
- committed graph selections do not limit back-chaining practice,
- marker placement still respects zoomed viewport time,
- marker row still does not steal top-of-graph cursor drag,
- adding a marker mid-practice is reflected by the next longer-suffix action.

Verification target:

- `python3 scripts/dev.py test-svelte`
- focused Python tests for config/settings/editor UI
- `python3 scripts/dev.py check`
- `python3 scripts/dev.py test-e2e`
