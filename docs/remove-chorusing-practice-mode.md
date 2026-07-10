# Remove Dedicated Chorusing Practice Mode

## Summary

The dedicated `Play chorusing` button is not carrying enough unique behavior to justify a separate playback mode. In the current implementation, chorusing practice is a bundle of three independent capabilities:

- marker navigation changes the selection start while keeping the right edge stable,
- normal repeat playback loops the current selected region,
- auto-advance performs the same left-limit movement after a configured number of completed repeats.

The proposed target is to remove `aqe:chorusing-practice` as a mode command and keep chorusing as a marker/navigation layer over ordinary selected playback. The user workflow becomes:

1. Use marker back/forward buttons to choose the current suffix.
2. Use the normal Play button to play the selected suffix.
3. Use the normal Repeat toggle to loop it.
4. Enable auto-advance in the Play menu to move the selection start one marker left after N repeats.

This would simplify both the UI and the state model: there is no separate chorusing playback source, no special pause/resume path, no restoration of the user's ordinary repeat setting, and no need for generic playback to know that a hidden practice mode is active.

## Current Code Shape

### UI surface

The chorusing panel is currently defined as an atomic-ish toolbar panel containing three commands:

- `aqe:chorusing-practice`
- `aqe:chorusing-next`
- `aqe:chorusing-previous`

Relevant files:

- `settings_ui/src/lib/editor-toolbar-panel-definitions.ts`
- `settings_ui/src/editor-inline/EditorControls.svelte`
- `settings_ui/src/editor-inline/ChorusingSplitButton.svelte`
- `settings_ui/src/editor-inline/chorusing-toolbar.ts`

`EditorControls.svelte` special-cases `aqe:chorusing-practice` and renders `ChorusingSplitButton`. That split button owns settings that mostly overlap with the Play split button:

- `chorusingPauseSeconds`
- `chorusingAutoAdvance`
- `chorusingRepeatCount`

Meanwhile `PlaySplitButton.svelte` already owns the normal repeat toggle and `repeatPauseSeconds`.

### Runtime state

`settings_ui/src/editor-inline/chorusing-state.ts` and `chorusing-controller.ts` currently mix several concepts into one state object:

- marker model: `baseRegion`, `markersMs`, `sourceFilename`
- selection/suffix model: `activeMarkerIndex`, `activeStartMs`, `activeEndMs`
- playback mode: `practiceState`
- repeat accounting: `repeatPassesCompleted`
- repeat restoration: `ordinaryRepeatEnabled`

That shape makes sense only because `Play chorusing` is modeled as a separate mode. Without the mode, the active suffix should mostly be derived from the normal editor selection:

- current right limit = current `selection.endMs`
- current left limit = current `selection.startMs`
- active marker = exact marker at `selection.startMs`, or nearest marker navigation target relative to `selection.startMs`

The one stateful piece that remains is the auto-advance repeat counter.

### Playback coupling

`command-actions.ts` currently intercepts normal play:

```ts
if (command === "aqe:play" && pauseChorusingForNormalPlay(ord)) {
  return;
}
```

That means pressing Play while chorusing is active does not play; it pauses chorusing. This is a clear signal that chorusing is fighting the user's real primary action.

`startPracticePlayback()` also forces repeat on and starts an HTML request with `source: "chorusing"`. The frontend and Python backend then special-case that source:

- `actions-audio-clock.ts` calls `handleChorusingLoopBoundary()` only when the session request source is `chorusing`.
- `actions-playback.ts` has `chorusingPlaybackRequestForCurrentSuffix()` to preserve chorusing source after cursor movement.
- `html-audio-session-controller.ts` adjusts pass start for `source === "chorusing"`.
- `editor_playback_request.py` appends "Practice mode. Use the toolbar buttons for chorusing."

All of that becomes unnecessary if auto-advance is a generic selected-repeat behavior instead of a chorusing playback source.

### Marker model already works outside playback

The marker row is installed by `GraphVisualizer.svelte` and `installChorusingHandlers()` as soon as the graph exists. Tests already assert that the marker row is editable before practice starts. That means marker placement is not inherently a playback mode. It can remain as a graph annotation/navigation feature.

## Recommended Product Model

### Commands

Keep two marker navigation commands, but make their behavior independent from practice state:

- Back / longer suffix: move `selection.startMs` to the nearest marker strictly left of the current selection start.
- Forward / shorter suffix: move `selection.startMs` to the nearest marker strictly right of the current selection start and strictly left of `selection.endMs`.

If there is no active selection, Back should initialize the selection to the rightmost suffix:

- `selection.startMs = last marker before audio end`
- `selection.endMs = audio duration`

That replaces the old "start chorusing" entry point without starting playback. The user can inspect the selection, then press Play.

The current command names are confusing because `aqe:chorusing-next` means "longer suffix" and `aqe:chorusing-previous` means "shorter suffix". During implementation, prefer explicit internal names such as:

- `aqe:selection-start-left`
- `aqe:selection-start-right`

The visible labels can be user-facing:

- "Back"
- "Forward"
- or "Longer" / "Shorter" if we want to keep the suffix language.

### Play menu

Move auto-advance settings into `PlaySplitButton.svelte`, next to Repeat:

- Repeat checkbox: existing `repeatPlaybackByDefault` / runtime repeat.
- Pause between repeats: existing `repeatPauseSeconds`.
- Auto-advance checkbox: new selected-playback auto-advance setting.
- Repeat count before auto-advance: selected-playback auto-advance threshold.

This makes auto-advance explicitly part of repeated playback. There should not be a separate `chorusingPauseSeconds`; a repeated selected region should have one repeat pause value regardless of whether auto-advance is enabled.

### Settings

Move the auto-advance defaults away from the `aqe:chorusing-practice` settings block. Recommended mapping:

- Keep `repeat_pause_seconds` as the only pause-between-repeats setting.
- Rename or re-home `chorusing_auto_advance_by_default` to a Play setting. A schema-compatible migration can keep the existing config key initially and expose it under Play UI.
- Rename or re-home `chorusing_auto_advance_repeats` the same way.
- Keep `chorusing_marker_interval_ms` for marker generation, but consider renaming later to `selection_marker_interval_ms` or `suffix_marker_interval_ms`.
- Remove `chorusing_pause_seconds` after a compatibility window, or migrate it into `repeat_pause_seconds` only if the user had not explicitly edited normal repeat pause.

The low-risk first pass is to keep the existing config keys but present them in the Play settings UI. A later config cleanup can rename keys with a migration.

## Proposed Architecture

### Split the current chorusing state into two concepts

Replace the mode-shaped `ChorusingState` with a marker/navigation state:

```ts
interface SelectionMarkerState {
  baseRegion: PlaybackRegion | null;
  markersMs: number[];
  sourceFilename: string;
  repeatPassesCompleted: number;
}
```

Then derive the active suffix from the normal selection:

```ts
interface ActiveSuffix {
  startMs: number;
  endMs: number;
}
```

The selection controller remains the source of truth for left and right limits. Marker navigation writes selection. Playback reads selection. Auto-advance writes selection after the repeat threshold is reached.

This removes the need for:

- `practiceState`
- `ordinaryRepeatEnabled`
- most uses of `activeMarkerIndex`
- most uses of `activeStartMs` and `activeEndMs`
- `chorusingPlaybackRequestForCurrentSuffix()`

The repeat counter can live in the marker state or in `visualizer-runtime-state.ts`. It should reset on:

- manual marker navigation,
- user selection edit,
- normal Play start for a different pass,
- source file change.

It should not reset on marker add/remove.

### Make auto-advance a generic playback boundary hook

Today, `handleChorusingLoopBoundary()` is only considered for `source: "chorusing"`. Replace that with a generic selected-repeat hook:

```ts
handleSelectionAutoAdvanceBoundary(visualizer, pass)
```

It should run before normal repeat restarts when all of these are true:

- repeat is enabled,
- auto-advance is enabled for the field,
- playback is selected-region playback,
- the active playback pass matches the current selection,
- markers exist for the current source,
- the current selection has a stable right limit.

Decision flow:

1. Increment `repeatPassesCompleted`.
2. If completed count is below threshold, let normal repeat continue.
3. If threshold is reached, find the nearest marker strictly left of `selection.startMs`.
4. If found, set `selection.startMs` to that marker, preserve `selection.endMs`, reset counter, and restart selected playback from the new start.
5. If not found, stop or pause playback at the leftmost suffix.

The current leftmost behavior pauses chorusing instead of wrapping. I would preserve "do not wrap", but the exact generic-playback behavior needs a product decision: should Play become stopped, paused, or still playing with repeat disabled?

### Marker edits become simpler

Removing the mode makes marker edits easier to reason about:

- Add marker left of the selection: no immediate playback effect; later Back or auto-advance can use it.
- Add marker inside selection: no immediate playback effect; Forward can use it.
- Add marker right of selection: no immediate playback effect.
- Remove marker at current selection start: no hidden active marker needs preserving. The current selection remains where the user left it, and the next auto-advance naturally chooses the next marker strictly left.

This avoids the special "removed current marker but keep current cycle anchored" state currently needed in `chorusing-controller.ts`.

### Normal Play remains normal Play

Remove the `pauseChorusingForNormalPlay()` interception. Pressing Play should always mean:

- start selected playback if a selection exists,
- otherwise start full-source playback,
- pause/resume if already playing according to the existing Play semantics.

Auto-advance only has an effect when the pass is selected-region playback and repeat is on.

## Expected Simplifications

### Frontend source files

Likely removals or major reductions:

- `settings_ui/src/editor-inline/ChorusingSplitButton.svelte`: remove.
- `settings_ui/src/editor-inline/chorusing-toolbar.ts`: reduce to marker navigation button sync, or merge into a marker navigation toolbar module.
- `settings_ui/src/editor-inline/chorusing-controller.ts`: remove practice start/pause/restore paths; keep marker initialization, marker toggle, and selection-start navigation.
- `settings_ui/src/editor-inline/chorusing-state.ts`: remove mode fields and keep pure marker utilities.

Likely edits:

- `PlaySplitButton.svelte`: add auto-advance checkbox and repeat count.
- `split-button-state-*`: move chorusing auto-advance values under play/repeat state, or keep existing fields but expose them from Play.
- `actions-audio-clock.ts`: replace `handleChorusingLoopBoundary()` with generic auto-advance boundary handling.
- `playback-actions.ts` / `actions-playback.ts`: remove `chorusingPlaybackRequestForCurrentSuffix()` path.
- `html-audio-session-controller.ts`: remove `source === "chorusing"` pass-start adjustment.
- `command-actions.ts`: remove `aqe:chorusing-practice` and `pauseChorusingForNormalPlay()`.
- `control-actions.ts`: remove practice-specific disabled state; keep nav disabled state.
- `EditorControls.svelte`: remove `ChorusingSplitButton` special case.
- `editor-toolbar-panel-definitions.ts`: remove `aqe:chorusing-practice` from the panel, or rename the panel from "Chorusing" to "Markers".

### Backend/config/locales

Likely edits:

- `editor_playback_request.py`: remove chorusing-specific playback guidance.
- `editor_webview_injection.py`: keep or rename auto-advance defaults under split defaults.
- `editor_split_defaults.py`: stop treating auto-advance as a `chorusing-practice` split default.
- `config.schema.json` and generated contracts: either keep compatibility fields or migrate to new names.
- locale files: remove `editor.command.chorusing_practice.*`, rewrite panel labels/tooltips, move auto-advance copy under Play.

### Tests

The current tests are mode-oriented. They should become selected-playback tests:

- Svelte integration:
  - Back initializes the rightmost suffix without starting playback.
  - Back/Forward move only `selectionStartMs`.
  - Play + Repeat loops selected region with existing pause behavior.
  - Play + Repeat + Auto-advance moves left after N repeats.
  - Manual Back/Forward resets auto-advance counter.
  - Selection edits reset counter.
  - Marker edits do not reset counter.
  - Removing current-left marker advances left after the current cycle.

- E2E:
  - One real-Anki smoke for Back -> Play -> Repeat -> Auto-advance across suffixes.
  - One mixed workflow with manual navigation, marker add/remove, and cursor/selection changes.

The e2e helper `_click_chorusing_practice()` should disappear. Existing marker helpers remain useful.

## Migration Plan

### Phase 1: Add tests for the target behavior

Add tests that use normal Play instead of `aqe:chorusing-practice`:

- marker navigation creates/updates selection only,
- Play starts selected playback,
- auto-advance works on normal repeated selected playback,
- generic Play is not intercepted by any practice state.

Keep existing chorusing tests initially so the regression surface is visible.

### Phase 2: Extract marker/navigation utilities

Rename or wrap the pure parts of `chorusing-state.ts` around selection markers:

- marker normalization,
- default marker generation,
- marker toggle,
- nearest marker left/right of selection start,
- navigation availability.

Avoid changing command/UI labels in this phase. The goal is to isolate mode-independent logic first.

### Phase 3: Move auto-advance into generic playback

Introduce `selection-auto-advance` logic called from the playback boundary path. It should use:

- current field selection,
- current repeat settings,
- auto-advance settings,
- marker state.

At this point, normal selected playback can auto-advance without `source: "chorusing"`.

### Phase 4: Remove the practice command

Remove:

- `aqe:chorusing-practice`,
- `ChorusingSplitButton.svelte`,
- `toggleChorusingForOrd()`,
- `startPracticePlayback()`,
- `pauseChorusingForNormalPlay()`,
- `ordinaryRepeatEnabled`,
- `practiceState`,
- `source: "chorusing"` playback request paths.

Move the auto-advance controls to the Play popover and update settings.

### Phase 5: Rename user-facing concepts

After behavior is stable, rename UI copy away from "chorusing mode":

- panel: "Markers" or "Practice markers",
- navigation: "Back" and "Forward", or "Longer" and "Shorter",
- setting: "Auto-advance selected repeat".

This phase should include locale updates and screenshots/gifs if the settings toolbar demo depends on the old panel.

## Open Decisions

1. At the leftmost marker, when auto-advance reaches the threshold, should normal playback stop, pause, or continue repeating the full selected suffix? I recommend stop/pause without wrapping, matching the current no-wrap behavior.
2. If the user enables auto-advance but has no selection, should Play ignore auto-advance or should it initialize the rightmost suffix automatically? I recommend ignoring auto-advance until a selection exists; Back is the explicit selection initializer.
3. Should marker interval remain under graph/marker settings or move into the Play menu? I recommend keeping marker interval with graph/marker settings, not Play.
4. Should old config keys be renamed now or only re-homed in UI? I recommend re-home first, rename later with a migration.

## Recommendation

Proceed with this refactor. The current dedicated mode creates accidental complexity:

- duplicate repeat pause settings,
- special playback source,
- Play button interception,
- hidden active suffix state separate from selection,
- backend status copy for a frontend-only practice mode,
- a larger test matrix because normal playback and chorusing playback can diverge.

The simpler model is: markers choose the selection, Play plays the selection, Repeat repeats the selection, and Auto-advance changes the selection start after enough repeated passes.
